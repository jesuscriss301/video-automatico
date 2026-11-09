#!/usr/bin/env python3
"""Arma src/datos.json (tiempos de escenas, subtítulos y audios) desde la narración de
../inmobiliaria/voz/<idioma>/narracion.json. La voz manda el reloj."""
import importlib.util
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("serie_dia", AQUI.parent / "serie-dia/build.py")
sd = importlib.util.module_from_spec(_s)
_s.loader.exec_module(sd)

FPS = 30
LOGO = 2.6  # cierre con el logo de EasyPro Digital (solo al final)
CIFRAS = {"es": [("siete minutos", "7 minutos"), ("cinco portales", "5 portales")],
          "en": [("seven minutes", "7 minutes"), ("five different", "5 different")]}
ORDEN = ["contexto", "funciones", "encuesta", "fundadores", "cta"]

out = {}
for lang in ("es", "en"):
    voz = json.loads((AQUI.parent / f"inmobiliaria/voz/{lang}/narracion.json").read_text(encoding="utf-8"))
    V = {l["id"]: l for l in voz["lineas"]}
    sd.CIFRAS = CIFRAS[lang]
    for g in "abc":
        orden = [f"gancho_{g}"] + ORDEN
        base = {lid: V[lid]["duracion"] + .25 for lid in orden}
        base[orden[0]] += .35
        base["cta"] += .6
        falta = max(0.0, 31.0 - LOGO - sum(base.values()))
        base["funciones"] += falta * .6
        base["cta"] += falta * .4
        escenas, subs, audios, t = [], [], [], 0.0
        for lid in orden:
            d = base[lid]
            escenas.append({"id": "gancho" if lid.startswith("gancho") else lid, "from": round(t * FPS), "dur": round(d * FPS)})
            audios.append({"src": f"voz/{lang}/{lid}.wav", "from": round((t + .08) * FPS)})
            if not lid.startswith("gancho") and lid != "cta":
                for c in V[lid]["subtitulos"]:
                    for txt, t0, dd in sd.grupos(c["texto"], t + c["inicio"] - V[lid]["inicio"] + .04, t + c["fin"] - V[lid]["inicio"]):
                        subs.append({"text": txt, "from": round(t0 * FPS), "dur": max(4, round(dd * FPS))})
            t += d
        escenas.append({"id": "logo", "from": round(t * FPS), "dur": round(LOGO * FPS)})
        total = round((t + LOGO) * FPS)
        out[f"{lang}-{g}"] = {"lang": lang, "gancho": g, "total": total, "escenas": escenas, "subs": subs, "audios": audios}
        print(f"{lang}_{g}: {total / FPS:.1f} s")
(AQUI / "src").mkdir(exist_ok=True)
(AQUI / "src/datos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
