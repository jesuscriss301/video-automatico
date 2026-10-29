@echo off
rem Abre la interfaz web del proyecto en http://localhost:8000
call "%~dp0_entorno.cmd"
cd /d "%~dp0.."
start "" http://localhost:8000
%PY% -m uvicorn api.main:app --port 8000
pause
