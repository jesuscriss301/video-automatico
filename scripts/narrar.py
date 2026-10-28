#!/usr/bin/env python3
"""
Puente de voz: genera la narracion con una voz de este proyecto (incluida la
voz CLONADA de Chatterbox) y la deja lista para HyperFrames o Remotion.

Entrada: un JSON con las lineas a narrar, en orden.

    {
      "voz": "Voz clonada — referencia 20s",     # nombre en assets/voices_library.json
      "pausa_ms": 250,                           # opcional, silencio entre lineas
      "lineas": [
        {"id": "gancho", "texto": "Tu negocio pierde clientes cada noche."},
        {"id": "solucion", "texto": "Con un asistente en WhatsApp, responde solo."}
      ]
    }

Salida (en --salida):
    <id>.wav            una pista por linea
    narracion.wav       todas las lineas unidas, normalizada a -16 LUFS
    narracion.json      tiempos exactos: inicio/duracion de cada linea y de cada
                        subtitulo, mas "remotion_captions" (formato Caption de
                        @remotion/captions: text, startMs, endMs, timestampMs, confidence)

Uso:
    python scripts/narrar.py narracion.json --salida ../mi-video/assets/voz
    python scripts/narrar.py narracion.json --salida ../mi-remotion/public/voz --voz "Voz piper"

Los tiempos no se estiman: cada frase se sintetiza aparte y se mide su
duracion real (misma logica que el Flujo 1).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")  # OMP Error #15 con Anaconda
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from pipeline.models import Scene  # noqa: E402
from pipeline.tts_engine import get_backend, synthesize_scene, _wav_duration_seconds  # noqa: E402

PERMITIDAS = {
    "piper": {"voice", "speaker_id", "length_scale", "noise_scale", "noise_w_scale"},
    "espeak": {"voice", "speed_wpm", "pitch"},
    "chatterbox": {"voice_sample", "language_id", "exaggeration", "cfg_weight",
                   "temperature", "device", "max_chars_per_chunk"},
}


def cargar_voz(nombre: str) -> tuple[str, dict]:
    biblioteca = json.loads((RAIZ / "assets" / "voices_library.json").read_text(encoding="utf-8"))
    for voz in biblioteca:
        if voz["name"] == nombre:
            backend = voz["backend"]
            opciones = {k: v for k, v in (voz.get("options") or {}).items()
                        if k in PERMITIDAS[backend] and v not in (None, "")}
            return backend, opciones
    nombres = "\n  ".join(v["name"] for v in biblioteca)
    sys.exit(f"No encuentro la voz '{nombre}'. Voces guardadas:\n  {nombres}")


def unir_y_normalizar(partes: list[Path], destino: Path, lufs: float) -> None:
    lista = destino.with_suffix(".txt")
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
         "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1",
         "-c:a", "pcm_s16le", str(destino)],
        check=True,
    )
    lista.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Narracion con voz del proyecto para HyperFrames/Remotion")
    ap.add_argument("entrada", help="JSON con 'lineas' (y opcionalmente 'voz' y 'pausa_ms')")
    ap.add_argument("--salida", required=True, help="Carpeta destino (ej. assets/voz de HyperFrames o public/voz de Remotion)")
    ap.add_argument("--voz", help="Nombre de la voz guardada (pisa el del JSON)")
    ap.add_argument("--lufs", type=float, default=-16.0, help="Volumen final de la narracion (default -16 LUFS)")
    args = ap.parse_args()

    datos = json.loads(Path(args.entrada).read_text(encoding="utf-8"))
    nombre_voz = args.voz or datos.get("voz")
    if not nombre_voz:
        sys.exit("Falta la voz: ponla en el JSON ('voz') o con --voz.")
    backend_nombre, opciones = cargar_voz(nombre_voz)
    pausa = int(datos.get("pausa_ms", 250))

    salida = Path(args.salida).resolve()
    trabajo = salida / ".trabajo"
    trabajo.mkdir(parents=True, exist_ok=True)

    print(f"[narrar] voz: {nombre_voz} ({backend_nombre})")
    backend = get_backend(backend_nombre, **opciones)

    lineas_json, captions, partes = [], [], []
    cursor = 0.0
    for i, linea in enumerate(datos["lineas"]):
        lid = linea.get("id") or f"linea_{i + 1:02d}"
        print(f"[narrar] {i + 1}/{len(datos['lineas'])}: {lid}")
        escena = Scene(id=lid, text=linea["texto"], image_path="-",
                       pause_after_ms=linea.get("pausa_ms", pausa))
        audio = synthesize_scene(escena, backend, trabajo)
        wav = salida / f"{lid}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(audio.path), "-ar", "48000",
                        "-ac", "1", "-c:a", "pcm_s16le", str(wav)], check=True)
        partes.append(wav)
        cues = []
        for c in audio.cues:
            ini = round(cursor + c.start_seconds, 3)
            fin = round(ini + c.duration_seconds, 3)
            cues.append({"texto": c.text, "inicio": ini, "fin": fin})
            captions.append({"text": c.text, "startMs": int(ini * 1000), "endMs": int(fin * 1000),
                             "timestampMs": int(ini * 1000), "confidence": 1})
        dur = _wav_duration_seconds(wav)
        lineas_json.append({"id": lid, "texto": linea["texto"], "archivo": wav.name,
                            "inicio": round(cursor, 3), "duracion": round(dur, 3), "subtitulos": cues})
        cursor += dur

    unir_y_normalizar(partes, salida / "narracion.wav", args.lufs)
    resultado = {
        "voz": nombre_voz,
        "backend": backend_nombre,
        "duracion_total": round(_wav_duration_seconds(salida / "narracion.wav"), 3),
        "lineas": lineas_json,
        "remotion_captions": captions,
    }
    (salida / "narracion.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(trabajo, ignore_errors=True)
    print(f"[narrar] listo: {salida / 'narracion.wav'} ({resultado['duracion_total']} s)")


if __name__ == "__main__":
    main()
