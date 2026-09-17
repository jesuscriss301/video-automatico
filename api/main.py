"""
API mínima que expone el pipeline del Flujo 1 como un servicio — el primer
paso hacia la "red de APIs" completa. Por ahora es un solo endpoint
síncrono; cuando conectemos los Flujos 2 y 3, cada uno puede vivir como su
propio microservicio y reusar estos mismos módulos de pipeline/.

Correr con:
    uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402

from config.settings import OUTPUTS_DIR  # noqa: E402
from pipeline.models import Script  # noqa: E402
from pipeline.run import _run_pipeline  # noqa: E402

app = FastAPI(
    title="Video Editing API Network — Flujo 1",
    description="Genera un video a partir de un guion de texto + imágenes con Ken Burns, "
    "transiciones, subtítulos y audio normalizado.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/generate")
def generate(script: Script) -> dict:
    """Recibe un guion en JSON (mismo formato que examples/sample_script.json,
    pero con rutas de imagen absolutas o accesibles desde este servidor) y
    devuelve la ruta del video generado + el reporte de QA."""
    job_id = uuid.uuid4().hex[:12]
    output_path = OUTPUTS_DIR / f"{job_id}.mp4"
    work_dir = Path(tempfile.mkdtemp(prefix=f"job_{job_id}_"))

    try:
        report = _run_pipeline(script, output_path, tts_backend="piper", work_dir=work_dir)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "job_id": job_id,
        "output_path": str(output_path),
        "download_url": f"/download/{job_id}",
        "qa": report.model_dump(),
    }


@app.get("/download/{job_id}")
def download(job_id: str) -> FileResponse:
    path = OUTPUTS_DIR / f"{job_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No existe ese video.")
    return FileResponse(path, media_type="video/mp4", filename=path.name)
