@echo off
rem Versiones en espanol del plan de videos (Video 3 y Video 1), en esta PC.
rem 1) Voz clonada "El documentalista" (tarda: ~20-40 min sin tarjeta NVIDIA)
rem 2) Capturas reales de las demos (Edge sin ventana)
rem 3) Arma los 8 cortes en espanol + bucle y los renderiza (HyperFrames)
call "%~dp0..\..\local\_entorno.cmd"
cd /d "%~dp0..\.."
echo [1/4] Voz del Video 3...
%PY% scripts\narrar.py estudio\plan-videos\guiones\v3_es.json --salida estudio\plan-videos\voz\v3_es || goto error
echo [2/4] Voz del Video 1...
%PY% scripts\narrar.py estudio\plan-videos\guiones\v1_es.json --salida estudio\plan-videos\voz\v1_es || goto error
echo [3/4] Capturas de las demos...
%PY% estudio\plan-videos\capturar.py %TURNERO%
echo [4/4] Armando y renderizando los cortes en espanol...
%PY% estudio\plan-videos\build.py --idiomas es --render || goto error
echo.
echo Listo. Videos en estudio\plan-videos\renders\
start "" estudio\plan-videos\renders
goto fin
:error
echo.
echo Algo fallo. Revisa el mensaje de arriba.
:fin
pause
