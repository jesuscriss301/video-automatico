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
└── outputs/                   # Videos renderizados
```

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
