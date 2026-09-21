"""
Construye el EDL (Edit Decision List): la lista de qué imagen se ve, en qué
segundo empieza y cuánto dura — a partir de las duraciones exactas de los
audios TTS ya generados. Esta es la parte que hace que los cortes sean
precisos: el tiempo no se adivina, se mide.
"""
from __future__ import annotations

from pipeline.models import EDLClip, RenderedScene, SubtitleCue


def build_subtitle_cues(rendered_scenes: list[RenderedScene]) -> list[SubtitleCue]:
    """Pasa los subtítulos de cada escena (con tiempos relativos a su escena) a
    tiempos absolutos del video final.

    La referencia de tiempo es el audio: la pista final es la concatenación de
    los audios de cada escena en orden, así que el inicio de una escena en el
    video es la suma de las duraciones de las anteriores. Por eso los tiempos
    salen exactos sin estimar nada.
    """
    cues: list[SubtitleCue] = []
    cursor = 0.0

    for rs in rendered_scenes:
        for cue in rs.cues:
            cues.append(
                SubtitleCue(
                    text=cue.text,
                    start_seconds=round(cursor + cue.start_seconds, 3),
                    duration_seconds=round(cue.duration_seconds, 3),
                )
            )
        cursor += rs.duration_seconds

    return cues


def build_edl(rendered_scenes: list[RenderedScene]) -> list[EDLClip]:
    clips: list[EDLClip] = []
    cursor = 0.0

    for rs in rendered_scenes:
        subtitle = rs.scene.subtitle_override or rs.scene.text
        clips.append(
            EDLClip(
                scene_id=rs.scene.id,
                image_path=rs.image_path_resolved,
                start_seconds=round(cursor, 3),
                duration_seconds=round(rs.duration_seconds, 3),
                subtitle_text=subtitle,
            )
        )
        cursor += rs.duration_seconds

    return clips


def total_duration(clips: list[EDLClip]) -> float:
    if not clips:
        return 0.0
    last = clips[-1]
    return round(last.start_seconds + last.duration_seconds, 3)
