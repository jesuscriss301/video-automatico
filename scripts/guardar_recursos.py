#!/usr/bin/env python3
"""
Guarda en recursos/ todo lo que se usó para hacer los videos, para reutilizarlo después.

Recorre estudio/<proyecto>/ y copia (sin borrar nada y sin duplicar lo que ya está igual):
    capturas*/  -> recursos/capturas/<proyecto>[-es]/      (pantallazos de demos y webs)
    voz*/       -> recursos/voces/<proyecto>[-es]/<grupo>/ (cada frase en .wav + narracion.json con tiempos)
    guiones*/   -> recursos/guiones/<proyecto>[-es]/       (textos de la narración)
    fonts/      -> recursos/fuentes/
    vendor/     -> recursos/librerias/
    build*.py, SPEC.md, PUBLICAR.md, *.bat de captura -> recursos/plantillas/<proyecto>/
Además copia los efectos de sonido usados (de la skill media-use) a recursos/efectos/
y reescribe recursos/INDICE.md con la lista de todo, para encontrarlo rápido.

Uso (en la PC o en la nube, solo necesita Python):
    python scripts/guardar_recursos.py
"""
from __future__ import annotations

import filecmp
import json
import re
import shutil
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EST = RAIZ / "estudio"
REC = RAIZ / "recursos"
SFX = RAIZ / ".claude/skills/media-use/audio/assets/sfx"
EXT_AUDIO = {".wav", ".mp3"}
EXT_IMG = {".png", ".jpg", ".jpeg", ".webp"}
NO = {"narracion.wav"}  # la mezcla completa se rehace con las frases sueltas


def copiar(src: Path, dst: Path) -> bool:
    if dst.exists() and filecmp.cmp(src, dst, shallow=False):
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def sufijo(carpeta: str) -> str:
    return "-es" if carpeta.endswith("_es") else ""


def main():
    nuevos = 0
    usados_sfx = set()
    for proy in sorted(p for p in EST.iterdir() if p.is_dir()):
        for sub in sorted(p for p in proy.iterdir() if p.is_dir()):
            n = sub.name
            if n.startswith("capturas"):
                for f in sub.rglob("*"):
                    if f.suffix.lower() in EXT_IMG and ".perfil" not in str(f):
                        nuevos += copiar(f, REC / "capturas" / f"{proy.name}{sufijo(n)}" / f.name)
            elif n.startswith("voz"):
                falsos = {j.parent for j in sub.rglob("narracion.json") if '"falso": true' in j.read_text(encoding="utf-8")}
                for f in sub.rglob("*"):
                    if f.parent in falsos:  # voz de prueba (tono), no se guarda
                        continue
                    if f.is_file() and f.name not in NO and (f.suffix.lower() in EXT_AUDIO or f.name == "narracion.json"):
                        nuevos += copiar(f, REC / "voces" / f"{proy.name}{sufijo(n)}" / f.relative_to(sub))
            elif n.startswith("guiones"):
                for f in sub.glob("*.json"):
                    nuevos += copiar(f, REC / "guiones" / f"{proy.name}{sufijo(n)}" / f.name)
            elif n == "fonts":
                for f in sub.glob("*.woff2"):
                    nuevos += copiar(f, REC / "fuentes" / f.name)
            elif n == "vendor":
                for f in sub.glob("*.js"):
                    nuevos += copiar(f, REC / "librerias" / f.name)
            elif n.startswith("cortes"):
                for f in sub.rglob("assets/sfx/*"):
                    usados_sfx.add(f.name)
        for f in proy.iterdir():
            if f.is_file() and (f.name.startswith("build") and f.suffix == ".py" or f.name in ("SPEC.md", "PUBLICAR.md")
                                or f.name.startswith("captur") or f.suffix == ".bat"):
                nuevos += copiar(f, REC / "plantillas" / proy.name / f.name)
    for nom in sorted(usados_sfx):
        if (SFX / nom).exists():
            nuevos += copiar(SFX / nom, REC / "efectos" / nom)
    escribir_indice()
    print(f"[recursos] {nuevos} archivos nuevos o actualizados en {REC}")


def frases(json_path: Path):
    try:
        d = json.loads(json_path.read_text(encoding="utf-8"))
        return d.get("voz", ""), [(l["id"], l["texto"]) for l in d.get("lineas", [])]
    except Exception:
        return "", []


def escribir_indice():
    L = [f"# Recursos para videos (actualizado {date.today().isoformat()})", "",
         "Todo lo que se usó para hacer los videos, listo para reutilizar. Se actualiza con",
         "`python scripts/guardar_recursos.py` después de cada video.", ""]
    cap = REC / "capturas"
    if cap.exists():
        L += ["## Capturas de demos y webs", "", "| Carpeta | Archivos |", "|---|---|"]
        for d in sorted(cap.iterdir()):
            fs = sorted(f.name for f in d.iterdir())
            L.append(f"| `capturas/{d.name}` | {', '.join(fs)} |")
        L.append("")
    voc = REC / "voces"
    if voc.exists():
        L += ["## Voces (una frase por archivo)", "",
              "Cada grupo trae `narracion.json` con los tiempos y el texto de cada frase.", ""]
        for d in sorted(voc.iterdir()):
            for g in sorted(x for x in d.iterdir() if x.is_dir()):
                guion = next((REC / "guiones" / d.name).glob(f"{g.name}.json"), None) if (REC / "guiones" / d.name).exists() else None
                voz, lineas = frases(guion) if guion else ("", [])
                L.append(f"- **`voces/{d.name}/{g.name}`**" + (f" · {voz}" if voz else ""))
                for i, t in lineas:
                    L.append(f"  - `{i}.wav`: {t}")
        L.append("")
    for titulo, sub in (("Fuentes", "fuentes"), ("Efectos de sonido", "efectos"), ("Librerías", "librerias")):
        d = REC / sub
        if d.exists():
            L += [f"## {titulo}", "", ", ".join(f"`{f.name}`" for f in sorted(d.iterdir())), ""]
    pl = REC / "plantillas"
    if pl.exists():
        L += ["## Plantillas (cómo se armó cada serie de videos)", ""]
        for d in sorted(pl.iterdir()):
            L.append(f"- `plantillas/{d.name}`: " + ", ".join(f"`{f.name}`" for f in sorted(d.iterdir())))
        L.append("")
    (REC / "INDICE.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
