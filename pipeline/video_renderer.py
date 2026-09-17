"""
Renderiza el video final: por cada escena aplica Ken Burns (zoom/pan lento)
sobre la imagen, encadena todas las escenas con crossfade, quema los
subtítulos y mezcla el audio final ya normalizado.

Estrategia (en dos pasadas, más fácil de depurar que un único comando gigante):
  1) Se renderiza un clip de video mudo por escena (imagen + Ken Burns),
     con la duración exacta que le toca según el EDL — y un pequeño
     "colchón" extra en todas las escenas menos la última, para que el
     crossfade tenga material de sobra que mezclar sin acortar la escena.
  2) Se encadenan todos los clips con `xfade`, se queman los subtítulos y se
     mezcla con la pista de audio final, en un solo render de salida.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from config.settings import DEFAULTS
from pipeline.image_processor import crop_to_aspect
from pipeline.models import EDLClip


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló: {' '.join(cmd)}\n{result.stderr[-3000:]}")


def _render_scene_clip(image_path: Path, duration: float, out_path: Path) -> None:
    """Genera un clip mudo con efecto Ken Burns a partir de una sola imagen."""
    q = DEFAULTS
    fps = q.video.fps
    frames = max(1, round(duration * fps))
    zoom_step = (q.zoom_end - q.zoom_start) / frames

    vf = (
        f"scale=3840:-2,"
        f"zoompan=z='min(zoom+{zoom_step:.6f},{q.zoom_end})':"
        f"d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={q.video.width}x{q.video.height}:fps={fps},"
        f"format={q.video.pixel_format}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-vf", vf,
        "-t", f"{duration:.3f}",
        "-an",
        str(out_path),
    ]
    _run(cmd)


def _prepare_images(clips: list[EDLClip], work_dir: Path) -> list[Path]:
    prepared = []
    for clip in clips:
        dst = work_dir / f"{clip.scene_id}.cropped.png"
        crop_to_aspect(Path(clip.image_path), dst, DEFAULTS.video.width, DEFAULTS.video.height)
        prepared.append(dst)
    return prepared


def _escape_filter_path(path: Path) -> str:
    # Escapa caracteres que el parser de filtros de ffmpeg trata como especiales.
    s = str(path)
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def render_final_video(
    clips: list[EDLClip],
    final_audio: Path,
    subtitles_ass: Path,
    out_path: Path,
    work_dir: Path,
) -> Path:
    if not clips:
        raise ValueError("No hay escenas en el EDL, no hay nada que renderizar.")

    work_dir.mkdir(parents=True, exist_ok=True)
    cf = DEFAULTS.crossfade_seconds
    n = len(clips)

    prepared_images = _prepare_images(clips, work_dir)

    # --- Paso 1: un clip mudo con Ken Burns por escena ---
    scene_clip_paths: list[Path] = []
    for i, (clip, image) in enumerate(zip(clips, prepared_images)):
        is_last = i == n - 1
        render_duration = clip.duration_seconds if is_last else clip.duration_seconds + cf
        clip_path = work_dir / f"clip_{i:03d}.mp4"
        _render_scene_clip(image, render_duration, clip_path)
        scene_clip_paths.append(clip_path)

    # --- Paso 2: encadenar con xfade, quemar subtítulos y mezclar audio ---
    inputs_cmd: list[str] = []
    for p in scene_clip_paths:
        inputs_cmd += ["-i", str(p)]
    inputs_cmd += ["-i", str(final_audio)]
    audio_input_index = n  # el último -i agregado es el audio

    if n == 1:
        video_label = "0:v"
        filter_parts = []
    else:
        filter_parts = []
        cumulative = clips[0].duration_seconds + cf  # duración del primer clip renderizado
        prev_label = "0:v"
        for i in range(1, n):
            offset = cumulative - cf
            out_label = f"x{i}"
            filter_parts.append(
                f"[{prev_label}][{i}:v]xfade=transition=fade:duration={cf:.3f}:offset={offset:.3f}[{out_label}]"
            )
            is_last_pair = i == n - 1
            this_len = clips[i].duration_seconds if is_last_pair else clips[i].duration_seconds + cf
            cumulative = cumulative + this_len - cf
            prev_label = out_label
        video_label = prev_label

    ass_escaped = _escape_filter_path(subtitles_ass)
    filter_parts.append(f"[{video_label}]ass='{ass_escaped}'[vout]")
    filter_complex = ";".join(filter_parts)

    q = DEFAULTS
    cmd = [
        "ffmpeg", "-y",
        *inputs_cmd,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{audio_input_index}:a",
        "-c:v", q.video.video_codec,
        "-preset", q.video.preset,
        "-crf", str(q.video.crf),
        "-pix_fmt", q.video.pixel_format,
        "-r", str(q.video.fps),
        "-c:a", q.video.audio_codec,
        "-b:a", q.video.audio_bitrate,
        "-shortest",
        str(out_path),
    ]
    _run(cmd)
    return out_path
