"""
Verificación automática del video final antes de darlo por bueno: que la
duración coincida con la esperada, que la resolución sea la correcta, que
tenga audio, y que no haya tramos de frames negros (señal de que algo se
rompió en el render).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from config.settings import DEFAULTS
from pipeline.models import QAReport


def _ffprobe_json(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _detect_black_frames(path: Path, max_seconds_to_scan: float = 600.0) -> bool:
    """Corre el filtro blackdetect de ffmpeg; si reporta algún intervalo, algo
    salió mal en el render (p.ej. una escena que no cargó la imagen)."""
    cmd = [
        "ffmpeg", "-i", str(path),
        "-t", str(max_seconds_to_scan),
        "-vf", "blackdetect=d=0.5:pic_th=0.98",
        "-an", "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return "black_start" in result.stderr


def run_qa(output_path: Path, expected_duration_seconds: float, tolerance_seconds: float = 0.35) -> QAReport:
    issues: list[str] = []
    info = _ffprobe_json(output_path)

    duration = float(info["format"].get("duration", 0.0))
    video_streams = [s for s in info["streams"] if s["codec_type"] == "video"]
    audio_streams = [s for s in info["streams"] if s["codec_type"] == "audio"]

    width = video_streams[0]["width"] if video_streams else 0
    height = video_streams[0]["height"] if video_streams else 0
    has_audio = len(audio_streams) > 0

    diff = abs(duration - expected_duration_seconds)
    if diff > tolerance_seconds:
        issues.append(
            f"La duración del video ({duration:.2f}s) difiere de la esperada "
            f"({expected_duration_seconds:.2f}s) por más de {tolerance_seconds}s."
        )

    if width != DEFAULTS.video.width or height != DEFAULTS.video.height:
        issues.append(
            f"Resolución {width}x{height} distinta a la configurada "
            f"{DEFAULTS.video.width}x{DEFAULTS.video.height}."
        )

    if not has_audio:
        issues.append("El video no tiene pista de audio.")

    black_frames = _detect_black_frames(output_path)
    if black_frames:
        issues.append("Se detectaron frames negros — revisa las escenas, alguna imagen pudo no cargar bien.")

    return QAReport(
        output_path=str(output_path),
        ok=len(issues) == 0,
        duration_seconds=duration,
        expected_duration_seconds=expected_duration_seconds,
        duration_diff_seconds=round(diff, 3),
        width=width,
        height=height,
        has_audio=has_audio,
        black_frames_detected=black_frames,
        issues=issues,
    )
