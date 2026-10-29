---
name: estudio-video
description: Usar SIEMPRE que el usuario pida hacer, crear, generar o editar un video (intro, reel, short, promo, explicativo, motion graphic, narración). Empieza con un briefing (voz, colores, idea previa, gancho) y luego une los 4 proyectos (pipeline con voz clonada, HyperFrames, Remotion y diseño de movimiento de iart-ai) para producirlo.
---

# Estudio de video unificado

Este repo tiene cuatro piezas que se combinan. Ninguna hace todo; esta skill decide qué pieza hace cada paso y cómo se pasan el trabajo.

| Pieza | Dónde | Lo que hace mejor |
|---|---|---|
| **video-automatico** (pipeline propio) | `pipeline/`, `api/`, `scripts/` | Voz: Piper, espeak y **voz clonada con Chatterbox** (`assets/voices_library.json`). Video de guion + imágenes con Ken Burns, subtítulos y QA. Separar voz de música (`services/voice-separator-api`). |
| **HyperFrames** | skills `hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `media-use`, `remotion-to-hyperframes`, `slideshow` | Motion graphics en HTML + GSAP: títulos, intros, overlays, lower thirds, subtítulos con estilo, gráficos, ajustar/editar video existente, etalonaje, mezcla de audio. **Motor visual por defecto.** |
| **Remotion** | skills `remotion-*` | Video en React: plantillas alimentadas por datos (CSV/JSON → muchos videos), integrar en una app (`<Player>`), proyectos Remotion ya existentes. |
| **iart-ai motion design** | skills `animation-principles`, `shot-composition`, `motion-art-direction`, `color-motion`, `logo-animation`, `beat-sync-editing`, `motion-background`, `remotion-video`, `after-effects`; scripts en `motion-verify-tools/` | Criterio: easing, tiempos, composición, color, ritmo con la música, y verificación con fotogramas. Aplica a todo lo anterior. |

Los proyectos visuales nuevos viven en `estudio/<nombre>/` (HyperFrames o Remotion). Su `node_modules` y renders están en `.gitignore`.

## 0. Briefing (siempre, antes de construir)

Ningún video se empieza sin estas respuestas. Pregunta **en una sola tanda** con la
herramienta de preguntas (AskUserQuestion, máx. 4 preguntas por tanda) y **salta
las que el pedido ya responde**. Si el usuario dice "tú decide" o "sin preguntas",
usa los valores por defecto (★) y dilo en una línea.

**Tanda 1 — lo creativo**

1. **Voz** — ¿Quién narra?
   - ★ El documentalista de español latino (voz clonada, 20s)
   - Voz Kokoro en español (Dora mujer / Alex hombre), gratis y rápida
   - Piper (borrador rápido)
   - Sin voz, solo música y texto
2. **Colores / estilo**
   - ★ Marca EasyPro Digital: fondo oscuro + acento verde, tipografía moderna en negrita
   - Colores del cliente (pedir logo, web o códigos de color)
   - Claro y minimalista
   - Que Claude proponga 2–3 paletas
3. **Idea previa**
   - Tengo guion o texto (que lo pegue)
   - Tengo un video o imagen de referencia (que lo comparta y diga qué copiar: ritmo, look, apertura)
   - ★ Partir de cero: Claude propone 3 enfoques distintos en palabras y el usuario elige
4. **Gancho** (primeros 1–3 segundos)
   - ★ Pregunta que toque un dolor ("¿Tu negocio deja de responder cuando cierras?")
   - Dato o cifra impactante
   - Promesa de resultado ("En 30 días…")
   - Sin gancho, entrada directa
   - (Si elige uno, proponer 2–3 frases de gancho concretas para que escoja.)

**Tanda 2 — lo técnico** (solo si no se sabe; se puede deducir del destino)

5. **Formato**: ★ vertical 1080×1920 (Reels/TikTok/Shorts) · horizontal 1920×1080 (YouTube/web) · cuadrado 1080×1080.
6. **Duración**: ★ 15–30 s · 30–60 s · más de 1 min.
7. **Cierre / llamado a la acción**: ★ logo + easyprodigital.com · WhatsApp · otro.
8. **Música**: ★ suave bajo la voz · enérgica · ninguna · la del usuario.

**Después del briefing:** resume en 4–6 líneas lo elegido (voz, paleta en hex,
gancho exacto, formato, duración, cierre) y empieza. Guarda ese resumen como
`SPEC.md` dentro de `estudio/<nombre>/` para que el video sea reproducible.

## 1. Elegir la ruta

| El pedido | Ruta |
|---|---|
| Guion + fotos → video narrado sencillo | Flujo 1 tal cual: `python scripts/run_pipeline.py guion.json outputs/x.mp4 --tts chatterbox --voice-sample <wav>` (o la interfaz `.\start.ps1`) |
| Intro, logo, título, texto animado, overlay, clip social, explicativo con gráficos | **HyperFrames** + voz del pipeline (receta A) |
| Muchos videos iguales cambiando datos, o video dentro de una app | **Remotion** + voz del pipeline (receta B) |
| Mejorar un video que ya existe (del Flujo 1 o grabado) | **HyperFrames** encima del MP4 (receta C) |
| Un proyecto Remotion que se quiere seguir editando con HyperFrames | skill `remotion-to-hyperframes` (receta D) |
| Video de Flujo 1 con intro/cierre animados | receta E |
| Audio con música de fondo que hay que transcribir o reutilizar | `services/voice-separator-api` primero (receta F) |

Antes de animar, leer `animation-principles` y `shot-composition` (números de easing, duraciones, stagger, regla de 1/3, zonas seguras). Para algo de marca, `motion-art-direction` y `color-motion`. Para cortes al ritmo de la música, `beat-sync-editing`.

## 2. El puente de voz: `scripts/narrar.py`

Es la pieza que une todo: genera la narración con **cualquier voz guardada del proyecto, incluida la clonada**, y la entrega con tiempos exactos para HyperFrames o Remotion.

```json
{
  "voz": "El documentalista de español latino (20s)",
  "pausa_ms": 250,
  "lineas": [
    {"id": "gancho", "texto": "..."},
    {"id": "cierre", "texto": "..."}
  ]
}
```

```powershell
$env:KMP_DUPLICATE_LIB_OK="TRUE"
.\.venv\Scripts\python scripts\narrar.py narracion.json --salida estudio\mi-video\assets\voz
```

Deja en la carpeta destino: `<id>.wav` por línea, `narracion.wav` (todo unido, -16 LUFS, 48 kHz) y `narracion.json` con `inicio`/`duracion` de cada línea, sus subtítulos con tiempos, y `remotion_captions` (formato `Caption` de `@remotion/captions`). Ejemplo: `examples/narracion_ejemplo.json`. Voces disponibles: las que estén en `assets/voices_library.json` (nombre exacto).

**Importante:** Chatterbox descarga su modelo de Hugging Face la primera vez y esa descarga está bloqueada en los entornos que controla Claude. La voz clonada se genera **en la terminal del usuario** (PowerShell en su PC). Si Claude no puede correrla: preparar el JSON, darle el comando exacto y seguir con el resto cuando exista `narracion.json`. Para avanzar mientras tanto, usar `"voz": "Voz piper"` como voz provisional y cambiarla al final (los tiempos se recalculan solos al regenerar).

La voz **manda el reloj**: la duración de cada escena sale de `narracion.json`, nunca de un número inventado.

## 2b. Voces disponibles y cómo gestionarlas

| Voz | Motor | Dónde vive | Cuándo |
|---|---|---|---|
| **El documentalista de español latino (20s / 60s)** | Chatterbox (clonada) | `assets/voices_library.json` + `assets/voice_samples/` | Narración principal en español latino. La de 20s suele sonar más fiel. |
| Voz piper | Piper (`es_ES-davefx-medium`) | `assets/voices/` (se descarga, ver README) | Borradores rápidos, sin GPU. |
| Grave (espeak) | espeak-ng | sistema | Solo pruebas offline. |
| 54 voces Kokoro (`ef_dora`, `em_alex`, `em_santa` en español) | Kokoro vía HyperFrames | `npx hyperframes tts --voice <id>` | Voz gratis y local cuando no se quiere la clonada. |
| HeyGen, ElevenLabs, Gemini | servicios de pago | skill `media-use` / `remotion-markup/voiceover.md` | Solo si el usuario tiene cuenta o API key. |

- **Usar una voz guardada:** por su nombre exacto en `voices_library.json` (en `narrar.py`, en el JSON del guion o en la interfaz). `muestra_voces.py --voces` acepta parte del nombre (ej. `documentalista`).
- **Las rutas de `voice_sample` son relativas a la raíz del proyecto**, así la biblioteca funciona en cualquier PC. Al agregar una voz a mano, usa `assets/voice_samples/<archivo>.wav`.
- **Agregar una voz clonada:** WAV de 10–30 s, una sola persona, sin música (si tiene música, pasar antes por `services/voice-separator-api`). Guardarlo en `assets/voice_samples/` y agregar una entrada `{"name", "backend": "chatterbox", "options": {"voice_sample", "language_id": "es"}}`, o usar la interfaz (`.\start.ps1` → Chatterbox → "Guardar…").
- **Comparar voces:** `python scripts/muestra_voces.py` (voces del proyecto + Kokoro en español), `--kokoro todas` para las 54, `--kokoro no` para solo las del proyecto. Doble clic en `muestra_clonadas.bat` para solo las clonadas.
- **Chatterbox en Windows:** usa el Python que tenga `chatterbox-tts` instalado (en este equipo, `%USERPROFILE%\anaconda3\python.exe`) y `KMP_DUPLICATE_LIB_OK=TRUE`. La primera vez descarga ~2 GB de Hugging Face, así que debe correr en la PC del usuario, no en un entorno de Claude. Si Claude controla la PC, lanzar un `.bat` desde el Explorador funciona.

## 2c. Lo que solo funciona en la PC del usuario (local)

Antes de ejecutar algo, ubícate: **¿estás corriendo en la PC del usuario** (Claude Code
local, la ruta del proyecto es `C:\...\video-automatico`) **o en la nube**?

| Función | ¿Nube? | Por qué |
|---|---|---|
| Voz clonada (Chatterbox) | No | Descarga ~2 GB de Hugging Face (bloqueado en la nube) y los audios de referencia están en la PC |
| Voz Piper (primera descarga del modelo) | No | Hugging Face |
| Interfaz web (`localhost:8000`), cola de renders | No | Es un servidor en la PC del usuario |
| Vista previa de HyperFrames / Remotion Studio para que el usuario edite | No | Se abre en el navegador de la PC |
| Renders largos (más de unos minutos) | No | La sesión en la nube se detiene al terminar la respuesta |
| Aceleración por gráfica (Intel QSV) | No | Depende del hardware de la PC |
| Separador de voz (`services/voice-separator-api`) | No recomendado | Usa su propio entorno con TensorFlow |
| Kokoro, espeak, renders cortos, revisar fotogramas | Sí | — |

**Cómo ejecutarlo según dónde estés:**

1. **En la PC del usuario (Claude Code local):** córrelo directo en la terminal. Antes: `set KMP_DUPLICATE_LIB_OK=TRUE` y usa el Python que tiene Chatterbox (`local\_entorno.cmd` lo detecta; en el equipo de Jesús es `%USERPROFILE%\anaconda3\python.exe`).
2. **En la nube con la PC enlazada** (herramientas `device_*` y `computer_*`):
   - Escribe el comando exacto en `local/tarea.cmd` (líneas `.cmd` de Windows; usa `%PY%` para Python; rutas relativas a la raíz del proyecto).
   - Abre `local\correr_tarea.bat` con doble clic desde el Explorador de archivos (computer use, nivel "click").
   - Espera revisando `local/tarea.fin` (aparece al terminar, con el código de salida) y lee `local/tarea.log`. Libera el control de la pantalla mientras esperas.
   - Para un render largo, avisa al usuario cuánto puede tardar.
3. **Sin acceso a la PC:** prepara todo (guion, JSON, proyecto) y dale al usuario el `.bat` o comando exacto en una línea; continúa cuando confirme.

**Lanzadores listos** en `local/` (doble clic): `interfaz.bat` (interfaz web), `muestra_voces.bat`, `revisar_equipo.bat` (qué está instalado y aceleración por gráfica), `correr_tarea.bat` (tareas que deja Claude). En la raíz: `muestra_clonadas.bat`.

**Equipo de Jesús (29/10/2026):** Python 3.13 de Anaconda con Chatterbox, FastAPI y Piper; FFmpeg; Node v26 (HyperFrames y Remotion funcionan); **sin GPU NVIDIA**: la voz clonada va por procesador (~1,5 min por frase corta).

## 3. Recetas

### A. Voz clonada + motion graphics en HyperFrames
1. `npx hyperframes init estudio/<nombre> --non-interactive --example blank`
2. Narración con `scripts/narrar.py --salida estudio/<nombre>/assets/voz`.
3. En `index.html`: `<audio id="voz" src="assets/voz/narracion.wav" class="clip" data-start="0" data-duration="<duracion_total>">`. Cada escena empieza en el `inicio` de su línea y dura su `duracion`; el texto en pantalla aparece en el momento de su subtítulo.
4. Duración de la raíz = `duracion_total` + el cierre.
5. Música y efectos: `media-use` (`npx hyperframes media-use resolve --type bgm|sfx ...`). Música bajo la voz ≈ 0.14 de volumen o con `data-automation` bajando al entrar la voz. Música propia: `assets/music/` del pipeline.
6. Subtítulos con estilo: los de `narracion.json`, o palabra por palabra con `npx hyperframes transcribe assets/voz/narracion.wav`. Estilos en el registro (`hyperframes-registry`).
7. `npx hyperframes check --json` → `snapshot --review` → render.

### B. Voz clonada + Remotion (plantillas con datos)
1. `npx create-video@latest estudio/<nombre>` (ver `remotion-create`).
2. Narración con `--salida estudio/<nombre>/public/voz`.
3. `<Audio src={staticFile("voz/narracion.wav")} />`; duración de la composición = `Math.ceil(duracion_total * fps)` (usar `calculateMetadata` leyendo `narracion.json`).
4. Cada escena en `<Sequence from={inicio*fps} durationInFrames={duracion*fps}>`.
5. Subtítulos: `remotion_captions` → `createTikTokStyleCaptions()` de `@remotion/captions` (ver `remotion-captions`).
6. Para muchos videos: un JSON de datos por video, un `narracion.json` por video, render por lote (`remotion-render`).

### C. Ajustar un video que ya existe con HyperFrames
1. Copiar el MP4 (p. ej. `outputs/<id>.mp4`) a `estudio/<nombre>/assets/`.
2. `<video src="assets/base.mp4" class="clip" data-start="0" data-duration="<dur>" data-has-audio="true">`.
3. Encima: lower thirds, títulos, llamados, logo, barra de progreso, subtítulos nuevos (`references/overlays.md`, `captions.md`).
4. Footage oscuro o plano: `npx hyperframes media-treatment` (nunca filtros CSS).
5. Para recortar silencios o muletillas: `npx hyperframes transcribe` + el recorte por transcripción de `media-use` (`scripts/transcript-cut.mjs`).

### D. Remotion → HyperFrames
Usar la skill `remotion-to-hyperframes` para pasar la composición a HTML y seguir editando en el Studio de HyperFrames. Los assets de `public/` pasan a `assets/`.

### E. Flujo 1 con intro y cierre animados
1. Hacer `intro.mp4` y `cierre.mp4` en HyperFrames con la **misma resolución y fps** que el video del Flujo 1 (ver `config/settings.py`).
2. Unir: `ffmpeg -i intro.mp4 -i flujo1.mp4 -i cierre.mp4 -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset veryfast -c:a aac final.mp4`. Si la intro no tiene audio, agregarle silencio (`anullsrc`) antes.
3. Pasar `final.mp4` por el QA del pipeline (`pipeline/qa_check.py`).

### F. Separar voz y música
`services/voice-separator-api` (su propio venv, ver su README). La voz limpia sirve como muestra para clonar (10–30 s, sin ruido) o para transcribir; la música se reutiliza como fondo en HyperFrames/Remotion.

## 4. Verificación (siempre, en cualquier ruta)
- HyperFrames: `npx hyperframes check --json` y `snapshot --review`.
- Cualquier MP4: fotogramas inicio/medio/final con `ffmpeg -ss <t> -i out.mp4 -frames:v 1 f<t>.png`, hoja de contacto con `motion-verify-tools/contact-sheet.sh`, revisar la imagen.
- Especificación: `motion-verify-tools/probe-mp4.sh out.mp4 1920x1080 30`.
- Audio: la voz se entiende sobre la música, nada satura, el texto aparece cuando la voz lo dice.
- Videos del pipeline: el `*.qa.json` que genera solo.

## 5. Reglas de la casa
- Todo en español; textos del cliente literales.
- No sobrescribir cambios que el usuario haya hecho a mano en un proyecto.
- Renderizar el entregable cuando el usuario aprueba la vista previa o lo pide.
- En Windows: comandos en PowerShell, `KMP_DUPLICATE_LIB_OK=TRUE` antes de usar Chatterbox, y `VIDEO_ENCODER=h264_qsv` si `scripts/check_hw.py` dice que funciona.
