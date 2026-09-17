#!/usr/bin/env python3
"""
Genera un solo audio que recorre TODOS los hablantes en español disponibles
en el backend de respaldo (espeak-ng), cada uno diciendo su nombre y una
frase de muestra — útil para escuchar y comparar antes de decidir cuál usar
por defecto.

Nota: esto es sobre las voces "de fábrica" de espeak-ng (el respaldo offline).
Piper (el motor de producción) también tiene varios modelos de voz en
español, pero esos hay que descargarlos primero (ver README) — no vienen
instalados en el sistema, así que no se pueden listar/probar así.

Uso:
    python scripts/voice_sampler.py outputs/muestra_hablantes.wav
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DEFAULTS  # noqa: E402
from pipeline import audio_processor  # noqa: E402
from pipeline.tts_engine import EspeakBackend  # noqa: E402

# Todos los "hablantes" de español que trae espeak-ng en este sistema:
# los dos de síntesis por formantes (genéricos) + los siete de MBROLA
# (voces grabadas de una persona real, se oyen más naturales).
VOICES = [
    ("es", "Español España, síntesis por formantes"),
    ("es-419", "Español Latinoamérica, síntesis por formantes"),
    ("mb/mb-es1", "España, hablante masculino 1 (MBROLA)"),
    ("mb/mb-es2", "España, hablante masculino 2 (MBROLA)"),
    ("mb/mb-es3", "España, hablante femenino (MBROLA)"),
    ("mb/mb-es4", "España, hablante masculino 4 (MBROLA)"),
    ("mb/mb-mx1", "México, hablante masculino 1 (MBROLA)"),
    ("mb/mb-mx2", "México, hablante masculino 2 (MBROLA)"),
    ("mb/mb-vz1", "Venezuela, hablante masculino (MBROLA)"),
]

SAMPLE_TEXT = "Esta es una muestra de esta voz, leyendo el mismo texto que las demás para poder compararlas."


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/voice_sampler.py <ruta_salida.wav>")
        sys.exit(1)

    out_path = Path(sys.argv[1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = out_path.parent / "_voice_sampler_tmp"
    work_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    for voice_id, label in VOICES:
        print(f"Generando muestra de: {voice_id} — {label}")
        backend = EspeakBackend(voice=voice_id, speed_wpm=DEFAULTS.espeak_speed_wpm, pitch=DEFAULTS.espeak_pitch)
        safe_name = voice_id.replace("/", "_")

        intro_path = work_dir / f"{safe_name}_intro.wav"
        sample_path = work_dir / f"{safe_name}_sample.wav"
        gap_path = work_dir / f"{safe_name}_gap.wav"

        backend.synthesize(f"Hablante: {label}.", intro_path)
        backend.synthesize(SAMPLE_TEXT, sample_path)
        _make_silence(gap_path, 700)  # medio segundo largo de silencio entre hablantes

        clip_paths += [intro_path, sample_path, gap_path]

    concatenated = audio_processor.concat_wavs(clip_paths, work_dir / "concatenado.wav")
    normalized = audio_processor.normalize_loudness(concatenated, out_path.with_suffix(".wav"))

    print(f"\nListo: {normalized}")
    print(f"Contiene {len(VOICES)} hablantes, en este orden:")
    for i, (voice_id, label) in enumerate(VOICES, start=1):
        print(f"  {i}. {voice_id} — {label}")


def _make_silence(path: Path, ms: int) -> None:
    import subprocess

    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=22050:cl=mono",
        "-t", f"{ms / 1000:.3f}",
        "-c:a", "pcm_s16le",
        str(path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)


if __name__ == "__main__":
    main()
