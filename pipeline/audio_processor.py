"""
Procesamiento de audio: concatenar las escenas en una sola pista, normalizar
el loudness (para que no "grite" ni quede muy bajito) y, opcionalmente,
mezclar con música de fondo bajando su volumen cuando hay voz (ducking).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from config.settings import DEFAULTS


def concat_wavs(wav_paths: list[Path], out_path: Path) -> Path:
    """Concatena varios WAV en uno solo, en orden, sin recodificar más de lo
    necesario (todos deben tener el mismo sample rate/canales, que es el caso
    porque todos salen del mismo backend de TTS)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_path.with_suffix(".txt")
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in wav_paths))

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "pcm_s16le",
        str(out_path),
    ]
    _run(cmd)
    return out_path


def normalize_loudness(src: Path, dst: Path, target_lufs: float | None = None) -> Path:
    """Normaliza a un loudness objetivo (EBU R128) con el filtro loudnorm de
    ffmpeg, en dos pasadas: la primera mide, la segunda corrige con esos
    valores medidos (da un resultado mucho más preciso que una sola pasada)."""
    target = target_lufs if target_lufs is not None else DEFAULTS.target_lufs

    measure_cmd = [
        "ffmpeg", "-i", str(src),
        "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-",
    ]
    result = subprocess.run(measure_cmd, capture_output=True, text=True)
    measured = _extract_loudnorm_json(result.stderr)

    if measured is None:
        # Si por lo que sea no se pudo medir, aplicamos una sola pasada simple.
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11",
            str(dst),
        ]
        _run(cmd)
        return dst

    af = (
        f"loudnorm=I={target}:TP=-1.5:LRA=11:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured.get('target_offset', 0)}:linear=true:print_format=summary"
    )
    cmd = ["ffmpeg", "-y", "-i", str(src), "-af", af, str(dst)]
    _run(cmd)
    return dst


def mix_with_background_music(
    voice_path: Path,
    music_path: Path,
    out_path: Path,
    duck_db: float | None = None,
) -> Path:
    """Mezcla la voz con música de fondo, bajando la música automáticamente
    mientras hay voz (sidechain compression) para que no compita con la
    narración — así suena a producción y no a 'música tapando la voz'."""
    duck = duck_db if duck_db is not None else DEFAULTS.music_duck_db
    filter_complex = (
        f"[1:a]volume=0dB[music];"
        f"[music][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=300:makeup=1[ducked];"
        f"[0:a][ducked]amix=inputs=2:duration=first:weights='1 1'[aout]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(voice_path),
        "-stream_loop", "-1", "-i", str(music_path),
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-t", _duration_seconds(voice_path).__str__(),
        str(out_path),
    ]
    _run(cmd)
    return out_path


def _duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def _extract_loudnorm_json(stderr_text: str) -> dict | None:
    import json
    import re

    match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr_text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Comando falló: {' '.join(cmd)}\n{result.stderr[-2000:]}")
