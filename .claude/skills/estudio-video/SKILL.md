---
name: estudio-video
description: Leer primero para cualquier video en este proyecto. Une los 4 proyectos (pipeline video-automatico con voz clonada, HyperFrames, Remotion y las skills de diseño de movimiento de iart-ai) y dice cuál usar en cada paso y cómo pasar audio, subtítulos y clips de uno a otro.
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
  "voz": "Voz clonada — referencia 20s",
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
