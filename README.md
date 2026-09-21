# Video Editing API Network — Flujo 1 (Guion → Video)

Primer flujo de la red de APIs de edición automática de video: convierte un
**guion de texto** (dividido en escenas, cada una con su imagen) en un video
terminado, con voz generada por TTS, efecto Ken Burns, transiciones,
subtítulos quemados y audio normalizado — sin necesidad de grabar audio real.

Este es el Flujo 1 de los tres discutidos: el más determinista, porque el
tiempo de cada corte se calcula a partir de la duración exacta del audio TTS
generado (no depende de detectar nada en un audio ya grabado, como sí harían
los Flujos 2 y 3).

## Cómo está armado

```
Guion (JSON) ──▶ TTS por escena (Piper) ──▶ medir duración exacta
                                                     │
Imágenes + descripciones ──▶ validar/ajustar resolución
                                                     │
                                                     ▼
                                    EDL (lista de cortes con tiempos)
                                                     │
                                                     ▼
                         Render: Ken Burns + crossfade + subtítulos (ffmpeg)
                                                     │
                                                     ▼
                              Normalización de audio (loudnorm EBU R128)
                                                     │
                                                     ▼
                                  QA automático (ffprobe) ──▶ video final .mp4
```

## Estructura del proyecto

```
video-editing-api-network/
├── pipeline/
│   ├── models.py           # Modelos de datos (Escena, Guion, Clip del EDL)
│   ├── script_parser.py    # Carga y valida el guion JSON
│   ├── tts_engine.py       # Síntesis de voz por escena (Piper)
│   ├── audio_processor.py  # Normalización, pausas naturales, mezcla con música
│   ├── image_processor.py  # Valida/ajusta resolución de las imágenes
│   ├── edl.py               # Construye la lista de cortes (Edit Decision List)
│   ├── subtitles.py         # Genera subtítulos .ass a partir del guion
│   ├── video_renderer.py   # Ken Burns + crossfade + subtítulos + export final
│   ├── qa_check.py          # Verificación automática del video final
│   ├── hw.py                 # Detecta qué gráfica hay y qué puede acelerar
│   └── run.py                # Orquesta todo el pipeline de punta a punta
├── api/
│   ├── main.py               # API FastAPI + interfaz gráfica (sirve la web en /)
│   └── static/
│       └── index.html        # Interfaz gráfica: armar el guion escena por escena
├── scripts/
│   ├── run_pipeline.py       # CLI: genera un video a partir de un guion
│   ├── check_hw.py           # Prueba qué aceleración por gráfica funciona aquí
│   └── make_sample_assets.py # Genera imágenes de prueba (para probar sin fotos reales)
├── examples/
│   └── sample_script.json    # Guion de ejemplo con 4 escenas
├── config/
│   └── settings.py           # Configuración central (resoluciones, calidad, rutas)
├── assets/
│   ├── images/                # Imágenes de entrada (o generadas de prueba)
│   ├── fonts/                 # Tipografía para subtítulos
│   └── music/                 # Música de fondo opcional
├── services/
│   └── voice-separator-api/   # API aparte: aísla voz de música instrumental (ver su propio README)
└── outputs/                   # Videos renderizados
```

## Otros nodos de la red de APIs

Además del pipeline de Flujo 1 (arriba), el proyecto incluye servicios
independientes que se pueden usar solos o encadenados:

- **`services/voice-separator-api/`** — recibe un audio con voz y música
  mezcladas, devuelve ambas por separado (backend real: Spleeter). Vive en
  su propia carpeta con su propio venv porque sus dependencias (TensorFlow)
  chocan con las de este proyecto principal — ver el README de esa carpeta
  para instalación y uso. Útil antes de transcribir audio real con música de
  fondo (Flujo 2), o para reciclar solo la música de un video existente.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Descargar una voz de Piper en español (una sola vez)
python -m piper.download_voices es_ES-davefx-medium
```

## Uso — interfaz gráfica (lo más fácil)

En Windows basta con:

```powershell
.\start.ps1
```

Ese script pone la variable que evita el choque de OpenMP con Anaconda (el
error `OMP: Error #15` al usar clonación de voz), levanta el servidor y abre el
navegador. Para desarrollar con recarga automática: `.\start.ps1 -Dev` (ojo:
recargar mata el render que esté en curso). El equivalente a mano, en cualquier
sistema:

```bash
uvicorn api.main:app --port 8000
```

Abre **http://localhost:8000** en el navegador. Ahí armas el video sin tocar
JSON ni terminal:

- Una tarjeta por escena: arrastras (o eliges) la imagen, escribes el texto
  que se va a narrar, la descripción de la imagen, y la pausa que quieras
  después de esa escena. Puedes reordenar las escenas con las flechas ↑↓ o
  eliminarlas.
- En el panel de la izquierda eliges la voz: Piper (voces prefabricadas, con
  sus perillas de velocidad y expresividad), espeak (respaldo sin descargas),
  o Chatterbox (subes un audio de referencia y clona esa voz). También puedes
  subir música de fondo opcional.
- **Voces guardadas:** "Guardar…" le pone un nombre a la configuración de voz
  actual y la deja en `assets/voices_library.json` — incluida la ruta del
  audio de referencia si es una voz clonada. Queda ahí aunque cierres el
  navegador o reinicies el servidor, así que la próxima vez solo la eliges y
  le das "Usar", sin volver a subir nada ni recordar los números.
- "Generar video" muestra el avance en vivo (qué escena va, si está
  renderizando o normalizando audio) y al terminar reproduce el video ahí
  mismo, con el resultado del QA y un botón para descargarlo.
- **Videos generados:** al final de la página está la lista de todo lo que hay
  en `outputs/`, con su duración, resolución, voz usada, peso y fecha, y
  botones para verlo ahí mismo, descargarlo o eliminarlo. Se lee del disco, no
  de la memoria, así que también aparecen los videos de sesiones anteriores.
- **No se pierde el trabajo:** todo lo que armas (escenas, textos,
  descripciones, pausas, imágenes ya subidas y los ajustes de voz) se guarda
  solo en el navegador mientras trabajas. Si recargas la página, la cierras
  por accidente o reinicias el servidor, al volver aparece tal cual estaba.
  El botón "Empezar de cero" borra ese borrador cuando quieras arrancar
  limpio (las imágenes subidas se quedan en el disco).
- "Exportar JSON" guarda el guion armado para reusarlo luego (o correrlo por
  CLI); "Importar JSON" carga uno ya hecho.

**Qué necesita reinicio y qué no:** los cambios en la interfaz
(`api/static/index.html`) se sirven leyendo el archivo del disco en cada visita
y sin caché, así que basta con recargar la página. Los cambios en código Python
sí necesitan reiniciar el servidor — o arrancarlo con `.\start.ps1 -Dev`, que
recarga solo. En modo normal no recarga a propósito: un reinicio corta el
render que esté corriendo (ver "Cola de trabajos" más abajo).

## Uso — CLI

1. Escribe tu guion en un JSON como `examples/sample_script.json` (cada escena:
   texto, ruta de imagen, descripción, y opcionalmente pausa después).
2. Corre el pipeline:

```bash
python scripts/run_pipeline.py examples/sample_script.json outputs/mi_video.mp4
```

3. El video final queda en `outputs/`, junto con un reporte de QA (`*.qa.json`).

## Uso — API (desde otro servicio: n8n, otro backend, etc.)

Con el servidor levantado:

| Endpoint | Qué hace |
|---|---|
| `POST /api/upload?kind=images` | sube una imagen (o `audio` / `music`) y devuelve su ruta |
| `POST /api/jobs` | arranca una generación, devuelve `job_id` (no bloquea) |
| `GET /api/jobs/{id}` | estado, avance y reporte de QA |
| `GET /api/jobs/{id}/video` | el mp4 para reproducir |
| `GET /download/{id}` | el mp4 como descarga |
| `GET /api/voices` · `POST /api/voices` · `DELETE /api/voices/{nombre}` | biblioteca de voces guardadas |
| `GET /api/outputs` | lista de videos ya generados (lee `outputs/` del disco) |
| `GET /api/outputs/{archivo}/video` · `/download` · `DELETE` | ver, descargar o eliminar uno |
| `POST /generate` | generación síncrona con un guion JSON completo |

## Cambiar o "crear" voces

Hay tres formas de tener una voz distinta, de más simple a más elaborada:

**1) Descargar otro modelo de voz de Piper (la forma real de tener otra voz).**
Cada modelo `.onnx` es un hablante entrenado por separado — no son variaciones
del mismo, son personas distintas. Para español hay varias: `es_ES-davefx-medium`
(la que trae por defecto este proyecto), `es_ES-sharvard-medium`, `es_ES-mls_10246-low`,
`es_MX-ald-medium`, entre otras (la lista completa está en
[rhasspy/piper/voices.json](https://github.com/rhasspy/piper)). Se descargan igual
que la primera:

```bash
python -m piper.download_voices es_ES-sharvard-medium --download-dir assets/voices
python scripts/run_pipeline.py examples/sample_script.json outputs/video.mp4 --voice es_ES-sharvard-medium
```

**2) Tocar los parámetros de síntesis (varía cómo suena el MISMO modelo, no lo cambia por otro).**
Piper expone estas perillas por cada síntesis:

| Parámetro | Qué hace | Rango típico |
|---|---|---|
| `--length-scale` | velocidad: menor = más rápido, mayor = más lento | 0.8 - 1.3 |
| `--noise-scale` | expresividad: más alto = menos plano/monótono | 0.5 - 1.0 |
| `--noise-w-scale` | variación de ritmo entre sílabas: más alto = menos robótico | 0.5 - 1.0 |
| `--speaker-id` | cambia de hablante, **solo si** el modelo es multi-hablante | depende del modelo |

Ejemplo, una narración más lenta y expresiva:

```bash
python scripts/run_pipeline.py examples/sample_script.json outputs/video.mp4 \
  --voice es_ES-davefx-medium --length-scale 1.15 --noise-scale 0.85 --noise-w-scale 0.85
```

Estos valores también se pueden dejar fijos por defecto en `config/settings.py`
(`piper_length_scale`, `piper_noise_scale`, `piper_noise_w_scale`, `piper_speaker_id`)
para no tener que pasarlos cada vez.

Con el backend `espeak` (el de respaldo/pruebas) las perillas equivalentes son
`--espeak-pitch` (0-99, tono) y la velocidad ya existente por config.

**3) Clonar tu propia voz (`--tts chatterbox`) — ya está integrado.** Si ninguna
voz prefabricada te convence, esta es la opción real: clonar una voz a partir
de un audio de referencia — la tuya, la de otra persona (con su permiso), o un
locutor que contrates. No hay que entrenar nada, solo darle una muestra corta.

Instalación (aparte, porque pesa varios GB):

```bash
pip install -r requirements-chatterbox.txt
```

Uso — necesitas un WAV de **10 a 30 segundos**, limpio (sin música ni ruido de
fondo, una sola persona hablando):

```bash
python scripts/run_pipeline.py examples/sample_script.json outputs/video.mp4 \
  --tts chatterbox --voice-sample mi_voz.wav
```

Perillas opcionales: `--exaggeration` (0-1, expresividad/dramatismo, default
0.5) y `--cfg-weight` (0-1, qué tanto se apega al estilo del audio de
referencia, default 0.5).

**Importante — esto no se pudo probar de punta a punta desde este entorno de
desarrollo:** la primera vez que se usa, Chatterbox descarga su modelo (~2 GB)
desde Hugging Face automáticamente, y ese acceso está bloqueado por política
de red tanto en este sandbox como en el equipo del usuario cuando se opera a
través de Claude — no es un límite del proyecto, es de la red de estos
entornos. El código quedó escrito y verificado contra el código fuente real de
`chatterbox-tts` (confirmé los nombres exactos de clases y parámetros), pero la
descarga del modelo y la primera síntesis real hay que probarlas en tu propia
terminal o en tu servidor, donde el internet es normal. Además, sin GPU la
generación es notablemente más lenta que Piper — para uso ocasional está bien,
para producción en volumen te conviene correrlo en un servidor con GPU.

## Consumo de CPU y aceleración por hardware

Al renderizar, ffmpeg se come casi todo el procesador. Midiendo dónde se va el
tiempo (32 segundos de video, 4 escenas):

| Paso | Tiempo |
|---|---|
| Filtros: decodificar + crossfades + subtítulos | 6,4 s |
| **Codificar el video (preset slow)** | **43,8 s** |
| Codificar el video (preset veryfast) | 18,4 s |

O sea que **casi el 90% del trabajo es codificar**, no los efectos. De ahí
salen las tres palancas, en orden de impacto:

**1) Codificar en la gráfica en vez del procesador.** Las gráficas integradas
Intel traen un bloque dedicado a esto (Quick Sync) que no compite con los
núcleos del procesador; las Iris Plus lo tienen. Para saber si funciona en tu
máquina y cuánto gana, hay un script que lo prueba de verdad codificando un
video:

```bash
python scripts/check_hw.py
```

Te dice qué encoders funcionan, cuánto tardan comparados con el procesador, y
qué poner en el archivo `.env` (copia `.env.example`). Normalmente:

```
VIDEO_ENCODER=h264_qsv
```

Ojo con la expectativa: Quick Sync se lleva solo la codificación. El Ken Burns,
los crossfades y los subtítulos siguen en el procesador, y en un portátil la
gráfica integrada comparte RAM y calor con el procesador — vas a ver el CPU
bajar bastante, pero el tiempo total baja menos de lo que parece. Si el encoder
de hardware falla (driver viejo, ffmpeg sin QSV), el render **no se pierde**:
se reintenta solo con el procesador y te avisa.

**2) Bajarle al preset si te quedas en procesador.** El preset es la palanca de
velocidad; el CRF es la de calidad. En `.env`: `VIDEO_PRESET=veryfast` para que
el PC quede libre antes, dejando `VIDEO_CRF=17` para no perder calidad.

**3) Que el PC siga usable aunque marque 99%.** Ya viene activo: ffmpeg se
lanza con prioridad baja (`VIDEO_LOW_PRIORITY=true`), así cede procesador a lo
que estés haciendo. Con `VIDEO_THREADS=4` además le dejas núcleos libres.

Otras dos cosas que ya están aplicadas por defecto y bajaron el consumo sin
tocar la calidad final: los clips intermedios de cada escena se codifican en
`ultrafast` (se recodifican en el paso final, así que comprimirlos bien era
gastar procesador para nada: 8,3 s → 3,2 s por escena), y la imagen se escala
solo un 25% por encima de la salida antes del Ken Burns en vez de a 4K.

Si el que está al 100% no es ffmpeg sino Python, entonces es la clonación de
voz (Chatterbox), y eso es otro asunto: no usa Quick Sync — necesitaría una
gráfica NVIDIA. En procesador es inevitablemente lento.

## Cola de trabajos (los renders no se pisan ni se cortan)

Los videos no se generan en el momento en que le das a "Generar": entran en una
cola y se procesan **de a uno** (configurable con `JOB_WORKERS`). Dos renders a
la vez en un PC tardan más en total que en fila y pueden quedarse sin memoria,
que es justo lo que hace que un trabajo se caiga a medias.

Qué pasa en cada caso:

- Si mandas varios videos seguidos, la interfaz te dice *"En cola — hay 2
  trabajo(s) delante"* y los va sacando en orden. Ninguno se pierde.
- Si un trabajo falla, el worker sigue vivo y atiende el siguiente; el que
  falló queda marcado con el error, no desaparece.
- El estado de cada trabajo se guarda en `outputs/jobs/<id>.json`, así que
  sobrevive a reiniciar el servidor. Los que estaban a medias quedan marcados
  como **interrumpidos** con la razón, en vez de quedarse en "generando" para
  siempre o esfumarse.
- Puedes cerrar el navegador: el trabajo corre en el servidor, no en la página,
  y el video aparece en "Videos generados" cuando termine.

Lo único que sí corta un render en curso es reiniciar el servidor. Por eso
`.\start.ps1` **ya no usa `--reload`** por defecto: con recarga automática,
guardar un archivo `.py` mientras renderizas mata el trabajo. Para desarrollar
usa `.\start.ps1 -Dev`, que además excluye `outputs/` y `assets/` del vigilante
de cambios.

Limitar hilos (`VIDEO_THREADS`) no corta nada: solo hace que ffmpeg use menos
núcleos y tarde un poco más. Se combina bien con la cola — un trabajo a la vez,
con cores libres para que puedas seguir trabajando.

## Qué calidad aplica por defecto

- Audio normalizado a **-16 LUFS** (estándar de streaming) con el filtro
  `loudnorm` de ffmpeg.
- Micro-pausas de 250ms entre escenas (configurable por escena).
- Ken Burns (zoom/pan lento) con interpolación suave, exportado a **1080p /
  30fps** por defecto (configurable a 4K/60fps en `config/settings.py`).
- Transición de crossfade de 0.6s entre escenas.
- Subtítulos quemados en formato `.ass` con tipografía legible.
- Validación de que cada imagen tenga resolución suficiente para el zoom sin
  pixelarse; si no, se hace upscaling básico (con un hook listo para conectar
  Real-ESRGAN más adelante si se necesita más calidad).
- Export final en H.264 High Profile, CRF 17, `yuv420p`, audio AAC 320kbps.
- Chequeo automático (QA) de duración, resolución y frames negros antes de
  dar el video por bueno.

## Estado de esta entrega

El pipeline completo fue corrido de punta a punta (`scripts/run_pipeline.py`)
y quedó verificado por el QA automático: duración exacta (0.00s de
diferencia contra lo esperado), resolución 1920x1080, audio presente, sin
frames negros. Hay un video de ejemplo ya generado en
`outputs/demo_flujo1.mp4`.

Esa prueba se hizo con el backend `--tts espeak` porque el entorno de
desarrollo donde se armó este proyecto no tiene salida de red a
huggingface.co (política del sandbox), que es de donde se descargan los
modelos de voz de Piper. En tu servidor/PC esto no debería pasar — instala
`piper-tts`, corre `python -m piper.download_voices <voz>` y usa `--tts
piper` (el valor por defecto) para la calidad de voz real de producción. El
resto del pipeline (Ken Burns, transiciones, subtítulos, normalización de
audio, QA) es exactamente el mismo sin importar qué backend de TTS uses.

## Siguientes pasos (fuera de este primer entregable)

- Conectar Real-ESRGAN de verdad para imágenes de baja resolución (hoy hay un
  fallback simple con Pillow).
- Voces con clonación (Chatterbox) para narración de marca.
- Flujo 2 (audio real + VAD + STT + matching de imágenes) como servicio
  separado que reutiliza `edl.py`, `video_renderer.py` y `qa_check.py`.
