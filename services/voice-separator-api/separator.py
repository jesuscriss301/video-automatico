"""
Motor de separación voz / instrumental.

Dos backends, mismo patrón que el resto del proyecto (Piper vs espeak,
Chatterbox vs nada): uno de calidad real basado en un modelo entrenado, y uno
de respaldo instantáneo sin dependencias pesadas ni descargas, útil para
probar que el resto del sistema (API, subida de archivos, etc.) funciona
mientras se decide si vale la pena esperar el modelo.

- "spleeter" (recomendado, calidad real): usa Spleeter (Deezer, MIT,
  https://github.com/deezer/spleeter), un modelo entrenado específicamente
  para separar voz de instrumental. Descarga su modelo (~73MB) una sola vez
  desde GitHub releases. Corre en CPU sin problema.

- "centerchannel" (respaldo instantáneo, sin descargas): truco clásico de
  cancelación de fase usado antes de que existiera separación por IA. Le
  resta un canal al otro para aislar lo que está paneado al centro de la
  mezcla (donde casi siempre está la voz principal). Es MUCHO más burdo:
  no aísla voz de verdad, solo remueve o resalta lo que está centrado —
  funciona razonablemente en mezclas comerciales estéreo bien producidas, y
  NO funciona en audio mono (necesita dos canales distintos para poder
  restar uno del otro) ni en mezclas paneadas de forma no convencional.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class SeparationError(RuntimeError):
    pass


@dataclass
class SeparationResult:
    vocals_path: Path
    instrumental_path: Path
    backend: str


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SeparationError(f"Comando falló: {' '.join(cmd)}\n{result.stderr[-2000:]}")


def _to_stereo_wav(src: Path, dst: Path, sample_rate: int = 44100) -> Path:
    """Normaliza cualquier audio de entrada (mp3, m4a, wav mono, etc.) a un
    WAV estéreo PCM, que es lo que ambos backends esperan."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-ac", "2", "-ar", str(sample_rate), "-c:a", "pcm_s16le",
        str(dst),
    ]
    _run(cmd)
    return dst


class SpleeterBackend:
    """Backend de producción: separación real por IA (Deezer Spleeter,
    modelo `spleeter:2stems` — voz vs. todo lo demás).

    IMPORTANTE — instalar en su propio entorno virtual, NO junto al resto del
    proyecto: Spleeter depende de TensorFlow con versiones de numpy/protobuf/
    typing-extensions bastante viejas que chocan con FastAPI/Pydantic del
    pipeline de video (lo comprobamos: instalarlo en el mismo venv rompió
    fastapi). Por eso este servicio vive aislado en
    services/voice-separator-api/ con su propio requirements.txt y su propio
    venv — un microservicio real de la "red de APIs", no un módulo más
    dentro del pipeline de Flujo 1.
    """

    name = "spleeter"

    def __init__(self, model: str = "spleeter:2stems", model_dir: Path | None = None):
        try:
            from spleeter.separator import Separator
        except ImportError as exc:  # pragma: no cover
            raise SeparationError(
                "spleeter no está instalado en este entorno. Instálalo con: "
                "pip install -r requirements.txt (dentro del venv de este servicio)"
            ) from exc

        self.model = model
        # Carpeta donde Spleeter cachea el modelo descargado (~73MB, una sola
        # vez). Por defecto queda relativa al directorio desde donde se corre
        # el proceso — lo fijamos explícito para que sea predecible sin
        # importar desde dónde se invoque este servicio.
        self.model_dir = model_dir or (Path(__file__).resolve().parent / "pretrained_models")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        import os
        os.environ.setdefault("MODEL_PATH", str(self.model_dir))

        self._separator = Separator(model, multiprocess=False)

    def separate(self, audio_path: Path, out_dir: Path) -> SeparationResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        normalized = _to_stereo_wav(audio_path, out_dir / "_input_normalizado.wav")

        # Separator.separate_to_file crea <out_dir>/<nombre_sin_extension>/{vocals,accompaniment}.wav
        self._separator.separate_to_file(str(normalized), str(out_dir))
        stem_dir = out_dir / normalized.stem

        vocals = stem_dir / "vocals.wav"
        instrumental = stem_dir / "accompaniment.wav"
        if not vocals.exists() or not instrumental.exists():
            raise SeparationError(
                f"Spleeter no generó los archivos esperados en {stem_dir}"
            )
        return SeparationResult(vocals_path=vocals, instrumental_path=instrumental, backend=self.name)


class CenterChannelBackend:
    """Respaldo offline instantáneo, sin modelo ni descargas: cancelación de
    fase entre canales L/R (el truco "karaoke" de toda la vida).

    - instrumental ≈ L - R  (cancela lo que está centrado — usualmente la voz)
    - "voz"        ≈ (L + R) / 2  (solo remarca el centro, NO aísla la voz de
      verdad — sigue sonando con música de fondo encima, solo que la voz
      queda relativamente más presente)

    Sirve para probar rápido que la API/el flujo de subida-y-descarga
    funciona, o como demo instantánea. Para un resultado que realmente aísle
    la voz, usar el backend "spleeter".
    """

    name = "centerchannel"

    def __init__(self):
        if shutil.which("ffmpeg") is None:
            raise SeparationError("ffmpeg no está instalado.")

    def separate(self, audio_path: Path, out_dir: Path) -> SeparationResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        normalized = _to_stereo_wav(audio_path, out_dir / "_input_normalizado.wav")

        instrumental = out_dir / "accompaniment.wav"
        vocals = out_dir / "vocals.wav"

        _run([
            "ffmpeg", "-y", "-i", str(normalized),
            "-af", "pan=stereo|c0=c0-c1|c1=c1-c0",
            str(instrumental),
        ])
        _run([
            "ffmpeg", "-y", "-i", str(normalized),
            "-af", "pan=mono|c0=0.5*c0+0.5*c1",
            str(vocals),
        ])
        return SeparationResult(vocals_path=vocals, instrumental_path=instrumental, backend=self.name)


def get_backend(name: str = "spleeter", **kwargs):
    if name == "spleeter":
        return SpleeterBackend(**kwargs)
    if name == "centerchannel":
        return CenterChannelBackend(**kwargs)
    raise ValueError(f"Backend de separación desconocido: {name}")
