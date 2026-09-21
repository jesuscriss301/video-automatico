# Arranca la interfaz gráfica en Windows.
#
#   .\start.ps1              -> modo normal (recomendado para generar videos)
#   .\start.ps1 -Dev         -> modo desarrollo: recarga sola al cambiar código
#   .\start.ps1 -Puerto 8080 -> otro puerto
#
# Hace tres cosas que si no hay que recordar a mano cada vez:
#
# 1. Pone KMP_DUPLICATE_LIB_OK=TRUE, que evita el error
#    "OMP: Error #15: Initializing libiomp5md.dll..." al usar la clonación de
#    voz (Chatterbox) en una máquina que también tiene Anaconda: cada uno trae
#    su propia copia de la librería OpenMP de Intel y chocan.
#
# 2. Levanta el servidor.
#
# 3. Abre el navegador en la interfaz.
#
# POR QUÉ EL MODO NORMAL NO RECARGA SOLO:
# con --reload, uvicorn reinicia el servidor en cuanto cambia un archivo .py —
# y eso MATA el render que esté en curso. Un video de 15 escenas con voz
# clonada puede tardar media hora: no vale la pena arriesgarlo por comodidad.
# Usa -Dev solo cuando estés tocando el código, y no mientras generas.
#
# Los cambios en la interfaz (api/static/index.html) NO necesitan reinicio ni
# -Dev: se leen del disco en cada visita, basta recargar la página.

param(
    [int]$Puerto = 8000,
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$env:KMP_DUPLICATE_LIB_OK = "TRUE"

Write-Host ""
if ($Dev) {
    Write-Host "MODO DESARROLLO: el servidor se reinicia al cambiar codigo .py" -ForegroundColor Yellow
    Write-Host "Ojo: un reinicio corta cualquier video que se este generando." -ForegroundColor Yellow
} else {
    Write-Host "Modo normal: los renders no se cortan por cambios en el codigo." -ForegroundColor DarkGray
    Write-Host "Para desarrollar con recarga automatica: .\start.ps1 -Dev" -ForegroundColor DarkGray
}
Write-Host "Interfaz en http://localhost:$Puerto  (Ctrl+C para detener)" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://localhost:$Puerto"

if ($Dev) {
    # Se excluyen las carpetas de salida y de assets: ahí se escriben los
    # archivos de estado de la cola y los videos, y no deben provocar reinicios.
    python -m uvicorn api.main:app --reload `
        --reload-exclude "outputs/*" --reload-exclude "assets/*" `
        --port $Puerto
} else {
    python -m uvicorn api.main:app --port $Puerto
}
