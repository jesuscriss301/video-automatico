"""
API + interfaz gráfica del Flujo 1 (guion + imágenes -> video).

Levanta un servidor local que sirve dos cosas:

1. La interfaz web en `/` (ver api/static/index.html): un formulario donde
   armas el guion escena por escena — imagen, texto que se narra, descripción
   de la imagen, pausa — eliges la voz, y le das a "Generar video". Muestra el
   avance en vivo y al final reproduce el video ahí mismo.

2. La API REST que esa interfaz consume, y que también puedes llamar desde
   otro servicio (n8n, otro backend, etc.):
     POST /api/upload        sube una imagen / audio de referencia / música
     POST /api/jobs          arranca una generación (devuelve job_id)
     GET  /api/jobs/{id}     estado + avance + reporte de QA
     GET  /api/jobs/{id}/video   el mp4 (para reproducir en el navegador)
     GET  /download/{id}     el mp4 como descarga
     POST /generate          (compatibilidad) generación síncrona con un guion JSON

Correr con:
    uvicorn api.main:app --reload --port 8000
y abrir http://localhost:8000 en el navegador.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from config.settings import ASSETS_DIR, DEFAULTS, OUTPUTS_DIR, PROJECT_ROOT  # noqa: E402
from pipeline.models import Script  # noqa: E402
from pipeline.run import _run_pipeline  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"
UPLOADS_DIR = ASSETS_DIR / "uploads"
VOICES_DIR = ASSETS_DIR / "voices"
# Biblioteca de voces guardadas: un JSON con los ajustes de voz que el usuario
# quiso conservar con un nombre (incluida la ruta del audio de referencia si
# es una voz clonada), para no tener que volver a subir/configurar cada vez.
VOICES_LIBRARY = ASSETS_DIR / "voices_library.json"
for _d in (UPLOADS_DIR / "images", UPLOADS_DIR / "audio", UPLOADS_DIR / "music"):
    _d.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Video Editing API Network — Flujo 1",
    description="Genera un video a partir de un guion de texto + imágenes, con Ken Burns, "
    "transiciones, subtítulos y audio normalizado. Incluye interfaz gráfica en /.",
    version="0.2.0",
)

# Para que la interfaz pueda mostrar miniaturas de las imágenes subidas.
app.mount("/files", StaticFiles(directory=str(ASSETS_DIR)), name="files")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --------------------------------------------------------------------------
# Registro de trabajos en memoria
# --------------------------------------------------------------------------
# Un trabajo de video tarda minutos (sobre todo con clonación de voz), así que
# la interfaz no puede quedarse esperando una respuesta HTTP: se arranca el
# trabajo en un hilo, se devuelve un job_id, y la interfaz pregunta por el
# avance cada segundo. En memoria alcanza para un uso local de una persona;
# si algún día esto corre en un servidor con varios usuarios, este dict se
# reemplaza por Redis o una tabla en base de datos.
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _set_job(job_id: str, **fields: Any) -> None:
    with _jobs_lock:
        _jobs.setdefault(job_id, {"job_id": job_id}).update(fields)


def _get_job(job_id: str) -> dict[str, Any] | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


class JobRequest(BaseModel):
    """Lo que manda la interfaz al presionar 'Generar video'."""

    script: Script
    tts_backend: Literal["piper", "espeak", "chatterbox"] = "piper"
    tts_options: dict[str, Any] = Field(default_factory=dict)


def _clean_tts_options(backend: str, options: dict[str, Any]) -> dict[str, Any]:
    """Quita los campos vacíos que manda el formulario (para que cada backend
    reciba solo lo que entiende y el resto use sus valores por defecto)."""
    allowed = {
        "piper": {"voice", "speaker_id", "length_scale", "noise_scale", "noise_w_scale"},
        "espeak": {"voice", "speed_wpm", "pitch"},
        "chatterbox": {
            "voice_sample", "language_id", "exaggeration", "cfg_weight", "temperature", "device",
        },
    }[backend]
    return {
        key: value
        for key, value in options.items()
        if key in allowed and value is not None and value != ""
    }


def _run_job(job_id: str, request: JobRequest) -> None:
    output_path = OUTPUTS_DIR / f"{job_id}.mp4"
    work_dir = Path(tempfile.mkdtemp(prefix=f"job_{job_id}_"))
    started = time.time()

    def progress_cb(stage: str, pct: float) -> None:
        _set_job(job_id, stage=stage, progress=round(pct, 1))

    try:
        _set_job(job_id, status="running", stage="Arrancando", progress=1)
        options = _clean_tts_options(request.tts_backend, request.tts_options)
        report = _run_pipeline(
            request.script,
            output_path,
            request.tts_backend,
            work_dir,
            options,
            progress_cb,
        )
        # Sidecar con los datos "humanos" del video (título, voz usada, fecha).
        # El reporte de QA no los trae, y son justo los que la sección de
        # videos generados necesita mostrar aunque se reinicie el servidor.
        meta = {
            "job_id": job_id,
            "title": request.script.title,
            "tts_backend": request.tts_backend,
            "scenes": len(request.script.scenes),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "elapsed_seconds": round(time.time() - started, 1),
        }
        output_path.with_suffix(".meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        _set_job(
            job_id,
            status="done",
            stage="Listo",
            progress=100,
            elapsed_seconds=round(time.time() - started, 1),
            qa=report.model_dump(),
        )
    except Exception as exc:  # noqa: BLE001 — cualquier fallo debe llegar a la interfaz
        _set_job(
            job_id,
            status="error",
            stage="Falló",
            error=f"{type(exc).__name__}: {exc}",
            elapsed_seconds=round(time.time() - started, 1),
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


# --------------------------------------------------------------------------
# Interfaz gráfica
# --------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def ui() -> HTMLResponse:
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=500, detail="Falta api/static/index.html")
    # Se lee del disco en cada visita y se pide al navegador que no la cachee:
    # así, si se cambia el HTML de la interfaz, basta con recargar la página —
    # no hay que reiniciar el servidor ni hacer Ctrl+Shift+R.
    return HTMLResponse(
        index.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store, must-revalidate"},
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/config")
def config() -> dict:
    """Le dice a la interfaz qué voces de Piper hay descargadas y cuáles son
    los valores por defecto, para no tener nada hardcodeado en el HTML."""
    piper_voices = sorted(p.stem for p in VOICES_DIR.glob("*.onnx")) if VOICES_DIR.exists() else []
    return {
        "piper_voices": piper_voices,
        "piper_default_voice": DEFAULTS.piper_voice,
        "piper_voices_dir": str(VOICES_DIR),
        "piper_download_cmd": (
            f"python -m piper.download_voices {DEFAULTS.piper_voice} --download-dir \"{VOICES_DIR}\""
        ),
        "espeak_pitch": DEFAULTS.espeak_pitch,
        "espeak_speed_wpm": DEFAULTS.espeak_speed_wpm,
        "silence_between_scenes_ms": DEFAULTS.silence_between_scenes_ms,
        "video": {
            "width": DEFAULTS.video.width,
            "height": DEFAULTS.video.height,
            "fps": DEFAULTS.video.fps,
        },
    }


# --------------------------------------------------------------------------
# Subida de archivos
# --------------------------------------------------------------------------
@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),
    kind: Literal["images", "audio", "music"] = "images",
) -> dict:
    """Guarda un archivo dentro de assets/uploads/<kind>/ y devuelve su ruta
    absoluta (que es lo que el pipeline necesita) más una URL para
    previsualizarlo en la interfaz."""
    original = Path(file.filename or "archivo")
    safe_stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in original.stem)[:60]
    dest = UPLOADS_DIR / kind / f"{uuid.uuid4().hex[:8]}_{safe_stem}{original.suffix.lower()}"

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    return {
        "path": str(dest.resolve()),
        "url": f"/files/uploads/{kind}/{dest.name}",
        "name": original.name,
    }


# --------------------------------------------------------------------------
# Trabajos de generación
# --------------------------------------------------------------------------
@app.post("/api/jobs")
def create_job(request: JobRequest) -> dict:
    if not request.script.scenes:
        raise HTTPException(status_code=400, detail="El guion no tiene escenas.")

    for scene in request.script.scenes:
        if not scene.text.strip():
            raise HTTPException(status_code=400, detail=f"La escena '{scene.id}' no tiene texto.")
        if not Path(scene.image_path).exists():
            raise HTTPException(
                status_code=400,
                detail=f"La escena '{scene.id}' no tiene una imagen válida ({scene.image_path}).",
            )

    if request.tts_backend == "chatterbox" and not request.tts_options.get("voice_sample"):
        raise HTTPException(
            status_code=400,
            detail="Para clonar voz (chatterbox) hay que subir un audio de referencia.",
        )

    # Piper necesita su modelo .onnx descargado. Se comprueba ANTES de arrancar
    # el trabajo: si no, un guion largo se pone a generar y falla a mitad de la
    # primera escena, cuando ya el usuario está esperando.
    if request.tts_backend == "piper":
        voice_name = request.tts_options.get("voice") or DEFAULTS.piper_voice
        if not (VOICES_DIR / f"{voice_name}.onnx").exists():
            disponibles = sorted(p.stem for p in VOICES_DIR.glob("*.onnx"))
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Falta el modelo de voz '{voice_name}'. Descárgalo una sola vez con:\n"
                    f"python -m piper.download_voices {voice_name} --download-dir \"{VOICES_DIR}\"\n"
                    + (
                        f"Voces que ya tienes: {', '.join(disponibles)}."
                        if disponibles
                        else "Mientras tanto puedes usar una voz clonada (chatterbox) o espeak."
                    )
                ),
            )

    job_id = uuid.uuid4().hex[:12]
    _set_job(
        job_id,
        status="queued",
        stage="En cola",
        progress=0,
        title=request.script.title,
        scenes=len(request.script.scenes),
        tts_backend=request.tts_backend,
        created_at=datetime.now().isoformat(timespec="seconds"),
    )

    thread = threading.Thread(target=_run_job, args=(job_id, request), daemon=True)
    thread.start()

    return {"job_id": job_id, "status_url": f"/api/jobs/{job_id}"}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    job = _get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="No existe ese trabajo.")
    if job.get("status") == "done":
        job["video_url"] = f"/api/jobs/{job_id}/video"
        job["download_url"] = f"/download/{job_id}"
    return job


@app.get("/api/jobs")
def list_jobs() -> list[dict]:
    with _jobs_lock:
        jobs = [dict(job) for job in _jobs.values()]
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


@app.get("/api/jobs/{job_id}/video")
def job_video(job_id: str) -> FileResponse:
    path = OUTPUTS_DIR / f"{job_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Ese video todavía no existe.")
    return FileResponse(path, media_type="video/mp4")


@app.get("/download/{job_id}")
def download(job_id: str) -> FileResponse:
    path = OUTPUTS_DIR / f"{job_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No existe ese video.")
    job = _get_job(job_id) or {}
    nice_name = job.get("title") or job_id
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in str(nice_name)).strip()
    return FileResponse(path, media_type="video/mp4", filename=f"{safe or job_id}.mp4")


# --------------------------------------------------------------------------
# Voces guardadas
# --------------------------------------------------------------------------
class SavedVoice(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)
    backend: Literal["piper", "espeak", "chatterbox"]
    options: dict[str, Any] = Field(default_factory=dict)
    note: Optional[str] = None


def _read_voices() -> list[dict]:
    if not VOICES_LIBRARY.exists():
        return []
    try:
        data = json.loads(VOICES_LIBRARY.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _write_voices(voices: list[dict]) -> None:
    VOICES_LIBRARY.write_text(
        json.dumps(voices, ensure_ascii=False, indent=2), encoding="utf-8"
    )


@app.get("/api/voices")
def list_voices() -> list[dict]:
    """Las voces que el usuario guardó con un nombre. Para las voces clonadas
    se marca si el audio de referencia todavía existe en el disco."""
    voices = _read_voices()
    for voice in voices:
        sample = voice.get("options", {}).get("voice_sample")
        voice["sample_exists"] = bool(sample) and Path(sample).exists()
    return voices


@app.post("/api/voices")
def save_voice(voice: SavedVoice) -> dict:
    options = _clean_tts_options(voice.backend, voice.options)

    if voice.backend == "chatterbox":
        sample = options.get("voice_sample")
        if not sample:
            raise HTTPException(
                status_code=400,
                detail="Una voz clonada necesita su audio de referencia para poder guardarse.",
            )
        if not Path(sample).exists():
            raise HTTPException(status_code=400, detail=f"No existe el audio {sample}.")

    voices = [v for v in _read_voices() if v.get("name") != voice.name]  # reemplaza si ya existía
    voices.append({
        "name": voice.name,
        "backend": voice.backend,
        "options": options,
        "note": voice.note,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    _write_voices(voices)
    return {"saved": voice.name, "total": len(voices)}


@app.delete("/api/voices/{name}")
def delete_voice(name: str) -> dict:
    voices = _read_voices()
    remaining = [v for v in voices if v.get("name") != name]
    if len(remaining) == len(voices):
        raise HTTPException(status_code=404, detail="No existe esa voz guardada.")
    # Solo se borra la entrada de la biblioteca: el audio de referencia se deja
    # en assets/uploads/audio/ por si otra voz o otro video lo están usando.
    _write_voices(remaining)
    return {"deleted": name, "total": len(remaining)}


# --------------------------------------------------------------------------
# Videos ya generados (sección "outputs")
# --------------------------------------------------------------------------
def _safe_output(name: str) -> Path:
    """Evita que alguien pida ../../algo: solo nombres de archivo simples
    que existan dentro de outputs/."""
    candidate = Path(name).name
    if not candidate.endswith(".mp4"):
        candidate += ".mp4"
    path = (OUTPUTS_DIR / candidate).resolve()
    if path.parent != OUTPUTS_DIR.resolve() or not path.exists():
        raise HTTPException(status_code=404, detail="No existe ese video.")
    return path


@app.get("/api/outputs")
def list_outputs() -> list[dict]:
    """Lee la carpeta outputs/ del disco (no la memoria), así la lista sigue
    ahí después de reiniciar el servidor."""
    items = []
    for path in OUTPUTS_DIR.glob("*.mp4"):
        meta_path = path.with_suffix(".meta.json")
        qa_path = Path(str(path) + ".qa.json")

        meta: dict[str, Any] = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                meta = {}

        qa: dict[str, Any] = {}
        if qa_path.exists():
            try:
                qa = json.loads(qa_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                qa = {}

        stat = path.stat()
        items.append({
            "file": path.name,
            "title": meta.get("title") or path.stem,
            "tts_backend": meta.get("tts_backend"),
            "scenes": meta.get("scenes"),
            "created_at": meta.get("created_at")
            or datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "modified_ts": stat.st_mtime,
            "size_mb": round(stat.st_size / 1_048_576, 1),
            "duration_seconds": qa.get("duration_seconds"),
            "width": qa.get("width"),
            "height": qa.get("height"),
            "qa_ok": qa.get("ok"),
            "video_url": f"/api/outputs/{path.name}/video",
            "download_url": f"/api/outputs/{path.name}/download",
        })

    return sorted(items, key=lambda i: i["modified_ts"], reverse=True)


@app.get("/api/outputs/{name}/video")
def output_video(name: str) -> FileResponse:
    return FileResponse(_safe_output(name), media_type="video/mp4")


@app.get("/api/outputs/{name}/download")
def output_download(name: str) -> FileResponse:
    path = _safe_output(name)
    meta_path = path.with_suffix(".meta.json")
    filename = path.name
    if meta_path.exists():
        try:
            title = json.loads(meta_path.read_text(encoding="utf-8")).get("title")
            if title:
                safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title).strip()
                filename = f"{safe or path.stem}.mp4"
        except json.JSONDecodeError:
            pass
    return FileResponse(path, media_type="video/mp4", filename=filename)


@app.delete("/api/outputs/{name}")
def output_delete(name: str) -> dict:
    path = _safe_output(name)
    path.unlink()
    for sidecar in (path.with_suffix(".meta.json"), Path(str(path) + ".qa.json")):
        if sidecar.exists():
            sidecar.unlink()
    return {"deleted": path.name}


# --------------------------------------------------------------------------
# Endpoint síncrono original (se mantiene por compatibilidad)
# --------------------------------------------------------------------------
@app.post("/generate")
def generate(script: Script) -> dict:
    """Generación síncrona: se queda esperando hasta que el video esté listo.
    Útil para llamarlo desde otro backend; para la interfaz se usa /api/jobs,
    que no bloquea."""
    job_id = uuid.uuid4().hex[:12]
    output_path = OUTPUTS_DIR / f"{job_id}.mp4"
    work_dir = Path(tempfile.mkdtemp(prefix=f"job_{job_id}_"))

    try:
        report = _run_pipeline(script, output_path, "piper", work_dir)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return {
        "job_id": job_id,
        "output_path": str(output_path),
        "download_url": f"/download/{job_id}",
        "qa": report.model_dump(),
    }
