# Genera la prueba corta (10 segundos, 2 escenas) con tu VOZ CLONADA.
#
#   .\prueba_voz.ps1                       -> usa assets\voice_samples\referencia_20s.wav
#   .\prueba_voz.ps1 -Muestra "otra.wav"   -> usa otro audio de referencia
#   .\prueba_voz.ps1 -Expresividad 0.7 -Apego 0.4
#
# Sirve para oír la voz clonada en 2-3 minutos en vez de esperar media hora por
# las 15 escenas. Hace tres cosas por ti:
#   1. Pone KMP_DUPLICATE_LIB_OK (el error "OMP: Error #15" con Anaconda).
#   2. Corre el pipeline con --tts chatterbox y tu audio de referencia.
#   3. Abre el video al terminar.

param(
    [string]$Muestra = "assets\voice_samples\referencia_20s.wav",
    [string]$Guion = "examples\prueba_10s.json",
    [double]$Expresividad = -1,
    [double]$Apego = -1
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$env:KMP_DUPLICATE_LIB_OK = "TRUE"

if (-not (Test-Path $Muestra)) {
    Write-Host "No encuentro el audio de referencia: $Muestra" -ForegroundColor Red
    Write-Host "Audios disponibles en assets\voice_samples:" -ForegroundColor Yellow
    Get-ChildItem "assets\voice_samples" -Filter *.wav | ForEach-Object { Write-Host "   $($_.Name)" }
    exit 1
}
if (-not (Test-Path $Guion)) {
    Write-Host "No encuentro el guion: $Guion" -ForegroundColor Red
    exit 1
}

$sello = Get-Date -Format "HHmm"
$salida = "outputs\prueba_voz_$sello.mp4"

$argumentos = @($Guion, $salida, "--tts", "chatterbox", "--voice-sample", $Muestra, "--language", "es")
if ($Expresividad -ge 0) { $argumentos += @("--exaggeration", $Expresividad) }
if ($Apego -ge 0)        { $argumentos += @("--cfg-weight", $Apego) }

Write-Host ""
Write-Host "Generando la prueba con voz clonada..." -ForegroundColor Cyan
Write-Host "  guion:      $Guion"
Write-Host "  referencia: $Muestra"
Write-Host "  salida:     $salida"
Write-Host ""
Write-Host "La primera vez carga el modelo (1-2 min sin avance visible). Despues va escena por escena." -ForegroundColor DarkGray
Write-Host ""

python scripts\run_pipeline.py @argumentos

if ($LASTEXITCODE -eq 0 -and (Test-Path $salida)) {
    Write-Host ""
    Write-Host "Listo: $salida" -ForegroundColor Green
    Write-Host "Si la voz no te convence, prueba variando:" -ForegroundColor DarkGray
    Write-Host "   .\prueba_voz.ps1 -Expresividad 0.7 -Apego 0.4" -ForegroundColor DarkGray
    Start-Process (Resolve-Path $salida)
} else {
    Write-Host ""
    Write-Host "Algo fallo. Copia el error completo y te digo que es." -ForegroundColor Red
}
