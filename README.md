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
│   └── run.py                # Orquesta todo el pipeline de punta a punta
├── api/
│   └── main.py               # API FastAPI para exponer el pipeline
├── scripts/
│   ├── run_pipeline.py       # CLI: genera un video a partir de un guion
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

## Uso

1. Escribe tu guion en un JSON como `examples/sample_script.json` (cada escena:
   texto, ruta de imagen, descripción, y opcionalmente pausa después).
2. Corre el pipeline:

```bash
python scripts/run_pipeline.py examples/sample_script.json outputs/mi_video.mp4
```

3. El video final queda en `outputs/`, junto con un reporte de QA (`*.qa.json`).

También puedes levantar la API:

```bash
uvicorn api.main:app --reload --port 8000
```

y mandar un POST a `/generate` con el guion en el body.

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
