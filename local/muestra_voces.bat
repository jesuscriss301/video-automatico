@echo off
rem Video de muestra de las voces del proyecto + Kokoro en espanol.
call "%~dp0_entorno.cmd"
cd /d "%~dp0.."
%PY% scripts\muestra_voces.py --salida outputs\muestra_voces.mp4
if exist outputs\muestra_voces.mp4 start "" outputs\muestra_voces.mp4
pause
