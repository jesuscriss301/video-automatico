#!/usr/bin/env python3
"""
Mini videos por nicho (guiones-7-mini-videos-nichos.md): 7 nichos x 3 ganchos,
vertical 1080x1920, en inglés, con los colores y la tipografía de cada demo.

Estructura de cada video:
    gancho  -> barra de búsqueda con la palabra clave + frase del gancho + demo en el celular
    s1      -> la palabra clave dicha y en pantalla, la demo baja (scroll)
    s2      -> qué hace la web (etiquetas) + sección de servicios de la demo
    s3      -> el sistema que va detrás: maqueta "How it works" en los colores de la demo
    s4      -> "Comment DEMO" + selector de estilos (variantes reales de la demo)

Uso:
    python estudio/nichos/build.py                 # genera los 21 proyectos
    python estudio/nichos/build.py --solo medspa_a # uno
    python estudio/nichos/build.py --render        # y renderiza a renders/
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
SFX_DIR = RAIZ / ".claude/skills/media-use/audio/assets/sfx"
W, H = 1080, 1920
WA = "wa.me/573238816434"
CIERRE_EXTRA = 2.6
HOLD_S3 = 1.4  # aire extra para ver la maqueta del software

N = {
    "medspa": dict(
        slug="aesthetics", variantes=[("aesthetics", "Blush & Gold"), ("aesthetics-champagne", "Champagne Taupe"), ("aesthetics-night", "Midnight Blush")],
        p="#c17f8a", a="#caa057", bg="#fdf8f4", ink="#3b2a2d", font=("Cormorant Garamond", "cormorant-garamond-latin-700-normal.woff2", 700),
        kw="injectables website design",
        ganchos={"a": "Your injectables clients research for weeks. Then they book whoever answers their questions *first*.",
                 "b": "This is what *injectables website design* should look like in 2026.",
                 "c": "Botox clients come back every few months. Does your website *remind them*?"},
        s2=["One page per treatment", "Free consult button"], s3=["Client CRM", "Rebooking reminders"], mock="crm_medspa",
        cta=["Comment DEMO 👇"], scroll=[(0, 900), (900, 2600), (3300, 4700)]),
    "masons": dict(
        slug="masons", variantes=[("masons", "Brick Red"), ("masons-slate", "Slate Gray")],
        p="#8a3324", a="#c9922f", bg="#faf6f2", ink="#2b211d", font=("Rajdhani", "rajdhani-latin-700-normal.woff2", 700),
        kw="masonry contractor website hosting",
        ganchos={"a": "Masonry contractors: your website is *down* and you don't even know it.",
                 "b": "What a *masonry contractor website and hosting* should include, in 40 seconds.",
                 "c": "Stop sending estimates by text. Let the website do *the first one*."},
        s2=["Hosting", "Backups", "Updates included"], s3=["Photo estimate", "Price / sq ft", "Your pipeline"], mock="kanban_masons",
        cta=["Comment DEMO 👇"], scroll=[(0, 900), (900, 2700), (2700, 4400)]),
    "autoshop": dict(
        slug="automechanics", variantes=[("automechanics", "Racing Red"), ("automechanics-yellow", "Shop Yellow")],
        p="#c8102e", a="#1d1d1f", bg="#f7f7f8", ink="#1d1d1f", font=("Teko", "teko-latin-600-normal.woff2", 600),
        kw="affordable auto shop website design",
        ganchos={"a": "Your shop is full and your phone *still rings all day*.",
                 "b": "*Affordable auto shop website design:* what $450 actually gets you.",
                 "c": "Customers don't trust mechanics they *can't see online*."},
        s2=["Prices", "Booking", "Reviews"], s3=["Work orders", "Photo inspections", "Reminders", "Inventory"], mock="orden_taller",
        cta=["Comment DEMO 👇", "Websites from $450"], scroll=[(0, 900), (900, 2500), (3000, 4600)]),
    "storage": dict(
        slug="self-storage", variantes=[("self-storage", "SafeBox")],
        p="#2b4c7e", a="#e8a33d", bg="#f6f7fa", ink="#1b2638", font=("Sora", "sora-latin-700-normal.woff2", 700),
        kw="cheap web design for self storage",
        ganchos={"a": "Empty units *cost you money* every single day.",
                 "b": "*Cheap web design for self storage,* but built to rent units online.",
                 "c": "Your customers don't know what unit size they need. *Your website should tell them.*"},
        s2=["Size calculator", "Reserve online"], s3=["Live availability", "Auto billing", "Occupancy"], mock="bodegas",
        cta=["Comment DEMO 👇", "Low setup · monthly plan"], scroll=[(0, 900), (900, 2400), (2600, 4200)]),
    "plumbers": dict(
        slug="plumbers-emergency", variantes=[("plumbers-emergency", "Emergency Orange"), ("plumbers-night", "Night Call")],
        p="#d9531e", a="#1d6fa5", bg="#f5f8fb", ink="#14212e", font=("Barlow Condensed", "barlow-condensed-latin-700-normal.woff2", 700),
        kw="website design for plumbers · Independence",
        ganchos={"a": "2 a.m., burst pipe. Your customer calls whoever *shows up first* on their phone.",
                 "b": "*Website design for plumbers in Independence:* what wins the call.",
                 "c": "Plumbers who reply in 5 minutes *win the job*. Here's how to do it automatically."},
        s2=["Drain cleaning", "Water heaters", "Leaks"], s3=["Auto-reply in 5 min", "Job → tech's phone"], mock="despacho",
        cta=["Comment DEMO 👇"], scroll=[(0, 900), (900, 2500), (3200, 4800)], oscuro=True),
    "dentists": dict(
        slug="dentists", variantes=[("dentists", "Mint Clinical"), ("dentists-sky", "Sky Blue")],
        p="#2f8f82", a="#f0a24b", bg="#f4fbfa", ink="#16302d", font=("Lexend", "lexend-latin-700-normal.woff2", 700),
        kw="responsive prosthodontic websites",
        ganchos={"a": "One implant case can *pay for your whole website*.",
                 "b": "*Responsive prosthodontic websites:* what patients check on their phone before calling.",
                 "c": "Every missed dental appointment is money that never comes back. *Unless your system recovers it.*"},
        s2=["Implants", "Dentures", "Crowns", "Financing"], s3=["Dental CRM", "No-show reminders", "Recalls"], mock="agenda_dental",
        cta=["Comment DEMO 👇"], scroll=[(0, 900), (900, 2500), (3000, 4600)], escritorio=True),
    "carwash": dict(
        slug="car-wash", variantes=[("car-wash", "Aqua Pro"), ("car-wash-turbo", "Turbo Red"), ("car-wash-night", "Night Shift")],
        p="#0f7ea3", a="#f2b705", bg="#f4fbfd", ink="#0f2733", font=("Sora", "sora-latin-700-normal.woff2", 700),
        kw="car wash website design texas",
        ganchos={"a": "The most profitable car washes in Texas don't sell washes. *They sell memberships.*",
                 "b": "*Car wash website design, Texas edition:* what actually makes money.",
                 "c": "Rainy week? *Members still pay.*"},
        s2=["Prices", "Before / after", "Monthly sign-up"], s3=["Auto billing", "QR entry", "Member perks"], mock="membresia",
        cta=["Comment DEMO 👇"], scroll=[(0, 900), (900, 2500), (3000, 4700)]),
}
CIFRAS = [("four hundred fifty dollars", "$450"), ("Two A M", "2 a.m."), ("five minutes", "5 minutes"),
          ("under five minutes", "under 5 minutes"), ("six-month", "6-month")]

# ------------------------------------------------------------------ utilidades
def mezclar(c1, c2, f):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(a, b))


def pt(n):
    """Color de marca para texto y botones con contraste suficiente."""
    return mezclar(n["p"], n["ink"], .35)

def resaltar(texto, clase="acc"):
    out = []
    for m in re.finditer(r"\*([^*]+)\*|([^*]+)", texto):
        trozo, acento = (m.group(1), True) if m.group(1) else (m.group(2), False)
        for p in trozo.split():
            if not acento and re.fullmatch(r"[.,;:?!]+", p) and out:
                out[-1] = out[-1][:-7] + p + "</span>"
                continue
            out.append(f'<span class="w{" " + clase if acento else ""}">{p}</span>')
    return " ".join(out)


def escena(sid, cuerpo, css, js):
    return f"""<template>
  <style>
    #root {{ position:absolute; inset:0; font-family:'Inter',sans-serif; }}
    .w {{ display:inline-block; }}
    {css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
{cuerpo}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def chips(sid, items, n, y, fs=40):
    html = "".join(f'<span id="{sid}-c{i}" class="chip">{t}</span>' for i, t in enumerate(items))
    css = (f".chips {{ position:absolute; left:60px; right:60px; top:{y}px; display:flex; flex-wrap:wrap; justify-content:center; gap:16px; }}"
           f".chip {{ font-weight:800; font-size:{fs}px; padding:12px 26px; border-radius:999px; background:{pt(n)}; color:#fff; }}")
    return f'<div class="chips">{html}</div>', css


def js_chips(sid, k, t0, paso):
    return "".join(f'    tl.fromTo("#{sid}-c{i}", {{opacity:0, y:20, scale:.9}}, {{opacity:1, y:0, scale:1, duration:.4, ease:"back.out(1.6)"}}, {t0 + i * paso:.2f});\n'
                   for i in range(k))


def telefono(tid, src, y=380, w=520):
    """Celular con la captura real dentro; la imagen se desplaza (scroll)."""
    h = int(w * 2.06)
    return (f'<div id="{tid}" class="tel" style="left:{(W - w) // 2}px; top:{y}px; width:{w}px; height:{h}px">'
            f'<div class="pant" data-layout-allow-overflow><img id="{tid}-img" src="assets/capturas/{src}.jpg" alt=""></div></div>')


CSS_TEL = """
.tel { position:absolute; border-radius:58px; background:#0d0d10; padding:16px; box-shadow:0 40px 90px rgba(0,0,0,.28); }
.pant { position:relative; width:100%; height:100%; border-radius:44px; overflow:hidden; background:#fff; }
.pant img { position:absolute; left:0; top:0; width:100%; }
"""


def js_scroll(tid, w, desde, hasta, t0, dur, ease="power1.inOut"):
    k = (w - 32) / 960  # px de pantalla por px de captura
    return (f'    tl.fromTo("#{tid}-img", {{y:{-desde * k:.0f}}}, {{y:{-hasta * k:.0f}, duration:{dur:.2f}, ease:"{ease}"}}, {t0:.2f});\n')


# ------------------------------------------------------------- maquetas (s3)
def maqueta(tipo, n, sid):
    p, a, ink = n["p"], n["a"], n["ink"]
    card = f"background:#fff; border-radius:28px; box-shadow:0 30px 80px rgba(0,0,0,.14); padding:34px; color:{ink};"
    head = lambda t: f'<div style="font-weight:800; font-size:34px; margin-bottom:22px">{t}</div>'
    fila = lambda i, a1, a2, col="#eef1f4": (f'<div id="{sid}-f{i}" class="fila" style="background:{col}"><b>{a1}</b><span>{a2}</span></div>')
    if tipo == "crm_medspa":
        cuerpo = (head("Patient · Sarah M.") +
                  fila(0, "Botox · 20 units", "Mar 3") + fila(1, "Lip filler", "Jan 12") + fila(2, "HydraFacial", "Dec 1") +
                  f'<div id="{sid}-msg" class="msg" style="background:{p}">📱 “Hi Sarah! It’s been 3 months since your Botox. Book your touch-up?”<div class="hora">Scheduled · Jun 3, 10:00</div></div>')
    elif tipo == "kanban_masons":
        cols = [("New", ["Patio · 240 sq ft", "Chimney repair"]), ("Quoted", ["Retaining wall"]), ("Won", ["Brick steps"])]
        cuerpo = head("Estimates pipeline") + '<div class="kan">' + "".join(
            f'<div class="col"><div class="colt" style="color:{p}">{c}</div>' + "".join(
                f'<div id="{sid}-k{ci}{j}" class="kcard">{t}</div>' for j, t in enumerate(items)) + "</div>"
            for ci, (c, items) in enumerate(cols)) + "</div>" + \
            f'<div id="{sid}-msg" class="msg" style="background:{p}">📷 New request: 3 photos · 240 sq ft → estimate sent</div>'
    elif tipo == "orden_taller":
        cuerpo = (head("Work order #1042 · 2019 Civic") +
                  fila(0, "Brake pads (front)", "Needs replacing") + fila(1, "Oil change", "Due now") + fila(2, "Tires", "OK") +
                  '<div class="fotos"><div></div><div></div><div></div></div>' +
                  f'<div id="{sid}-btn" class="btn" style="background:{p}">Send to customer</div>')
    elif tipo == "bodegas":
        celdas = "".join(f'<div class="u{" lib" if i in (2, 7, 11, 16) else ""}"></div>' for i in range(20))
        cuerpo = (head("Occupancy · 16 of 20 rented") + f'<div id="{sid}-mapa" class="mapa">{celdas}</div>' +
                  f'<div class="ley"><span style="background:#2e9e5b"></span>Rented <span style="background:#d9d9d9"></span>Available</div>' +
                  f'<div id="{sid}-msg" class="msg" style="background:{p}">💳 Monthly billing ran · 1 late-fee alert</div>')
    elif tipo == "despacho":
        cuerpo = (head("Missed call · 2:07 a.m.") +
                  f'<div id="{sid}-msg" class="msg" style="background:{p}">💬 “Sorry we missed you! Drain cleaning from $99. Reply YES and a tech is on the way.”<div class="hora">Sent in 2 min</div></div>' +
                  f'<div id="{sid}-job" class="job"><b>Tech app · New job</b><span>Drain cleaning · 412 Elm St</span><span>Route: 14 min</span></div>')
    elif tipo == "agenda_dental":
        cuerpo = (head("Today’s schedule") +
                  fila(0, "9:00 · Implant consult", "✓ Confirmed", "#e7f5f2") + fila(1, "10:30 · Denture fitting", "✓ Confirmed", "#e7f5f2") +
                  fila(2, "1:00 · Crown", "⏳ Reminder sent") +
                  f'<div id="{sid}-msg" class="msg" style="background:{p}">📱 6-month recall: “Time for your check-up. Pick a time →”</div>')
    else:  # membresia
        qr = "".join(f'<i style="background:{ink if (i * 7 + i // 9) % 3 else "transparent"}"></i>' for i in range(81))
        cuerpo = (head("Member pass · Unlimited") +
                  f'<div class="memb"><div class="qr">{qr}</div><div><b style="color:{p}">$39/mo</b><span>Auto billing · next charge Jul 1</span><span>Perk: free tire shine</span></div></div>' +
                  f'<div id="{sid}-msg" class="msg" style="background:{p}">✅ Plate checked at entrance · Welcome back!</div>')
    css = f"""
#{sid}-mq {{ position:absolute; left:80px; right:80px; top:490px; {card} font-size:30px; }}
#{sid}-tag {{ position:absolute; left:0; right:0; top:420px; text-align:center; font-size:30px; font-weight:800; letter-spacing:.14em; color:{mezclar(p, ink, .35)}; }}
.fila {{ display:flex; justify-content:space-between; padding:18px 22px; border-radius:16px; margin-bottom:12px; font-size:28px; }}
.fila span {{ color:#5b6672; }}
.msg {{ color:#fff; border-radius:22px 22px 22px 6px; padding:20px 24px; margin-top:22px; font-size:28px; line-height:1.3; }}
.hora {{ font-size:28px; opacity:.85; margin-top:8px; }}
.kan {{ display:flex; gap:14px; }} .col {{ flex:1; background:#f2f3f5; border-radius:16px; padding:12px; min-height:300px; }}
.colt {{ font-weight:800; font-size:28px; margin-bottom:10px; }} .kcard {{ background:#fff; border-radius:12px; padding:14px; font-size:28px; margin-bottom:10px; box-shadow:0 4px 10px rgba(0,0,0,.06); }}
.fotos {{ display:flex; gap:12px; margin:16px 0; }} .fotos div {{ flex:1; height:120px; border-radius:14px; background:linear-gradient(135deg,#c9ced6,#8d96a3); }}
.btn {{ color:#fff; text-align:center; font-weight:800; border-radius:999px; padding:20px; font-size:30px; }}
.mapa {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; }} .u {{ height:90px; border-radius:10px; background:#2e9e5b; }} .u.lib {{ background:#d9d9d9; }}
.ley {{ display:flex; gap:14px; align-items:center; font-size:28px; margin-top:16px; }} .ley span {{ width:22px; height:22px; border-radius:6px; display:inline-block; }}
.job {{ margin-top:22px; border:3px solid {p}; border-radius:20px; padding:20px; display:flex; flex-direction:column; gap:6px; font-size:28px; }}
.memb {{ display:flex; gap:26px; align-items:center; }} .memb div:last-child {{ display:flex; flex-direction:column; gap:6px; font-size:28px; }}
.memb b {{ font-size:48px; }} .qr {{ display:grid; grid-template-columns:repeat(9,20px); gap:3px; padding:14px; background:#fff; border:2px solid #e3e6ea; border-radius:14px; }}
.qr i {{ width:20px; height:20px; display:block; }}
"""
    html = f'<div id="{sid}-tag">HOW IT WORKS</div><div id="{sid}-mq">{cuerpo}</div>'
    return html, css


def js_maqueta(sid, dur):
    js = (f'    tl.fromTo("#{sid}-tag", {{opacity:0}}, {{opacity:1, duration:.3}}, .1);\n'
          f'    tl.fromTo("#{sid}-mq", {{opacity:0, y:60, scale:.95}}, {{opacity:1, y:0, scale:1, duration:.6, ease:"expo.out"}}, .15);\n'
          f'    tl.fromTo("#{sid}-mq .fila, #{sid}-mq .kcard, #{sid}-mq .u, #{sid}-mq .fotos div", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:.3, ease:"power3.out", stagger:.06}}, .6);\n'
          f'    tl.fromTo("#{sid}-mq .msg, #{sid}-mq .job, #{sid}-mq .btn, #{sid}-mq .memb", {{opacity:0, y:24, scale:.96}}, {{opacity:1, y:0, scale:1, duration:.45, ease:"back.out(1.5)", stagger:.5}}, {min(dur * .45, 4):.2f});\n')
    return js


# ------------------------------------------------------------------ escenas
def escena_gancho(clave, n, gch, dur):
    sid = "gancho"
    txt = n["ganchos"][gch]
    largo = len(re.sub(r"\*", "", txt))
    fs = 96 if largo <= 45 else 80 if largo <= 75 else 68
    tel = telefono(f"{sid}-t", n["slug"], y=900, w=560)
    css = CSS_TEL + f"""
#{sid}-txt {{ position:absolute; left:70px; right:70px; top:330px; text-align:center; color:{n['ink']}; font-family:'{n['font'][0]}',serif;
   font-weight:{n['font'][2]}; font-size:{fs}px; line-height:1.05; }}
.acc {{ color:{pt(n)}; }}
"""
    html = f'<div id="{sid}-txt">{resaltar(txt)}</div>{tel}'
    js = (f'    tl.fromTo("#{sid}-txt .w", {{opacity:.5}}, {{opacity:1, duration:.12, stagger:{max(dur * .7, .5) / max(len(txt.split()), 1):.3f}}}, 0);\n'
          f'    tl.fromTo("#{sid}-t", {{y:120}}, {{y:0, duration:.6, ease:"expo.out"}}, 0);\n'
          + js_scroll(f"{sid}-t", 560, n["scroll"][0][0], n["scroll"][0][1], .2, dur - .2, "power2.inOut"))
    return sid, escena(sid, html, css, js)


def escena_s1(n, dur):
    sid = "s1"
    if n.get("escritorio"):
        # dentistas: de escritorio a celular
        css = CSS_TEL + f"""
#{sid}-esc {{ position:absolute; left:60px; width:960px; top:420px; border-radius:22px; overflow:hidden; box-shadow:0 30px 80px rgba(0,0,0,.2); }}
#{sid}-esc img {{ width:100%; display:block; }}
"""
        html = (f'<div id="{sid}-esc"><img src="assets/capturas/{n["slug"]}_escritorio.jpg" alt=""></div>' + telefono(f"{sid}-t", n["slug"], y=420, w=520))
        js = (f'    tl.fromTo("#{sid}-esc", {{opacity:1, scale:1}}, {{opacity:0, scale:.6, duration:.7, ease:"power3.inOut"}}, {dur * .35:.2f});\n'
              f'    tl.fromTo("#{sid}-t", {{opacity:0, scale:1.2}}, {{opacity:1, scale:1, duration:.7, ease:"expo.out"}}, {dur * .35:.2f});\n'
              + js_scroll(f"{sid}-t", 520, n["scroll"][1][0], n["scroll"][1][1], dur * .4, dur * .6))
    else:
        css = CSS_TEL
        html = telefono(f"{sid}-t", n["slug"], y=420, w=520)
        js = js_scroll(f"{sid}-t", 520, n["scroll"][1][0], n["scroll"][1][1], 0, dur)
    return sid, escena(sid, html, css, js)


def escena_s2(n, dur):
    sid = "s2"
    ch, css_ch = chips(sid, n["s2"], n, 300, 36)
    css = CSS_TEL + css_ch
    html = ch + telefono(f"{sid}-t", n["slug"], y=470, w=500)
    js = js_chips(sid, len(n["s2"]), .2, min(dur / (len(n["s2"]) + 1), 1.2)) + js_scroll(f"{sid}-t", 500, n["scroll"][2][0], n["scroll"][2][1], 0, dur)
    return sid, escena(sid, html, css, js)


def escena_s3(n, dur):
    sid = "s3"
    ch, css_ch = chips(sid, n["s3"], n, 230, 32)
    mq, css_mq = maqueta(n["mock"], n, sid)
    js = js_chips(sid, len(n["s3"]), .3, min(dur / (len(n["s3"]) + 1), 1.3)) + js_maqueta(sid, dur)
    return sid, escena(sid, ch + mq, css_ch + css_mq, js)


def escena_s4(n, dur):
    sid = "s4"
    vs = n["variantes"]
    css = CSS_TEL + f"""
#{sid}-cta {{ position:absolute; left:0; right:0; top:250px; text-align:center; font-family:'{n['font'][0]}',serif; font-weight:{n['font'][2]};
   font-size:104px; color:{n['ink']}; line-height:1; }}
#{sid}-sub {{ position:absolute; left:0; right:0; top:372px; text-align:center; font-size:38px; font-weight:800; color:{pt(n)}; }}
.var {{ position:absolute; left:0; right:0; top:1250px; text-align:center; font-size:34px; font-weight:800; color:{n['ink']}; }}
#{sid}-wa {{ position:absolute; left:0; right:0; top:1290px; text-align:center; font-family:'JetBrains Mono',monospace; font-size:34px; color:{pt(n)}; }}
"""
    sub = n["cta"][1] if len(n["cta"]) > 1 else ""
    html = f'<div id="{sid}-cta">{n["cta"][0]}</div>' + (f'<div id="{sid}-sub">{sub}</div>' if sub else "")
    paso = max(dur - .4, 1) / len(vs)
    js = (f'    tl.fromTo("#{sid}-cta", {{opacity:0, scale:.8}}, {{opacity:1, scale:1, duration:.5, ease:"back.out(1.7)"}}, 0);\n'
          + (f'    tl.fromTo("#{sid}-sub", {{opacity:0}}, {{opacity:1, duration:.4}}, .4);\n' if sub else ""))
    if len(vs) == 1:  # sin variantes: logo + WhatsApp
        html += telefono(f"{sid}-t0", vs[0][0], y=470, w=360) + f'<div id="{sid}-wa">&gt;_ {WA}</div>'
        js += f'    tl.fromTo("#{sid}-wa", {{opacity:0}}, {{opacity:1, duration:.4}}, .6);\n'
    for i, (slug, label) in enumerate(vs):
        if len(vs) == 1:
            break
        html += telefono(f"{sid}-t{i}", slug, y=470, w=360) + f'<div id="{sid}-l{i}" class="var" data-layout-allow-overlap>{label}</div>'
        t0 = i * paso
        js += (f'    tl.fromTo("#{sid}-t{i}, #{sid}-l{i}", {{opacity:0, x:80}}, {{opacity:1, x:0, duration:.4, ease:"expo.out"}}, {t0:.2f});\n')
        if i < len(vs) - 1:
            js += f'    tl.to("#{sid}-t{i}, #{sid}-l{i}", {{opacity:0, x:-80, duration:.3, ease:"power3.in"}}, {t0 + paso - .05:.2f});\n'
    return sid, escena(sid, html, css, js)


# --------------------------------------------------------------- subtítulos
def grupos(texto, ini, fin, maxp=3):
    for a, b in CIFRAS:
        texto = texto.replace(a, b)
    pal = texto.split()
    gs, act = [], []
    for p in pal:
        act.append(p)
        if len(act) >= maxp or re.search(r"[.,;:?!]$", p):
            gs.append(" ".join(act)); act = []
    if act:
        gs.append(" ".join(act))
    tot = sum(len(g) + 2 for g in gs)
    out, t = [], ini
    for g in gs:
        d = (fin - ini) * (len(g) + 2) / tot
        out.append((g, t, d)); t += d
    return out


def comp_subs(gs, n, kw):
    sid = "subs"
    css = f"""
.grp {{ position:absolute; left:0; right:0; top:1140px; text-align:center; }}
.grp span {{ display:inline-block; font-weight:900; font-size:66px; color:#fff; max-width:920px; padding:8px 26px 12px;
   border-radius:16px; background:rgba(15,15,20,.86); line-height:1.12; }}
.grp b {{ color:{n['a'] if n.get('oscuro') else n['p']}; filter:brightness(1.35); }}
"""
    kw_words = set(re.sub(r"[^a-z ]", " ", kw.lower()).split())
    html, js = "", ""
    for i, (txt, t0, d) in enumerate(gs):
        partes = []
        for w in txt.split():
            limpio = re.sub(r"[^a-z$0-9]", "", w.lower())
            partes.append(f"<b>{w}</b>" if (limpio in kw_words and len(limpio) > 3) or re.search(r"\d", w) else w)
        html += f'    <div id="g{i}" class="grp clip" data-start="{t0:.3f}" data-duration="{d:.3f}"><span id="g{i}s">{" ".join(partes)}</span></div>\n'
        js += (f'    tl.fromTo("#g{i}s", {{opacity:0, scale:.9}}, {{opacity:1, scale:1, duration:.12, ease:"back.out(2)"}}, {t0:.3f});\n'
               f'    tl.to("#g{i}s", {{opacity:0, duration:.06}}, {t0 + d - .06:.3f});\n')
    return escena(sid, html, css, js)


# -------------------------------------------------------------------- armar
def ffmpeg(*a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)


def raiz(n, total, escenas, audios, titulo):
    hosts = "".join(
        f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{t0:.3f}" '
        f'data-duration="{d:.3f}" data-track-index="{i + 2}" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:{i + 2}"></div>\n'
        for i, (sid, t0, d) in enumerate(escenas))
    aud = "".join(f'      <audio id="{aid}" class="clip" src="{src}" data-start="{t0:.3f}" data-track-index="{40 + i}" data-volume="{vol}"></audio>\n'
                  for i, (aid, src, t0, vol) in enumerate(audios))
    fam, archivo, peso = n["font"]
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{titulo}</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family:'{fam}'; src:url('assets/fonts/{archivo}') format('woff2'); font-weight:{peso}; }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:{n['bg']}; }}
      #fondo {{ position:absolute; inset:0; background:{n['bg']}; z-index:0; }}
      #fondo .halo {{ position:absolute; width:1400px; height:1400px; border-radius:50%; left:-160px; top:-500px;
        background:radial-gradient(circle, {n['p']}33, {n['p']}00 65%); }}
      #busca {{ position:absolute; left:80px; right:80px; top:185px; z-index:30; height:96px; border-radius:48px; background:#fff;
        box-shadow:0 10px 30px rgba(0,0,0,.12); display:flex; align-items:center; gap:18px; padding:0 34px; font-size:36px; color:#20242a; font-weight:600; }}
      #busca i {{ font-style:normal; font-size:36px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}">
      <div id="fondo" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="0" data-layout-allow-overflow><div class="halo"></div></div>
      <div id="busca" class="clip" data-start="0" data-duration="{escenas[1][1] + escenas[1][2]:.3f}" data-track-index="1"><i>🔍</i><span id="busca-t">{n['kw']}</span></div>
{hosts}      <div id="subs" data-composition-id="subs" data-composition-src="compositions/subs.html" data-start="0" data-duration="{total:.3f}"
        data-track-index="30" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:30"></div>
{aud}    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#fondo .halo", {{x:0, y:0}}, {{x:300, y:900, duration:{total:.3f}, ease:"none"}}, 0);
      tl.to("#busca", {{opacity:0, y:-20, duration:.25, ease:"power3.in"}}, {escenas[1][1] + escenas[1][2] - .3:.3f});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def copiar_captura(src: Path, dst: Path):
    if not dst.exists():
        Image.open(src).convert("RGB").save(dst, quality=88)


def video(clave, gch, salida: Path):
    n = N[clave]
    voz = json.loads((AQUI / f"voz/{clave}/narracion.json").read_text(encoding="utf-8"))
    L = {l["id"]: l for l in voz["lineas"]}
    nombre = f"{clave}_{gch}"
    d = salida / nombre
    for sub in ("compositions", "assets/vendor", "assets/fonts", "assets/capturas", "assets/sfx"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy(AQUI / "vendor/gsap.min.js", d / "assets/vendor/gsap.min.js")
    shutil.copy(AQUI / "fonts" / n["font"][1], d / "assets/fonts" / n["font"][1])
    slugs = {n["slug"]} | {s for s, _ in n["variantes"]}
    for s in slugs:
        copiar_captura(AQUI / f"capturas/{s}_movil.png", d / f"assets/capturas/{s}.jpg")
    if n.get("escritorio"):
        copiar_captura(AQUI / f"capturas/{n['slug']}_escritorio.png", d / f"assets/capturas/{n['slug']}_escritorio.jpg")

    orden = [f"gancho_{gch}", "s1", "s2", "s3", "s4"]
    escenas, gs, t = [], [], 0.0
    base = {lid: L[lid]["duracion"] + (HOLD_S3 if lid == "s3" else 0) + (CIERRE_EXTRA if lid == "s4" else 0) for lid in orden}
    falta = max(0.0, 35.5 - sum(base.values()))  # el guion pide 35-45 s
    base["s3"] += falta * .6
    base["s4"] += falta * .4
    for lid in orden:
        dur = base[lid]
        if lid.startswith("gancho"):
            sid, html = escena_gancho(clave, n, gch, dur)
        else:
            sid, html = {"s1": escena_s1, "s2": escena_s2, "s3": escena_s3, "s4": escena_s4}[lid](n, dur)
        (d / f"compositions/{sid}.html").write_text(html, encoding="utf-8")
        escenas.append((sid, t, dur))
        if lid not in ("s4",) and not lid.startswith("gancho"):
            for c in L[lid]["subtitulos"]:
                gs += grupos(c["texto"], t + c["inicio"] - L[lid]["inicio"] + .04, t + c["fin"] - L[lid]["inicio"])
        t += dur
    total = t
    (d / "compositions/subs.html").write_text(comp_subs(gs, n, n["kw"]), encoding="utf-8")

    # voz: cada línea en su lugar (el aire extra de s3 queda en silencio)
    filtros, ins = [], []
    for i, (lid, (sid, t0, _)) in enumerate(zip(orden, escenas)):
        ins += ["-i", str(AQUI / f"voz/{clave}/{lid}.wav")]
        filtros.append(f"[{i}:a]adelay={int(t0 * 1000)}:all=1[a{i}]")
    filtros.append("".join(f"[a{i}]" for i in range(len(orden))) + f"amix=inputs={len(orden)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[o]")
    ffmpeg(*ins, "-filter_complex", ";".join(filtros), "-map", "[o]", "-ac", "1", "-t", f"{total:.3f}", "-c:a", "pcm_s16le", str(d / "assets/voz.wav"))

    def sfx(nom):
        shutil.copy(SFX_DIR / f"{nom}.mp3", d / f"assets/sfx/{nom}.mp3")
        return f"assets/sfx/{nom}.mp3"
    audios = [("voz", "assets/voz.wav", 0, 1)]
    for i, (sid, t0, _) in enumerate(escenas[1:], 1):
        audios.append((f"fx{i}", sfx("whoosh-short" if i % 2 else "whoosh"), max(t0 - .1, 0), .25))
    s3 = escenas[3][1]
    audios.append(("fx-msg", sfx("notification"), s3 + min(escenas[3][2] * .45, 4), .3))
    audios.append(("fx-cta", sfx("pop"), escenas[4][1] + .05, .35))

    (d / "index.html").write_text(raiz(n, total, escenas, audios, nombre), encoding="utf-8")
    return d, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    salida = AQUI / "cortes"
    hechos = []
    for clave in N:
        for g in "abc":
            if args.solo and args.solo != f"{clave}_{g}":
                continue
            hechos.append(video(clave, g, salida))
    for d, t in hechos:
        print(f"[nichos] {d.name}: {t:.1f} s")
    if args.render:
        (AQUI / "renders").mkdir(exist_ok=True)
        npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
        for d, _ in hechos:
            subprocess.run([npx, "-y", "hyperframes@latest", "render", "--output", str(AQUI / "renders" / f"{d.name}.mp4")], cwd=d, check=True)


if __name__ == "__main__":
    main()
