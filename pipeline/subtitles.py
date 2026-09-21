"""
Genera subtítulos quemados en formato .ass (Advanced SubStation Alpha), que a
diferencia de .srt permite controlar tipografía, tamaño, posición y color
directamente — necesario para que el video se vea "cuidado" y no como un
subtítulo genérico de reproductor.

Los tiempos vienen medidos, no estimados: cada frase se sintetiza por separado
(ver synthesize_scene) y se conoce su duración real, así el subtítulo entra y
sale con la voz.
"""
from __future__ import annotations

from pathlib import Path

from config.settings import DEFAULTS
from pipeline.models import EDLClip, SubtitleCue

_ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _wrap(text: str, ancho: int) -> str:
    """Parte el subtítulo en dos líneas si es largo, cortando en el espacio más
    cercano a la mitad — así queda equilibrado y no una línea larga y otra con
    dos palabras. Nunca corta una palabra."""
    text = " ".join(text.split())
    if len(text) <= ancho:
        return text

    mitad = len(text) // 2
    espacios = [i for i, c in enumerate(text) if c == " "]
    if not espacios:
        return text
    corte = min(espacios, key=lambda i: abs(i - mitad))
    return text[:corte] + "\\N" + text[corte + 1:]


def _escape(text: str) -> str:
    # En .ass, las llaves abren etiquetas de formato: si el texto las trae, hay
    # que neutralizarlas o libass se come el subtítulo.
    return text.replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def build_ass_subtitles(
    cues: list[SubtitleCue] | list[EDLClip],
    out_path: Path,
) -> Path:
    """Escribe el archivo .ass.

    Acepta la lista de subtítulos con tiempos exactos (lo normal) o, por
    compatibilidad con código viejo, la lista de clips del EDL — en ese caso
    cada clip aporta un solo subtítulo que dura toda la escena.
    """
    header = _ASS_HEADER.format(
        width=DEFAULTS.video.width,
        height=DEFAULTS.video.height,
        font=DEFAULTS.subtitle_font,
        size=DEFAULTS.subtitle_font_size,
        margin_v=DEFAULTS.subtitle_margin_v,
    )
    lines = [header]

    normalizados: list[SubtitleCue] = []
    for item in cues:
        if isinstance(item, SubtitleCue):
            normalizados.append(item)
        else:  # EDLClip
            normalizados.append(
                SubtitleCue(
                    text=item.subtitle_text,
                    start_seconds=item.start_seconds,
                    duration_seconds=item.duration_seconds,
                )
            )

    minimo = DEFAULTS.subtitle_min_seconds

    for i, cue in enumerate(normalizados):
        if not cue.text.strip():
            continue

        inicio = cue.start_seconds
        fin = inicio + max(cue.duration_seconds, minimo)

        # Si por alargar un subtítulo cortísimo se pisa con el siguiente, se
        # recorta: dos subtítulos a la vez se ven encimados.
        if i + 1 < len(normalizados):
            siguiente = normalizados[i + 1].start_seconds
            if fin > siguiente:
                fin = max(inicio + 0.2, siguiente - 0.02)

        texto = _wrap(_escape(cue.text), DEFAULTS.subtitle_wrap_chars)
        lines.append(
            f"Dialogue: 0,{_fmt_time(inicio)},{_fmt_time(fin)},Default,,0,0,0,,{texto}"
        )

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
