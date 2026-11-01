# Serie "Día X tratando de que una clínica estética no pierda ni una cita más… usando solo software"

7 videos verticales (1080×1920), en español, voz "El documentalista", sin cara.
El Día 1 tiene 3 ganchos (A, B, C): publica uno y guarda los otros para probar después.

| Archivo | Día | Qué muestra | Llamada a la acción |
|---|---|---|---|
| `dia1_a.mp4` / `dia1_b.mp4` / `dia1_c.mp4` | 1 | Las 3 fugas (no contestan, no recuerdan, no vuelven) y el plan de la semana | Sígueme 👉 Día 2 |
| `dia2.mp4` | 2 | Página por tratamiento → horario → cita reservada | Mañana: recordatorios |
| `dia3.mp4` | 3 | Recordatorio 24 h antes (Confirmar / Cambiar / Cancelar) y aviso de retoque | Mañana: clínicas reales |
| `dia4.mp4` | 4 | Lista de 10 clínicas (nombres ocultos) y el mensaje que les mando | Mañana: qué respondieron |
| `dia5.mp4` | 5 | Objeción "ya tenemos a alguien que contesta" y la respuesta | Comenta DEMO |
| `dia6.mp4` | 6 | Las 3 cosas que muestro en la llamada y las 2 preguntas que hago | Mañana: resumen |
| `dia7.mp4` | 7 | Resumen de la semana y votación del próximo nicho | Comenta DEMO |

## Antes de publicar (importante: todo tiene que ser real)

Los videos cuentan **la estrategia**, no resultados. No hay cifras inventadas. Antes de subir cada día:

- **Día 4:** el mensaje que aparece en pantalla es un ejemplo. Si el que envías de verdad es distinto, avísame y lo cambio. Envía de verdad el mensaje a las 10 clínicas ese día.
- **Día 5 y Día 6:** si ya tienes respuestas o una llamada real, en el texto de la publicación cuenta lo que pasó (aunque sea "nadie respondió todavía").
- **Día 7:** en la descripción agrega los números reales de la semana (cuántas respondieron, cuántas demos), si los tienes.
- La ficha de "Laura G." y los horarios son **ejemplos** de cómo se ve el sistema.

## Textos sugeridos para la publicación

- **Día 1:** Día 1/7. Voy a intentar que una clínica estética no pierda ni una cita más, solo con software. ¿Lo logro? #clinicaestetica #medellin #software
- **Día 2:** Día 2/7. Hoy: que agenden sin escribir por WhatsApp.
- **Día 3:** Día 3/7. El sistema les escribe solo: recordatorio 24 h antes y aviso de retoque.
- **Día 4:** Día 4/7. Hoy se lo mando a 10 clínicas de Medellín. Mañana les cuento.
- **Día 5:** Día 5/7. Cómo respondo los "no". Si tienes una clínica, comenta DEMO.
- **Día 6:** Día 6/7. La primera demo en llamada: muestro 3 cosas y hago 2 preguntas.
- **Día 7:** Día 7/7. Resumen de la semana. ¿Próximo nicho: taller, odontología o bodegas? Vota 👇

## Cómo regenerarlos

```
python scripts/narrar.py estudio/serie-dia/guiones/dia1.json --salida estudio/serie-dia/voz/dia1   (en la PC)
python estudio/serie-dia/build.py --solo dia1_a --render
```
