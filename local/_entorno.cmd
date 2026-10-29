@echo off
rem Prepara el entorno comun para todos los lanzadores de esta carpeta.
rem Elige el Python que tenga chatterbox-tts instalado (voz clonada).
chcp 65001 >nul
set KMP_DUPLICATE_LIB_OK=TRUE
set PYTHONIOENCODING=utf-8
set PY=
for %%P in ("%USERPROFILE%\anaconda3\python.exe" "%USERPROFILE%\miniconda3\python.exe" "%~dp0..\.venv\Scripts\python.exe") do (
  if not defined PY if exist %%P (
    %%P -c "import chatterbox" >nul 2>&1 && set PY=%%P
  )
)
if not defined PY if exist "%~dp0..\.venv\Scripts\python.exe" set PY="%~dp0..\.venv\Scripts\python.exe"
if not defined PY set PY=python
