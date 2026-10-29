@echo off
rem Revisa que hay instalado en esta PC y que aceleracion de video funciona.
call "%~dp0_entorno.cmd"
cd /d "%~dp0.."
echo Python elegido: %PY%
%PY% --version
%PY% -c "import chatterbox; print('Chatterbox (voz clonada): OK')" 2>nul || echo Chatterbox (voz clonada): NO instalado
%PY% -c "import torch; print('Grafica NVIDIA (CUDA):', torch.cuda.is_available())" 2>nul
where ffmpeg >nul 2>&1 && echo FFmpeg: OK || echo FFmpeg: NO encontrado
where node >nul 2>&1 && (echo|set /p=Node.js: & node --version) || echo Node.js: NO encontrado (necesario para HyperFrames y Remotion)
%PY% scripts\check_hw.py
pause
