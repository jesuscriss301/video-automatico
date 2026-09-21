"""
Detección de hardware: qué gráfica hay disponible y qué se puede acelerar con ella.

Hay dos usos distintos de la gráfica en este proyecto, y no son lo mismo:

1. **Codificar el video** (ffmpeg). Sirve casi cualquier gráfica, integrada o
   dedicada, porque usan un bloque de hardware dedicado a video:
   h264_nvenc (NVIDIA), h264_qsv (Intel), h264_amf (AMD).
   Es ~88% del tiempo del render, así que es la ganancia más grande.

2. **Generar la voz clonada** (Chatterbox / PyTorch). Esto SOLO lo acelera una
   NVIDIA con CUDA: es cálculo de red neuronal, no video. Con GPU pasa de
   minutos a segundos por escena.

La detección no se hace leyendo modelos de tarjeta (poco fiable): se intenta
usar de verdad cada cosa y se ve si funciona. El resultado se guarda en caché
para no repetir la prueba en cada render.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

CACHE_PATH = Path(__file__).resolve().parent.parent / "outputs" / ".hw_cache.json"
CACHE_TTL_SECONDS = 7 * 24 * 3600  # una semana: si cambia el driver, se re-prueba

# Orden de preferencia: primero la dedicada (NVIDIA suele ser la dedicada y la
# más rápida), luego la integrada Intel, luego AMD.
ENCODER_CANDIDATES = [
    ("h264_nvenc", ["-rc", "vbr", "-cq", "22", "-preset", "p5"], "gráfica NVIDIA (dedicada)"),
    ("h264_qsv", ["-global_quality", "22", "-preset", "medium", "-pix_fmt", "nv12"],
     "gráfica Intel (integrada, Quick Sync)"),
    ("h264_amf", ["-rc", "cqp", "-qp_i", "22", "-qp_p", "22"], "gráfica AMD"),
]

_memoria: dict | None = None


def _probe_encoder(encoder: str, args: list[str]) -> tuple[bool, float, str]:
    """Intenta codificar 2 segundos de video de prueba con ese encoder."""
    destino = CACHE_PATH.parent / f"_probe_{encoder}.mp4"
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "testsrc2=size=1920x1080:rate=30:duration=2",
        "-c:v", encoder, *args, str(destino),
    ]
    inicio = time.time()
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return False, 0.0, f"{type(exc).__name__}"
    finally:
        destino.unlink(missing_ok=True)

    elapsed = time.time() - inicio
    if res.returncode != 0:
        utiles = [
            l.strip() for l in res.stderr.splitlines()
            if any(p in l.lower() for p in ("error", "cannot", "failed", "no device", "not supported"))
        ]
        return False, elapsed, (utiles[0] if utiles else "no disponible")[:160]
    return True, elapsed, ""


def _probe_todo() -> dict:
    compilados = set()
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
        compilados = {l.split()[1] for l in out.stdout.splitlines() if len(l.split()) > 1}
    except FileNotFoundError:
        return {"error": "ffmpeg no está instalado o no está en el PATH", "encoders": {}, "cuda": False}

    resultados: dict[str, dict] = {}

    ok_cpu, t_cpu, _ = _probe_encoder("libx264", ["-preset", "fast", "-crf", "19"])
    resultados["libx264"] = {"funciona": ok_cpu, "segundos": round(t_cpu, 2),
                             "descripcion": "procesador (CPU)"}

    for encoder, args, descripcion in ENCODER_CANDIDATES:
        if encoder not in compilados:
            resultados[encoder] = {"funciona": False, "motivo": "no viene en este build de ffmpeg",
                                   "descripcion": descripcion}
            continue
        ok, elapsed, motivo = _probe_encoder(encoder, args)
        resultados[encoder] = {
            "funciona": ok, "segundos": round(elapsed, 2), "descripcion": descripcion,
            **({"motivo": motivo} if not ok else {}),
        }

    return {
        "encoders": resultados,
        "cuda": _cuda_disponible_real(),
        "probado_en": time.time(),
    }


def _cuda_disponible_real() -> bool:
    """Si hay una NVIDIA usable por PyTorch (para la voz clonada). Se consulta
    en un proceso aparte porque importar torch es lento y pesado, y no queremos
    cargarlo solo para preguntar."""
    codigo = "import torch, json; print(json.dumps(bool(torch.cuda.is_available())))"
    try:
        import sys
        res = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, timeout=180)
        return json.loads(res.stdout.strip() or "false")
    except Exception:  # noqa: BLE001 — torch puede no estar instalado, y está bien
        return False


def detectar(forzar: bool = False) -> dict:
    """Devuelve el informe de hardware, usando caché si ya se probó antes."""
    global _memoria
    if _memoria is not None and not forzar:
        return _memoria

    if not forzar and CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if time.time() - cache.get("probado_en", 0) < CACHE_TTL_SECONDS:
                _memoria = cache
                return cache
        except (json.JSONDecodeError, OSError):
            pass

    informe = _probe_todo()
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        CACHE_PATH.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    _memoria = informe
    return informe


def mejor_encoder() -> tuple[str, str]:
    """El encoder de video más rápido que funcione en esta máquina.

    Devuelve (encoder, por_qué). Si ninguna gráfica sirve, cae en libx264 (CPU),
    que siempre funciona.
    """
    informe = detectar()
    encoders = informe.get("encoders", {})

    candidatos = [
        (nombre, datos) for nombre, datos in encoders.items()
        if nombre != "libx264" and datos.get("funciona")
    ]
    if not candidatos:
        return "libx264", "no hay gráfica usable; se codifica en el procesador"

    # El más rápido de los que funcionan.
    nombre, datos = min(candidatos, key=lambda c: c[1].get("segundos", 999))
    cpu = encoders.get("libx264", {}).get("segundos")
    comparacion = ""
    if cpu and datos.get("segundos"):
        comparacion = f", {cpu / datos['segundos']:.1f}x más rápido que el procesador"
    return nombre, f"{datos.get('descripcion', nombre)}{comparacion}"


def dispositivo_tts(preferencia: str = "auto") -> str:
    """Dónde generar la voz clonada: 'cuda' (NVIDIA) o 'cpu'."""
    if preferencia in ("cpu", "cuda"):
        return preferencia
    return "cuda" if detectar().get("cuda") else "cpu"
