"""Modelos de datos que viajan entre las etapas del pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Scene(BaseModel):
    """Una escena del guion: un fragmento de texto + la imagen que lo acompaña."""

    id: str
    text: str = Field(..., description="Texto que se convierte a voz (TTS)")
    image_path: str = Field(..., description="Ruta a la imagen de esta escena")
    image_description: Optional[str] = Field(
        default=None,
        description="Descripción detallada de la imagen (útil para los Flujos 2/3, "
        "y para dejar registro de qué se pidió mostrar aquí)",
    )
    pause_after_ms: Optional[int] = Field(
        default=None,
        description="Pausa extra después de esta escena, en milisegundos. "
        "Si no se define, se usa el valor por defecto de config/settings.py",
    )
    subtitle_override: Optional[str] = Field(
        default=None,
        description="Texto a mostrar en el subtítulo si debe ser distinto al texto hablado",
    )


class Script(BaseModel):
    """El guion completo: metadatos + lista de escenas en orden."""

    title: str
    language: str = "es"
    scenes: list[Scene]
    background_music: Optional[str] = Field(
        default=None, description="Ruta a un archivo de música de fondo opcional"
    )


class SubtitleCue(BaseModel):
    """Un subtítulo: el trozo de texto que se muestra, con su tiempo exacto.

    Los tiempos NO se estiman: cada trozo se sintetiza por separado y se mide
    su duración real, así el subtítulo entra y sale con la voz.
    """

    text: str
    start_seconds: float
    duration_seconds: float


class RenderedScene(BaseModel):
    """Una escena ya con su audio generado y su duración medida."""

    scene: Scene
    audio_path: str
    duration_seconds: float
    image_path_resolved: str  # después de validar/ajustar resolución
    cues: list[SubtitleCue] = Field(
        default_factory=list,
        description="Subtítulos de esta escena con tiempos relativos al inicio de la escena",
    )


class EDLClip(BaseModel):
    """Una entrada del Edit Decision List: qué imagen se ve, cuándo y por cuánto."""

    scene_id: str
    image_path: str
    start_seconds: float
    duration_seconds: float
    subtitle_text: str


class QAReport(BaseModel):
    """Resultado del chequeo automático de calidad del video final."""

    output_path: str
    ok: bool
    duration_seconds: float
    expected_duration_seconds: float
    duration_diff_seconds: float
    width: int
    height: int
    has_audio: bool
    black_frames_detected: bool
    issues: list[str] = Field(default_factory=list)
