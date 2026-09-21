"""
Orquesta el pipeline completo de punta a punta:

  guion (JSON) -> TTS por escena -> EDL -> imágenes validadas ->
  render con Ken Burns/crossfade/subtítulos -> audio normalizado -> QA

Este módulo es el que usan tanto la CLI (scripts/run_pipeline.py) como la
API (api/main.py), para no duplicar la lógica.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable

from config.settings import DEFAULTS
from pipeline import audio_processor, edl as edl_module, video_renderer, qa_check
from pipeline.image_processor import ensure_quality
from pipeline.models import QAReport, RenderedScene, Script
from pipeline.script_parser import load_script
from pipeline.subtitles import build_ass_subtitles
from pipeline.tts_engine import get_backend, synthesize_scene


def generate_video(
    script_path: str | Path,
    output_path: str | Path,
    tts_backend: str = "piper",
    keep_work_dir: bool = False,
    tts_options: dict | None = None,
    progress_cb: Callable[[str, float], None] | None = None,
) -> QAReport:
    script = load_script(script_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    work_dir = Path(tempfile.mkdtemp(prefix="video_pipeline_"))
    try:
        report = _run_pipeline(
            script, output_path, tts_backend, work_dir, tts_options or {}, progress_cb
        )
    finally:
        if not keep_work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)
        else:
            print(f"[run_pipeline] Archivos intermedios conservados en: {work_dir}")

    return report


def _run_pipeline(
    script: Script,
    output_path: Path,
    tts_backend: str,
    work_dir: Path,
    tts_options: dict | None = None,
    progress_cb: Callable[[str, float], None] | None = None,
) -> QAReport:
    def progress(stage: str, pct: float) -> None:
        # La interfaz gráfica (api/main.py) usa esto para mostrar en qué va;
        # la CLI no pasa callback y aquí no pasa nada.
        if progress_cb is not None:
            progress_cb(stage, pct)

    audio_dir = work_dir / "audio"
    images_dir = work_dir / "images"
    audio_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    progress("Preparando el motor de voz", 2)
    backend = get_backend(tts_backend, **(tts_options or {}))

    total_scenes = len(script.scenes)
    rendered_scenes: list[RenderedScene] = []
    for index, scene in enumerate(script.scenes, start=1):
        progress(
            f"Generando voz — escena {index} de {total_scenes}",
            5 + (index - 1) / max(total_scenes, 1) * 55,
        )
        synthesized = synthesize_scene(scene, backend, audio_dir)
        image_resolved = ensure_quality(scene.image_path, images_dir, scene.id)
        rendered_scenes.append(
            RenderedScene(
                scene=scene,
                audio_path=str(synthesized.path),
                duration_seconds=synthesized.duration_seconds,
                image_path_resolved=str(image_resolved),
                cues=synthesized.cues,
            )
        )

    progress("Calculando los cortes (EDL)", 62)
    clips = edl_module.build_edl(rendered_scenes)
    expected_duration = edl_module.total_duration(clips)

    # --- audio: concatenar todas las escenas + normalizar (+ música opcional) ---
    progress("Uniendo y normalizando el audio", 68)
    voice_track = audio_processor.concat_wavs(
        [Path(rs.audio_path) for rs in rendered_scenes], work_dir / "voice_raw.wav"
    )
    normalized_track = audio_processor.normalize_loudness(voice_track, work_dir / "voice_normalized.wav")

    final_audio = normalized_track
    if script.background_music:
        music_path = Path(script.background_music)
        if music_path.exists():
            final_audio = audio_processor.mix_with_background_music(
                normalized_track, music_path, work_dir / "voice_with_music.wav"
            )

    # --- subtítulos ---
    # Se construyen desde los cues (una frase cada uno, con su duración real
    # medida al sintetizar), no desde los clips: así el subtítulo va sincronizado
    # con la voz en vez de mostrar el párrafo entero toda la escena.
    progress("Generando subtítulos", 74)
    cues = edl_module.build_subtitle_cues(rendered_scenes)
    subtitles_path = build_ass_subtitles(cues, work_dir / "subtitles.ass")

    # --- render final ---
    progress("Renderizando el video (Ken Burns + transiciones)", 78)
    video_renderer.render_final_video(
        clips=clips,
        final_audio=final_audio,
        subtitles_ass=subtitles_path,
        out_path=output_path,
        work_dir=work_dir / "render",
    )

    # --- QA ---
    progress("Verificando el resultado (QA)", 95)
    report = qa_check.run_qa(output_path, expected_duration_seconds=expected_duration)

    report_path = output_path.with_suffix(output_path.suffix + ".qa.json")
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    progress("Listo", 100)
    return report
