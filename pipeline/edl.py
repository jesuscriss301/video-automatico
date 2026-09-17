"""
Construye el EDL (Edit Decision List): la lista de qué imagen se ve, en qué
segundo empieza y cuánto dura — a partir de las duraciones exactas de los
audios TTS ya generados. Esta es la parte que hace que los cortes sean
precisos: el tiempo no se adivina, se mide.
"""
from __future__ import annotations

from pipeline.models import EDLClip, RenderedScene


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
