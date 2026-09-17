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
        "--keep-work-dir", action="store_true",
        help="No borrar los archivos intermedios (útil para depurar)",
    )
    args = parser.parse_args()

    print(f"[run_pipeline] Generando video desde '{args.script}' con backend de TTS '{args.tts}'...")
    start = time.time()

    report = generate_video(
        script_path=args.script,
        output_path=args.output,
        tts_backend=args.tts,
        keep_work_dir=args.keep_work_dir,
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
