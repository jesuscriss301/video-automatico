"""
API para aislar voces de la música/instrumental de fondo — otro nodo de la
"red de APIs" de edición de video, independiente del Flujo 1.

Por qué es un servicio aparte y no un módulo más del pipeline principal:
Spleeter (el backend de calidad real) necesita TensorFlow con versiones de
numpy/protobuf viejas que chocan con FastAPI/Pydantic del proyecto de video
— lo comprobamos instalándolo ahí y rompió el otro servicio. Por eso vive en
su propio venv, con su propio requirements.txt, expuesto por HTTP como
cualquier otro nodo de la red.

Dónde encaja en el proyecto más grande:
- Flujo 2 (audio real grabado + VAD + STT): correr el audio de entrada por
  este servicio ANTES de VAD/STT mejora la transcripción cuando hay música
  de fondo, porque el modelo de voz a texto transcribe mucho mejor una pista
  de solo voz que una con música mezclada encima.
- Reutilización de música: si tienes un video de referencia y quieres
  reusar solo su música de fondo (o solo su voz), este servicio separa
  ambas por igual.

Correr con:
    source .venv/bin/activate
    uvicorn main:app --reload --port 8001
"""
from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from separator import SeparationError, get_backend

OUTPUTS_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Voice Separator API — Aislar voz de música instrumental",
    description="Sube un audio (voz + música mezcladas) y recibe dos archivos: "
    "solo la voz y solo el instrumental.",
    version="0.1.0",
)

# El modelo de Spleeter se carga una sola vez al arrancar el proceso (tarda
# unos segundos) y se reutiliza en cada request — cargarlo por request sería
# mucho más lento. Si Spleeter no está instalado en este venv, el servicio
# igual arranca: /separate devuelve 503 explicando qué falta, y
# /separate/centerchannel (el respaldo sin dependencias) sigue funcionando.
_spleeter_backend = None
_spleeter_error: str | None = None
try:
    _spleeter_backend = get_backend("spleeter")
except SeparationError as exc:
    _spleeter_error = str(exc)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "spleeter_disponible": _spleeter_backend is not None,
        "spleeter_error": _spleeter_error,
    }


@app.post("/separate")
async def separate(
    file: UploadFile = File(...),
    backend: str = "spleeter",
) -> dict:
    """Recibe un archivo de audio (wav/mp3/m4a/lo que sea que ffmpeg lea) y
    devuelve un job_id + links de descarga para la voz y el instrumental
    aislados.

    `backend`: "spleeter" (calidad real, default) o "centerchannel"
    (respaldo instantáneo sin modelo, mucho más burdo — ver separator.py).
    """
    if backend == "spleeter" and _spleeter_backend is None:
        raise HTTPException(
            status_code=503,
            detail=f"Backend 'spleeter' no disponible en este servicio: {_spleeter_error}",
        )

    job_id = uuid.uuid4().hex[:12]
    work_dir = Path(tempfile.mkdtemp(prefix=f"job_{job_id}_"))
    input_path = work_dir / (file.filename or "input.audio")

    with input_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        engine = _spleeter_backend if backend == "spleeter" else get_backend("centerchannel")
        result = engine.separate(input_path, OUTPUTS_DIR / job_id)
    except SeparationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return {
        "job_id": job_id,
        "backend": result.backend,
        "vocals_url": f"/download/{job_id}/vocals",
        "instrumental_url": f"/download/{job_id}/instrumental",
    }


@app.get("/download/{job_id}/{stem}")
def download(job_id: str, stem: str) -> FileResponse:
    if stem not in ("vocals", "instrumental"):
        raise HTTPException(status_code=400, detail="stem debe ser 'vocals' o 'instrumental'.")

    filename = "vocals.wav" if stem == "vocals" else "accompaniment.wav"
    # Spleeter/centerchannel escriben dentro de una subcarpeta con el nombre
    # del archivo de entrada normalizado; la buscamos porque no sabemos su
    # nombre exacto desde aquí.
    job_dir = OUTPUTS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="No existe ese job_id.")

    matches = list(job_dir.rglob(filename))
    if not matches:
        raise HTTPException(status_code=404, detail=f"No se encontró {filename} para ese job.")

    return FileResponse(matches[0], media_type="audio/wav", filename=f"{job_id}_{stem}.wav")
