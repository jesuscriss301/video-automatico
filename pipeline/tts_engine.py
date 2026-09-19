"""
Motor de texto a voz.

Tiene tres backends intercambiables:

- "piper" (recomendado, calidad de producción con voces prefabricadas): usa
  Piper TTS (MIT, CPU-only, https://github.com/rhasspy/piper). Necesita un
  modelo de voz descargado una vez (ver README). Los modelos se bajan de
  Hugging Face, así que esta parte requiere que la máquina donde corra esto
  tenga salida a huggingface.co (en este sandbox de desarrollo esa salida
  está bloqueada por política de red, así que aquí se prueba con el backend
  "espeak" — en tu servidor/PC no debería haber ese problema).

- "espeak" (fallback offline, calidad robótica): usa espeak-ng, que no
  necesita descargar nada. Sirve para probar el pipeline completo sin
  depender de internet, o como respaldo si Piper falla.

- "chatterbox" (clonación de voz — tu propio hablante): usa Chatterbox
  (MIT, https://github.com/resemble-ai/chatterbox) para clonar cualquier voz
  a partir de un audio de referencia corto. También descarga su modelo de
  Hugging Face la primera vez, así que aplica la misma limitación de red que
  Piper en este sandbox — ver el docstring de ChatterboxBackend más abajo.

Los tres backends devuelven lo mismo: un WAV por escena + su duración exacta,
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
    # Usamos ffprobe en vez del módulo `wave` de Python porque `wave` solo
    # entiende WAV en PCM entero (formato 1) — un WAV en float32 (formato 3,
    # lo que escribe torchaudio.save por defecto, como hace ChatterboxBackend)
    # lo revienta con "unknown format: 3". ffprobe lee cualquier variante.
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise TTSEngineError(f"No se pudo leer la duración de {path}: {result.stderr}")
    return float(result.stdout.strip())


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


class ChatterboxBackend:
    """
    Backend de CLONACIÓN de voz — esta es la respuesta a "quiero mi propio
    hablante". Usa Chatterbox (Resemble AI, MIT, https://github.com/resemble-ai/chatterbox),
    que a partir de 10-30 segundos de un audio de referencia (tu voz, la de
    otra persona con su permiso, o un locutor que contrates) genera CUALQUIER
    texto con esa voz. No hace falta entrenar nada.

    Requiere instalar dependencias pesadas aparte (ver requirements-chatterbox.txt):
      pip install -r requirements-chatterbox.txt

    Y, muy importante: la primera vez que se usa, descarga automáticamente el
    modelo (~2 GB) desde Hugging Face. Esa descarga necesita una máquina con
    internet normal — no funciona desde un entorno que Claude controle
    directamente (este sandbox de desarrollo, o el equipo del usuario cuando
    Claude opera ahí), porque esos entornos tienen bloqueado el acceso a
    huggingface.co por política de red. Corre esto en tu propia terminal o en
    tu servidor de producción.
    """

    name = "chatterbox"

    def __init__(
        self,
        voice_sample: str | Path,
        language_id: str = "es",
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
        temperature: float = 0.8,
        device: str = "cpu",
        max_chars_per_chunk: int = 280,
    ):
        self.max_chars_per_chunk = max_chars_per_chunk
        self.voice_sample = Path(voice_sample)
        if not self.voice_sample.exists():
            raise TTSEngineError(
                f"No se encontró el audio de referencia en {self.voice_sample}. "
                "Necesitas un WAV limpio de 10-30 segundos con la voz que quieres clonar "
                "(sin música ni ruido de fondo, una sola persona hablando)."
            )

        self.language_id = language_id
        self.exaggeration = exaggeration
        self.cfg_weight = cfg_weight
        self.temperature = temperature

        try:
            import torch
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        except ImportError as exc:  # pragma: no cover
            raise TTSEngineError(
                "chatterbox-tts no está instalado. Instálalo con: "
                "pip install -r requirements-chatterbox.txt"
            ) from exc

        resolved_device = device
        if resolved_device == "cuda" and not torch.cuda.is_available():
            resolved_device = "cpu"

        self._torch = torch
        self._model = ChatterboxMultilingualTTS.from_pretrained(device=resolved_device)

    def _generate_one(self, text: str):
        return self._model.generate(
            text,
            language_id=self.language_id,
            audio_prompt_path=str(self.voice_sample),
            exaggeration=self.exaggeration,
            cfg_weight=self.cfg_weight,
            temperature=self.temperature,
        )

    def synthesize(self, text: str, out_path: Path) -> SynthesizedAudio:
        import torchaudio

        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Un párrafo largo en una sola pasada sale atropellado o cortado: el
        # modelo tiene un tope de tokens por generación y, al acercarse, fuerza
        # el final de la frase. Por eso el texto se parte en trozos por frase
        # (ver split_for_cloning) y se genera cada uno por separado con la
        # MISMA voz de referencia, pegándolos con una pausa corta. Para textos
        # cortos esto es exactamente igual que antes: un solo trozo.
        chunks = split_for_cloning(text, self.max_chars_per_chunk)

        if len(chunks) == 1:
            wav = self._generate_one(chunks[0])
        else:
            torch = self._torch
            piezas = []
            silencio = torch.zeros(1, int(self._model.sr * 0.18))
            for i, chunk in enumerate(chunks):
                print(f"[chatterbox] trozo {i + 1}/{len(chunks)} ({len(chunk)} caracteres)")
                piezas.append(self._generate_one(chunk))
                if i < len(chunks) - 1:
                    piezas.append(silencio)
            wav = torch.cat(piezas, dim=1)
        # encoding/bits_per_sample explícitos: por defecto torchaudio.save
        # escribe float32 (formato WAV 3), que ffmpeg lee sin problema pero
        # es el doble de pesado y menos compatible en general que el PCM de
        # 16 bits (formato 1) que usan Piper y espeak en el resto del
        # pipeline — lo dejamos igual para todos los backends.
        torchaudio.save(str(out_path), wav, self._model.sr, encoding="PCM_S", bits_per_sample=16)
        return SynthesizedAudio(path=out_path, duration_seconds=_wav_duration_seconds(out_path))


def split_for_cloning(text: str, max_chars: int = 280) -> list[str]:
    """Parte un texto largo en trozos para clonación de voz, cortando SIEMPRE
    en final de frase cuando se puede (nunca a mitad de palabra).

    Por qué: los modelos de clonación generan bien tramos cortos, pero con un
    párrafo largo se quedan sin presupuesto de tokens y aceleran o cortan la
    última frase. Partir por frases y pegar los trozos suena mucho mejor que
    una sola pasada larga.

    Si una sola frase ya pasa del límite (frases kilométricas con muchas
    comas), se parte por comas y puntos y comas; y si aún así no cabe, por
    palabras — nunca a mitad de palabra.
    """
    text = " ".join(text.split())  # normaliza espacios y saltos de línea
    if len(text) <= max_chars:
        return [text] if text else [""]

    import re

    # Corta después de . ! ? … y de : ; cuando van seguidos de espacio.
    frases = [f.strip() for f in re.split(r"(?<=[.!?…])\s+", text) if f.strip()]

    trozos: list[str] = []
    actual = ""

    def empujar(pieza: str) -> None:
        nonlocal actual
        if not pieza:
            return
        if not actual:
            actual = pieza
        elif len(actual) + 1 + len(pieza) <= max_chars:
            actual = f"{actual} {pieza}"
        else:
            trozos.append(actual)
            actual = pieza

    for frase in frases:
        if len(frase) <= max_chars:
            empujar(frase)
            continue

        # Frase demasiado larga por sí sola: se parte por comas / puntos y coma.
        partes = [p.strip() for p in re.split(r"(?<=[,;:])\s+", frase) if p.strip()]
        for parte in partes:
            if len(parte) <= max_chars:
                empujar(parte)
                continue
            # Último recurso: por palabras.
            linea = ""
            for palabra in parte.split():
                if not linea:
                    linea = palabra
                elif len(linea) + 1 + len(palabra) <= max_chars:
                    linea = f"{linea} {palabra}"
                else:
                    empujar(linea)
                    linea = palabra
            empujar(linea)

    if actual:
        trozos.append(actual)

    return trozos


def get_backend(name: str = "piper", **kwargs):
    if name == "piper":
        return PiperBackend(**kwargs)
    if name == "espeak":
        return EspeakBackend(**kwargs)
    if name == "chatterbox":
        return ChatterboxBackend(**kwargs)
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
