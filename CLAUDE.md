# Proyecto video-automatico

## Regla principal: pedidos de video

Cuando el usuario pida un video (hazme / crea / genera / edita un video, intro,
reel, short, promo, explicativo, animación, motion graphic, narración…):

1. **Carga primero la skill `estudio-video`** (`.claude/skills/estudio-video/SKILL.md`).
   Ella decide qué herramienta usar (pipeline propio, HyperFrames, Remotion o las
   skills de diseño de movimiento).
2. **Antes de construir nada, haz el briefing** de la sección "0. Briefing" de esa
   skill: voz, colores, idea previa y gancho (más formato y duración si no los dijo).
   Usa la herramienta de preguntas (AskUserQuestion) en una sola tanda.
   No preguntes lo que el pedido ya responde.
3. Solo después de tener las respuestas, arma el plan y empieza.

Excepción: si el usuario dice "hazlo sin preguntar", "tú decide" o similar, usa
los valores por defecto del briefing y dilo en una línea al inicio.

## Funciones que solo corren en la PC

Voz clonada, interfaz web, vistas previas para editar, renders largos y
aceleración por gráfica **solo funcionan en la PC del usuario**. Antes de
ejecutarlas, mira si estás en la PC o en la nube y sigue la sección
"2c. Lo que solo funciona en la PC del usuario" de la skill `estudio-video`
(en la nube con la PC enlazada: escribir `local/tarea.cmd` y lanzar
`local\correr_tarea.bat`). Lanzadores listos en `local/`.

## Guardar los recursos de cada video (siempre)

Todo lo que se use para un video se guarda en `recursos/` para reutilizarlo:
capturas de demos y webs, voces (una frase por archivo + `narracion.json`), guiones,
fuentes, efectos de sonido y la plantilla (`build.py`) con la que se armó.

1. **Antes de empezar**, mira `recursos/INDICE.md`: si ya hay capturas o voces que
   sirven, úsalas en vez de volver a generarlas.
2. **Al terminar**, corre `python scripts/guardar_recursos.py` (actualiza `recursos/`
   y el índice) en la nube y en la PC, y súbelo a GitHub junto con el video.

## Otras notas
- Todo en español.
- La voz clonada principal es "El documentalista de español latino" (versiones 20s y 60s).
- En Windows, Chatterbox necesita `KMP_DUPLICATE_LIB_OK=TRUE` y el Python que tenga
  `chatterbox-tts` instalado.
