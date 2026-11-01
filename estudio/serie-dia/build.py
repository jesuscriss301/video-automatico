#!/usr/bin/env python3
"""
Serie "Día X tratando de que una clínica estética no pierda ni una cita más… usando solo software".
7 videos verticales 1080x1920 en español (el Día 1 con 3 ganchos = 9 videos), voz "El documentalista".

Plantilla fija:
    gancho  -> fondo oscuro, "DÍA X / 7" en cian y la frase del gancho
    ayer    -> tarjeta "Ayer" (días 2-6)
    hoy     -> lo que se arma hoy, con maqueta etiquetada "Así lo estoy armando"
    meta    -> la meta del día
    mañana / cta -> lo que viene o la llamada a la acción

Uso:
    python estudio/serie-dia/build.py                # genera los 9 proyectos en cortes/
    python estudio/serie-dia/build.py --solo dia3    # uno
    python estudio/serie-dia/build.py --render       # y renderiza a renders/
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
NICHOS = AQUI.parent / "nichos"
SFX_DIR = RAIZ / ".claude/skills/media-use/audio/assets/sfx"

_spec = importlib.util.spec_from_file_location("nichos_build", NICHOS / "build.py")
nb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nb)
escena, telefono, CSS_TEL, js_scroll, resaltar, mezclar = nb.escena, nb.telefono, nb.CSS_TEL, nb.js_scroll, nb.resaltar, nb.mezclar
W, H = nb.W, nb.H

# Marca de la serie + colores de la demo (Lumora · Blush & Gold)
CIAN, OSCURO = "#38BFF0", "#0B0F1A"
P, A, BG, INK = "#c17f8a", "#caa057", "#fdf8f4", "#3b2a2d"
PT = mezclar(P, INK, .35)          # rosa con contraste para texto
SERIF = ("Cormorant Garamond", "cormorant-garamond-latin-700-normal.woff2", 700)
MIN_TOTAL = 31.0
CIERRE_EXTRA = 1.6
SUB_TOP = 1590
VEL = 1.12           # voz 12 % más rápida (sin cambiar el tono): retiene mejor en reels

GANCHOS = {
    "gancho_a": "Tratando de que una clínica estética *no pierda ni una cita más,* solo con software.",
    "gancho_b": "Tratando de *llenarle la agenda* a una clínica estética *sin pagar anuncios.*",
    "gancho_c": "Le voy a demostrar a una clínica de Medellín *cuánta plata pierde* por citas perdidas.",
    2: "Hoy toca que *agenden sin escribir.*",
    3: "Hoy, que el sistema *les escriba solo.*",
    4: "Hoy se lo muestro a *diez clínicas* de Medellín.",
    5: "Hoy toca *responder los no.*",
    6: "Hoy, la *primera demo* en llamada.",
    7: "*El resumen* de la semana.",
}
AYER = {2: "El problema: citas perdidas", 3: "La web que agenda sola", 4: "La demo lista",
        5: "El mensaje a las clínicas", 6: "Cómo responder los no"}
META = {2: "Ninguna clienta espera una respuesta para agendar", 4: "Que al menos una quiera verlo en una llamada",
        5: "Agendar las primeras demos en llamada"}
MANANA = {1: "Que agenden sin escribirte", 2: "Los recordatorios automáticos", 3: "Mostrarlo a clínicas reales",
          4: "Qué respondieron (y quién me dejó en visto)", 6: "El resumen de la semana"}
CTA = {1: ("Sígueme 👉", "Mañana: Día 2"), 5: ("Comenta DEMO 👇", "Si tienes una clínica, lo ves con la tuya"),
       7: ("Comenta DEMO 👇", "Y lo ves con tu clínica")}
# escena "hoy" (y algunas metas) de cada día
TIPO = {(1, "problema"): "problema", (1, "hoy"): "plan", (2, "hoy"): "reserva", (3, "hoy"): "recordatorio",
        (3, "meta"): "retoque", (4, "hoy"): "clinicas", (5, "hoy"): "objecion", (6, "hoy"): "llamada",
        (6, "meta"): "escucho", (7, "hoy"): "semana", (7, "vota"): "vota"}
VIDEOS = [("dia1_a", 1, "gancho_a"), ("dia1_b", 1, "gancho_b"), ("dia1_c", 1, "gancho_c")] + \
         [(f"dia{d}", d, "gancho") for d in range(2, 8)]
CIFRAS = [("diez de la noche", "10 p. m."), ("diez clínicas", "10 clínicas"), ("siete días", "7 días"),
          ("Día uno", "Día 1"), ("Día dos", "Día 2"), ("Día tres", "Día 3"), ("Día cuatro", "Día 4"),
          ("Día cinco", "Día 5"), ("Día seis", "Día 6"), ("Día siete", "Día 7")]

# ----------------------------------------------------------------- estilos
CSS_BASE = f"""
.tag {{ position:absolute; left:0; right:0; top:{{TOP}}px; text-align:center; font-size:30px; font-weight:800; letter-spacing:.16em; color:{PT}; }}
.titulo {{ position:absolute; left:70px; right:70px; text-align:center; font-family:'{SERIF[0]}',serif; font-weight:700; color:{INK}; line-height:1.02; }}
.card {{ background:#fff; border-radius:30px; box-shadow:0 30px 80px rgba(59,42,45,.14); color:{INK}; }}
.fila {{ display:flex; justify-content:space-between; align-items:center; padding:20px 24px; border-radius:18px; background:#f6efea; font-size:32px; margin-bottom:14px; }}
.fila span {{ color:#6b5a5d; }}
.btn {{ display:inline-block; color:#fff; background:{PT}; font-weight:800; border-radius:999px; padding:18px 30px; font-size:30px; }}
.btn.sec {{ background:#fff; color:{PT}; border:3px solid {PT}; }}
.burb {{ border-radius:28px 28px 28px 8px; padding:24px 28px; font-size:32px; line-height:1.3; }}
.mini {{ font-size:28px; color:#6b5a5d; }}
"""


def tel_izq(tid, y, w):
    return telefono(tid, "lumora", y=y, w=w).replace(f"left:{(W - w) // 2}px", "left:50px")


def tag(sid, texto, top):
    return f'<div id="{sid}-tag" class="tag in" style="top:{top}px">{texto}</div>'


def js_in(sid, dur, t0=.15, frac=.55, sel=".in"):
    """Entrada escalonada de todo lo que tenga la clase .in, repartida en la primera parte de la escena."""
    return (f'    (function(){{ const els = document.querySelectorAll("#root {sel}");'
            f' const paso = Math.min(.9, {dur * frac:.2f} / Math.max(els.length, 1));'
            f' els.forEach((e, i) => tl.fromTo(e, {{opacity:0, y:34}}, {{opacity:1, y:0, duration:.45, ease:"expo.out"}}, {t0} + i * paso)); }})();\n')


# ------------------------------------------------------------------ escenas
def e_gancho(dia, gid, dur):
    sid = "gancho"
    txt = GANCHOS[gid] if dia == 1 else GANCHOS[dia]
    largo = len(txt.replace("*", ""))
    fs = 92 if largo <= 40 else 80 if largo <= 70 else 70
    puntos = "".join(f'<i class="{"on" if k + 1 == dia else "pas" if k + 1 < dia else ""}"></i>' for k in range(7))
    css = f"""
#root {{ background:{OSCURO}; }}
#{sid}-dia {{ position:absolute; left:0; right:0; top:430px; text-align:center; font-family:'JetBrains Mono',monospace; font-weight:800;
   font-size:190px; color:{CIAN}; letter-spacing:-.02em; }}
#{sid}-dia small {{ font-size:90px; color:#5d6b85; }}
#{sid}-pts {{ position:absolute; left:0; right:0; top:700px; display:flex; justify-content:center; gap:22px; }}
#{sid}-pts i {{ width:26px; height:26px; border-radius:50%; background:#232a3b; display:block; }}
#{sid}-pts i.pas {{ background:#3f6f86; }} #{sid}-pts i.on {{ background:{CIAN}; box-shadow:0 0 30px {CIAN}; }}
#{sid}-txt {{ position:absolute; left:80px; right:80px; top:860px; text-align:center; color:#f2f4f8; font-weight:800;
   font-size:{fs}px; line-height:1.08; }}
#{sid}-txt .acc {{ color:{CIAN}; }}
#{sid}-sub {{ position:absolute; left:0; right:0; top:1480px; text-align:center; font-size:30px; font-weight:700; letter-spacing:.14em; color:#8a96ad; }}
"""
    html = (f'<div id="{sid}-dia">DÍA {dia}<small> / 7</small></div><div id="{sid}-pts">{puntos}</div>'
            f'<div id="{sid}-txt">{resaltar(txt)}</div><div id="{sid}-sub">SOLO CON SOFTWARE · MEDELLÍN</div>')
    n = len(txt.split())
    js = (f'    tl.fromTo("#{sid}-dia", {{opacity:0, scale:1.25}}, {{opacity:1, scale:1, duration:.5, ease:"expo.out"}}, 0);\n'
          f'    tl.fromTo("#{sid}-pts i", {{opacity:0, scale:0}}, {{opacity:1, scale:1, duration:.25, ease:"back.out(2)", stagger:.05}}, .3);\n'
          f'    tl.fromTo("#{sid}-txt .w", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:.25, ease:"power3.out", stagger:{max(dur * .75 - .6, .5) / n:.3f}}}, .6);\n'
          f'    tl.fromTo("#{sid}-sub", {{opacity:0}}, {{opacity:1, duration:.4}}, {min(dur * .6, 3):.2f});\n')
    return sid, escena(sid, html, css, js)


def e_texto(sid, rotulo, texto, dur, sub=None, grande=False):
    """Tarjetas de ayer / meta / mañana / cta."""
    fs = 120 if grande else (92 if len(texto) <= 34 else 76)
    css = CSS_BASE.replace("{TOP}", "520") + f"""
#{sid}-t {{ top:620px; font-size:{fs}px; }}
#{sid}-s {{ position:absolute; left:0; right:0; top:1180px; text-align:center; font-size:40px; font-weight:800; color:{PT}; }}
#{sid}-l {{ position:absolute; left:440px; right:440px; top:590px; height:6px; border-radius:3px; background:{A}; }}
"""
    html = (tag(sid, rotulo, 520) + f'<div id="{sid}-t" class="titulo in">{texto}</div>' +
            (f'<div id="{sid}-s" class="in">{sub}</div>' if sub else ""))
    js = js_in(sid, dur, frac=.4)
    if grande:
        js += f'    tl.to("#{sid}-t", {{scale:1.06, duration:.5, yoyo:true, repeat:3, ease:"sine.inOut"}}, 1.2);\n'
    return sid, escena(sid, html, css, js)


def e_problema(sid, dur):
    items = [("💬", "No contestan", "a tiempo"), ("📅", "No recuerdan", "la cita"), ("🔁", "No vuelven", "al retoque")]
    css = CSS_BASE.replace("{TOP}", "330") + f"""
#{sid}-h {{ top:390px; font-size:84px; }}
.prob {{ position:absolute; left:110px; right:110px; height:250px; display:flex; align-items:center; gap:40px; padding:0 50px; }}
.prob .ico {{ font-size:96px; }} .prob b {{ display:block; font-family:'{SERIF[0]}',serif; font-size:72px; }}
.prob span {{ font-size:36px; color:#6b5a5d; }}
.prob .x {{ margin-left:auto; font-size:72px; color:#c0392b; font-weight:900; }}
"""
    html = tag(sid, "POR QUÉ SE PIERDEN CITAS", 330) + f'<div id="{sid}-h" class="titulo in">Tres fugas</div>' + "".join(
        f'<div class="prob card in" style="top:{600 + i * 290}px"><div class="ico">{ic}</div><div><b>{a}</b><span>{b}</span></div><div class="x">✕</div></div>'
        for i, (ic, a, b) in enumerate(items))
    return sid, escena(sid, html, css, js_in(sid, dur, frac=.7))


def e_plan(sid, dur):
    piezas = [("🗓️", "Web que agenda sola"), ("💬", "Recordatorios por WhatsApp"), ("👩", "Registro de cada clienta")]
    css = CSS_TEL + CSS_BASE.replace("{TOP}", "300") + f"""
.pz {{ position:absolute; left:550px; right:60px; height:220px; padding:30px; display:flex; flex-direction:column; justify-content:center; gap:10px; }}
.pz i {{ font-style:normal; font-size:60px; }} .pz b {{ font-size:38px; line-height:1.1; }}
#{sid}-fin {{ position:absolute; left:60px; right:60px; top:1390px; text-align:center; font-size:40px; font-weight:800; color:#fff; background:{PT};
   border-radius:999px; padding:22px; }}
"""
    html = (tag(sid, "EL PLAN DE LA SEMANA", 300) + tel_izq(f"{sid}-t", 380, 460) +
            "".join(f'<div class="pz card in" style="top:{390 + i * 250}px"><i>{ic}</i><b>{t}</b></div>' for i, (ic, t) in enumerate(piezas)) +
            f'<div id="{sid}-fin" class="in">→ y presentarlo a clínicas reales</div>')
    js = js_in(sid, dur, frac=.75) + js_scroll(f"{sid}-t", 460, 0, 2600, 0, dur)
    return sid, escena(sid, html, css, js)


def e_reserva(sid, dur):
    horas = ["9:00", "10:30", "12:00", "3:00", "4:30", "6:00"]
    css = CSS_TEL + CSS_BASE.replace("{TOP}", "290") + f"""
.paso {{ position:absolute; left:540px; right:50px; padding:28px; }}
.paso .n {{ font-size:26px; font-weight:800; letter-spacing:.12em; color:{PT}; margin-bottom:12px; }}
.paso b {{ font-family:'{SERIF[0]}',serif; font-size:52px; display:block; }}
.grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
.grid span {{ text-align:center; padding:14px 0; border-radius:12px; background:#f6efea; font-size:28px; font-weight:700; }}
.grid span.sel {{ background:{PT}; color:#fff; }}
#{sid}-ok {{ text-align:center; }} #{sid}-ok .chk {{ font-size:80px; }}
"""
    html = (tag(sid, "ASÍ LO ESTOY ARMANDO", 290) + tel_izq(f"{sid}-t", 370, 440) +
            f'<div class="paso card in" style="top:370px"><div class="n">1 · TRATAMIENTO</div><b>Limpieza facial</b><div class="mini">Qué es · cuánto dura · precio</div></div>'
            f'<div class="paso card in" style="top:660px"><div class="n">2 · HORARIO</div><div class="grid">' +
            "".join(f'<span class="{"sel" if h == "3:00" else ""}">{h}</span>' for h in horas) + '</div></div>'
            f'<div id="{sid}-ok" class="paso card in" style="top:1010px"><div class="chk">✅</div><b>Cita reservada</b><div class="mini">sin esperar respuesta</div></div>')
    js = js_scroll(f"{sid}-t", 440, 3500, 6200, 0, dur) + js_in(sid, dur, t0=.4, frac=.65)
    return sid, escena(sid, html, css, js)


def e_recordatorio(sid, dur):
    css = CSS_BASE.replace("{TOP}", "300") + f"""
#{sid}-wa {{ position:absolute; left:60px; right:60px; top:380px; font-size:40px; background:#e9dfd6; border-radius:34px; overflow:hidden; }}
#{sid}-wa .hd {{ background:#075e54; color:#fff; font-size:38px; font-weight:700; padding:22px 30px; }}
#{sid}-wa .bd {{ padding:30px; }}
#{sid}-wa .burb {{ background:#fff; color:{INK}; font-size:40px; }}
.btns {{ display:flex; flex-direction:column; gap:12px; margin-top:14px; }}
.btns div {{ background:#fff; border-radius:18px; text-align:center; padding:24px; font-size:40px; font-weight:800; color:#128c7e; }}
#{sid}-ag {{ position:absolute; left:60px; right:60px; top:1260px; padding:26px 30px; }}
"""
    html = (tag(sid, "ASÍ LO ESTOY ARMANDO · 24 H ANTES", 300) +
            f'<div id="{sid}-wa" class="in"><div class="hd">Clínica · WhatsApp</div><div class="bd">'
            f'<div class="burb in">Hola 👋 Te recordamos tu cita de mañana:<br><b>Limpieza facial · 3:00 p. m.</b></div>'
            f'<div class="btns"><div class="in">✅ Confirmar</div><div class="in">🔄 Cambiar hora</div><div id="{sid}-can" class="in">✕ Cancelar</div></div></div></div>'
            f'<div id="{sid}-ag" class="card in"><div class="fila" style="margin:0"><b>3:00 p. m.</b><span id="{sid}-lib">Libre para otra clienta</span></div></div>')
    js = js_in(sid, dur, frac=.7) + \
        f'    tl.to("#{sid}-can", {{backgroundColor:"#ffe3e3", color:"#c0392b", scale:1.04, duration:.3, yoyo:true, repeat:1}}, {dur * .62:.2f});\n'
    return sid, escena(sid, html, css, js)


def e_retoque(sid, dur):
    css = CSS_BASE.replace("{TOP}", "300") + f"""
#{sid}-c {{ position:absolute; left:90px; right:90px; top:380px; padding:36px; }}
#{sid}-c h3 {{ font-family:'{SERIF[0]}',serif; font-size:62px; margin-bottom:22px; }}
#{sid}-m {{ position:absolute; left:90px; right:90px; top:1050px; background:{PT}; color:#fff; }}
#{sid}-m .mini {{ color:#fff; opacity:.85; margin-top:10px; }}
"""
    html = (tag(sid, "FICHA DE LA CLIENTA · EJEMPLO", 300) +
            f'<div id="{sid}-c" class="card in"><h3>Clienta · Laura G.</h3>'
            f'<div class="fila in"><b>Toxina botulínica</b><span>hace 4 meses</span></div>'
            f'<div class="fila in"><b>Limpieza facial</b><span>hace 2 meses</span></div>'
            f'<div class="fila in" style="background:#fbe9d0"><b>Próximo retoque</b><span>esta semana</span></div></div>'
            f'<div id="{sid}-m" class="burb in">💬 “Hola Laura, ya toca tu retoque. ¿Te agendo?”<div class="mini">Enviado solo por el sistema</div></div>')
    return sid, escena(sid, html, css, js_in(sid, dur, frac=.6))


def e_clinicas(sid, dur):
    css = CSS_BASE.replace("{TOP}", "290") + f"""
#{sid}-l {{ position:absolute; left:80px; right:80px; top:360px; padding:26px; display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
#{sid}-l div {{ display:flex; align-items:center; gap:12px; font-size:28px; padding:14px 18px; border-radius:14px; background:#f6efea; }}
#{sid}-l i {{ font-style:normal; flex:1; height:22px; border-radius:6px; background:#d9c8c2; }}
#{sid}-m {{ position:absolute; left:80px; right:80px; top:870px; background:#dcf8c6; color:#1f2d1f; }}
"""
    filas = "".join(f'<div class="in">🏥 <i></i> ✔</div>' for _ in range(10))
    html = (tag(sid, "10 CLÍNICAS DE MEDELLÍN · NOMBRES OCULTOS", 290) + f'<div id="{sid}-l" class="card in">{filas}</div>'
            f'<div id="{sid}-m" class="burb in">Hola 👋 Armé una demo de cómo <b>[su clínica]</b> podría agendar sin WhatsApp '
            f'y recordarle cada cita a sus clientas. Ya tiene su nombre puesto. ¿Se la muestro en 10 minutos?</div>')
    return sid, escena(sid, html, css, js_in(sid, dur, frac=.75))


def e_objecion(sid, dur):
    css = CSS_BASE.replace("{TOP}", "300") + f"""
#{sid}-o {{ top:390px; font-size:76px; font-style:italic; }}
#{sid}-r {{ position:absolute; left:90px; right:90px; top:760px; padding:34px; }}
#{sid}-r .hora {{ font-family:'JetBrains Mono',monospace; font-size:64px; font-weight:800; color:{INK}; margin-bottom:20px; }}
#{sid}-r .burb {{ background:#f6efea; margin-bottom:16px; }}
#{sid}-r .ok {{ background:{PT}; color:#fff; border-radius:28px 28px 8px 28px; margin-left:80px; }}
"""
    html = (tag(sid, "OBJECIÓN TÍPICA", 300) + f'<div id="{sid}-o" class="titulo in">“Ya tenemos a alguien que contesta.”</div>'
            f'<div id="{sid}-r" class="card in"><div class="hora">🌙 10:00 p. m.</div>'
            f'<div class="burb in">Hola, ¿tienen cita para mañana? 🙏</div>'
            f'<div class="mini in" style="margin:0 0 16px 10px">La recepcionista ya se fue a casa…</div>'
            f'<div class="burb ok in">✅ Agendada · mañana 11:00 a. m.<br><span style="font-size:26px; opacity:.85">respuesta automática</span></div></div>')
    return sid, escena(sid, html, css, js_in(sid, dur, frac=.8))


def e_llamada(sid, dur):
    items = [("🗓️", "Cómo agenda una clienta"), ("💬", "El recordatorio que le llega"), ("👩", "La ficha con su historial")]
    css = CSS_BASE.replace("{TOP}", "330") + f"""
#{sid}-h {{ top:400px; font-size:82px; }}
.it {{ position:absolute; left:100px; right:100px; height:220px; display:flex; align-items:center; gap:34px; padding:0 44px; font-size:44px; font-weight:800; }}
.it .num {{ width:90px; height:90px; border-radius:50%; background:{PT}; color:#fff; display:flex; align-items:center; justify-content:center; font-size:44px; flex:none; }}
"""
    html = tag(sid, "EN LA LLAMADA · CON SU NOMBRE", 330) + f'<div id="{sid}-h" class="titulo in">Muestro 3 cosas</div>' + "".join(
        f'<div class="it card in" style="top:{620 + i * 260}px"><div class="num">{i + 1}</div><div>{ic} {t}</div></div>' for i, (ic, t) in enumerate(items))
    return sid, escena(sid, html, css, js_in(sid, dur, frac=.75))


def e_escucho(sid, dur):
    css = CSS_BASE.replace("{TOP}", "380") + f"""
#{sid}-h {{ top:450px; font-size:96px; }}
.pq {{ position:absolute; left:100px; right:100px; padding:40px 44px; font-size:50px; font-weight:800; }}
"""
    html = (tag(sid, "ESCUCHO MÁS DE LO QUE HABLO", 380) + f'<div id="{sid}-h" class="titulo in">Dos preguntas</div>'
            f'<div class="pq card in" style="top:720px">❓ ¿Qué usan hoy para agendar?</div>'
            f'<div class="pq card in" style="top:1000px">💸 ¿Cuánto les cuesta una cita perdida?</div>')
    return sid, escena(sid, html, css, js_in(sid, dur, frac=.6))


def e_semana(sid, dur):
    filas = [("Día 1", "El problema"), ("Día 2", "Web que agenda sola"), ("Día 3", "Recordatorios y retoque"),
             ("Día 4", "Mensaje a 10 clínicas"), ("Día 5", "Responder los no"), ("Día 6", "Demo en llamada")]
    css = CSS_BASE.replace("{TOP}", "300") + f"""
#{sid}-c {{ position:absolute; left:80px; right:80px; top:380px; padding:30px; }}
#{sid}-c .fila b {{ color:{PT}; width:150px; }} #{sid}-c .fila em {{ font-style:normal; flex:1; }}
#{sid}-c .fila span {{ color:#2e9e5b; font-size:40px; }}
"""
    html = tag(sid, "LA SEMANA EN 7 DÍAS", 300) + f'<div id="{sid}-c" class="card in">' + "".join(
        f'<div class="fila in"><b>{d}</b><em>{t}</em><span>✔</span></div>' for d, t in filas) + '</div>'
    return sid, escena(sid, html, css, js_in(sid, dur, frac=.8))


def e_vota(sid, dur):
    ops = [("🔧", "Taller mecánico"), ("🦷", "Odontología"), ("📦", "Bodegas")]
    css = CSS_BASE.replace("{TOP}", "330") + f"""
#{sid}-h {{ top:400px; font-size:84px; }}
.op {{ position:absolute; left:120px; right:120px; height:220px; display:flex; align-items:center; gap:40px; padding:0 50px; font-size:56px; font-weight:800; }}
.op i {{ font-style:normal; font-size:100px; }}
"""
    html = tag(sid, "LA PRÓXIMA SEMANA", 330) + f'<div id="{sid}-h" class="titulo in">Vota en los comentarios</div>' + "".join(
        f'<div class="op card in" style="top:{640 + i * 260}px"><i>{ic}</i>{t}</div>' for i, (ic, t) in enumerate(ops))
    return sid, escena(sid, html, css, js_in(sid, dur, frac=.6))


ESCENAS = {"problema": e_problema, "plan": e_plan, "reserva": e_reserva, "recordatorio": e_recordatorio, "retoque": e_retoque,
           "clinicas": e_clinicas, "objecion": e_objecion, "llamada": e_llamada, "escucho": e_escucho, "semana": e_semana, "vota": e_vota}


def hacer_escena(dia, lid, sid, dur):
    if lid.startswith("gancho"):
        return e_gancho(dia, lid, dur)
    tipo = TIPO.get((dia, lid))
    if tipo:
        return sid, ESCENAS[tipo](sid, dur)[1]
    if lid == "ayer":
        return e_texto(sid, "AYER", AYER[dia], dur)
    if lid == "meta":
        return e_texto(sid, "LA META", META[dia], dur)
    if lid == "manana":
        return e_texto(sid, "MAÑANA", MANANA[dia], dur, sub=f"Día {dia + 1} 👉")
    if lid == "cta":
        a, b = CTA[dia]
        return e_texto(sid, "", a, dur, sub=b, grande=True)
    raise ValueError((dia, lid))


# --------------------------------------------------------------- subtítulos
def grupos(texto, ini, fin, maxp=3):
    for a, b in CIFRAS:
        texto = texto.replace(a, b)
    gs, act = [], []
    for p in texto.split():
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


def comp_subs(gs):
    sid = "subs"
    css = f"""
.grp {{ position:absolute; left:0; right:0; top:{SUB_TOP}px; text-align:center; }}
.grp span {{ display:inline-block; font-weight:900; font-size:64px; color:#fff; max-width:940px; padding:8px 26px 12px;
   border-radius:16px; background:rgba(20,14,16,.86); line-height:1.12; }}
.grp b {{ color:{CIAN}; }}
"""
    html, js = "", ""
    for i, (txt, t0, d) in enumerate(gs):
        partes = [f"<b>{w}</b>" if re.search(r"\d|DEMO|WhatsApp", w) else w for w in txt.split()]
        html += f'    <div id="g{i}" class="grp clip" data-start="{t0:.3f}" data-duration="{d:.3f}"><span id="g{i}s">{" ".join(partes)}</span></div>\n'
        js += (f'    tl.fromTo("#g{i}s", {{opacity:0, scale:.9}}, {{opacity:1, scale:1, duration:.12, ease:"back.out(2)"}}, {t0:.3f});\n'
               f'    tl.to("#g{i}s", {{opacity:0, duration:.06}}, {t0 + d - .06:.3f});\n')
    return escena(sid, html, css, js)


# -------------------------------------------------------------------- armar
def ffmpeg(*a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)


def raiz(dia, total, escenas, audios, titulo):
    hosts = "".join(
        f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{t0:.3f}" '
        f'data-duration="{d:.3f}" data-track-index="{i + 2}" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:{i + 2}"></div>\n'
        for i, (sid, t0, d) in enumerate(escenas))
    aud = "".join(f'      <audio id="{aid}" class="clip" src="{src}" data-start="{t0:.3f}" data-track-index="{40 + i}" data-volume="{vol}"></audio>\n'
                  for i, (aid, src, t0, vol) in enumerate(audios))
    g_fin = escenas[0][2]
    puntos = "".join(f'<i class="{"on" if k + 1 == dia else "pas" if k + 1 < dia else ""}"></i>' for k in range(7))
    return f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{titulo}</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family:'{SERIF[0]}'; src:url('assets/fonts/{SERIF[1]}') format('woff2'); font-weight:700; }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:{BG}; }}
      #fondo {{ position:absolute; inset:0; background:{BG}; z-index:0; }}
      #fondo .halo {{ position:absolute; width:1400px; height:1400px; border-radius:50%; left:-200px; top:-420px;
        background:radial-gradient(circle, {P}30, {P}00 65%); }}
      #insignia {{ position:absolute; left:60px; top:110px; z-index:31; display:flex; align-items:center; gap:22px; }}
      #insignia b {{ font-family:'JetBrains Mono',monospace; font-size:34px; font-weight:800; color:{CIAN}; background:{OSCURO};
        padding:10px 22px; border-radius:14px; }}
      #insignia .pts {{ display:flex; gap:10px; }} #insignia .pts i {{ width:16px; height:16px; border-radius:50%; background:#e6dbd5; display:block; }}
      #insignia .pts i.pas {{ background:#9fc9da; }} #insignia .pts i.on {{ background:{CIAN}; }}
      #marca {{ position:absolute; right:60px; top:118px; z-index:31; font-size:28px; font-weight:800; color:{PT}; letter-spacing:.06em; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}">
      <div id="fondo" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="0" data-layout-allow-overflow><div class="halo"></div></div>
{hosts}      <div id="insignia" class="clip" data-start="{g_fin:.3f}" data-duration="{total - g_fin:.3f}" data-track-index="1"><b>DÍA {dia}/7</b><div class="pts">{puntos}</div></div>
      <div id="marca" class="clip" data-start="{g_fin:.3f}" data-duration="{total - g_fin:.3f}" data-track-index="20">EasyPro Digital</div>
      <div id="subs" data-composition-id="subs" data-composition-src="compositions/subs.html" data-start="0" data-duration="{total:.3f}"
        data-track-index="30" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:30"></div>
{aud}    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#fondo .halo", {{x:0, y:0}}, {{x:320, y:900, duration:{total:.3f}, ease:"none"}}, 0);
      tl.fromTo("#insignia, #marca", {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:.4, ease:"expo.out"}}, {g_fin + .1:.3f});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def video(nombre, dia, gancho, salida: Path):
    voz = json.loads((AQUI / f"voz/dia{dia}/narracion.json").read_text(encoding="utf-8"))
    L = {l["id"]: l for l in voz["lineas"]}
    orden = [gancho] + [l["id"] for l in voz["lineas"] if not l["id"].startswith("gancho")]
    d = salida / nombre
    for sub in ("compositions", "assets/vendor", "assets/fonts", "assets/capturas", "assets/sfx"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy(NICHOS / "vendor/gsap.min.js", d / "assets/vendor/gsap.min.js")
    shutil.copy(NICHOS / "fonts" / SERIF[1], d / "assets/fonts" / SERIF[1])
    cap = d / "assets/capturas/lumora.jpg"
    if not cap.exists():
        Image.open(AQUI / "capturas/lumora_movil.png").convert("RGB").save(cap, quality=88)

    base = {lid: L[lid]["duracion"] / VEL + .15 for lid in orden}
    base[orden[0]] += .3                       # aire tras el gancho
    base[orden[-1]] += CIERRE_EXTRA
    falta = max(0.0, MIN_TOTAL - sum(base.values()))
    principal = "hoy" if "hoy" in base else orden[1]
    base[principal] += falta * .7
    base[orden[-1]] += falta * .3

    escenas, gs, t = [], [], 0.0
    for k, lid in enumerate(orden):
        dur = base[lid]
        sid, html = hacer_escena(dia, lid, f"e{k}", dur)
        (d / f"compositions/{sid}.html").write_text(html, encoding="utf-8")
        escenas.append((sid, t, dur))
        if not lid.startswith("gancho"):
            for c in L[lid]["subtitulos"]:
                gs += grupos(c["texto"], t + (c["inicio"] - L[lid]["inicio"]) / VEL + .04, t + (c["fin"] - L[lid]["inicio"]) / VEL)
        t += dur
    total = t
    (d / "compositions/subs.html").write_text(comp_subs(gs), encoding="utf-8")

    filtros, ins = [], []
    for i, (lid, (sid, t0, _)) in enumerate(zip(orden, escenas)):
        ins += ["-i", str(AQUI / f"voz/dia{dia}/{lid}.wav")]
        filtros.append(f"[{i}:a]atempo={VEL},adelay={int(t0 * 1000)}:all=1[a{i}]")
    filtros.append("".join(f"[a{i}]" for i in range(len(orden))) +
                   f"amix=inputs={len(orden)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[o]")
    ffmpeg(*ins, "-filter_complex", ";".join(filtros), "-map", "[o]", "-ac", "1", "-t", f"{total:.3f}", "-c:a", "pcm_s16le", str(d / "assets/voz.wav"))

    def sfx(nom):
        shutil.copy(SFX_DIR / f"{nom}.mp3", d / f"assets/sfx/{nom}.mp3")
        return f"assets/sfx/{nom}.mp3"
    audios = [("voz", "assets/voz.wav", 0, 1), ("fx0", sfx("impact-bass-1"), 0, .3)]
    for i, (sid, t0, _) in enumerate(escenas[1:], 1):
        audios.append((f"fx{i}", sfx("whoosh-short" if i % 2 else "whoosh"), max(t0 - .1, 0), .22))
    for lid, (sid, t0, dur) in zip(orden, escenas):
        if TIPO.get((dia, lid)) in ("recordatorio", "retoque", "objecion", "clinicas"):
            audios.append((f"msg-{sid}", sfx("notification"), t0 + dur * .35, .28))
    audios.append(("fx-fin", sfx("pop"), escenas[-1][1] + .1, .3))

    (d / "index.html").write_text(raiz(dia, total, escenas, audios, nombre), encoding="utf-8")
    return d, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    salida = AQUI / "cortes"
    hechos = [video(nom, dia, g, salida) for nom, dia, g in VIDEOS if not args.solo or args.solo == nom]
    for d, t in hechos:
        print(f"[serie] {d.name}: {t:.1f} s")
    if args.render:
        (AQUI / "renders").mkdir(exist_ok=True)
        npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
        for d, _ in hechos:
            subprocess.run([npx, "-y", "hyperframes@latest", "render", "--output", str(AQUI / "renders" / f"{d.name}.mp4")], cwd=d, check=True)


if __name__ == "__main__":
    main()
