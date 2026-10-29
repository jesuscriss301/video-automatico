#!/usr/bin/env python3
"""
Capturas reales para el plan de videos (corre en la PC, con internet normal).

Usa Edge o Chrome sin ventana (--headless) para fotografiar páginas a 1920x1080.
Guarda en estudio/plan-videos/capturas/:
    demo1.png ... demo6.png   -> 6 demos de demos.easyprodigital.com
    turnero_tv.png            -> pantalla pública de Turnero (si se da el link)
    turnero_panel.png         -> panel del asesor de Turnero (si se da el link)

Uso:
    python estudio/plan-videos/capturar.py
    python estudio/plan-videos/capturar.py --turnero-tv URL --turnero-panel URL
    python estudio/plan-videos/capturar.py --demos URL1,URL2,...   (elegir demos a mano)
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DESTINO = AQUI / "capturas"
CATALOGO = "https://demos.easyprodigital.com/"

NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "msedge", "google-chrome", "chromium",
]


def navegador() -> str:
    for n in NAVEGADORES:
        if Path(n).exists() or shutil.which(n):
            return n
    raise SystemExit("No encuentro Edge ni Chrome para tomar las capturas.")


def capturar(url: str, salida: Path, ancho=1920, alto=1080, espera_ms=6000) -> bool:
    salida.parent.mkdir(parents=True, exist_ok=True)
    perfil = AQUI / ".perfil-captura"
    cmd = [navegador(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
           f"--user-data-dir={perfil}", f"--window-size={ancho},{alto}",
           f"--virtual-time-budget={espera_ms}", f"--screenshot={salida}", url]
    subprocess.run(cmd, capture_output=True, timeout=120)
    ok = salida.exists() and salida.stat().st_size > 20000
    print(f"[capturar] {'ok   ' if ok else 'FALLO'} {salida.name} <- {url}")
    return ok


def demos_del_catalogo(n=6) -> list[str]:
    html = urllib.request.urlopen(CATALOGO, timeout=30).read().decode("utf-8", "ignore")
    links = re.findall(r'href="([^"#]+)"', html)
    vistos, out = set(), []
    for l in links:
        if l.startswith("/"):
            l = CATALOGO.rstrip("/") + l
        if not l.startswith("http") or l.rstrip("/") == CATALOGO.rstrip("/"):
            continue
        if any(x in l for x in ("wa.me", "whatsapp", "mailto", "instagram", "facebook", "linkedin", "github")):
            continue
        if re.search(r"\.(css|js|png|jpg|svg|ico|webp)$", l):
            continue
        if l not in vistos:
            vistos.add(l)
            out.append(l)
    (AQUI / "capturas" / "demos_encontradas.txt").write_text("\n".join(out), encoding="utf-8")
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demos", help="URLs separadas por coma (si no, se toman del catálogo)")
    ap.add_argument("--turnero-tv")
    ap.add_argument("--turnero-panel")
    args = ap.parse_args()
    DESTINO.mkdir(exist_ok=True)

    urls = args.demos.split(",") if args.demos else demos_del_catalogo()
    if not urls:
        print("[capturar] No encontré demos en el catálogo; pasa --demos.")
    for i, u in enumerate(urls[:6], 1):
        capturar(u.strip(), DESTINO / f"demo{i}.png")
    if args.turnero_tv:
        capturar(args.turnero_tv, DESTINO / "turnero_tv.png")
    if args.turnero_panel:
        capturar(args.turnero_panel, DESTINO / "turnero_panel.png")
    capturar(CATALOGO, DESTINO / "catalogo.png")


if __name__ == "__main__":
    main()
