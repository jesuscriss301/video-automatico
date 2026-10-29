# Inventario de habilidades de los 4 proyectos

> Actualizado: 29/10/2026. Incluye **todo** lo que trae cada proyecto, esté instalado o no.
> Versiones revisadas: Remotion skills `30d4553`, HyperFrames `67c7ec2`, iart-ai (19 paquetes, última versión de cada repo).

## Resumen

| Proyecto | Skills | Instaladas en video-automatico | Fuerte en |
|---|---|---|---|
| **video-automatico** (propio) | 2 skills propias + 7 scripts + pipeline de 11 módulos + 5 lanzadores | Todo | Voz clonada, guion + fotos → video, separar voz y música, trabajo en tu PC |
| **Remotion** (oficial) | 12 skills (+ 34 guías dentro de `remotion-markup`) | 12 de 12 | Videos en React, plantillas con datos, mapas, apps/SaaS |
| **HyperFrames** (HeyGen) | 7 skills + 469 bloques listos + 6 skills internas del repo | 6 de 7 (falta `figma`) | Motion graphics en HTML, historia y guion, audio, subtítulos, efectos listos |
| **iart-ai** | 56 skills en 19 paquetes | 9 de 56 (paquete `motion-design-skills`) | Criterio de diseño de movimiento y formatos concretos (anuncios, TikTok, explicativos, web) |

**En una frase:** HyperFrames es el motor más completo y mejor pensado para hacer videos, Remotion es el mejor para videos con datos o dentro de una app, iart-ai es el mejor en criterio de diseño (con calidad desigual), y video-automatico es el único que tiene tu voz clonada y corre todo en tu PC.

### Cómo juzgué cuál está "mejor diseñada"

1. **¿Hace o solo explica?** Las que traen scripts, plantillas o comandos que producen y verifican el resultado ganan a las que solo dan consejos.
2. **¿Se revisa sola?** Las que obligan a mirar fotogramas o validar el archivo antes de entregar.
3. **Profundidad:** guías de apoyo y casos cubiertos.
4. **Al día:** las oficiales siguen la versión actual de su herramienta; algunas de terceros usan formas viejas.
5. **Encaje:** si funciona con el resto del estudio (tu voz, tus formatos, tu PC).

Leyenda: ✅ instalada · ⬜ no instalada · ★ la mejor de su tema.

---

## 1. video-automatico (proyecto propio)

### Skills propias

| Skill | Dónde | Qué hace |
|---|---|---|
| ✅ `estudio-video` | `.claude/skills/` | La que coordina todo: briefing (voz, colores, idea, gancho), elegir motor, recetas para combinar los 4 proyectos, voces, qué corre solo en tu PC, verificación. |
| `pedido-de-video` | tu cuenta de Claude | Hace el briefing y manda al proyecto cuando pides un video fuera de él. |

### Scripts y módulos

| Pieza | Qué hace | ¿Lo tiene otro proyecto? |
|---|---|---|
| `pipeline/run.py` (Flujo 1) | Guion + imágenes → video narrado con Ken Burns, transiciones, subtítulos y QA | Parecido: `photo-slideshow` (iart), pero sin voz ni QA |
| `pipeline/tts_engine.py` | Voz con Piper, espeak y **Chatterbox (voz clonada)** | **Único con voz clonada local y gratis** |
| `pipeline/subtitles.py` | Subtítulos sincronizados frase por frase con la voz real | Sí (ver tema Subtítulos) |
| `pipeline/audio_processor.py` | Normaliza volumen (EBU R128), pausas, mezcla con música | Sí: `media-use` (HyperFrames) |
| `pipeline/image_processor.py` | Ajusta resolución de imágenes | — |
| `pipeline/edl.py` | Lista de cortes con tiempos exactos | — |
| `pipeline/video_renderer.py` | Render con ffmpeg, aceleración Intel QSV | **Único con aceleración por gráfica** |
| `pipeline/qa_check.py` | Revisa el video final automáticamente | Sí: `hyperframes check`, verify de iart |
| `pipeline/hw.py`, `scripts/check_hw.py` | Detecta la gráfica y qué acelera | Único |
| `api/main.py` + interfaz web | Armar videos desde el navegador, cola de renders, biblioteca de voces | Parecido: Studio de HyperFrames / Remotion (editan, no narran) |
| `services/voice-separator-api` | Separa voz y música de un audio | **Único** |
| `scripts/narrar.py` | Puente de voz → HyperFrames/Remotion con tiempos exactos | Único |
| `scripts/muestra_voces.py` | Video de muestra de todas las voces | Único |
| `scripts/voice_sampler.py`, `make_sample_assets.py` | Muestras de voz y fotos de prueba | — |
| `local/*.bat` | Lanzadores para lo que solo corre en tu PC | Único |

---

## 2. Remotion (oficial, todas instaladas ✅)

| Skill | Qué hace | Calidad |
|---|---|---|
| `remotion-best-practices` | Enrutador: decide qué otra skill leer | Buena puerta de entrada |
| `remotion-create` | Crear proyecto o composición nueva | Corta y clara |
| `remotion-markup` | **El corazón**: animación, textos, medios, efectos (60+ efectos), transiciones, audio, voz en off, multiescena, 34 guías | ★ Muy completa y al día |
| `remotion-interactivity` | Dejar el código editable desde Studio | Detallada (332 líneas) |
| `remotion-captions` | Transcribir con Whisper, importar SRT, mostrar subtítulos | Correcta, básica en estilo |
| `remotion-maps` | Mapas animados: rutas, marcadores, Mapbox/MapLibre, vuelos 3D | ★ 14 guías + 5 scripts |
| `remotion-multimedia` | Recortar, cortar y leer datos de videos (Mediabunny) | Corta |
| `remotion-studio` | Abrir la vista previa | Corta |
| `remotion-render` | Exportar el video | Corta |
| `remotion-saas` | Apps con Remotion: Player, Lambda, Vercel | Útil para productos |
| `remotion-docs` | Buscar en la documentación oficial | Útil |
| `remotion-upgrade` | Actualizar Remotion | Mantenimiento |

Guías dentro de `remotion-markup`: 3D, texto árabe, visualizar audio, audio, metadatos dinámicos, corrección de color, composiciones, composiciones conectadas, recorte, efectos, insertar video, ffmpeg, GIFs, Google Fonts, HTML en canvas, imágenes, light leaks, fuentes locales, Lottie, medir textos y elementos, desenfoque de movimiento, multiescena, parámetros, secuencias, efectos de sonido, **detección de silencios**, resaltar texto, tiempos, transiciones, edición de video, **voz en off (ElevenLabs)**.

**Puntos fuertes:** oficial y al día, ideal para datos y plantillas. **Débil:** no trae historia ni criterio creativo; la voz solo con ElevenLabs (de pago); licencia de pago desde 4 empleados.

---

## 3. HyperFrames (HeyGen)

| Skill | Estado | Qué hace | Calidad |
|---|---|---|---|
| `hyperframes` | ✅ | La principal: reglas de render, ciclo de trabajo, qué necesita cada tipo de video | ★ La mejor diseñada de todas |
| `hyperframes-cli` | ✅ | Todos los comandos: crear, revisar, ver fotogramas, editar la línea de tiempo, render local o en la nube | Muy completa |
| `hyperframes-registry` | ✅ | 469 bloques listos (210 bloques + 239 componentes): transiciones, títulos, texto cinético, subtítulos, gráficos, mapas, 3D, cámaras | ★ Ahorra más trabajo que cualquier otra |
| `media-use` | ✅ | Conseguir o crear música, efectos, imágenes, logos, voz (Kokoro, HeyGen, ElevenLabs, Gemini), transcripción, quitar fondo, etalonaje, mezcla | ★ 44 scripts, la más práctica en audio |
| `remotion-to-hyperframes` | ✅ | Pasar un proyecto de Remotion (u otras herramientas) a HyperFrames y compararlo fotograma a fotograma | Única en su tipo |
| `slideshow` | ✅ | Presentaciones en vivo con notas del presentador | Buena |
| `figma` | ⬜ | Traer diseños de Figma al video | Solo si usas Figma |

Guías dentro de `hyperframes`: tipos de video (lanzamiento, explicativo, música, datos, vertical, 3D, personaje), historia, SPEC, storyboard, movimiento, look, sonido, subtítulos, overlays sobre video, formato, revisión final.

**Skills internas del repo** (las usa el equipo de HeyGen, no se instalan): `motion-doctrine` (continuidad entre escenas), `cut-the-curve` (catálogo de transiciones), `seam-craft` (transiciones sin parpadeos), `captions-overlay` (modelos de subtítulos), `oversized-cursor` (cursor grande para demos), `changelog-video` (video semanal de novedades). Ideas reutilizables, pero dependen de su marca.

**Puntos fuertes:** cada video es igual en cada render, obliga a historia → SPEC → revisión, audio muy cuidado, 469 bloques listos, gratis. **Débil:** la mejor calidad de voz y música requiere cuenta HeyGen.

---

## 4. iart-ai (19 paquetes, 56 skills)

Calidad desigual: los paquetes **nuevos** (lower-thirds, b-roll, talking-head, javascript-animation) traen plantillas y scripts que producen y revisan el resultado. Los **antiguos** son guías de criterio, buenas para pensar pero sin herramientas.

| Paquete | Skills | Estado | Qué cubre | Calidad |
|---|---|---|---|---|
| motion-design-skills | `animation-principles`, `shot-composition`, `motion-art-direction`, `color-motion`, `logo-animation`, `beat-sync-editing`, `motion-background`, `remotion-video`, `after-effects` | ✅ 9 | Fundamentos: easing, tiempos, composición, color, ritmo, logos, fondos, After Effects | ★ `animation-principles` y `shot-composition` son el mejor criterio de todos los proyectos |
| tiktok-video-skills | `short-form-video`, `caption-animation`, `countdown-video`, `lower-thirds` | ⬜ | Reels/TikTok/Shorts, ganchos, subtítulos palabra por palabra, cuentas regresivas | Buena guía de ganchos |
| youtube-video-skills | `youtube-intro-outro`, `audiogram` | ⬜ | Intros/outros de canal, clips de podcast con onda de audio | Guía |
| ecommerce-video-skills | `product-demo-video`, `promo-video`, `photo-slideshow` | ⬜ | Demos de producto, ofertas (precio antes → después), fotos a video | Guía |
| ad-video-skills | `ad-creative-video`, `launch-video`, `testimonial-video` | ⬜ | Anuncios, lanzamientos, testimonios animados | Guía |
| data-animation-skills | `chart-animation`, `animated-infographic`, `presentation-video` | ⬜ | Gráficos animados desde CSV, infografías, deck → video | Guía |
| explainer-video-skills | `explainer-video`, `diagram-animation`, `whiteboard-animation`, `isometric-animation`, `wrapped-video` | ⬜ | Explicativos, diagramas, pizarra, isométrico, resumen tipo "Wrapped" | Guía; `explainer-video` muy buena en estructura |
| map-animation-skills | `map-animation` | ⬜ | Mapas estilo Vox (Google Earth Studio + After Effects, o vectores) | Buena dirección de estilo |
| kinetic-typography-skills | `kinetic-typography` | ⬜ | Texto cinético al ritmo | Guía |
| lower-thirds-skills | `lower-thirds` | ⬜ | Rótulos con fondo transparente (WebM alfa / ProRes 4444) con plantilla y script | ★ Produce y verifica |
| b-roll-skills | `talking-head-b-roll` | ⬜ | Transcribe un video de alguien hablando y agrega gráficos donde dice cosas | ★ Con scripts |
| talking-head-skills | `talking-head` | ⬜ | Crea un presentador con IA desde fotos + muestra de voz | Con 7 scripts; encaja con tu voz clonada |
| javascript-animation-skills | `javascript-animation`, `soundtrack` | ⬜ | Animación dibujada en código y música hecha en código | Con scripts |
| generative-illustration-skills | `generative-illustration` | ⬜ | Ilustraciones animadas generativas | Guía |
| manim-skills | `manim` | ⬜ | Matemáticas estilo 3Blue1Brown | Guía |
| webgl-animation-skills | `threejs-animation`, `shader-glsl`, `particle-system` | ⬜ | 3D, shaders, partículas | Guía, sobre todo para web |
| text-message-video-skills | `text-message-animation` | ⬜ | Historias en chat (iMessage/WhatsApp) | Guía; formato viral |
| web-animation-skills | `gsap-web`, `svg-animation`, `lottie-animation`, `micro-interaction`, `page-transition-animation`, `60fps-animation`, `accessible-animation`, `glassmorphism`, `ascii-animation` | ⬜ | Animación para **sitios web**, no video | Útil para tus webs de clientes, no para este proyecto |
| freelance-motion-skills | `creative-brief`, `motion-pricing`, `client-revisions`, `video-delivery-specs`, `brand-motion-guidelines` | ⬜ | Negocio: brief, cotizar, límite de revisiones, especificaciones de entrega, guía de marca | Útil si vendes videos a clientes |

---

## 5. Habilidades repetidas: cuál usar

| Tema | Quién lo tiene | ★ Mejor | Por qué |
|---|---|---|---|
| **Voz / narración** | video-automatico (Piper, espeak, Chatterbox); `media-use` (Kokoro, HeyGen, ElevenLabs, Gemini); `remotion-markup/voiceover` (ElevenLabs); `talking-head` (muestra de voz) | **video-automatico** para tu voz; **media-use** para el resto | Solo el tuyo clona voz gratis y local; media-use tiene más opciones y da tiempos por palabra |
| **Subtítulos** | `pipeline/subtitles.py`; `remotion-captions`; HyperFrames `captions.md` + registro (17 estilos listos); `caption-animation` (iart); `captions-overlay` (interna) | **HyperFrames** | 17 estilos listos, transcribe por palabra y los integra en la escena; iart explica bien el estilo TikTok pero depende de Remotion |
| **Transcribir / detectar silencios** | `media-use` (Parakeet/whisper, recorte por transcripción); `remotion-captions` (Whisper); `remotion-markup/silence-detection`; video-automatico (planeado) | **media-use** | Ya trae el recorte por transcripción listo para usar |
| **Rótulos inferiores (lower thirds)** | `lower-thirds` (iart, paquete propio); `lower-thirds` (iart, tiktok); HyperFrames `overlays.md` + registro | **lower-thirds-skills (iart)** | Única que entrega con fondo transparente y verifica; la de tiktok es una versión antigua solo con consejos |
| **Mapas** | `remotion-maps`; `map-animation` (iart); registro de HyperFrames | **remotion-maps** para hacerlos; **map-animation** para el estilo | Remotion trae 14 guías y scripts; iart enseña el estilo Vox |
| **Cómo usar Remotion** | `remotion-markup` y demás (oficial); `remotion-video` (iart) | **Remotion oficial** | La de iart usa la forma vieja de animar; la oficial está al día y es más completa |
| **Historia / guion / brief** | HyperFrames `story.md` + `spec.md`; `explainer-video` (iart); `creative-brief` (iart); `estudio-video` (briefing) | **HyperFrames** para la historia; **estudio-video** para preguntarte | HyperFrames obliga a 3 historias distintas y a poner números a todo |
| **Criterio de movimiento** | `animation-principles`, `shot-composition`, `motion-art-direction` (iart); HyperFrames `motion.md`, `motion-doctrine` (interna) | **iart** (`animation-principles` + `shot-composition`) | Números concretos para easing, tiempos, composición y zonas seguras; HyperFrames agrega la continuidad entre escenas |
| **Ritmo con la música** | `beat-sync-editing` (iart); HyperFrames `sound.md` + `hyperframes beats` | **HyperFrames** para ejecutar; **iart** para teoría de montaje | HyperFrames detecta los tiempos de la música por sí mismo |
| **Mezcla de audio / volumen** | `audio_processor.py`; `media-use/mixing`; `remotion-markup/audio` | **media-use** | Envolventes, bajar la música cuando habla la voz, efectos por pista |
| **Color / etalonaje** | `color-motion` (iart); `media-use` (media-treatment, LUTs); `remotion-markup` (efectos de color) | **media-use** para video real; **color-motion** para paletas | Cada uno cubre una mitad |
| **Fondos animados** | `motion-background`, `shader-glsl`, `particle-system` (iart); registro de HyperFrames (aurora, blob…) | **Registro de HyperFrames** | Ya están hechos; iart sirve si quieres uno a medida |
| **Logo animado / intros** | `logo-animation`, `youtube-intro-outro` (iart); registro de HyperFrames | **logo-animation** (criterio) + **registro** (hacerlo) | — |
| **Texto cinético** | `kinetic-typography` (iart); HyperFrames `film.md` + registro | **HyperFrames** | Bloques listos |
| **Gráficos con datos** | `chart-animation`, `animated-infographic` (iart); HyperFrames `types/data.md` + registro (bar-chart-race…); Remotion | **Remotion** para muchos videos desde datos; **HyperFrames** para uno solo | — |
| **Explicativos** | `explainer-video`, `diagram-animation`, `whiteboard-animation`, `isometric-animation` (iart); HyperFrames `types/explainer.md` | **HyperFrames** para producir; **iart `explainer-video`** para la estructura | — |
| **Lanzamiento / promo / anuncios** | `launch-video`, `promo-video`, `ad-creative-video`, `product-demo-video` (iart); HyperFrames `types/launch.md` | **HyperFrames** | Más completo y con revisión |
| **Vertical / redes** | `short-form-video` (iart); HyperFrames `types/vertical.md` | Empate: **iart** para ganchos, **HyperFrames** para producir | — |
| **Presentaciones** | `slideshow` (HyperFrames); `presentation-video` (iart) | **slideshow** para presentar en vivo; **presentation-video** para convertir un deck en video | Hacen cosas distintas |
| **Fotos → video** | Flujo 1 de video-automatico; `photo-slideshow` (iart) | **video-automatico** | Ya narra, sincroniza y revisa |
| **3D** | `threejs-animation` (iart); HyperFrames `types/3d.md` + registro; `remotion-markup/3d` | **HyperFrames** | — |
| **Formatos de entrega** | `video-delivery-specs` (iart); `estudio-video` sección 10 | **video-delivery-specs** | Más plataformas y detalle |
| **Revisar antes de entregar** | `qa_check.py`; `hyperframes check` + `snapshot --review`; verify de iart; Studio de Remotion | **HyperFrames** | Revisión con reglas y fotogramas; iart y el QA propio la complementan |
| **Vista previa para editar** | Studio de HyperFrames; Remotion Studio; interfaz web propia | Empate | Cada uno para su motor |

## 6. Habilidades que solo tiene un proyecto

- **video-automatico:** voz clonada local, separar voz y música, aceleración por gráfica, cola de renders, interfaz web de guion → video, lanzadores para tu PC.
- **Remotion:** apps/SaaS con video (`remotion-saas`), dejar el código editable (`remotion-interactivity`), metadatos dinámicos, mapas con scripts.
- **HyperFrames:** 469 bloques listos, migrar desde otras herramientas (`remotion-to-hyperframes`), presentaciones en vivo, Figma, render en la nube, publicar proyectos para remezclar.
- **iart-ai:** presentador con IA (`talking-head`), gráficos sobre video de alguien hablando (`talking-head-b-roll`), historias en chat, pizarra, isométrico, "Wrapped", Manim, After Effects, animación web, y el paquete de negocio (cotizar, brief, revisiones).

## 7. Recomendaciones

1. **Mantener como base:** `estudio-video` (coordina) + HyperFrames (producir) + tu pipeline (voz) + iart `motion-design-skills` (criterio). Remotion solo para datos o apps.
2. **Vale la pena instalar de iart:**
   - `lower-thirds-skills`: rótulos con fondo transparente para tus videos y los de clientes.
   - `b-roll-skills`: gráficos automáticos sobre videos donde alguien habla.
   - `talking-head-skills`: presentador con IA usando la voz del documentalista.
   - `freelance-motion-skills`: cotizar, hacer briefs y fijar revisiones si vendes videos.
   - `tiktok-video-skills` (solo `short-form-video`): ganchos para Reels/TikTok.
3. **No hace falta:** `remotion-video` de iart (la oficial es mejor), `lower-thirds` del paquete tiktok (la del paquete propio es mejor), `web-animation-skills` y `webgl-animation-skills` en este proyecto (son para sitios web; úsalas en tus proyectos web).
4. **Instalar solo si lo necesitas:** `figma` (HyperFrames), `manim-skills`, `text-message-video-skills`, `explainer-video-skills`, `data-animation-skills`.
