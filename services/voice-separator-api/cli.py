#!/usr/bin/env python3
"""
CLI para probar la separación sin levantar la API.

Uso:
    python cli.py mezcla.wav outputs/
    python cli.py mezcla.wav outputs/ --backend centerchannel
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from separator import get_backend


def main() -> None:
    parser = argparse.ArgumentParser(description="Separa voz de instrumental en un audio.")
    parser.add_argument("audio", help="Ruta al audio de entrada (voz + música mezcladas)")
    parser.add_argument("out_dir", help="Carpeta donde dejar vocals.wav y accompaniment.wav")
    parser.add_argument(
        "--backend", default="spleeter", choices=["spleeter", "centerchannel"],
        help="spleeter = calidad real (default, necesita el modelo descargado la primera vez). "
        "centerchannel = truco instantáneo sin descargas, mucho más burdo.",
    )
    args = parser.parse_args()

    print(f"[cli] Separando '{args.audio}' con backend '{args.backend}'...")
    start = time.time()

    engine = get_backend(args.backend)
    result = engine.separate(Path(args.audio), Path(args.out_dir))

    elapsed = time.time() - start
    print(f"[cli] Listo en {elapsed:.1f}s")
    print(f"  Voz:          {result.vocals_path}")
    print(f"  Instrumental: {result.instrumental_path}")


if __name__ == "__main__":
    main()
