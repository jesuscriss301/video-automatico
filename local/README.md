# Lanzadores locales (Windows)

Funciones que **solo corren en tu PC** (no en los entornos en la nube de Claude).
Doble clic en el `.bat` que necesites:

| Archivo | Qué hace |
|---|---|
| `interfaz.bat` | Abre la interfaz web en http://localhost:8000 (guion → video, voces, cola). |
| `muestra_voces.bat` | Video de muestra de todas las voces (incluida la clonada). |
| `revisar_equipo.bat` | Dice qué está instalado (Chatterbox, NVIDIA, FFmpeg, Node) y prueba la aceleración de video. |
| `correr_tarea.bat` | Ejecuta la tarea que Claude dejó en `tarea.cmd` y guarda el resultado en `tarea.log`. |

`_entorno.cmd` lo usan todos: activa la corrección del error OMP #15 y elige el
Python que tenga la voz clonada instalada.
