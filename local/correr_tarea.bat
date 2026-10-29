@echo off
rem Lanzador generico que usa Claude: ejecuta local\tarea.cmd (lo escribe Claude
rem con el comando exacto), guarda la salida en local\tarea.log y al terminar
rem escribe local\tarea.fin con el codigo de salida. Claude lee esos archivos.
call "%~dp0_entorno.cmd"
cd /d "%~dp0.."
if not exist "%~dp0tarea.cmd" (echo No hay tarea pendiente en local\tarea.cmd & pause & exit /b 1)
del "%~dp0tarea.fin" "%~dp0tarea.log" >nul 2>&1
echo Ejecutando tarea de Claude... (puedes minimizar esta ventana)
echo.
call "%~dp0tarea.cmd" > "%~dp0tarea.log" 2>&1
echo %ERRORLEVEL% > "%~dp0tarea.fin"
type "%~dp0tarea.log"
echo.
echo Tarea terminada (codigo %ERRORLEVEL%). Puedes cerrar esta ventana.
pause
