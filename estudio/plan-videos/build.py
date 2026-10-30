#!/usr/bin/env python3
"""
Genera los cortes del "Plan de 3 videos para easyprodigital.com" como proyectos
HyperFrames (uno por corte) y, con --render, los renderiza a MP4.

Cada corte = gancho (A/B/C) + cuerpo del video, en un idioma y un formato:
    cortes/<video>_<idioma>_<gancho>_<formato>/   (formato: v = 1080x1920, h = 1920x1080)
Además, el bucle de portada de 10 s sin voz (video 1, horizontal).

Entradas:
    voz/<video>_<idioma>/narracion.json + <linea>.wav   (de scripts/narrar.py)
    capturas/*.png                                       (capturas reales de las demos)

Uso:
    python estudio/plan-videos/build.py                       # genera todos los proyectos
    python estudio/plan-videos/build.py --solo v3_en_a_v      # uno solo
    python estudio/plan-videos/build.py --render              # genera y renderiza a renders/
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
SFX_DIR = RAIZ / ".claude/skills/media-use/audio/assets/sfx"
GSAP = AQUI / "vendor/gsap.min.js"

NOCHE, CIAN, TINTA, SUAVE = "#0B0F1A", "#38BFF0", "#F2F6FA", "#8A97AD"
WA = "wa.me/573238816434"
CIERRE_EXTRA = 2.2  # segundos de cierre sin voz (la última línea debe sostenerse >= 2 s)

# ---------------------------------------------------------------- textos ----
# *palabra* = palabra en cian
T = {
    "v3": {
        "es": {
            "gancho": {"a": "¿Cuántos se fueron *sin ser atendidos*?",
                       "b": "*Cero filas* con una pantalla y un QR",
                       "c": "¿Todavía agendas en un *cuaderno*?"},
            "problema": ["Filas", "Citas perdidas", "Llamadas"],
            "turnero": ["Turno", "Pantalla", "Siguiente"],
            "reservas": ["Reserva online", "Confirmación", "Anticipo"],
            "cierre": ["Prueba la demo", "Escríbeme por WhatsApp"],
            "caps": {"turnero": [("turnero_recepcion", "Recepción: emite el turno"), ("turnero_operador", "Asesor: atiende el A-001")],
                     "reservas": [("turnero_admin", "Panel de administración"), ("turnero_siguiente", "Siguiente, con un clic")]},
        },
        "en": {
            "gancho": {"a": "How many left *without being served*?",
                       "b": "*No more lines:* one screen + a QR code",
                       "c": "Still booking in a *notebook*?"},
            "problema": ["Lines", "Missed appointments", "Phone calls"],
            "turnero": ["Number", "Screen", "Next"],
            "reservas": ["Online booking", "Confirmation", "Deposit"],
            "cierre": ["Try the demo", "Message us on WhatsApp"],
            "caps": {"turnero": [("turnero_recepcion", "Reception: issue a number"), ("turnero_operador", "Staff: serving A-001")],
                     "reservas": [("turnero_admin", "Admin panel"), ("turnero_siguiente", "Next, in one click")]},
        },
    },
    "v1": {
        "es": {
            "gancho": {"a": "Sin intermediarios entre tú y *quien programa*",
                       "b": "¿Tienes una *idea de app*?",
                       "c": "*3.000* transacciones al día. *Una sola persona.*"},
            "intro": ["EasyPro Digital", "Jesús · Desarrollador full stack · Medellín"],
            "servicios": ["Web", "Tiendas", "Apps", "SaaS", "IA", "SEO"],
            "caso": ["Integración con el Ministerio de Salud", "3.000", "transacciones/día",
                     "−40 %", "tiempo de respuesta"],
            "cierre": ["Escríbeme por WhatsApp", "Te respondo en 24 horas"],
            "bucle": "De la idea al *software funcionando*",
        },
        "en": {
            "gancho": {"a": "No middleman between you and *your developer*",
                       "b": "Got an *app idea*?",
                       "c": "*3,000* transactions a day. *One developer.*"},
            "intro": ["EasyPro Digital", "Jesús · Full stack developer · Medellín"],
            "servicios": ["Web", "Stores", "Apps", "SaaS", "AI", "SEO"],
            "caso": ["Ministry of Health integration", "3,000", "transactions/day",
                     "−40%", "response time"],
            "cierre": ["Message Jesús on WhatsApp", "Answer within 24 hours"],
            "bucle": "From idea to *working software*",
        },
    },
}
CUERPO = {"v3": ["problema", "turnero", "reservas", "cierre"],
          "v1": ["intro", "servicios", "caso", "cierre"]}
# Lo que la voz dice en palabras y el subtítulo muestra en cifras.
CIFRAS = {
    "es": [("Tres mil", "3.000"), ("tres mil", "3.000"), ("cuarenta por ciento", "40 %"),
           ("veinticuatro horas", "24 horas")],
    "en": [("Three thousand", "3,000"), ("three thousand", "3,000"), ("forty percent", "40%"),
           ("twenty-four hours", "24 hours")],
}
DEMOS = [f"demo{i}" for i in range(1, 7)]


def resaltar(texto: str) -> str:
    """'*hola* mundo' -> palabras en spans con la acentuada en cian."""
    out = []
    for m in re.finditer(r"\*([^*]+)\*|([^*]+)", texto):
        trozo, acento = (m.group(1), True) if m.group(1) else (m.group(2), False)
        for p in trozo.split():
            cls = "w acc" if acento else "w"
            out.append(f'<span class="{cls}">{p}</span>')
    return " ".join(out)


# ------------------------------------------------------------ geometría ----
class G:
    def __init__(self, vertical: bool):
        self.v = vertical
        self.W, self.H = (1080, 1920) if vertical else (1920, 1080)
        k = 1.35 if vertical else 1.0
        self.titulo = int(96 * k) if not vertical else 104
        self.sub = int(40 * k)
        self.etiqueta = int(44 * k)
        # zona útil para contenido (vertical: banda 168-1330 px)
        self.top = 300 if vertical else 120
        self.bottom = 1330 if vertical else 960
        self.cap_y = 1150 if vertical else 1080 - 160


# ---------------------------------------------------------------- escenas ----
CSS_BASE = """
#root {{ position:absolute; inset:0; font-family:'Inter',sans-serif; color:{tinta}; }}
.w {{ display:inline-block; }}
.acc {{ color:{cian}; }}
.mono {{ font-family:'JetBrains Mono',monospace; }}
"""


def escena(sid: str, g: G, cuerpo_html: str, css: str, js: str, dur: float) -> str:
    return f"""<template>
  <style>
    {CSS_BASE.format(tinta=TINTA, cian=CIAN)}
    {css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{g.W}" data-height="{g.H}">
{cuerpo_html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def entrada_palabras(sel: str, t0: float, paso=0.08) -> str:
    return (f'    tl.fromTo("{sel} .w", {{opacity:0, filter:"blur(8px)"}}, '
            f'{{opacity:1, filter:"blur(0px)", duration:0.16, ease:"power4.out", stagger:{paso}}}, {t0});\n')


def etiquetas_html(sid, items, g, y, apilar):
    fs = g.etiqueta
    if apilar:
        filas = "".join(f'<div id="{sid}-e{i}" class="et">{t}</div>' for i, t in enumerate(items))
        return f'<div id="{sid}-ets" class="ets col" style="top:{y}px">{filas}</div>', fs
    partes = []
    for i, t in enumerate(items):
        if i:
            partes.append(f'<span id="{sid}-s{i}" class="sep">·</span>')
        partes.append(f'<span id="{sid}-e{i}" class="et">{t}</span>')
    return f'<div id="{sid}-ets" class="ets fila" style="top:{y}px">{"".join(partes)}</div>', fs


CSS_ETS = """
.ets { position:absolute; left:0; right:0; display:flex; justify-content:center; align-items:center;
       gap:26px; font-weight:700; }
.ets.col { flex-direction:column; gap:18px; }
.et { padding:12px 28px; border:2px solid rgba(56,191,240,.55); border-radius:999px; color:%s;
      background:rgba(56,191,240,.08); }
.sep { color:CIANX; font-weight:400; }
""".replace("%s", TINTA).replace("CIANX", CIAN)


def js_etiquetas(sid, n, t0, paso, con_sep=True):
    js = ""
    for i in range(n):
        t = t0 + i * paso
        js += (f'    tl.fromTo("#{sid}-e{i}", {{opacity:0, y:24, scale:.94}}, '
               f'{{opacity:1, y:0, scale:1, duration:.45, ease:"expo.out"}}, {t:.2f});\n')
        if con_sep and i:
            js += f'    tl.fromTo("#{sid}-s{i}", {{opacity:0}}, {{opacity:1, duration:.2}}, {t - .05:.2f});\n'
    return js


def marco_captura(cid, src, g, x, y, w, h, etiqueta="", ajuste="cover"):
    """Captura dentro de un marco con barra de navegador; la imagen se mueve (Ken Burns)."""
    eti = (f'<div id="{cid}-eti" class="cap-eti" style="left:{x}px; top:{y + h + 14}px; width:{w}px">{etiqueta}</div>'
           if etiqueta else "")
    return (f'<div id="{cid}" class="marco" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px">'
            f'<div class="barra"><i></i><i></i><i></i></div>'
            f'<div class="vista {ajuste}" data-layout-allow-overflow><img id="{cid}-img" src="assets/capturas/{src}.png" alt=""></div></div>{eti}')


CSS_MARCO = """
.marco { position:absolute; border-radius:18px; overflow:hidden; background:#121826;
         border:1.5px solid rgba(56,191,240,.35); box-shadow:0 30px 80px rgba(0,0,0,.55), 0 0 60px rgba(56,191,240,.12); }
.barra { height:34px; display:flex; align-items:center; gap:9px; padding-left:16px; background:#161D2E; }
.barra i { width:11px; height:11px; border-radius:50%; background:#2A3550; display:block; }
.vista { position:absolute; left:0; right:0; top:34px; bottom:0; overflow:hidden; }
.vista img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:top center; }
.vista.contain { background:#0F172A; }
.vista.contain img { object-fit:contain; object-position:center; }
.cap-eti { position:absolute; text-align:center; font-size:30px; color:%s; font-family:'JetBrains Mono',monospace; }
""".replace("%s", SUAVE)


def js_kenburns(cid, dur, t0=0.0, desde=1.0, hasta=1.08, y_hasta=-3):
    return (f'    tl.fromTo("#{cid}, #{cid}-eti", {{opacity:0, y:40, scale:.96}}, {{opacity:1, y:0, scale:1, duration:.6, ease:"expo.out"}}, {t0:.2f});\n'
            f'    tl.fromTo("#{cid}-img", {{scale:{desde}, yPercent:0}}, {{scale:{hasta}, yPercent:{y_hasta}, duration:{max(dur - t0, .5):.2f}, ease:"none"}}, {t0:.2f});\n')


# ---- ilustraciones de los ganchos (dibujadas: no son capturas de producto) ----
def svg_sala(sid, w):
    sillas, js, n = [], "", 8
    for i in range(n):
        x = 40 + i * 110
        sillas.append(f'<g id="{sid}-p{i}"><circle cx="{x + 40}" cy="70" r="26" fill="{CIAN}" opacity=".85"/>'
                      f'<rect x="{x + 12}" y="102" width="56" height="70" rx="22" fill="{CIAN}" opacity=".85"/></g>'
                      f'<rect x="{x}" y="150" width="80" height="60" rx="10" fill="#1E2840"/>')
    se_van = [1, 4, 6, 2, 7]
    for k, i in enumerate(se_van):
        js += (f'    tl.to("#{sid}-p{i}", {{opacity:0, y:-30, duration:.45, ease:"power3.in"}}, {0.9 + k * 0.45:.2f});\n')
    svg = (f'<svg id="{sid}-ilus" viewBox="0 0 {40 + n * 110} 230" style="width:{w}px">'
           f'{"".join(sillas)}</svg>')
    return svg, js


def svg_qr(sid, w):
    celdas = []
    semilla = 7
    for f in range(9):
        for c in range(9):
            semilla = (semilla * 1103515245 + 12345) % 2 ** 31
            esquina = (f < 3 and c < 3) or (f < 3 and c > 5) or (f > 5 and c < 3)
            if esquina or semilla % 3 == 0:
                celdas.append(f'<rect x="{20 + c * 20}" y="{20 + f * 20}" width="18" height="18" rx="3" fill="{CIAN}"/>')
    tv = ('<rect x="300" y="10" width="330" height="200" rx="16" fill="#121826" stroke="#38BFF0" stroke-width="3"/>'
          f'<text id="{sid}-num" x="465" y="135" text-anchor="middle" font-family="JetBrains Mono" '
          f'font-size="78" font-weight="700" fill="{TINTA}">A-12</text>')
    svg = (f'<svg id="{sid}-ilus" viewBox="0 0 650 230" style="width:{w}px">'
           f'<g id="{sid}-qr">{"".join(celdas)}</g>{tv}</svg>')
    js = (f'    tl.fromTo("#{sid}-qr rect", {{opacity:0, scale:.4, transformOrigin:"50% 50%"}}, '
          f'{{opacity:1, scale:1, duration:.25, ease:"back.out(1.6)", stagger:{{each:.01, from:"random"}}}}, .3);\n'
          f'    tl.fromTo("#{sid}-num", {{opacity:0}}, {{opacity:1, duration:.2}}, 1.2);\n')
    return svg, js


def svg_cuaderno(sid, w):
    lineas = "".join(f'<line x1="60" y1="{60 + i * 34}" x2="{360 - (i % 3) * 40}" y2="{60 + i * 34}" '
                     f'stroke="#55617A" stroke-width="5" stroke-linecap="round"/>' for i in range(5))
    tachas = "".join(f'<line class="tacha" x1="50" y1="{58 + i * 68}" x2="380" y2="{64 + i * 68}" '
                     f'stroke="#FF6B6B" stroke-width="7" stroke-linecap="round" '
                     f'stroke-dasharray="340" stroke-dashoffset="340"/>' for i in range(3))
    svg = (f'<svg id="{sid}-ilus" viewBox="0 0 420 240" style="width:{w}px">'
           f'<rect x="20" y="20" width="380" height="210" rx="14" fill="#F2EBDD" opacity=".95"/>'
           f'<rect x="20" y="20" width="24" height="210" rx="6" fill="#C9B88F"/>{lineas}{tachas}</svg>')
    js = (f'    tl.to("#{sid}-ilus .tacha", {{attr:{{"stroke-dashoffset":0}}, duration:.35, ease:"power2.inOut", stagger:.35}}, .9);\n')
    return svg, js


def svg_terminal(sid, w, lang):
    codigo = ["const proyecto = await idea.validar();", "api.conectar(pagos, whatsapp);",
              "deploy({ entorno: 'produccion' });"] if lang == "es" else \
             ["const project = await idea.validate();", "api.connect(payments, whatsapp);",
              "deploy({ env: 'production' });"]
    filas = "".join(f'<div id="{sid}-c{i}" class="cod">{l}</div>' for i, l in enumerate(codigo))
    html = (f'<div id="{sid}-ilus" class="term" style="width:{w}px">'
            f'<div class="prompt mono"><span id="{sid}-pr">&gt;_</span></div>{filas}</div>')
    js = (f'    tl.fromTo("#{sid}-pr", {{opacity:0, scale:.6}}, {{opacity:1, scale:1, duration:.35, ease:"expo.out"}}, .05);\n')
    for i in range(len(codigo)):
        js += (f'    tl.fromTo("#{sid}-c{i}", {{opacity:0, clipPath:"inset(0 100% 0 0)"}}, '
               f'{{opacity:1, clipPath:"inset(0 0% 0 0)", duration:.5, ease:"none"}}, {0.45 + i * 0.4:.2f});\n')
    return html, js


CSS_TERM = """
.term { background:#0E1424; border:1.5px solid rgba(56,191,240,.35); border-radius:16px; padding:26px 30px; }
.prompt { font-size:64px; font-weight:700; color:%s; margin-bottom:10px; }
.cod { font-family:'JetBrains Mono',monospace; font-size:26px; color:#9FB3D1; line-height:1.7; white-space:nowrap; }
""".replace("%s", CIAN)


def escena_gancho(v, lang, gancho, g, dur):
    sid = "gancho"
    texto = T[v][lang]["gancho"][gancho]
    ancho_ilus = 860 if g.v else 900
    css = CSS_TERM + f"""
#{sid}-txt {{ position:absolute; left:{80 if g.v else 140}px; right:{80 if g.v else 140}px; text-align:center;
   font-weight:900; font-size:{g.titulo}px; line-height:1.08; letter-spacing:-.02em; }}
#{sid}-box {{ position:absolute; left:0; right:0; display:flex; justify-content:center; }}
#{sid}-cnt {{ font-family:'JetBrains Mono',monospace; font-weight:700; color:{CIAN};
   font-size:{200 if g.v else 220}px; letter-spacing:-.04em; }}
"""
    if v == "v3":
        ilus, js_ilus = {"a": svg_sala, "b": svg_qr, "c": svg_cuaderno}[gancho](sid, ancho_ilus)
    elif gancho == "c":
        num = "3.000" if lang == "es" else "3,000"
        ilus = f'<div id="{sid}-cnt" data-final="{num}">0</div>'
        sep = "." if lang == "es" else ","
        js_ilus = (f'    const cnt = {{n:0}}; const el = document.querySelector("#{sid}-cnt");\n'
                   f'    tl.fromTo(cnt, {{n:0}}, {{n:3000, duration:1.4, ease:"expo.out", onUpdate:() => {{'
                   f' el.textContent = Math.round(cnt.n).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, "{sep}"); }}}}, .2);\n')
    else:
        ilus, js_ilus = svg_terminal(sid, ancho_ilus, lang)
    if g.v:
        ilus_y, txt_y = 300, 980
    else:
        ilus_y, txt_y = 110, 640
    html = (f'    <div id="{sid}-box" style="top:{ilus_y}px">{ilus}</div>\n'
            f'    <div id="{sid}-txt" style="top:{txt_y}px">{resaltar(texto)}</div>\n')
    js = js_ilus + entrada_palabras(f"#{sid}-txt", 0.15, 0.07)
    js += (f'    tl.to("#{sid}-txt, #{sid}-box", {{opacity:0, filter:"blur(6px)", duration:.18, ease:"power3.in"}}, {dur - .2:.2f});\n')
    return sid, escena(sid, g, html, css, js, dur)


def escena_cuerpo(v, lang, sid, g, dur, demos_dur=None):
    tx = T[v][lang]
    css = CSS_ETS + CSS_MARCO + f"""
.grande {{ position:absolute; left:0; right:0; text-align:center; font-weight:900; letter-spacing:-.02em; }}
.sub {{ position:absolute; left:0; right:0; text-align:center; color:{SUAVE}; }}
.boton {{ position:absolute; left:0; right:0; margin:auto; text-align:center; border-radius:999px; font-weight:800; }}
"""
    html, js = "", ""
    W, H = g.W, g.H
    out = 0.22  # salida de la escena

    if sid == "problema":
        et, fs = etiquetas_html(sid, tx["problema"], g, g.top + (60 if g.v else 20), apilar=g.v)
        css += f".ets {{ font-size:{fs}px; }}"
        ilus, js_ilus = svg_cuaderno(sid, 700 if g.v else 620)
        y_ilus = 760 if g.v else 300
        html += et + f'<div style="position:absolute; left:0; right:0; top:{y_ilus}px; display:flex; justify-content:center">{ilus}</div>'
        js += js_etiquetas(sid, 3, .25, dur * .22, con_sep=not g.v) + js_ilus.replace(", .9);", f", {dur * .35:.2f});")
        js += f'    tl.fromTo("#{sid}-ilus", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:.6, ease:"expo.out"}}, .4);\n'

    elif sid in ("turnero", "reservas"):
        et, fs = etiquetas_html(sid, tx[sid], g, g.top, apilar=False)
        css += f".ets {{ font-size:{int(fs * (0.8 if g.v else 1))}px; flex-wrap:wrap; }}"
        html += et
        (src1, eti1), (src2, eti2) = tx["caps"][sid]
        if g.v:
            html += marco_captura(f"{sid}-tv", src1, g, 50, 420, 480, 560, eti1, ajuste="contain")
            html += marco_captura(f"{sid}-pn", src2, g, 550, 420, 480, 560, eti2, ajuste="contain")
        else:
            html += marco_captura(f"{sid}-tv", src1, g, 130, 250, 820, 500, eti1, ajuste="contain")
            html += marco_captura(f"{sid}-pn", src2, g, 970, 250, 820, 500, eti2, ajuste="contain")
        js += js_etiquetas(sid, 3, .2, dur * .25)
        js += js_kenburns(f"{sid}-tv", dur, .3) + js_kenburns(f"{sid}-pn", dur, .55, hasta=1.1, y_hasta=-6)

    elif sid == "intro":
        nombre, sub = tx["intro"]
        y = 520 if g.v else 300
        html += (f'<div id="{sid}-logo" class="grande mono" style="top:{y}px; font-size:{170 if g.v else 150}px; color:{CIAN}">&gt;_</div>'
                 f'<div id="{sid}-nom" class="grande" style="top:{y + (230 if g.v else 200)}px; font-size:{g.titulo}px">{resaltar(nombre)}</div>'
                 f'<div id="{sid}-sub" class="sub mono" style="top:{y + (380 if g.v else 330)}px; font-size:{g.sub - 6}px">{sub}</div>')
        # Medellín: montañas y edificios en línea (ilustración)
        base = H - (400 if g.v else 120)
        pts = " ".join(f"{x},{base - int(120 * abs(math.sin(x / 260)) + 40 * abs(math.sin(x / 70)))}" for x in range(0, W + 1, 30))
        edificios = "".join(f'<rect x="{x}" y="{base - h}" width="{bw}" height="{h}" fill="none" stroke="{CIAN}" stroke-width="2" opacity="{.55 if g.v else .3}"/>'
                            for x, h, bw in [(W * .18, 150, 40), (W * .23, 230, 46), (W * .29, 180, 38), (W * .62, 260, 50),
                                             (W * .68, 170, 36), (W * .73, 210, 44), (W * .44, 120, 34)])
        html += (f'<svg id="{sid}-city" viewBox="0 0 {W} {H}" style="position:absolute; inset:0; width:{W}px; height:{H}px">'
                 f'<polyline id="{sid}-mont" points="{pts}" fill="none" stroke="{CIAN}" stroke-width="3" opacity="{.7 if g.v else .35}" '
                 f'stroke-dasharray="6000" stroke-dashoffset="6000"/>{edificios}</svg>')
        js += (f'    tl.to("#{sid}-mont", {{attr:{{"stroke-dashoffset":0}}, duration:{min(dur * .7, 3.5):.2f}, ease:"power2.out"}}, 0);\n'
               f'    tl.fromTo("#{sid}-city rect", {{opacity:0, scaleY:0, transformOrigin:"50% 100%"}}, {{opacity:{.55 if g.v else .3}, scaleY:1, duration:.6, ease:"expo.out", stagger:.12}}, .6);\n'
               f'    tl.fromTo("#{sid}-logo", {{opacity:0, scale:.7}}, {{opacity:1, scale:1, duration:.5, ease:"back.out(1.5)"}}, .1);\n'
               + entrada_palabras(f"#{sid}-nom", .45) +
               f'    tl.fromTo("#{sid}-sub", {{opacity:0}}, {{opacity:1, duration:.4}}, 1.0);\n')

    elif sid == "servicios":
        items = tx["servicios"]
        et, fs = etiquetas_html(sid, items, g, g.top, apilar=False)
        css += f".ets {{ font-size:{int(fs * (0.82 if g.v else 0.9))}px; flex-wrap:wrap; gap:16px; padding:0 40px; }}"
        html += et
        paso = dur / 6
        if g.v:
            x, y, w, h = 70, 540, 940, 520
        else:
            x, y, w, h = 310, 250, 1300, 650
        for i, d in enumerate(DEMOS):
            html += marco_captura(f"{sid}-d{i}", d, g, x, y, w, h)
        for i in range(6):
            t0 = i * paso
            js += (f'    tl.fromTo("#{sid}-e{i}", {{opacity:.25}}, {{opacity:1, duration:.2}}, {t0:.2f});\n'
                   f'    tl.fromTo("#{sid}-e{i}", {{borderColor:"rgba(56,191,240,.55)", backgroundColor:"rgba(56,191,240,.08)"}}, '
                   f'{{borderColor:"rgba(56,191,240,1)", backgroundColor:"rgba(56,191,240,.28)", duration:.2}}, {t0:.2f});\n')
            if i:
                js += f'    tl.fromTo("#{sid}-s{i}", {{opacity:0}}, {{opacity:1, duration:.2}}, {t0:.2f});\n'
            js += (f'    tl.fromTo("#{sid}-d{i}", {{opacity:0, xPercent:12}}, {{opacity:1, xPercent:0, duration:.35, ease:"expo.out"}}, {t0:.2f});\n'
                   f'    tl.fromTo("#{sid}-d{i}-img", {{scale:1.0}}, {{scale:1.06, duration:{paso + .3:.2f}, ease:"none"}}, {t0:.2f});\n')
            if i < 5:
                js += f'    tl.to("#{sid}-d{i}", {{opacity:0, xPercent:-10, duration:.25, ease:"power3.in"}}, {t0 + paso - .05:.2f});\n'
        js = js.replace(f'tl.fromTo("#{sid}-e0", {{opacity:.25}}', f'tl.fromTo("#{sid}-e0", {{opacity:.25}}')
        # todas las etiquetas visibles desde el inicio (apagadas)
        js = f'    tl.set("#{sid}-ets .et", {{opacity:.25}}, 0);\n' + js

    elif sid == "caso":
        tag, n1, l1, n2, l2 = tx["caso"]
        y0 = 260 if g.v else 170
        css += f"""
#{sid}-tag {{ position:absolute; left:0; right:0; text-align:center; color:{SUAVE}; font-size:{g.sub - 4}px; }}
.dato {{ position:absolute; left:0; right:0; text-align:center; }}
.num {{ font-family:'JetBrains Mono',monospace; font-weight:700; color:{CIAN}; letter-spacing:-.03em; }}
.lab {{ font-weight:700; color:{TINTA}; }}
.barra-d {{ position:absolute; height:26px; border-radius:13px; }}
"""
        fn = 170 if g.v else 150
        if g.v:
            p1, p2 = y0 + 100, y0 + 430
        else:
            p1 = p2 = y0 + 150
        x1, x2 = ("0", "0") if g.v else ("-480px", "480px")
        html += (f'<div id="{sid}-tag" style="top:{y0}px">{tag}</div>'
                 f'<div id="{sid}-d1" class="dato" style="top:{p1}px; transform:translateX({x1})">'
                 f'<div id="{sid}-n1" class="num" style="font-size:{fn}px">0</div><div class="lab" style="font-size:{g.sub}px">{l1}</div></div>'
                 f'<div id="{sid}-d2" class="dato" style="top:{p2}px; transform:translateX({x2})">'
                 f'<div id="{sid}-n2" class="num" style="font-size:{fn}px">{n2}</div><div class="lab" style="font-size:{g.sub}px">{l2}</div></div>')
        bw = 600
        bx = (W - bw) // 2 + (0 if g.v else 480)
        by = (p2 + fn + 100) if g.v else (p2 + fn + 110)
        html += (f'<div class="barra-d" style="left:{bx}px; top:{by}px; width:{bw}px; background:#1E2840"></div>'
                 f'<div id="{sid}-bar" class="barra-d" style="left:{bx}px; top:{by}px; width:{bw}px; background:{CIAN}; transform-origin:0 50%"></div>')
        sep = "." if lang == "es" else ","
        t2 = dur * .5
        js += (f'    tl.fromTo("#{sid}-tag", {{opacity:0}}, {{opacity:1, duration:.4}}, .1);\n'
               f'    tl.fromTo("#{sid}-d1", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:.5, ease:"expo.out"}}, .3);\n'
               f'    const c1 = {{n:0}}; const e1 = document.querySelector("#{sid}-n1");\n'
               f'    tl.fromTo(c1, {{n:0}}, {{n:3000, duration:1.6, ease:"expo.out", onUpdate:() => {{ e1.textContent = Math.round(c1.n).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, "{sep}"); }}}}, .3);\n'
               f'    tl.fromTo("#{sid}-d2", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:.5, ease:"expo.out"}}, {t2:.2f});\n'
               f'    tl.fromTo("#{sid}-bar", {{scaleX:1}}, {{scaleX:.6, duration:1.2, ease:"power3.inOut"}}, {t2 + .3:.2f});\n')

    elif sid == "cierre":
        botones = tx["cierre"]
        y = 330 if g.v else 230
        fs_b = 60 if g.v else 52
        html += f'<div id="{sid}-logo" class="grande mono" style="top:{y}px; font-size:{150 if g.v else 120}px; color:{CIAN}">&gt;_</div>'
        html += f'<div id="{sid}-marca" class="grande mono" style="top:{y + (190 if g.v else 160)}px; font-size:{g.sub}px; color:{TINTA}">EasyPro Digital</div>'
        yb = y + (330 if g.v else 270)
        if v == "v3":
            html += (f'<div id="{sid}-b1" class="boton" style="top:{yb}px; width:{800 if g.v else 700}px; font-size:{fs_b - 8}px; padding:22px 0; border:3px solid {CIAN}; color:{CIAN}">{botones[0]}</div>'
                     f'<div id="{sid}-b2" class="boton" style="top:{yb + (150 if g.v else 130)}px; width:{900 if g.v else 820}px; font-size:{fs_b - 4}px; padding:26px 0; background:{CIAN}; color:{NOCHE}">{botones[1]}</div>')
            ywa = yb + (300 if g.v else 260)
            js += (f'    tl.fromTo("#{sid}-b1", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:.5, ease:"expo.out"}}, .5);\n'
                   f'    tl.fromTo("#{sid}-b2", {{opacity:0, y:30, scale:.95}}, {{opacity:1, y:0, scale:1, duration:.55, ease:"back.out(1.4)"}}, .75);\n')
        else:
            html += (f'<div id="{sid}-b2" class="boton" style="top:{yb}px; width:{900 if g.v else 820}px; font-size:{fs_b - 4}px; padding:26px 0; background:{CIAN}; color:{NOCHE}">{botones[0]}</div>'
                     f'<div id="{sid}-sub" class="sub" style="top:{yb + (150 if g.v else 130)}px; font-size:{g.sub}px">{botones[1]}</div>')
            ywa = yb + (240 if g.v else 210)
            js += (f'    tl.fromTo("#{sid}-b2", {{opacity:0, y:30, scale:.95}}, {{opacity:1, y:0, scale:1, duration:.55, ease:"back.out(1.4)"}}, .5);\n'
                   f'    tl.fromTo("#{sid}-sub", {{opacity:0}}, {{opacity:1, duration:.4}}, .9);\n')
        html += f'<div id="{sid}-wa" class="sub mono" style="top:{ywa}px; font-size:{g.sub - 6}px; color:{CIAN}">{WA}</div>'
        js = (f'    tl.fromTo("#{sid}-logo", {{opacity:0, scale:.7}}, {{opacity:1, scale:1, duration:.5, ease:"back.out(1.5)"}}, 0);\n'
              f'    tl.fromTo("#{sid}-marca", {{opacity:0}}, {{opacity:1, duration:.4}}, .2);\n' + js +
              f'    tl.fromTo("#{sid}-wa", {{opacity:0}}, {{opacity:1, duration:.4}}, 1.1);\n')
        out = 0  # el cierre no sale

    if out:
        js += f'    tl.to("#root > *", {{opacity:0, duration:{out}, ease:"power3.in"}}, {dur - out - .02:.2f});\n'
    return sid, escena(sid, g, html, css, js, dur)


# -------------------------------------------------------------- subtítulos ----
def grupos_subtitulos(texto, ini, fin, lang, max_pal=4):
    for a, b in CIFRAS[lang]:
        texto = texto.replace(a, b)
    palabras = texto.split()
    grupos, actual = [], []
    for p in palabras:
        actual.append(p)
        if len(actual) >= max_pal or re.search(r"[.,;:?!]$", p):
            grupos.append(" ".join(actual))
            actual = []
    if actual:
        grupos.append(" ".join(actual))
    total = sum(len(gr) + 2 for gr in grupos)
    t, out = ini, []
    for gr in grupos:
        d = (fin - ini) * (len(gr) + 2) / total
        out.append((gr, t, d))
        t += d
    return out


def comp_subtitulos(grupos, g):
    sid = "subs"
    fs = 64 if g.v else 58
    maxw = 900 if g.v else 1500
    css = f"""
.grp {{ position:absolute; left:0; right:0; top:{g.cap_y}px; text-align:center; }}
.grp span {{ display:inline-block; font-weight:900; font-size:{fs}px; color:{TINTA}; max-width:{maxw}px;
   padding:6px 22px 10px; border-radius:14px; background:rgba(11,15,26,.72); line-height:1.15; }}
"""
    html, js = "", ""
    for i, (txt, t0, d) in enumerate(grupos):
        txt = re.sub(r"(\d[\d.,]*\s?%?)", rf'<b style="color:{CIAN}">\1</b>', txt)
        html += f'    <div id="g{i}" class="grp clip" data-start="{t0:.3f}" data-duration="{d:.3f}"><span id="g{i}s">{txt}</span></div>\n'
        js += (f'    tl.fromTo("#g{i}s", {{opacity:0, y:14, scale:.96}}, {{opacity:1, y:0, scale:1, duration:.14, ease:"power3.out"}}, {t0:.3f});\n'
               f'    tl.to("#g{i}s", {{opacity:0, duration:.08, ease:"power2.in"}}, {t0 + d - .08:.3f});\n')
    return sid, escena(sid, g, html, css, js, 0)


# ------------------------------------------------------------------ armar ----
def ffmpeg(*a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)


def armar_voz(wavs, destino):
    lista = destino.with_suffix(".txt")
    lista.write_text("".join(f"file '{w.as_posix()}'\n" for w in wavs), encoding="utf-8")
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(lista), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
           "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(destino))
    lista.unlink()


def raiz_html(g, total, escenas, audios, titulo):
    hosts = ""
    for i, (sid, t0, d) in enumerate(escenas):
        hosts += (f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                  f'data-start="{t0:.3f}" data-duration="{d:.3f}" data-track-index="{i + 2}" data-track-kind="graphics" '
                  f'data-width="{g.W}" data-height="{g.H}" style="z-index:{i + 2}"></div>\n')
    aud = ""
    for i, (aid, src, t0, vol) in enumerate(audios):
        aud += (f'      <audio id="{aid}" class="clip" src="{src}" data-start="{t0:.3f}" '
                f'data-track-index="{40 + i}" data-volume="{vol}"></audio>\n')
    bug_y = 190 if g.v else 54
    return f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={g.W}, height={g.H}" />
    <title>{titulo}</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{g.W}px; height:{g.H}px; overflow:hidden; background:{NOCHE}; }}
      #fondo {{ position:absolute; inset:0; background:{NOCHE}; overflow:hidden; z-index:0; }}
      #fondo .rejilla {{ position:absolute; inset:-80px; opacity:.07;
        background-image:linear-gradient({CIAN} 1px, transparent 1px), linear-gradient(90deg, {CIAN} 1px, transparent 1px);
        background-size:80px 80px; }}
      #fondo .brillo {{ position:absolute; width:{int(g.W * 1.1)}px; height:{int(g.W * 1.1)}px; border-radius:50%;
        background:radial-gradient(circle, rgba(56,191,240,.20), rgba(56,191,240,0) 62%); left:{-int(g.W * .3)}px; top:{-int(g.W * .35)}px; }}
      #bug {{ position:absolute; left:{70 if g.v else 64}px; top:{bug_y}px; z-index:30; font-family:'JetBrains Mono',monospace;
        font-size:{30 if g.v else 28}px; color:{TINTA}; opacity:.85; }}
      #bug b {{ color:{CIAN}; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{g.W}" data-height="{g.H}">
      <div id="fondo" class="clip" data-layout-allow-overflow data-start="0" data-duration="{total:.3f}" data-track-index="0"><div class="rejilla"></div><div class="brillo"></div></div>
      <div id="bug" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="1"><b>&gt;_</b> EasyPro Digital</div>
{hosts}      <div id="subs" data-composition-id="subs" data-composition-src="compositions/subs.html" data-start="0" data-duration="{total:.3f}"
        data-track-index="30" data-track-kind="captions" data-width="{g.W}" data-height="{g.H}" style="z-index:30"></div>
{aud}    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#fondo .brillo", {{x:0, y:0}}, {{x:{int(g.W * .5)}, y:{int(g.H * .45)}, duration:{total:.3f}, ease:"none"}}, 0);
      tl.fromTo("#fondo .rejilla", {{y:0}}, {{y:80, duration:{total:.3f}, ease:"none"}}, 0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def copiar_base(d: Path, capturas: Path):
    (d / "compositions").mkdir(parents=True, exist_ok=True)
    (d / "assets/vendor").mkdir(parents=True, exist_ok=True)
    shutil.copy(GSAP, d / "assets/vendor/gsap.min.js")
    if (d / "assets/capturas").exists():
        shutil.rmtree(d / "assets/capturas")
    shutil.copytree(capturas, d / "assets/capturas")
    (d / "assets/sfx").mkdir(exist_ok=True)


def sfx(d, nombre):
    shutil.copy(SFX_DIR / f"{nombre}.mp3", d / f"assets/sfx/{nombre}.mp3")
    return f"assets/sfx/{nombre}.mp3"


def corte(v, lang, gancho, vertical, salida: Path):
    g = G(vertical)
    voz = json.loads((AQUI / f"voz/{v}_{lang}/narracion.json").read_text(encoding="utf-8"))
    lineas = {l["id"]: l for l in voz["lineas"]}
    vdir = AQUI / f"voz/{v}_{lang}"
    orden = [f"gancho_{gancho}"] + CUERPO[v]
    nombre = f"{v}_{lang}_{gancho}_{'v' if vertical else 'h'}"
    d = salida / nombre
    copiar_base(d, AQUI / "capturas")

    escenas, grupos, t = [], [], 0.0
    for lid in orden:
        l = lineas[lid]
        dur = l["duracion"] + (CIERRE_EXTRA if lid == "cierre" else 0)
        sid_html = escena_gancho(v, lang, gancho, g, dur) if lid.startswith("gancho") else escena_cuerpo(v, lang, lid, g, dur)
        sid, html = sid_html
        (d / f"compositions/{sid}.html").write_text(html, encoding="utf-8")
        escenas.append((sid, t, dur))
        if not lid.startswith("gancho"):
            for c in l["subtitulos"]:
                ini = t + (c["inicio"] - l["inicio"])
                fin = t + (c["fin"] - l["inicio"])
                grupos += grupos_subtitulos(c["texto"], ini + .05, fin, lang)
        t += dur
    total = t
    _, subs = comp_subtitulos(grupos, g)
    (d / "compositions/subs.html").write_text(subs, encoding="utf-8")

    armar_voz([vdir / f"{lid}.wav" for lid in orden], d / "assets/voz.wav")
    audios = [("voz", "assets/voz.wav", 0, 1)]
    # Efectos: pocos y con causa en pantalla
    golpes = ["whoosh-short", "whoosh"]
    for i, (sid, t0, _) in enumerate(escenas[1:], 1):
        audios.append((f"fx-corte{i}", sfx(d, golpes[i % 2]), max(t0 - .12, 0), .30))
    if v == "v1" and gancho != "c":
        audios.append(("fx-teclas", sfx(d, "typing"), .4, .22))
    if v == "v1" and gancho == "c":
        audios.append(("fx-cifra", sfx(d, "ping"), .3, .3))
    cierre_t0 = escenas[-1][1]
    audios.append(("fx-boton", sfx(d, "pop"), cierre_t0 + .55, .35))
    audios.append(("fx-logo", sfx(d, "sparkle"), cierre_t0 + .05, .18))

    (d / "index.html").write_text(raiz_html(g, total, escenas, audios, nombre), encoding="utf-8")
    (d / "meta.json").write_text(json.dumps({"nombre": nombre, "duracion": round(total, 2)}, ensure_ascii=False), encoding="utf-8")
    return d, total


def bucle(lang, salida: Path, dur=10.0):
    g = G(False)
    nombre = f"v1_{lang}_bucle_h"
    d = salida / nombre
    copiar_base(d, AQUI / "capturas")
    sid = "bucle"
    css = CSS_MARCO + f"""
#{sid}-t {{ position:absolute; left:0; right:0; top:110px; text-align:center; font-weight:900; font-size:84px; letter-spacing:-.02em; }}
.w {{ display:inline-block; }} .acc {{ color:{CIAN}; }}
"""
    html = f'<div id="{sid}-t">{resaltar(T["v1"][lang]["bucle"])}</div>'
    paso = dur / 6
    js = entrada_palabras(f"#{sid}-t", .1, .06)
    for i, dm in enumerate(DEMOS):
        html += marco_captura(f"{sid}-d{i}", dm, g, 360, 270, 1200, 680)
        t0 = i * paso
        js += (f'    tl.fromTo("#{sid}-d{i}", {{opacity:0, xPercent:10}}, {{opacity:1, xPercent:0, duration:.4, ease:"expo.out"}}, {t0:.2f});\n'
               f'    tl.fromTo("#{sid}-d{i}-img", {{scale:1}}, {{scale:1.06, duration:{paso + .4:.2f}, ease:"none"}}, {t0:.2f});\n')
        js += f'    tl.to("#{sid}-d{i}", {{opacity:0, xPercent:-8, duration:.3, ease:"power3.in"}}, {t0 + paso - .05:.2f});\n'
    (d / f"compositions/{sid}.html").write_text(escena(sid, g, html, css, js, dur), encoding="utf-8")
    (d / "compositions/subs.html").write_text(comp_subtitulos([], g)[1], encoding="utf-8")
    (d / "index.html").write_text(raiz_html(g, dur, [(sid, 0, dur)], [], nombre), encoding="utf-8")
    return d, dur


def todos():
    for v in ("v3", "v1"):
        for lang in ("es", "en"):
            for gch in ("a", "b", "c"):
                yield (v, lang, gch, True)
            yield (v, lang, "a", False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", help="nombre del corte, ej. v3_en_a_v (o 'bucle_es')")
    ap.add_argument("--idiomas", default="es,en")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    salida = AQUI / "cortes"
    hechos = []
    idiomas = args.idiomas.split(",")
    for v, lang, gch, vert in todos():
        nombre = f"{v}_{lang}_{gch}_{'v' if vert else 'h'}"
        if (args.solo and args.solo != nombre) or lang not in idiomas:
            continue
        if not (AQUI / f"voz/{v}_{lang}/narracion.json").exists():
            print(f"[build] falta la voz de {v}_{lang}: se salta {nombre}")
            continue
        hechos.append(corte(v, lang, gch, vert, salida))
    for lang in idiomas:
        if not args.solo or args.solo == f"bucle_{lang}":
            hechos.append(bucle(lang, salida))
    for d, dur in hechos:
        print(f"[build] {d.name}: {dur:.1f} s")
    if args.render:
        (AQUI / "renders").mkdir(exist_ok=True)
        for d, _ in hechos:
            destino = AQUI / "renders" / f"{d.name}.mp4"
            print(f"[render] {d.name}")
            npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
            subprocess.run([npx, "-y", "hyperframes@latest", "render", "--output", str(destino)], cwd=d, check=True)


if __name__ == "__main__":
    main()
