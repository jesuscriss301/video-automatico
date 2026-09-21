#!/usr/bin/env python3
"""
Revisa qué aceleración por hardware tiene ESTA máquina y te dice exactamente
qué poner en el archivo .env para aprovecharla.

No se limita a mirar si el encoder viene compilado en ffmpeg (eso no garantiza
nada): intenta codificar de verdad un video de prueba con cada uno y mide
cuánto tarda. También comprueba si hay una gráfica NVIDIA usable por PyTorch,
que es lo único que acelera la clonación de voz.

Uso:
    python scripts/check_hw.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import hw  # noqa: E402


def main() -> None:
    if shutil.which("ffmpeg") is None:
        print("No encuentro ffmpeg en el PATH. Instálalo primero "
              "(en Windows: winget install --id Gyan.FFmpeg -e)")
        sys.exit(1)

    print("Probando de verdad cada encoder (1920x1080, 2 segundos)...\n")
    informe = hw.detectar(forzar=True)  # forzar: ignora la caché, re-prueba todo

    if informe.get("error"):
        print(informe["error"])
        sys.exit(1)

    encoders = informe.get("encoders", {})
    t_cpu = encoders.get("libx264", {}).get("segundos")

    print("CODIFICACIÓN DE VIDEO")
    for nombre, datos in encoders.items():
        etiqueta = f"  {nombre:<14}"
        if datos.get("funciona"):
            comparacion = ""
            if t_cpu and nombre != "libx264" and datos.get("segundos"):
                comparacion = f"  ({t_cpu / datos['segundos']:.1f}x más rápido que el procesador)"
            referencia = "  <- referencia" if nombre == "libx264" else ""
            print(f"{etiqueta} OK    {datos['segundos']:5.1f}s  {datos.get('descripcion','')}"
                  f"{comparacion}{referencia}")
        else:
            print(f"{etiqueta} no    {datos.get('motivo', 'no disponible')[:90]}")

    print("\nVOZ CLONADA (Chatterbox)")
    if informe.get("cuda"):
        print("  CUDA  OK    hay gráfica NVIDIA usable: la voz se generará ahí "
              "(de minutos a segundos por escena)")
    else:
        print("  CUDA  no    no hay gráfica NVIDIA usable por PyTorch; la voz se genera en el "
              "procesador.\n              (Quick Sync de Intel no sirve para esto: acelera video, "
              "no redes neuronales)")

    encoder, motivo = hw.mejor_encoder()
    print(f"\nEl sistema va a usar: {encoder} — {motivo}")
    print("Eso ya pasa solo, no hay que configurar nada (VIDEO_ENCODER=auto).\n")

    if encoder == "libx264":
        print("Para bajar el consumo de procesador, copia .env.example a .env y ajusta:")
        print("    VIDEO_PRESET=veryfast     # el encode es lo que más CPU gasta")
        print("    VIDEO_THREADS=4           # deja núcleos libres para trabajar")
        print("    VIDEO_LOW_PRIORITY=true   # ya viene activo: el PC sigue usable")
    else:
        print("Si algún día quieres forzarlo o volver al procesador, en .env:")
        print(f"    VIDEO_ENCODER={encoder}   # o libx264 para procesador")


if __name__ == "__main__":
    main()
