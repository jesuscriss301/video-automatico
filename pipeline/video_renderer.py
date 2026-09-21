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


def _low_priority_kwargs() -> dict:
    """Hace que ffmpeg corra con prioridad baja, para que aunque marque 99% de
    CPU el resto del sistema siga respondiendo. En Windows se usa la clase de
    prioridad 'below normal'; en Linux/mac, nice."""
    if not DEFAULTS.video.low_priority:
        return {}
    if hasattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS"):  # Windows
        return {"creationflags": subprocess.BELOW_NORMAL_PRIORITY_CLASS}

    import os

    def _nice() -> None:
        try:
            os.nice(10)
        except (OSError, AttributeError):
            pass

    return {"preexec_fn": _nice}


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, **_low_priority_kwargs())
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló: {' '.join(cmd)}\n{result.stderr[-3000:]}")


def _encoder_args(final: bool) -> list[str]:
    """Argumentos de codificación de video.

    Para los clips intermedios (final=False) se usa siempre libx264 en
    ultrafast: se van a recodificar en el paso final, así que comprimirlos bien
    es CPU tirada a la basura.

    Para el render final se respeta el encoder configurado. Si es uno de
    hardware (h264_qsv en gráficas Intel, h264_nvenc en NVIDIA, h264_amf en
    AMD), el control de calidad no es -crf sino global_quality/cq, así que los
    argumentos cambian.
    """
    v = DEFAULTS.video

    if not final:
        args = ["-c:v", "libx264", "-preset", v.intermediate_preset, "-crf", str(v.intermediate_crf)]
    elif v.video_codec.endswith("_qsv"):
        # QSV toma nv12; si le llega yuv420p ffmpeg convierte solo, pero
        # pedirlo explícito evita una conversión extra por frame.
        args = [
            "-c:v", v.video_codec,
            "-global_quality", str(v.qsv_global_quality),
            "-preset", v.preset if v.preset in _QSV_PRESETS else "medium",
            "-pix_fmt", "nv12",
        ]
    elif v.video_codec.endswith("_nvenc"):
        args = ["-c:v", v.video_codec, "-rc", "vbr", "-cq", str(v.qsv_global_quality), "-preset", "p5"]
    elif v.video_codec.endswith("_amf"):
        args = ["-c:v", v.video_codec, "-rc", "cqp", "-qp_i", str(v.qsv_global_quality),
                "-qp_p", str(v.qsv_global_quality)]
    else:
        args = ["-c:v", v.video_codec, "-preset", v.preset, "-crf", str(v.crf),
                "-pix_fmt", v.pixel_format]

    if v.threads:
        args += ["-threads", str(v.threads)]
    return args


_QSV_PRESETS = {"veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"}


def _render_scene_clip(image_path: Path, duration: float, out_path: Path) -> None:
    """Genera un clip mudo con efecto Ken Burns a partir de una sola imagen."""
    q = DEFAULTS
    fps = q.video.fps
    frames = max(1, round(duration * fps))
    zoom_step = (q.zoom_end - q.zoom_start) / frames

    # La imagen se escala solo un poco más que el zoom máximo: escalar a 4K
    # para hacer un zoom de 1.12x era gastar CPU y memoria en cada frame.
    source_width = int(q.video.width * max(q.zoom_end, q.video.kenburns_oversample))
    source_width -= source_width % 2  # ancho par, requisito de yuv420p

    vf = (
        f"scale={source_width}:-2,"
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
        *_encoder_args(final=False),
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
        *_encoder_args(final=True),
        "-r", str(q.video.fps),
        "-c:a", q.video.audio_codec,
        "-b:a", q.video.audio_bitrate,
        "-shortest",
        str(out_path),
    ]

    try:
        _run(cmd)
    except RuntimeError as exc:
        # Si el encoder de hardware no está disponible en esta máquina (no hay
        # gráfica compatible, driver viejo, ffmpeg sin QSV), no se pierde el
        # render: se reintenta una vez con libx264 y se avisa.
        if q.video.video_codec == "libx264":
            raise
        print(
            f"[video_renderer] El encoder '{q.video.video_codec}' falló en esta máquina; "
            f"reintentando con libx264 (CPU). Detalle: {str(exc)[-400:]}"
        )
        cmd_cpu = [
            "ffmpeg", "-y",
            *inputs_cmd,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", f"{audio_input_index}:a",
            "-c:v", "libx264", "-preset", q.video.preset, "-crf", str(q.video.crf),
            "-pix_fmt", q.video.pixel_format,
            "-r", str(q.video.fps),
            "-c:a", q.video.audio_codec,
            "-b:a", q.video.audio_bitrate,
            "-shortest",
            str(out_path),
        ]
        _run(cmd_cpu)

    return out_path
