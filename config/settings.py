"""
Configuración central del pipeline. Todo lo que define "qué tan buena"
sale la calidad del video vive aquí, para no tener números mágicos
regados por el código.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:  # opcional: permite dejar los ajustes en un archivo .env
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # pragma: no cover
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FONTS_DIR = ASSETS_DIR / "fonts"
MUSIC_DIR = ASSETS_DIR / "music"


def _env(nombre: str, default):
    """Lee una variable de entorno (o del archivo .env) y la convierte al tipo
    del valor por defecto. Permite cambiar cómo se codifica el video sin tocar
    el código: por ejemplo VIDEO_ENCODER=h264_qsv para usar la gráfica Intel."""
    raw = os.getenv(nombre)
    if raw is None or raw == "":
        return default
    if isinstance(default, bool):
        return raw.strip().lower() in ("1", "true", "yes", "si", "sí", "on")
    if isinstance(default, int):
        try:
            return int(raw)
        except ValueError:
            return default
    if isinstance(default, float):
        try:
            return float(raw)
        except ValueError:
            return default
    return raw


@dataclass
class VideoQuality:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    # CRF más bajo = más calidad / archivo más pesado. 17-18 es "casi visualmente
    # sin pérdida" para H.264.
    # El CRF es la perilla de CALIDAD (no de velocidad): se deja en 17, que es
    # "casi sin pérdida visible". Para bajar consumo se toca el preset, que es
    # lo que de verdad cuesta CPU.
    crf: int = field(default_factory=lambda: _env("VIDEO_CRF", 17))
    # "auto" = detecta y usa la gráfica más rápida que funcione en esta máquina
    # (dedicada NVIDIA > integrada Intel > AMD), y si ninguna sirve, el
    # procesador. También se puede fijar a mano: libx264, h264_nvenc,
    # h264_qsv, h264_amf.
    video_codec: str = field(default_factory=lambda: _env("VIDEO_ENCODER", "auto"))
    pixel_format: str = "yuv420p"
    # El preset es EL factor que más pesa en el consumo de CPU del render
    # (medido: preset slow tarda ~2.4x más que veryfast en el mismo video, y
    # el encode es ~88% del tiempo total del paso final). "fast" es el punto
    # medio razonable; "veryfast" si quieres el PC libre cuanto antes.
    preset: str = field(default_factory=lambda: _env("VIDEO_PRESET", "fast"))
    audio_codec: str = "aac"
    audio_bitrate: str = "320k"

    # --- Aceleración por hardware (gráfica Intel / NVIDIA) ---
    # h264_qsv usa la gráfica integrada Intel (Quick Sync) y baja el uso de CPU
    # drásticamente, porque el encode deja de hacerlo el procesador. Requiere
    # que el ffmpeg instalado traiga QSV compilado (los builds de gyan.dev para
    # Windows sí) y una gráfica Intel con Quick Sync (Iris Plus la tiene).
    # Comprobarlo con: python scripts/check_hw.py
    # Los encoders de hardware no usan CRF sino "global_quality" (misma idea:
    # menos = mejor calidad).
    qsv_global_quality: int = field(default_factory=lambda: _env("VIDEO_QSV_QUALITY", 22))

    # 0 = todos los hilos. Poner 2-4 deja cores libres para trabajar mientras
    # renderiza (a cambio de más tiempo total).
    threads: int = field(default_factory=lambda: _env("VIDEO_THREADS", 0))

    # Los clips intermedios de cada escena se vuelven a codificar en el paso
    # final, así que no tiene sentido gastar CPU en comprimirlos bien: con
    # ultrafast el paso 1 baja de ~8.3s a ~3.2s por escena (medido).
    intermediate_preset: str = field(default_factory=lambda: _env("VIDEO_INTERMEDIATE_PRESET", "ultrafast"))
    intermediate_crf: int = field(default_factory=lambda: _env("VIDEO_INTERMEDIATE_CRF", 18))

    # Cuánto más grande que la salida se escala la imagen antes del Ken Burns.
    # Solo hace falta un poco más que el zoom máximo (1.12): con 3840 fijo se
    # gastaba CPU de más en cada frame.
    kenburns_oversample: float = field(default_factory=lambda: _env("VIDEO_KENBURNS_OVERSAMPLE", 1.25))

    # Lanza ffmpeg con prioridad baja: usa la CPU que sobre, pero el resto del
    # sistema (navegador, editor) sigue respondiendo aunque marque 99%.
    low_priority: bool = field(default_factory=lambda: _env("VIDEO_LOW_PRIORITY", True))


@dataclass
class QualityDefaults:
    video: VideoQuality = field(default_factory=VideoQuality)

    # --- Audio ---
    target_lufs: float = -16.0  # estándar de loudness para streaming/redes
    # Frecuencia del audio en el video final. 48kHz es el estándar de entrega
    # de video; sin fijarlo, el filtro loudnorm dejaba el audio en 96kHz.
    audio_output_hz: int = 48000
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

    # Dónde generar la voz clonada (Chatterbox): "auto" usa la gráfica NVIDIA
    # si hay una con CUDA (pasa de minutos a segundos por escena), y si no,
    # el procesador. "cpu" o "cuda" lo fuerzan.
    # OJO: esto solo lo acelera una NVIDIA. Quick Sync (Intel) sirve para
    # codificar video, no para redes neuronales.
    tts_device: str = field(default_factory=lambda: _env("TTS_DEVICE", "auto"))

    # --- Cola de trabajos ---
    # Cuántos videos se generan a la vez. 1 = uno detrás de otro: es lo
    # correcto en un PC, porque dos renders peleándose el procesador tardan
    # más que en fila y arriesgan quedarse sin memoria.
    job_workers: int = field(default_factory=lambda: _env("JOB_WORKERS", 1))

    # Perillas de Piper para variar la voz SIN cambiar de modelo (ver README):
    # - length_scale: < 1 más rápido / > 1 más lento (también cambia el "peso" percibido de la voz)
    # - noise_scale: cuánta variación aleatoria mete el modelo al generar (más alto = más "vivo"/menos plano)
    # - noise_w_scale: variación en la duración de cada fonema (más alto = ritmo menos robótico)
    # - speaker_id: solo aplica si el modelo de voz es multi-hablante (varias voces en un mismo .onnx)
    # None = usar el valor por defecto que trae el propio modelo.
    piper_length_scale: Optional[float] = None
    piper_noise_scale: Optional[float] = None
    piper_noise_w_scale: Optional[float] = None
    piper_speaker_id: Optional[int] = None

    # Perillas del backend de respaldo (espeak-ng), para poder probar el efecto
    # de "voz distinta" en este mismo sandbox sin depender de Piper.
    # pitch=15 quedó guardado como default porque fue la variante "grave" que
    # se probó y gustó (ver outputs/demo_voz_grave.mp4); el default de fábrica
    # de espeak-ng es 50.
    espeak_pitch: int = 15
    espeak_speed_wpm: int = 165


DEFAULTS = QualityDefaults()

for d in (ASSETS_DIR, OUTPUTS_DIR, FONTS_DIR, MUSIC_DIR):
    d.mkdir(parents=True, exist_ok=True)
