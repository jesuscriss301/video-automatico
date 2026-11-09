# SPEC — Video inmobiliario en Remotion (09/11/2026)

- Misma voz y guion que `estudio/inmobiliaria` (Dora en español, Heart en inglés), 3 ganchos por idioma → 6 videos de 39–41 s.
- **Estilo (skill brand-guidelines):** fondo oscuro `#141413`, crema `#faf9f5`, gris claro `#e8e6dc`, gris medio `#b0aea5`;
  acentos naranja `#d97757`, azul `#6a9bcc`, verde `#788c5d`. Títulos en Poppins, textos en Lora.
- **Un color por escena:** gancho oscuro/naranja · contexto crema/azul · funciones gris claro/verde · encuesta azul · fundadores oscuro con azul y naranja · llamado naranja · logo oscuro.
- **Movimiento fluido:** cada escena se abre en círculo sobre la anterior, entradas con resortes (spring), iconos que se dibujan solos, tarjetas que flotan.
- **Logo de EasyPro Digital solo al final** (marca `>_` + "EasyPro Digital" + easyprodigital.com).
- Audio normalizado a −16 LUFS después del render.

Cómo regenerar:
```
python gen_datos.py                 # tiempos desde ../inmobiliaria/voz/*/narracion.json
npx remotion studio                 # vista previa para editar
npx remotion render src/index.ts es-a renders/crudo_es_a.mp4
ffmpeg -i renders/crudo_es_a.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac renders/es_a.mp4
```
