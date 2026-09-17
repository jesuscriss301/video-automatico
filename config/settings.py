"""
Configuración central del pipeline. Todo lo que define "qué tan buena"
sale la calidad del video vive aquí, para no tener números mágicos
regados por el código.
"""
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FONTS_DIR = ASSETS_DIR / "fonts"
MUSIC_DIR = ASSETS_DIR / "music"


@dataclass
class VideoQuality:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    # CRF más bajo = más calidad / archivo más pesado. 17-18 es "casi visualmente
    # sin pérdida" para H.264.
    crf: int = 17
    video_codec: str = "libx264"
    pixel_format: str = "yuv420p"
    preset: str = "slow"  # más lento de codificar, mejor relación calidad/peso
    audio_codec: str = "aac"
    audio_bitrate: str = "320k"


@dataclass
class QualityDefaults:
    video: VideoQuality = field(default_factory=VideoQuality)

    # --- Audio ---
    target_lufs: float = -16.0  # estándar de loudness para streaming/redes
    silence_between_scenes_ms: int = 250  # micro-pausa natural por defecto
    music_duck_db: float = -18.0  # cuánto se baja la música cuando hay voz

    # --- Ken Burns / movimiento ---
    zoom_start: float = 1.0
    zoom_end: float = 1.12
    crossfade_seconds: float = 0.6
    # margen de resolución que debe tener la imagen fuente sobre la de salida
    # para poder hacer zoom sin pixelar (1.5x el lado mayor de salida)
    min_source_scale: float = 1.5

    # --- Subtítulos ---
    subtitle_font: str = "DejaVuSans-Bold"
    subtitle_font_size: int = 46
    subtitle_margin_v: int = 80

    # --- TTS ---
    piper_voice: str = "es_ES-davefx-medium"
    tts_sample_rate: int = 22050


DEFAULTS = QualityDefaults()

for d in (ASSETS_DIR, OUTPUTS_DIR, FONTS_DIR, MUSIC_DIR):
    d.mkdir(parents=True, exist_ok=True)
