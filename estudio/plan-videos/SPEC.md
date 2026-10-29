# Plan de 3 videos — SPEC

- **Videos en esta tanda:** Video 3 (Turnero) y Video 1 (portada). Video 2 espera al bot estable.
- **Voz:** español = "El documentalista de español latino (20s)"; inglés = Heart (Kokoro, `af_heart`).
  En inglés, el Video 1 va en tercera persona ("Meet Jesús… he'll tell you") porque narra una voz femenina.
- **Paleta:** fondo `#0B0F1A`, acento `#38BFF0`, texto `#F2F6FA`, secundario `#8A97AD`. Logo `>_` en JetBrains Mono; títulos en Inter 900.
- **Ganchos:** A/B/C del plan en cada vertical; horizontales con el gancho A.
- **Formatos:** vertical 1080x1920 (texto en la banda 168–1330 px) y horizontal 1920x1080, 30 fps, H.264.
- **Imágenes:** capturas reales de las demos con movimiento lento (Ken Burns) dentro de un marco de navegador; ilustraciones dibujadas solo donde no hay fuente real (sala de espera, cuaderno, QR, código, ciudad).
- **Subtítulos:** grupos de hasta 4 palabras, fondo oscuro, cifras en cian.
- **Sonido:** voz a -16 LUFS; efectos de la librería de HyperFrames solo en cortes de escena, botones y logo; sin música de fondo (no hay fuente de música disponible).
- **Cierre:** wa.me/573238816434 con botón cian, 2,2 s de cierre sin voz.

Regenerar: `python estudio/plan-videos/build.py [--idiomas es,en] [--solo v3_es_a_v] [--render]`.
En la PC, todo el español con un doble clic: `estudio\plan-videos\hacer_espanol.bat`.
