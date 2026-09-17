"""
Genera subtítulos quemados en formato .ass (Advanced SubStation Alpha), que a
diferencia de .srt permite controlar tipografía, tamaño, posición y color
directamente — necesario para que el video se vea "cuidado" y no como un
subtítulo genérico de reproductor.
"""
from __future__ import annotations

from pathlib import Path

from config.settings import DEFAULTS
from pipeline.models import EDLClip

_ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def build_ass_subtitles(clips: list[EDLClip], out_path: Path) -> Path:
    header = _ASS_HEADER.format(
        width=DEFAULTS.video.width,
        height=DEFAULTS.video.height,
        font=DEFAULTS.subtitle_font,
        size=DEFAULTS.subtitle_font_size,
        margin_v=DEFAULTS.subtitle_margin_v,
    )
    lines = [header]

    for clip in clips:
        start = _fmt_time(clip.start_seconds)
        end = _fmt_time(clip.start_seconds + clip.duration_seconds)
        text = clip.subtitle_text.replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
