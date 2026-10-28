@echo off
chcp 65001 >nul
cd /d "%~dp0"
set KMP_DUPLICATE_LIB_OK=TRUE
set PY=python
if exist "%USERPROFILE%\anaconda3\python.exe" set PY="%USERPROFILE%\anaconda3\python.exe"
echo Generando muestra de las voces clonadas (El documentalista de español latino)...
echo La primera vez carga el modelo: puede tardar varios minutos sin avance visible.
echo.
%PY% scripts\muestra_voces.py --kokoro no --voces "documentalista" --salida outputs\muestra_clonadas.mp4 > outputs\muestra_clonadas.log 2>&1
type outputs\muestra_clonadas.log
if exist outputs\muestra_clonadas.mp4 start "" outputs\muestra_clonadas.mp4
echo.
echo Listo. Puedes cerrar esta ventana.
pause
