#!/usr/bin/env python3
"""
Video de muestra de voces: una tarjeta por cada voz guardada en
assets/voices_library.json, con el nombre de la voz en pantalla y una frase
corta dicha con esa voz. Sirve para comparar las voces de un vistazo antes de
elegir cuál usar en un video.

Uso:
    python scripts/muestra_voces.py
    python scripts/muestra_voces.py --frase "Hola, así sueno yo."
    python scripts/muestra_voces.py --voces "Voz piper,documentalista"
    python scripts/muestra_voces.py --salida outputs/mis_voces.mp4
    python scripts/muestra_voces.py --kokoro todas   # + las 54 voces Kokoro de HyperFrames
    python scripts/muestra_voces.py --kokoro no      # solo las voces de este proyecto

Por defecto incluye también las voces en español de Kokoro, el TTS gratuito y
local que trae HyperFrames (skill media-use): `npx hyperframes tts`. Necesita
Node y `pip install kokoro-onnx soundfile`; la primera vez descarga el modelo
(~300 MB) desde GitHub. Con `--kokoro todas` las voces de otros idiomas leen la
frase en español (con su acento), para ver cuáles sirven para tus videos.

Cada voz se normaliza al mismo volumen (-16 LUFS) para que la comparación sea
justa. Si una voz falla (por ejemplo, Chatterbox sin instalar), se salta y se
avisa al final; el video se arma con las que sí funcionaron.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")  # OMP Error #15 con Anaconda
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from pipeline.tts_engine import get_backend, _wav_duration_seconds  # noqa: E402

ANCHO, ALTO, FPS = 1920, 1080, 30
FONDO = (15, 17, 21)
TEXTO = (240, 242, 245)
SUAVE = (150, 156, 166)
ACENTO = (46, 204, 113)
FRASE = "Hola, esta es una prueba de voz. Así sonaría la narración de tus videos."
ANTES, DESPUES = 0.5, 0.7  # segundos de tarjeta antes y después de la voz

ETIQUETA_MOTOR = {
    "chatterbox": "Voz clonada · Chatterbox",
    "piper": "Voz prefabricada · Piper",
    "espeak": "Voz sintética · espeak",
}

IDIOMA_KOKORO = {
    "a": "inglés EE. UU.", "b": "inglés británico", "e": "español", "f": "francés",
    "h": "hindi", "i": "italiano", "j": "japonés", "p": "portugués", "z": "chino",
}
KOKORO = [
    "ef_dora", "em_alex", "em_santa",
    "af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", "af_kore", "af_nicole",
    "af_nova", "af_river", "af_sarah", "af_sky", "am_adam", "am_echo", "am_eric", "am_fenrir",
    "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa", "bf_alice", "bf_emma",
    "bf_isabella", "bf_lily", "bm_daniel", "bm_fable", "bm_george", "bm_lewis", "ff_siwis",
    "hf_alpha", "hf_beta", "hm_omega", "hm_psi", "if_sara", "im_nicola", "jf_alpha",
    "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo", "pf_dora", "pm_alex", "pm_santa",
    "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi", "zm_yunjian", "zm_yunxi",
    "zm_yunxia", "zm_yunyang",
]
NO_INCLUIDAS = [
    ("HeyGen", "voces y clonación de HyperFrames · necesita cuenta HeyGen"),
    ("ElevenLabs", "voz en off de Remotion y HyperFrames · necesita API key"),
    ("Gemini TTS", "opción de HyperFrames · necesita API key de Google"),
]

PERMITIDAS = {
    "piper": {"voice", "speaker_id", "length_scale", "noise_scale", "noise_w_scale"},
    "espeak": {"voice", "speed_wpm", "pitch"},
    "chatterbox": {"voice_sample", "language_id", "exaggeration", "cfg_weight",
                   "temperature", "device", "max_chars_per_chunk"},
}


def fuente(negrita: bool, tam: int) -> ImageFont.FreeTypeFont:
    candidatas = sorted((RAIZ / "assets" / "fonts").glob("*.ttf"))
    candidatas += [Path(p) for p in (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if negrita else
        ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )]
    for c in candidatas:
        if c.exists():
            return ImageFont.truetype(str(c), tam)
    return ImageFont.load_default(tam)


def partir(draw: ImageDraw.ImageDraw, texto: str, f, ancho_max: int) -> list[str]:
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if draw.textlength(prueba, font=f) <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def tarjeta(nombre: str, motor: str, frase: str, n: int, total: int, destino: Path) -> None:
    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(img)
    margen = 140

    # Etiqueta superior y contador
    d.text((margen, 110), "MUESTRA DE VOZ", font=fuente(True, 30), fill=ACENTO)
    cont = f"{n} / {total}"
    fc = fuente(True, 30)
    d.text((ANCHO - margen - d.textlength(cont, font=fc), 110), cont, font=fc, fill=SUAVE)

    # Nombre de la voz (protagonista) con barra de acento
    fn = fuente(True, 92)
    lineas = partir(d, nombre, fn, ANCHO - 2 * margen - 40)
    y = 330
    d.rectangle((margen, y + 8, margen + 10, y + 8 + len(lineas) * 108 - 20), fill=ACENTO)
    for linea in lineas:
        d.text((margen + 40, y), linea, font=fn, fill=TEXTO)
        y += 108
    d.text((margen + 40, y + 16), motor, font=fuente(False, 40), fill=SUAVE)

    # Frase como subtítulo, dentro de la zona segura inferior
    ff = fuente(False, 44)
    lf = partir(d, f"“{frase}”", ff, ANCHO - 2 * margen)
    y = ALTO - 140 - len(lf) * 58
    for linea in lf:
        d.text(((ANCHO - d.textlength(linea, font=ff)) / 2, y), linea, font=ff, fill=TEXTO)
        y += 58
    img.save(destino)


def tarjeta_seccion(titulo: str, detalle: list[str], destino: Path) -> None:
    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(img)
    margen = 140
    d.text((margen, 110), "MUESTRA DE VOCES", font=fuente(True, 30), fill=ACENTO)
    ft = fuente(True, 84)
    y = 380
    for linea in partir(d, titulo, ft, ANCHO - 2 * margen):
        d.text((margen, y), linea, font=ft, fill=TEXTO)
        y += 100
    y += 30
    fd = fuente(False, 40)
    for linea in detalle:
        d.text((margen, y), linea, font=fd, fill=SUAVE)
        y += 58
    img.save(destino)


def kokoro(voz: str, frase: str, destino: Path) -> None:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise RuntimeError("No encuentro npx (instala Node.js para usar las voces Kokoro).")
    r = subprocess.run([npx, "-y", "hyperframes@latest", "tts", frase, "--voice", voz,
                        "--lang", "es", "-o", str(destino)], capture_output=True, text=True)
    if r.returncode != 0 or not destino.exists():
        raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout) else "falló")


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def segmento(png: Path, wav: Path, destino: Path) -> float:
    voz = _wav_duration_seconds(wav)
    dur = round(ANTES + voz + DESPUES, 3)
    fade_out = dur - 0.35
    ffmpeg(
        "-loop", "1", "-framerate", str(FPS), "-i", str(png), "-i", str(wav),
        "-filter_complex",
        f"[0:v]scale={ANCHO}:{ALTO},format=yuv420p,fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out}:d=0.35[v];"
        f"[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,"
        f"adelay={int(ANTES * 1000)}:all=1,apad,atrim=0:{dur},aformat=channel_layouts=stereo[a]",
        "-map", "[v]", "-map", "[a]", "-t", str(dur),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", str(destino),
    )
    return dur


def segmento_mudo(png: Path, dur: float, destino: Path) -> None:
    ffmpeg(
        "-loop", "1", "-framerate", str(FPS), "-i", str(png),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-filter_complex",
        f"[0:v]scale={ANCHO}:{ALTO},format=yuv420p,fade=t=in:st=0:d=0.35,fade=t=out:st={dur - 0.35}:d=0.35[v]",
        "-map", "[v]", "-map", "1:a", "-t", str(dur),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", str(destino),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Video de muestra de las voces guardadas")
    ap.add_argument("--frase", default=FRASE, help="Frase que dice cada voz")
    ap.add_argument("--voces", help="Nombres (o parte del nombre) separados por coma; por defecto todas las guardadas")
    ap.add_argument("--salida", default=str(RAIZ / "outputs" / "muestra_voces.mp4"))
    ap.add_argument("--kokoro", choices=["no", "es", "todas"], default="es",
                    help="Voces Kokoro de HyperFrames: no, solo español (default) o las 54")
    args = ap.parse_args()

    biblioteca = json.loads((RAIZ / "assets" / "voices_library.json").read_text(encoding="utf-8"))
    if args.voces:
        pedidas = [v.strip() for v in args.voces.split(",")]
        biblioteca = [v for v in biblioteca
                      if any(x.lower() in v["name"].lower() for x in pedidas)]
    lista_kokoro = [] if args.kokoro == "no" else (
        [v for v in KOKORO if v[0] == "e"] if args.kokoro == "es" else KOKORO)
    if args.voces:
        pedidas = [v.strip() for v in args.voces.split(",")]
        lista_kokoro = [v for v in lista_kokoro if v in pedidas]
    if not biblioteca and not lista_kokoro:
        sys.exit("No hay voces para probar con esos filtros.")

    trabajo = Path(tempfile.mkdtemp(prefix="muestra_voces_"))
    grupos: list[tuple[str, list[str], list]] = []
    fallidas = []
    n = 0

    hechas = []
    for voz in biblioteca:
        n += 1
        nombre, motor = voz["name"], voz["backend"]
        print(f"[voces] {nombre} ({motor})")
        try:
            opciones = {k: v for k, v in (voz.get("options") or {}).items()
                        if k in PERMITIDAS.get(motor, set()) and v not in (None, "")}
            wav = trabajo / f"v{n:02d}.wav"
            get_backend(motor, **opciones).synthesize(args.frase, wav)
            hechas.append((nombre, ETIQUETA_MOTOR.get(motor, motor), wav))
        except Exception as exc:  # noqa: BLE001
            fallidas.append((nombre, f"{type(exc).__name__}: {exc}".splitlines()[0][:200]))
            print(f"[voces]   se salta: {fallidas[-1][1]}")
    if hechas:
        grupos.append(("Voces de video-automatico", ["Piper, espeak y voces clonadas con Chatterbox"], hechas))

    hechas = []
    for voz in lista_kokoro:
        n += 1
        print(f"[voces] Kokoro {voz}")
        try:
            wav = trabajo / f"v{n:02d}.wav"
            kokoro(voz, args.frase, wav)
            idioma = IDIOMA_KOKORO.get(voz[0], voz[0])
            genero = "mujer" if voz[1] == "f" else "hombre"
            etiqueta = (f"Kokoro · español nativo · {genero}" if voz[0] == "e"
                        else f"Kokoro · {idioma} leyendo en español · {genero}")
            hechas.append((f"{voz.split('_', 1)[1].capitalize()}  ·  {voz}", etiqueta, wav))
        except Exception as exc:  # noqa: BLE001
            fallidas.append((voz, str(exc)[:200]))
            print(f"[voces]   se salta: {fallidas[-1][1]}")
            if "npx" in str(exc) or "kokoro" in str(exc).lower():
                break
    if hechas:
        grupos.append(("Voces de HyperFrames · Kokoro",
                       ["Gratis y en tu PC: npx hyperframes tts --voice <id>"], hechas))

    if not grupos:
        sys.exit("No se pudo generar ninguna voz.")

    total = sum(len(g[2]) for g in grupos)
    segmentos, k = [], 0
    for gi, (titulo, detalle, voces) in enumerate(grupos):
        if len(grupos) > 1:
            png = trabajo / f"g{gi}.png"
            tarjeta_seccion(titulo, detalle, png)
            mp4 = trabajo / f"g{gi}.mp4"
            segmento_mudo(png, 2.2, mp4)
            segmentos.append(mp4)
        for nombre, etiqueta, wav in voces:
            k += 1
            png = trabajo / f"t{k:03d}.png"
            tarjeta(nombre, etiqueta, args.frase, k, total, png)
            mp4 = trabajo / f"s{k:03d}.mp4"
            segmento(png, wav, mp4)
            segmentos.append(mp4)

    pendientes = [f"{a} — {b}" for a, b in NO_INCLUIDAS]
    pendientes += [f"{a} — no se pudo generar aquí" for a, _ in fallidas]
    png = trabajo / "fin.png"
    tarjeta_seccion("Otras voces disponibles", pendientes[:9], png)
    mp4 = trabajo / "fin.mp4"
    segmento_mudo(png, 4.5, mp4)
    segmentos.append(mp4)
    hechas = [v for g in grupos for v in g[2]]

    lista = trabajo / "lista.txt"
    lista.write_text("".join(f"file '{s.as_posix()}'\n" for s in segmentos), encoding="utf-8")
    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(salida))
    shutil.rmtree(trabajo, ignore_errors=True)

    print(f"\n[voces] listo: {salida} ({round(_wav_duration_seconds(salida), 1)} s, {len(hechas)} voces)")
    for nombre, motivo in fallidas:
        print(f"[voces] no se incluyó «{nombre}»: {motivo}")


if __name__ == "__main__":
    main()
