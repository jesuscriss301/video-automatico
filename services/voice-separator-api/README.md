# Voice Separator API — Aislar voz de música instrumental

Otro nodo de la "red de APIs" de edición de video: recibe un audio con voz y
música mezcladas y devuelve dos archivos separados — solo la voz, solo el
instrumental.

## Por qué es un servicio aparte (y no un módulo del proyecto de video)

El backend de calidad real usa [Spleeter](https://github.com/deezer/spleeter)
(Deezer, licencia MIT), que internamente necesita TensorFlow con versiones de
`numpy`/`protobuf`/`typing-extensions` bastante viejas. Al instalarlo en el
mismo entorno que el pipeline de video (FastAPI + Pydantic modernos), rompió
esas dependencias — lo comprobamos directamente. Por eso este servicio vive
en su propia carpeta, con su propio `.venv` y su propio `requirements.txt`,
expuesto por HTTP como cualquier otro nodo de la red, sin compartir
dependencias con el resto.

## Instalación

```bash
cd services/voice-separator-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

La primera vez que se corre una separación, Spleeter descarga su modelo
(`spleeter:2stems`, ~73MB) automáticamente desde GitHub releases — después
queda cacheado en `pretrained_models/` y no se vuelve a descargar.

## Uso — API

```bash
uvicorn main:app --reload --port 8001
```

```bash
curl -X POST http://localhost:8001/separate -F "file=@mi_audio.mp3"
# → {"job_id": "...", "backend": "spleeter",
#     "vocals_url": "/download/.../vocals", "instrumental_url": "/download/.../instrumental"}

curl -o voz.wav       http://localhost:8001/download/<job_id>/vocals
curl -o instrumental.wav http://localhost:8001/download/<job_id>/instrumental
```

Acepta cualquier formato que ffmpeg pueda leer (mp3, wav, m4a, etc.) y lo
normaliza internamente a WAV estéreo 44.1kHz.

## Uso — CLI (sin levantar la API)

```bash
python cli.py mi_audio.mp3 outputs/
```

## Dos backends

| Backend | Calidad | Velocidad | Requiere descarga |
|---|---|---|---|
| `spleeter` (default) | Real — modelo entrenado para esto | Segundos por minuto de audio, CPU | Sí, ~73MB una sola vez |
| `centerchannel` | Burda — truco clásico de cancelación de fase | Instantáneo | No |

`centerchannel` sirve para probar que la subida/descarga de archivos
funciona sin esperar el modelo, o como demo rápida — pero solo remueve/
resalta lo que está paneado al centro de una mezcla estéreo (no es
separación de verdad, y no funciona en absoluto con audio mono). Para
aislar voz de verdad, usar `spleeter`:

```bash
python cli.py mi_audio.mp3 outputs/ --backend centerchannel
```

## Verificado

Se probó de punta a punta subiendo un audio de prueba (voz sintética +
"música" sintética mezcladas) a través de la API real corriendo en
`localhost:8001`: el modelo se descargó automáticamente, la separación
corrió, y se descargaron `vocals.wav` e `instrumental.wav` — distintos entre
sí y distintos del archivo mezclado original (confirmado por hash).

Nota honesta sobre esa prueba: la "música" usada para probar fue un audio
sintético (tonos senoidales generados con ffmpeg), no una canción real — es
la única forma de generar un audio de prueba en este entorno sin descargar
nada. Spleeter está entrenado con canciones reales (baterías, acordes,
timbres variados) y separa mucho mejor ese tipo de contenido que tonos
puros sintéticos, así que la calidad real con tu música de verdad debería
ser considerablemente mejor de lo que se ve con este audio de prueba
artificial. Pruébalo con un clip real tuyo para juzgar la calidad de verdad.

## Cómo conectarlo con el resto de la red de APIs

- **Antes de STT (Flujo 2):** si vas a transcribir audio real grabado que
  tiene música de fondo, pasarlo primero por `/separate` y transcribir solo
  `vocals.wav` da transcripciones bastante mejores que transcribir la
  mezcla completa.
- **Reciclar música de un video de referencia:** separar un video existente
  te da su pista de música sola, lista para reusar como música de fondo en
  uno nuevo (ver `mix_with_background_music` en el pipeline de Flujo 1).
