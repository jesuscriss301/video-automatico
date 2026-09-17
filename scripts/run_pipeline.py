#!/usr/bin/env python3
"""
CLI para correr el Flujo 1 completo: guion -> video final.

Uso:
    python scripts/run_pipeline.py examples/sample_script.json outputs/mi_video.mp4
    python scripts/run_pipeline.py examples/sample_script.json outputs/mi_video.mp4 --tts espeak
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.run import generate_video  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera un video a partir de un guion (Flujo 1).")
    parser.add_argument("script", help="Ruta al guion JSON")
    parser.add_argument("output", help="Ruta del video de salida (.mp4)")
    parser.add_argument(
        "--tts", default="piper", choices=["piper", "espeak"],
        help="Backend de TTS a usar (default: piper; 'espeak' es el respaldo offline sin descargas)",
    )
    parser.add_argument(
        "--voice", default=None,
        help="Nombre del modelo de voz de Piper a usar (p.ej. es_ES-davefx-medium, es_ES-sharvard-medium). "
        "Cada modelo es un hablante distinto — esta es la forma de tener una voz realmente diferente.",
    )
    parser.add_argument(
        "--speaker-id", type=int, default=None,
        help="Índice del hablante dentro del modelo, solo si es un modelo Piper multi-hablante.",
    )
    parser.add_argument(
        "--length-scale", type=float, default=None,
        help="Velocidad de habla de Piper: <1 más rápido, >1 más lento (default del modelo si se omite).",
    )
    parser.add_argument(
        "--noise-scale", type=float, default=None,
        help="Expresividad/variación de Piper: más alto suena menos plano (default del modelo si se omite).",
    )
    parser.add_argument(
        "--noise-w-scale", type=float, default=None,
        help="Variación de ritmo por sílaba de Piper: más alto suena menos robótico (default del modelo si se omite).",
    )
    parser.add_argument(
        "--espeak-pitch", type=int, default=None,
        help="Solo con --tts espeak: tono de la voz, 0-99 (default 50).",
    )
    parser.add_argument(
        "--keep-work-dir", action="store_true",
        help="No borrar los archivos intermedios (útil para depurar)",
    )
    args = parser.parse_args()

    if args.tts == "piper":
        tts_options = {
            "voice": args.voice,
            "speaker_id": args.speaker_id,
            "length_scale": args.length_scale,
            "noise_scale": args.noise_scale,
            "noise_w_scale": args.noise_w_scale,
        }
    else:
        tts_options = {}
        if args.espeak_pitch is not None:
            tts_options["pitch"] = args.espeak_pitch
        if args.voice:
            tts_options["voice"] = args.voice

    print(f"[run_pipeline] Generando video desde '{args.script}' con backend de TTS '{args.tts}'...")
    start = time.time()

    report = generate_video(
        script_path=args.script,
        output_path=args.output,
        tts_backend=args.tts,
        keep_work_dir=args.keep_work_dir,
        tts_options=tts_options,
    )

    elapsed = time.time() - start
    print(f"[run_pipeline] Listo en {elapsed:.1f}s -> {args.output}")
    print(f"[run_pipeline] QA: {'OK' if report.ok else 'CON PROBLEMAS'}")
    if report.issues:
        for issue in report.issues:
            print(f"  - {issue}")

    if not report.ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
