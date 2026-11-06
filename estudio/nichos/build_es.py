#!/usr/bin/env python3
"""
Versión en español (LatAm) de los 21 mini videos por nicho, con la voz "El documentalista".
Reutiliza la plantilla de build.py y cambia textos, capturas (demos en español), voz y salida.

    python estudio/nichos/build_es.py                    # 21 proyectos en cortes_es/
    python estudio/nichos/build_es.py --solo medspa_a
    python estudio/nichos/build_es.py --render           # a renders_es/
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("nichos_build", AQUI / "build.py")
nb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nb)

VEL = 1.15  # voz un poco más rápida: retiene mejor en reels
HOLD_S3, CIERRE = .8, 1.6

ES = {
    "medspa": dict(kw="diseño web para clínicas estéticas",
        ganchos={"a": "Tus clientas investigan durante semanas. Y reservan con quien les *responde primero*.",
                 "b": "Así debería verse el *diseño web para clínicas estéticas* en 2026.",
                 "c": "Las clientas de bótox vuelven cada pocos meses. ¿Tu web *se lo recuerda*?"},
        s2=["Una página por tratamiento", "Valoración gratis"], s3=["Historial de clientas", "Recordatorio de retoque"],
        cta=["Comenta DEMO 👇"]),
    "masons": dict(kw="página web con hosting para constructores",
        ganchos={"a": "Constructores: tu página web está *caída* y ni siquiera lo sabes.",
                 "b": "Lo que debe incluir la *página web y el hosting de un constructor*, en 40 segundos.",
                 "c": "Deja de mandar cotizaciones por mensaje. Que la web haga *la primera*."},
        s2=["Hosting", "Copias de seguridad", "Actualizaciones incluidas"], s3=["Cotización con fotos", "Precio por m²", "Tu lista de obras"],
        cta=["Comenta DEMO 👇"]),
    "autoshop": dict(kw="diseño web económico para talleres",
        ganchos={"a": "Tu taller está lleno y el teléfono *sigue sonando todo el día*.",
                 "b": "*Diseño web económico para talleres:* lo que incluye por US$450.",
                 "c": "La gente no confía en un mecánico que *no puede ver en internet*."},
        s2=["Precios", "Reservas", "Reseñas"], s3=["Órdenes de trabajo", "Revisión con fotos", "Recordatorios", "Inventario"],
        cta=["Comenta DEMO 👇", "Páginas desde US$450"]),
    "storage": dict(kw="diseño web económico para minibodegas",
        ganchos={"a": "Cada bodega vacía *te cuesta plata* todos los días.",
                 "b": "*Diseño web económico para minibodegas,* pero hecho para alquilar en línea.",
                 "c": "Tus clientes no saben qué tamaño necesitan. *Tu web debería decírselo.*"},
        s2=["Calculadora de tamaño", "Reserva en línea"], s3=["Disponibilidad en vivo", "Cobro automático", "Ocupación"],
        cta=["Comenta DEMO 👇", "Instalación baja · plan mensual"]),
    "plumbers": dict(kw="diseño web para plomeros",
        ganchos={"a": "2 a. m., se revienta un tubo. Tu cliente llama a quien *le aparezca primero*.",
                 "b": "*Diseño web para plomeros:* lo que hace que te llamen a ti.",
                 "c": "El plomero que responde en 5 minutos *se queda con el trabajo*."},
        s2=["Destapes", "Calentadores", "Fugas"], s3=["Respuesta en 5 min", "Trabajo → celular del técnico"],
        cta=["Comenta DEMO 👇"]),
    "dentists": dict(kw="páginas web para clínicas dentales",
        ganchos={"a": "Un solo caso de implantes puede *pagar toda tu página web*.",
                 "b": "*Páginas web para clínicas dentales:* lo que el paciente revisa antes de llamar.",
                 "c": "Cada cita perdida es plata que no vuelve. *A menos que tu sistema la recupere.*"},
        s2=["Implantes", "Prótesis", "Coronas", "Financiación"], s3=["Sistema del consultorio", "Recordatorios", "Controles"],
        cta=["Comenta DEMO 👇"]),
    "carwash": dict(kw="página web para lavaderos de carros",
        ganchos={"a": "Los lavaderos que más ganan no venden lavadas. *Venden membresías.*",
                 "b": "*Página web para lavaderos de carros:* lo que de verdad deja plata.",
                 "c": "¿Semana de lluvia? *Los miembros igual pagan.*"},
        s2=["Precios", "Antes / después", "Inscripción mensual"], s3=["Cobro automático", "Entrada con QR", "Beneficios"],
        cta=["Comenta DEMO 👇"]),
}

# textos de las maquetas "Cómo funciona"
MAQUETA = [
    ("HOW IT WORKS", "CÓMO FUNCIONA"),
    ("Patient · Sarah M.", "Clienta · Sara M."), ("Botox · 20 units", "Bótox · 20 unidades"), ("Mar 3", "3 mar"),
    ("Lip filler", "Relleno de labios"), ("Jan 12", "12 ene"), ("HydraFacial", "Limpieza facial"), ("Dec 1", "1 dic"),
    ("“Hi Sarah! It’s been 3 months since your Botox. Book your touch-up?”", "“¡Hola Sara! Ya van 3 meses desde tu bótox. ¿Agendamos el retoque?”"),
    ("Scheduled · Jun 3, 10:00", "Programado · 3 jun, 10:00"),
    ("Estimates pipeline", "Cotizaciones"), (">New<", ">Nuevas<"), (">Quoted<", ">Cotizadas<"), (">Won<", ">Ganadas<"),
    ("Patio · 240 sq ft", "Patio · 22 m²"), ("Chimney repair", "Arreglo de chimenea"), ("Retaining wall", "Muro de contención"),
    ("Brick steps", "Escalera en ladrillo"), ("New request: 3 photos · 240 sq ft → estimate sent", "Nueva solicitud: 3 fotos · 22 m² → cotización enviada"),
    ("Work order #1042 · 2019 Civic", "Orden de trabajo #1042 · Civic 2019"), ("Brake pads (front)", "Pastillas de freno (del.)"),
    ("Needs replacing", "Cambiar"), ("Oil change", "Cambio de aceite"), ("Due now", "Toca ya"), (">Tires<", ">Llantas<"),
    ("Send to customer", "Enviar al cliente"),
    ("Occupancy · 16 of 20 rented", "Ocupación · 16 de 20 alquiladas"), ("Rented", "Alquilada"), ("Available", "Libre"),
    ("Monthly billing ran · 1 late-fee alert", "Cobro mensual hecho · 1 alerta de atraso"),
    ("Missed call · 2:07 a.m.", "Llamada perdida · 2:07 a. m."),
    ("“Sorry we missed you! Drain cleaning from $99. Reply YES and a tech is on the way.”",
     "“¡Perdón, no alcanzamos a contestar! Destape desde US$99. Responde SÍ y un técnico va en camino.”"),
    ("Sent in 2 min", "Enviado en 2 min"), ("Tech app · New job", "App del técnico · Trabajo nuevo"),
    ("Drain cleaning · 412 Elm St", "Destape · Calle 45 #12-30"), ("Route: 14 min", "Ruta: 14 min"),
    ("Today’s schedule", "Agenda de hoy"), ("9:00 · Implant consult", "9:00 · Valoración implante"), ("✓ Confirmed", "✓ Confirmada"),
    ("10:30 · Denture fitting", "10:30 · Prueba de prótesis"), ("1:00 · Crown", "1:00 · Corona"), ("⏳ Reminder sent", "⏳ Recordatorio enviado"),
    ("6-month recall: “Time for your check-up. Pick a time →”", "Control de 6 meses: “Te toca la revisión. Elige tu hora →”"),
    ("Member pass · Unlimited", "Membresía · Ilimitada"), ("$39/mo", "US$39/mes"), ("Auto billing · next charge Jul 1", "Cobro automático · próximo 1 jul"),
    ("Perk: free tire shine", "Beneficio: brillo de llantas gratis"), ("Plate checked at entrance · Welcome back!", "Placa leída en la entrada · ¡Bienvenido!"),
]
_maqueta_en = nb.maqueta


def maqueta_es(tipo, n, sid):
    html, css = _maqueta_en(tipo, n, sid)
    for a, b in MAQUETA:
        html = html.replace(a, b)
    return html, css


nb.maqueta = maqueta_es
nb.CIFRAS = [("cuatrocientos cincuenta dólares", "US$450"), ("Dos de la mañana", "2 a. m."), ("cinco minutos", "5 minutos"),
             ("seis meses", "6 meses"), ("cuarenta segundos", "40 segundos"), ("en 2026", "en 2026")]
N_ES = {k: {**copy.deepcopy(v), **ES[k]} for k, v in nb.N.items()}


def video(clave, gch, salida: Path):
    n = N_ES[clave]
    voz = json.loads((AQUI / f"voz_es/{clave}/narracion.json").read_text(encoding="utf-8"))
    L = {l["id"]: l for l in voz["lineas"]}
    d = salida / f"{clave}_{gch}"
    for sub in ("compositions", "assets/vendor", "assets/fonts", "assets/capturas", "assets/sfx"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy(AQUI / "vendor/gsap.min.js", d / "assets/vendor/gsap.min.js")
    shutil.copy(AQUI / "fonts" / n["font"][1], d / "assets/fonts" / n["font"][1])
    for s in {n["slug"]} | {s for s, _ in n["variantes"]}:
        nb.copiar_captura(AQUI / f"capturas_es/{s}_movil.png", d / f"assets/capturas/{s}.jpg")
    if n.get("escritorio"):
        nb.copiar_captura(AQUI / f"capturas_es/{n['slug']}_escritorio.png", d / f"assets/capturas/{n['slug']}_escritorio.jpg")

    orden = [f"gancho_{gch}", "s1", "s2", "s3", "s4"]
    # si pasa de 45 s, se acelera un poco más ese video (hasta 22 %)
    pads = HOLD_S3 + CIERRE
    voz_tot = sum(L[lid]["duracion"] for lid in orden)
    v0 = 1.0 if "Kokoro" in voz.get("voz", "") else VEL  # Kokoro ya habla a buen ritmo
    vel = v0 if voz_tot / v0 + pads <= 45 else min(1.22, voz_tot / (45 - pads))
    base = {lid: L[lid]["duracion"] / vel + (HOLD_S3 if lid == "s3" else 0) + (CIERRE if lid == "s4" else 0) for lid in orden}
    falta = max(0.0, 35.5 - sum(base.values()))
    base["s3"] += falta * .6
    base["s4"] += falta * .4
    escenas, gs, t = [], [], 0.0
    for lid in orden:
        dur = base[lid]
        if lid.startswith("gancho"):
            sid, html = nb.escena_gancho(clave, n, gch, dur)
        else:
            sid, html = {"s1": nb.escena_s1, "s2": nb.escena_s2, "s3": nb.escena_s3, "s4": nb.escena_s4}[lid](n, dur)
        (d / f"compositions/{sid}.html").write_text(html, encoding="utf-8")
        escenas.append((sid, t, dur))
        if lid != "s4" and not lid.startswith("gancho"):
            for c in L[lid]["subtitulos"]:
                gs += nb.grupos(c["texto"], t + (c["inicio"] - L[lid]["inicio"]) / vel + .04, t + (c["fin"] - L[lid]["inicio"]) / vel)
        t += dur
    total = t
    (d / "compositions/subs.html").write_text(nb.comp_subs(gs, n, n["kw"]), encoding="utf-8")

    filtros, ins = [], []
    for i, (lid, (sid, t0, _)) in enumerate(zip(orden, escenas)):
        ins += ["-i", str(AQUI / f"voz_es/{clave}/{lid}.wav")]
        filtros.append(f"[{i}:a]atempo={vel:.3f},adelay={int(t0 * 1000)}:all=1[a{i}]")
    filtros.append("".join(f"[a{i}]" for i in range(len(orden))) +
                   f"amix=inputs={len(orden)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[o]")
    nb.ffmpeg(*ins, "-filter_complex", ";".join(filtros), "-map", "[o]", "-ac", "1", "-t", f"{total:.3f}", "-c:a", "pcm_s16le", str(d / "assets/voz.wav"))

    def sfx(nom):
        shutil.copy(nb.SFX_DIR / f"{nom}.mp3", d / f"assets/sfx/{nom}.mp3")
        return f"assets/sfx/{nom}.mp3"
    audios = [("voz", "assets/voz.wav", 0, 1)]
    for i, (sid, t0, _) in enumerate(escenas[1:], 1):
        audios.append((f"fx{i}", sfx("whoosh-short" if i % 2 else "whoosh"), max(t0 - .1, 0), .25))
    audios.append(("fx-msg", sfx("notification"), escenas[3][1] + min(escenas[3][2] * .45, 4), .3))
    audios.append(("fx-cta", sfx("pop"), escenas[4][1] + .05, .35))
    html = nb.raiz(n, total, escenas, audios, d.name).replace('<html lang="en">', '<html lang="es">')
    (d / "index.html").write_text(html, encoding="utf-8")
    return d, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--nicho")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    hechos = [video(c, g, AQUI / "cortes_es") for c in N_ES for g in "abc"
              if (not args.solo or args.solo == f"{c}_{g}") and (not args.nicho or args.nicho == c)]
    for d, t in hechos:
        print(f"[nichos-es] {d.name}: {t:.1f} s")
    if args.render:
        (AQUI / "renders_es").mkdir(exist_ok=True)
        npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
        for d, _ in hechos:
            subprocess.run([npx, "-y", "hyperframes@latest", "render", "--output", str(AQUI / "renders_es" / f"{d.name}.mp4")], cwd=d, check=True)


if __name__ == "__main__":
    main()
