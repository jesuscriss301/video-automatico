# Arranca la interfaz gráfica en Windows.
#
#   .\start.ps1
#
# Hace tres cosas que si no hay que recordar a mano cada vez:
#
# 1. Pone KMP_DUPLICATE_LIB_OK=TRUE, que es lo que evita el error
#    "OMP: Error #15: Initializing libiomp5md.dll..." cuando se usa la
#    clonación de voz (Chatterbox) en una máquina que también tiene
#    Anaconda instalado — cada uno trae su propia copia de la librería
#    OpenMP de Intel y chocan.
#
# 2. Levanta uvicorn con --reload, así los cambios en los archivos .py se
#    aplican solos, sin reiniciar nada a mano.
#
# 3. Abre el navegador en la interfaz.
#
# Nota: los cambios en api/static/index.html (la interfaz) no necesitan
# reinicio ni --reload — se leen del disco en cada visita, basta con
# recargar la página.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$env:KMP_DUPLICATE_LIB_OK = "TRUE"

$puerto = 8000
if ($args.Count -ge 1) { $puerto = $args[0] }

Write-Host "Interfaz en http://localhost:$puerto  (Ctrl+C para detener)" -ForegroundColor Cyan
Start-Process "http://localhost:$puerto"

python -m uvicorn api.main:app --reload --port $puerto
