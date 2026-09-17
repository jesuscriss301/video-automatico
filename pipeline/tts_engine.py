"""
Motor de texto a voz.

Tiene dos backends intercambiables:

- "piper" (recomendado, calidad de producción): usa Piper TTS (MIT, CPU-only,
  https://github.com/rhasspy/piper). Necesita un modelo de voz descargado una
  vez (ver README). Los modelos se bajan de Hugging Face, así que esta parte
  requiere que la máquina donde corra esto tenga salida a huggingface.co
  (en este sandbox de desarrollo esa salida está bloqueada por política de
  red, así que aquí se prueba con el backend "espeak" — en tu servidor/PC no
  debería haber ese problema).

- "espeak" (fallback offline, calidad robótica): usa espeak-ng, que no
  necesita descargar nada. Sirve para probar el pipeline completo sin
  depender de internet, o como respaldo si Piper falla.

Ambos backends devuelven lo mismo: un WAV por escena + su duración exacta,
que es lo único que el resto del pipeline necesita.
"""
from __future__ import annotations

import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

from config.settings import DEFAULTS
from pipeline.models import Scene


@dataclass
class SynthesizedAudio:
    path: Path
    duration_seconds: float


class TTSEngineError(RuntimeError):
    pass


def _wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


class EspeakBackend:
    """Backend offline de respaldo. No requiere descargar ningún modelo.

    Expone las mismas dos perillas "universales" que casi cualquier motor de
    TTS tiene (velocidad y tono), útiles aquí para probar rápido que un
    cambio de parámetro sí suena distinto, sin depender de Piper."""

    name = "espeak"

    def __init__(
        self,
        voice: str = "es",
        speed_wpm: int | None = None,
        pitch: int | None = None,
    ):
        if shutil.which("espeak-ng") is None:
            raise TTSEngineError(
                "espeak-ng no está instalado. Instálalo con: apt-get install espeak-ng"
            )
        self.voice = voice
        self.speed_wpm = speed_wpm if speed_wpm is not None else DEFAULTS.espeak_speed_wpm
        self.pitch = pitch if pitch is not None else DEFAULTS.espeak_pitch

    def synthesize(self, text: str, out_path: Path) -> SynthesizedAudio:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "espeak-ng",
            "-v",
            self.voice,
            "-s",
            str(self.speed_wpm),
            "-p",
            str(self.pitch),
            "-w",
            str(out_path),
            text,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise TTSEngineError(f"espeak-ng falló: {result.stderr}")
        return SynthesizedAudio(path=out_path, duration_seconds=_wav_duration_seconds(out_path))


class PiperBackend:
    """
    Backend de producción. Requiere:
      pip install piper-tts
      python -m piper.download_voices <voz> --download-dir assets/voices

    La voz por defecto se define en config/settings.py (DEFAULTS.piper_voice).

    Hay dos formas de tener una voz "distinta" con Piper, y son cosas
    diferentes:

    1) Cambiar de modelo (`voice=`): cada modelo .onnx es un hablante
       distinto entrenado por separado (davefx, sharvard, mls, carlfm...).
       Esto SÍ es una voz nueva de verdad — solo hay que descargarla.

    2) Tocar los parámetros de síntesis (`length_scale`, `noise_scale`,
       `noise_w_scale`, `speaker_id`): esto NO cambia de hablante, varía
       cómo suena el MISMO modelo — más rápido/lento, más "plano" o más
       "expresivo", ritmo más o menos robótico. `speaker_id` sí cambia de
       hablante, pero solo si el .onnx que descargaste es multi-hablante
       (la mayoría de las voces en español no lo son).
    """

    name = "piper"

    def __init__(
        self,
        voice: str | None = None,
        voices_dir: Path | None = None,
        length_scale: float | None = None,
        noise_scale: float | None = None,
        noise_w_scale: float | None = None,
        speaker_id: int | None = None,
    ):
        try:
            from piper import PiperVoice  # import diferido: no todos los entornos lo tienen
            from piper.config import SynthesisConfig
        except ImportError as exc:  # pragma: no cover
            raise TTSEngineError(
                "piper-tts no está instalado. Instálalo con: pip install piper-tts"
            ) from exc

        self.voice_name = voice or DEFAULTS.piper_voice
        self.voices_dir = voices_dir or (Path(__file__).resolve().parent.parent / "assets" / "voices")
        model_path = self.voices_dir / f"{self.voice_name}.onnx"
        config_path = self.voices_dir / f"{self.voice_name}.onnx.json"

        if not model_path.exists():
            raise TTSEngineError(
                f"No se encontró el modelo de voz en {model_path}. "
                f"Descárgalo con: python -m piper.download_voices {self.voice_name} "
                f"--download-dir {self.voices_dir}"
            )

        self._voice = PiperVoice.load(str(model_path), config_path=str(config_path) if config_path.exists() else None)

        self._syn_config = SynthesisConfig(
            speaker_id=speaker_id if speaker_id is not None else DEFAULTS.piper_speaker_id,
            length_scale=length_scale if length_scale is not None else DEFAULTS.piper_length_scale,
            noise_scale=noise_scale if noise_scale is not None else DEFAULTS.piper_noise_scale,
            noise_w_scale=noise_w_scale if noise_w_scale is not None else DEFAULTS.piper_noise_w_scale,
        )

    def synthesize(self, text: str, out_path: Path) -> SynthesizedAudio:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out_path), "wb") as wav_file:
            self._voice.synthesize_wav(text, wav_file, syn_config=self._syn_config)
        return SynthesizedAudio(path=out_path, duration_seconds=_wav_duration_seconds(out_path))


def get_backend(name: str = "piper", **kwargs):
    if name == "piper":
        return PiperBackend(**kwargs)
    if name == "espeak":
        return EspeakBackend(**kwargs)
    raise ValueError(f"Backend de TTS desconocido: {name}")


def synthesize_scene(scene: Scene, backend, work_dir: Path) -> SynthesizedAudio:
    """Sintetiza el audio de una escena y le agrega la micro-pausa configurada
    (o la de la escena, si la define) al final, para que la voz no suene
    'atropellada' al pegar una escena con la siguiente."""
    raw_path = work_dir / f"{scene.id}.raw.wav"
    audio = backend.synthesize(scene.text, raw_path)

    pause_ms = scene.pause_after_ms if scene.pause_after_ms is not None else DEFAULTS.silence_between_scenes_ms
    if pause_ms <= 0:
        return audio

    final_path = work_dir / f"{scene.id}.wav"
    _append_silence(audio.path, final_path, pause_ms)
    return SynthesizedAudio(path=final_path, duration_seconds=audio.duration_seconds + pause_ms / 1000.0)


def _append_silence(src: Path, dst: Path, ms: int) -> None:
    import ffmpeg

    (
        ffmpeg.input(str(src))
        .filter("apad", pad_dur=ms / 1000.0)
        .output(str(dst), acodec="pcm_s16le")
        .overwrite_output()
        .run(quiet=True)
    )
