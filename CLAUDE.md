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

## Otras notas
- Todo en español.
- La voz clonada principal es "El documentalista de español latino" (versiones 20s y 60s).
- En Windows, Chatterbox necesita `KMP_DUPLICATE_LIB_OK=TRUE` y el Python que tenga
  `chatterbox-tts` instalado.
