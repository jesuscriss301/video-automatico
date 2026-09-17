#!/usr/bin/env python3
"""
Genera imágenes de prueba (con Pillow) para poder correr el pipeline sin
depender de fotos reales del cliente. Sirve para validar que todo el flujo
funciona antes de conectar assets de verdad.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "images" / "sample"

# Tamaños grandes a propósito, para que ya cumplan el margen que pide
# image_processor.ensure_quality (1.5x de 1920x1080) sin necesitar upscaling.
SIZE = (3200, 1800)
COLORS = [
    ("#1f2937", "#f9fafb"),
    ("#7c2d12", "#fef3c7"),
    ("#064e3b", "#d1fae5"),
    ("#1e3a8a", "#dbeafe"),
]
LABELS = ["Escena 1", "Escena 2", "Escena 3", "Escena 4"]


def make_image(index: int, label: str, bg: str, fg: str) -> Path:
    img = Image.new("RGB", SIZE, color=bg)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140
        )
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((SIZE[0] - w) / 2, (SIZE[1] - h) / 2),
        label, font=font, fill=fg,
    )

    # Un marco simple para que se note el zoom/pan del Ken Burns.
    draw.rectangle([40, 40, SIZE[0] - 40, SIZE[1] - 40], outline=fg, width=8)

    out_path = OUT_DIR / f"scene_{index}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def main() -> None:
    for i, (label, (bg, fg)) in enumerate(zip(LABELS, COLORS), start=1):
        path = make_image(i, label, bg, fg)
        print(f"Generada: {path}")


if __name__ == "__main__":
    main()
