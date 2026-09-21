#!/usr/bin/env python3
"""
Revisa qué aceleración de video por hardware tiene ESTA máquina y te dice
exactamente qué poner en el archivo .env para usarla.

No solo mira si el encoder está compilado en ffmpeg (eso no garantiza nada):
intenta codificar de verdad un video de prueba de 2 segundos con cada uno, y
mide cuánto tarda. Así sabes si funciona y cuánto ganas.

Uso:
    python scripts/check_hw.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# (encoder, argumentos de calidad, qué gráfica lo usa)
CANDIDATOS = [
    ("h264_qsv", ["-global_quality", "22", "-preset", "medium", "-pix_fmt", "nv12"],
     "gráfica integrada Intel (Quick Sync) — Iris Plus, UHD, etc."),
    ("h264_nvenc", ["-rc", "vbr", "-cq", "22", "-preset", "p5"], "gráfica NVIDIA"),
    ("h264_amf", ["-rc", "cqp", "-qp_i", "22", "-qp_p", "22"], "gráfica AMD"),
]

FUENTE = ["-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30:duration=2"]


def _encoders_compilados() -> set[str]:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
    return {linea.split()[1] for linea in out.stdout.splitlines() if len(linea.split()) > 1}


def _probar(encoder: str, args: list[str], destino: Path) -> tuple[bool, float, str]:
    cmd = ["ffmpeg", "-y", *FUENTE, "-c:v", encoder, *args, str(destino)]
    inicio = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - inicio
    if res.returncode != 0:
        # Se buscan las líneas que de verdad explican el fallo (falta el
        # dispositivo, driver viejo...) y no el genérico del final.
        utiles = [
            l.strip() for l in res.stderr.splitlines()
            if any(p in l.lower() for p in ("error", "cannot", "failed", "no device", "not supported", "unavailable"))
        ]
        motivo = " / ".join(utiles[:2]) or res.stderr.strip().splitlines()[-1].strip()
        return False, elapsed, motivo
    return True, elapsed, ""


def main() -> None:
    if shutil.which("ffmpeg") is None:
        print("No encuentro ffmpeg en el PATH. Instálalo primero (en Windows: winget install --id Gyan.FFmpeg -e)")
        sys.exit(1)

    tmp = Path(__file__).resolve().parent.parent / "outputs" / "_check_hw"
    tmp.mkdir(parents=True, exist_ok=True)

    compilados = _encoders_compilados()

    print("Probando encoders de video de 1920x1080 (2 segundos cada uno)...\n")

    # Referencia en CPU, para poder comparar
    ok_cpu, t_cpu, _ = _probar("libx264", ["-preset", "fast", "-crf", "19"], tmp / "cpu.mp4")
    if ok_cpu:
        print(f"  libx264 (CPU, preset fast)   OK   {t_cpu:5.1f}s   <- referencia")
    else:
        print("  libx264 (CPU)                FALLA (raro: algo pasa con tu ffmpeg)")

    funcionan = []
    for encoder, args, descripcion in CANDIDATOS:
        if encoder not in compilados:
            print(f"  {encoder:<28} no viene en este build de ffmpeg")
            continue
        ok, elapsed, motivo = _probar(encoder, args, tmp / f"{encoder}.mp4")
        if ok:
            veces = f"{t_cpu / elapsed:.1f}x más rápido que la CPU" if ok_cpu and elapsed > 0 else ""
            print(f"  {encoder:<28} OK   {elapsed:5.1f}s   {veces}")
            funcionan.append((encoder, elapsed, descripcion))
        else:
            print(f"  {encoder:<28} no funciona aquí: {motivo[:110]}")

    print()
    if funcionan:
        mejor = min(funcionan, key=lambda f: f[1])
        print(f"Recomendado: {mejor[0]} ({mejor[2]}).")
        print("Para usarlo, crea (o edita) el archivo .env en la raíz del proyecto con:")
        print()
        print(f"    VIDEO_ENCODER={mejor[0]}")
        print("    VIDEO_QSV_QUALITY=22")
        print()
        print("Y vuelve a arrancar el servidor. Si algún día falla, el render se")
        print("reintenta solo con la CPU, no se pierde el video.")
    else:
        print("No hay aceleración por hardware usable en esta máquina.")
        print("Para bajar el consumo de CPU, en el archivo .env:")
        print()
        print("    VIDEO_PRESET=veryfast     # el encode es lo que más CPU gasta")
        print("    VIDEO_CRF=21              # un poco menos de calidad, archivos más chicos")
        print("    VIDEO_THREADS=4           # deja cores libres para trabajar")
        print("    VIDEO_LOW_PRIORITY=true   # ya viene así: el PC sigue usable")

    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
