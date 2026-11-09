#!/usr/bin/env python3
"""
Video para validar mercado del sistema para inmobiliarias (encuesta + clientes fundadores).
6 videos verticales 1080x1920: español (voz Dora) e inglés (voz Heart), 3 ganchos cada uno.

Estructura: gancho -> contexto (quién soy y qué construyo) -> funciones (las 4 de la encuesta)
-> encuesta (7 min) -> fundadores (prueba gratis + descuento de por vida) -> llamado (enlace en la descripción).

    python estudio/inmobiliaria/build.py                 # 6 proyectos en cortes/
    python estudio/inmobiliaria/build.py --solo es_a --render
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("serie_dia", AQUI.parent / "serie-dia/build.py")
sd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sd)
escena, resaltar, W, H = sd.escena, sd.resaltar, sd.W, sd.H

OSCURO, CIAN, TINTA, GRIS, LINEA = "#0B0F1A", "#38BFF0", "#F2F4F8", "#9AA5BA", "#1E2638"
PANEL = "#121A2B"
MIN_TOTAL, CIERRE = 31.0, 1.6
VIDEOS = [(f"{l}_{g}", l, f"gancho_{g}") for l in ("es", "en") for g in "abc"]

# iconos SVG de trazo (estilo Lucide), sin emojis
def ico(nombre, tam=64, color=CIAN):
    p = {
        "casa": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
        "portales": '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 9h18"/><path d="M8 21h8"/><path d="M12 18v3"/>',
        "billete": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/>',
        "chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-5A8 8 0 1 1 21 12z"/><path d="M9 11h6M9 14h4"/>',
        "check": '<path d="M5 12.5 10 17l9-10"/>',
        "reloj": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "regalo": '<rect x="3" y="8" width="18" height="13" rx="1.5"/><path d="M3 12h18M12 8v13"/><path d="M12 8c-2-4-6-4-6-1.5S9 8 12 8zm0 0c2-4 6-4 6-1.5S15 8 12 8z"/>',
        "estrella": '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1 6.2-5.5-2.9-5.5 2.9 1-6.2L3 9.6l6.2-.9z"/>',
        "flecha": '<path d="M12 4v15"/><path d="m6 13 6 6 6-6"/>',
        "usuario": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
    }[nombre]
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{p}</svg>')


T = {
    "es": dict(
        ganchos={"gancho_a": "¿Cuántas horas pierdes publicando el *mismo inmueble* en *5 portales?*",
                 "gancho_b": "Si tienes una inmobiliaria, necesito *7 minutos* de tu tiempo.",
                 "gancho_c": "Voy a crear un sistema para inmobiliarias, y quiero que *lo diseñes tú.*"},
        portal="Portal", ficha="3 hab · 2 baños · 85 m²", tag="SOFTWARE PARA INMOBILIARIAS",
        quien="Jesús Cristancho", rol="Desarrollador de software · Medellín",
        estado="Sistema para inmobiliarias", estado2="En diseño · con tu ayuda",
        pregunta="¿Qué te ahorraría más tiempo?",
        funciones=[("casa", "Inmuebles y clientes"), ("portales", "Publicar en portales"),
                   ("billete", "Cobro de arriendos"), ("chat", "WhatsApp automático")],
        enc_tit="Encuesta", enc_min="7 min", enc_q="¿Qué tarea te quita más tiempo hoy?",
        enc_ops=["Publicar inmuebles", "Responder clientes", "Cobrar arriendos"],
        fund=[("regalo", "Prueba gratis", "Para quienes respondan"),
              ("estrella", "Cliente fundador", "Descuento de por vida + todas las funciones")],
        cta1="Responde la encuesta", cta2="Enlace en la descripción", cta3="7 minutos",
        cifras=[("siete minutos", "7 minutos"), ("cinco portales", "5 portales")]),
    "en": dict(
        ganchos={"gancho_a": "How many hours do you lose posting the *same property* on *5 portals?*",
                 "gancho_b": "If you run a real estate agency, I need *7 minutes* of your time.",
                 "gancho_c": "I'm building a system for real estate agencies, and I want *you to design it.*"},
        portal="Portal", ficha="3 bd · 2 ba · 915 sq ft", tag="REAL ESTATE AGENCY SOFTWARE",
        quien="Jesús Cristancho", rol="Software developer · Medellín, Colombia",
        estado="Real estate agency system", estado2="In design · with your help",
        pregunta="What would save you the most time?",
        funciones=[("casa", "Listings & clients"), ("portales", "Publish to portals"),
                   ("billete", "Rent collection"), ("chat", "Automated WhatsApp")],
        enc_tit="Survey", enc_min="7 min", enc_q="Which task takes most of your time today?",
        enc_ops=["Posting listings", "Replying to clients", "Collecting rent"],
        fund=[("regalo", "Free trial", "For everyone who answers"),
              ("estrella", "Founding client", "Lifetime discount + every feature")],
        cta1="Take the survey", cta2="Link in the description", cta3="7 minutes",
        cifras=[("seven minutes", "7 minutes"), ("five different", "5 different")]),
}

CSS = f"""
.tag {{ position:absolute; left:0; right:0; text-align:center; font-size:30px; font-weight:800; letter-spacing:.18em; color:{CIAN}; }}
.card {{ background:{PANEL}; border:2px solid {LINEA}; border-radius:28px; color:{TINTA}; }}
.big {{ position:absolute; left:80px; right:80px; text-align:center; color:{TINTA}; font-weight:800; line-height:1.08; }}
.big .acc {{ color:{CIAN}; }}
"""


def js_in(dur, frac=.6, t0=.15, sel=".in"):
    return sd.js_in("x", dur, t0=t0, frac=frac, sel=sel)


def e_gancho(L, gid, dur):
    sid = "gancho"
    txt = L["ganchos"][gid]
    largo = len(txt.replace("*", ""))
    fs = 96 if largo < 60 else 84
    n = len(txt.split())
    if gid == "gancho_a":   # el mismo inmueble repetido en 5 portales
        vis = "".join(f'<div class="pt card" data-layout-allow-overlap style="left:{150 + i * 120}px; top:{360 + i * 34}px; z-index:{i}">'
                      f'<div class="ph"></div><b>{L["portal"]} {i + 1}</b><span>{L["ficha"]}</span></div>' for i in range(5))
        vjs = f'    tl.fromTo("#{sid} .pt", {{opacity:0, x:-120}}, {{opacity:1, x:0, duration:.35, ease:"expo.out", stagger:.16}}, .1);\n'
        vcss = f""".pt {{ position:absolute; width:420px; height:380px; padding:22px; box-shadow:0 30px 60px rgba(0,0,0,.45); }}
.pt .ph {{ height:210px; border-radius:16px; background:linear-gradient(135deg,#24324d,#1a2438); margin-bottom:18px;
   background-image:linear-gradient(135deg,#2b3d5e 0%,#1a2438 100%); }}
.pt b {{ display:block; font-size:34px; color:{CIAN}; }} .pt span {{ font-size:28px; color:{GRIS}; }}"""
        top = 940
    elif gid == "gancho_b":  # reloj de 7 minutos
        vis = (f'<div id="{sid}-rel"><svg width="380" height="380" viewBox="0 0 100 100"><circle cx="50" cy="50" r="44" fill="none" stroke="{LINEA}" stroke-width="6"/>'
               f'<circle id="{sid}-arc" cx="50" cy="50" r="44" fill="none" stroke="{CIAN}" stroke-width="6" stroke-linecap="round" '
               f'stroke-dasharray="276.5" stroke-dashoffset="276.5" transform="rotate(-90 50 50)"/></svg><b>7<small>min</small></b></div>')
        vjs = f'    tl.to("#{sid}-arc", {{strokeDashoffset:0, duration:{min(dur * .8, 3.2):.2f}, ease:"power2.inOut"}}, .2);\n'
        vcss = f"""#{sid}-rel {{ position:absolute; left:350px; top:380px; width:380px; height:380px; }}
#{sid}-rel b {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:150px; font-weight:800; color:{TINTA}; }}
#{sid}-rel small {{ font-size:44px; color:{GRIS}; margin:60px 0 0 8px; }}"""
        top = 880
    else:                    # plano de una casa que se dibuja
        vis = (f'<svg id="{sid}-casa" width="460" height="400" viewBox="0 0 24 21" fill="none" stroke="{CIAN}" stroke-width=".35" '
               f'stroke-linecap="round" stroke-linejoin="round"><path class="dib" d="M2 10 12 2l10 8"/><path class="dib" d="M4 8.5V20h16V8.5"/>'
               f'<path class="dib" d="M10 20v-6h4v6"/><path class="dib" d="M6 11h3v3H6zM15 11h3v3h-3z"/></svg>')
        vjs = (f'    document.querySelectorAll("#{sid}-casa .dib").forEach(p => {{ const L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.strokeDashoffset = L; }});\n'
               f'    tl.to("#{sid}-casa .dib", {{strokeDashoffset:0, duration:.9, ease:"power2.inOut", stagger:.25}}, .1);\n')
        vcss = f"#{sid}-casa {{ position:absolute; left:310px; top:360px; }}"
        top = 880
    css = CSS + vcss + f"""
#root {{ background:{OSCURO}; }}
#{sid}-t {{ top:{top}px; font-size:{fs}px; }}
#{sid}-tag {{ top:230px; }}
"""
    html = f'<div id="{sid}-tag" class="tag">{L["tag"]}</div>{vis}<div id="{sid}-t" class="big">{resaltar(txt)}</div>'
    js = vjs + (f'    tl.fromTo("#{sid}-tag", {{opacity:0}}, {{opacity:1, duration:.4}}, 0);\n'
                f'    tl.fromTo("#{sid}-t .w", {{opacity:0, y:22}}, {{opacity:1, y:0, duration:.25, ease:"power3.out", stagger:{max(dur * .7 - .5, .5) / n:.3f}}}, .4);\n')
    return sid, escena(sid, html, css, js)


def e_contexto(L, sid, dur):
    css = CSS + f"""
#{sid}-p {{ position:absolute; left:90px; right:90px; top:420px; padding:44px; display:flex; gap:36px; align-items:center; }}
#{sid}-p .av {{ width:150px; height:150px; border-radius:50%; border:3px solid {CIAN}; display:flex; align-items:center; justify-content:center; flex:none; }}
#{sid}-p b {{ display:block; font-size:54px; }} #{sid}-p span {{ font-size:34px; color:{GRIS}; }}
#{sid}-s {{ position:absolute; left:90px; right:90px; top:760px; padding:44px; }}
#{sid}-s .bp {{ height:330px; border-radius:18px; margin-bottom:30px;
   background-color:#0f1626; background-image:linear-gradient({LINEA} 2px, transparent 2px), linear-gradient(90deg, {LINEA} 2px, transparent 2px);
   background-size:54px 54px; display:flex; align-items:center; justify-content:center; }}
#{sid}-s b {{ display:block; font-size:50px; }} #{sid}-s span {{ font-size:34px; color:{CIAN}; font-weight:700; }}
"""
    html = (f'<div id="{sid}-p" class="card in"><div class="av">{ico("usuario", 90)}</div><div><b>{L["quien"]}</b><span>{L["rol"]}</span></div></div>'
            f'<div id="{sid}-s" class="card in"><div class="bp">{ico("casa", 200)}</div><b>{L["estado"]}</b><span>{L["estado2"]}</span></div>')
    return sid, escena(sid, html, css, js_in(dur, .45))


def e_funciones(L, sid, dur):
    css = CSS + f"""
#{sid}-h {{ top:330px; font-size:76px; }}
.op {{ position:absolute; left:90px; right:90px; height:200px; display:flex; align-items:center; gap:34px; padding:0 40px; font-size:48px; font-weight:800; }}
.op .bx {{ margin-left:auto; width:72px; height:72px; border-radius:18px; border:3px solid {LINEA}; display:flex; align-items:center; justify-content:center; }}
.op .bx svg {{ opacity:0; }}
"""
    html = f'<div id="{sid}-h" class="big in">{L["pregunta"]}</div>' + "".join(
        f'<div class="op card in" style="top:{600 + i * 230}px">{ico(ic, 76)}<span>{t}</span><div class="bx">{ico("check", 52)}</div></div>'
        for i, (ic, t) in enumerate(L["funciones"]))
    js = js_in(dur, .2) + (f'    document.querySelectorAll("#root .op").forEach((o, i) => {{ const t = .9 + i * {dur * .62 / 4:.2f};'
                           f' tl.to(o.querySelector(".bx svg"), {{opacity:1, duration:.2}}, t);'
                           f' tl.to(o.querySelector(".bx"), {{borderColor:"{CIAN}", backgroundColor:"rgba(56,191,240,.14)", duration:.2}}, t);'
                           f' tl.to(o, {{borderColor:"{CIAN}", duration:.25}}, t); }});\n')
    return sid, escena(sid, html, css, js)


def e_encuesta(L, sid, dur):
    css = CSS + f"""
#{sid}-f {{ position:absolute; left:90px; right:90px; top:420px; padding:48px; }}
#{sid}-f .hd {{ display:flex; align-items:center; justify-content:space-between; font-size:56px; font-weight:800; }}
#{sid}-f .hd span {{ display:flex; align-items:center; gap:12px; font-size:40px; color:{CIAN}; }}
#{sid}-f .bar {{ height:14px; border-radius:7px; background:{LINEA}; margin:30px 0 40px; overflow:hidden; }}
#{sid}-f .bar i {{ display:block; height:100%; width:8%; background:{CIAN}; border-radius:7px; }}
#{sid}-f .q {{ font-size:44px; margin-bottom:28px; line-height:1.2; }}
#{sid}-f .r {{ display:flex; align-items:center; gap:24px; padding:26px 28px; border:2px solid {LINEA}; border-radius:18px; font-size:40px; margin-bottom:16px; }}
#{sid}-f .r i {{ width:40px; height:40px; border-radius:50%; border:3px solid {GRIS}; flex:none; }}
#{sid}-f .r.sel {{ border-color:{CIAN}; }} #{sid}-f .r.sel i {{ border-color:{CIAN}; background:radial-gradient({CIAN} 45%, transparent 50%); }}
"""
    ops = "".join(f'<div class="r{" sel" if k == 0 else ""}"><i></i>{o}</div>' for k, o in enumerate(L["enc_ops"]))
    html = (f'<div id="{sid}-f" class="card in"><div class="hd">{L["enc_tit"]}<span>{ico("reloj", 46)}{L["enc_min"]}</span></div>'
            f'<div class="bar"><i></i></div><div class="q">{L["enc_q"]}</div>{ops}</div>')
    js = js_in(dur, .2) + f'    tl.to("#{sid}-f .bar i", {{width:"62%", duration:{dur * .7:.2f}, ease:"power1.inOut"}}, .4);\n'
    return sid, escena(sid, html, css, js)


def e_fundadores(L, sid, dur):
    css = CSS + f"""
.fd {{ position:absolute; left:90px; right:90px; padding:46px; display:flex; gap:36px; align-items:center; }}
.fd b {{ display:block; font-size:58px; }} .fd span {{ font-size:38px; color:{GRIS}; line-height:1.25; }}
.fd.top {{ border-color:{CIAN}; box-shadow:0 0 60px rgba(56,191,240,.18); }}
.fd.top span {{ color:{TINTA}; }}
"""
    html = "".join(f'<div class="fd card in{" top" if i else ""}" style="top:{470 + i * 380}px">{ico(ic, 110)}<div><b>{a}</b><span>{b}</span></div></div>'
                   for i, (ic, a, b) in enumerate(L["fund"]))
    js = sd.js_in("x", dur, t0=.15, frac=.55)
    return sid, escena(sid, html, css, js)


def e_cta(L, sid, dur):
    css = CSS + f"""
#{sid}-a {{ top:560px; font-size:96px; }}
#{sid}-b {{ position:absolute; left:140px; right:140px; top:900px; padding:34px; text-align:center; font-size:52px; font-weight:800;
   color:{OSCURO}; background:{CIAN}; border-radius:999px; }}
#{sid}-c {{ position:absolute; left:0; right:0; top:1080px; display:flex; justify-content:center; }}
#{sid}-d {{ position:absolute; left:0; right:0; top:1300px; text-align:center; font-size:38px; color:{GRIS}; font-weight:700; }}
"""
    html = (f'<div id="{sid}-a" class="big in">{L["cta1"]}</div><div id="{sid}-b" class="in">{L["cta2"]}</div>'
            f'<div id="{sid}-c" class="in">{ico("flecha", 150)}</div><div id="{sid}-d" class="in">{L["cta3"]} · EasyPro Digital</div>')
    js = js_in(dur, .3) + f'    tl.to("#{sid}-c", {{y:26, duration:.5, yoyo:true, repeat:5, ease:"sine.inOut"}}, 1.0);\n'
    return sid, escena(sid, html, css, js)


ESC = {"contexto": e_contexto, "funciones": e_funciones, "encuesta": e_encuesta, "fundadores": e_fundadores, "cta": e_cta}


def raiz(total, escenas, audios, titulo, lang):
    hosts = "".join(
        f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{t0:.3f}" '
        f'data-duration="{d:.3f}" data-track-index="{i + 2}" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:{i + 2}"></div>\n'
        for i, (sid, t0, d) in enumerate(escenas))
    aud = "".join(f'      <audio id="{aid}" class="clip" src="{src}" data-start="{t0:.3f}" data-track-index="{40 + i}" data-volume="{vol}"></audio>\n'
                  for i, (aid, src, t0, vol) in enumerate(audios))
    g = escenas[0][2]
    return f"""<!doctype html>
<html lang="{lang}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{titulo}</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:{OSCURO}; font-family:Inter, system-ui, sans-serif; }}
      #fondo {{ position:absolute; inset:0; background:{OSCURO}; }}
      #fondo .halo {{ position:absolute; width:1300px; height:1300px; border-radius:50%; left:-260px; top:-500px;
        background:radial-gradient(circle, rgba(56,191,240,.16), rgba(56,191,240,0) 65%); }}
      #marca {{ position:absolute; left:60px; top:110px; z-index:31; font-size:30px; font-weight:800; color:{TINTA}; letter-spacing:.04em; }}
      #marca b {{ color:{CIAN}; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}">
      <div id="fondo" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="0" data-layout-allow-overflow><div class="halo"></div></div>
{hosts}      <div id="marca" class="clip" data-start="{g:.3f}" data-duration="{total - g:.3f}" data-track-index="1">EasyPro <b>Digital</b></div>
      <div id="subs" data-composition-id="subs" data-composition-src="compositions/subs.html" data-start="0" data-duration="{total:.3f}"
        data-track-index="30" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:30"></div>
{aud}    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#fondo .halo", {{x:0, y:0}}, {{x:380, y:1000, duration:{total:.3f}, ease:"none"}}, 0);
      tl.fromTo("#marca", {{opacity:0}}, {{opacity:1, duration:.4}}, {g + .1:.3f});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def video(nombre, lang, gancho, salida: Path):
    L = T[lang]
    sd.CIFRAS = L["cifras"]
    voz = json.loads((AQUI / f"voz/{lang}/narracion.json").read_text(encoding="utf-8"))
    V = {l["id"]: l for l in voz["lineas"]}
    orden = [gancho, "contexto", "funciones", "encuesta", "fundadores", "cta"]
    d = salida / nombre
    for sub in ("compositions", "assets/vendor", "assets/sfx"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy(sd.NICHOS / "vendor/gsap.min.js", d / "assets/vendor/gsap.min.js")

    base = {lid: V[lid]["duracion"] + .2 for lid in orden}
    base[gancho] += .3
    base["cta"] += CIERRE
    falta = max(0.0, MIN_TOTAL - sum(base.values()))
    base["funciones"] += falta * .6
    base["cta"] += falta * .4

    escenas, gs, t = [], [], 0.0
    for k, lid in enumerate(orden):
        dur = base[lid]
        if lid.startswith("gancho"):
            sid, html = e_gancho(L, lid, dur)
        else:
            sid, html = ESC[lid](L, f"e{k}", dur)
        (d / f"compositions/{sid}.html").write_text(html, encoding="utf-8")
        escenas.append((sid, t, dur))
        if not lid.startswith("gancho") and lid != "cta":
            for c in V[lid]["subtitulos"]:
                gs += sd.grupos(c["texto"], t + c["inicio"] - V[lid]["inicio"] + .04, t + c["fin"] - V[lid]["inicio"])
        t += dur
    total = t
    (d / "compositions/subs.html").write_text(sd.comp_subs(gs), encoding="utf-8")

    filtros, ins = [], []
    for i, (lid, (sid, t0, _)) in enumerate(zip(orden, escenas)):
        ins += ["-i", str(AQUI / f"voz/{lang}/{lid}.wav")]
        filtros.append(f"[{i}:a]adelay={int(t0 * 1000)}:all=1[a{i}]")
    filtros.append("".join(f"[a{i}]" for i in range(len(orden))) +
                   f"amix=inputs={len(orden)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[o]")
    sd.ffmpeg(*ins, "-filter_complex", ";".join(filtros), "-map", "[o]", "-ac", "1", "-t", f"{total:.3f}", "-c:a", "pcm_s16le", str(d / "assets/voz.wav"))

    def sfx(nom):
        shutil.copy(sd.SFX_DIR / f"{nom}.mp3", d / f"assets/sfx/{nom}.mp3")
        return f"assets/sfx/{nom}.mp3"
    audios = [("voz", "assets/voz.wav", 0, 1)]
    for i, (sid, t0, _) in enumerate(escenas[1:], 1):
        audios.append((f"fx{i}", sfx("whoosh-short" if i % 2 else "whoosh"), max(t0 - .1, 0), .22))
    audios.append(("fx-cta", sfx("pop"), escenas[-1][1] + .1, .3))
    (d / "index.html").write_text(raiz(total, escenas, audios, nombre, lang), encoding="utf-8")
    return d, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    hechos = [video(n, l, g, AQUI / "cortes") for n, l, g in VIDEOS if not a.solo or a.solo == n]
    for d, t in hechos:
        print(f"[inmobiliaria] {d.name}: {t:.1f} s")
    if a.render:
        (AQUI / "renders").mkdir(exist_ok=True)
        npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
        for d, _ in hechos:
            subprocess.run([npx, "-y", "hyperframes@0.8.226", "render", "--output", str(AQUI / "renders" / f"{d.name}.mp4")], cwd=d, check=True)


if __name__ == "__main__":
    main()
