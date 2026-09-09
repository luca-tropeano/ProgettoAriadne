# Ariadne — Prepara il DB dimostrativo e avvia la Web UI per la presentazione.
# Uso:  powershell -ExecutionPolicy Bypass -File run_demo.ps1
# La prima esecuzione importa 2 BOM reali (71 + 160 componenti) in demo.db,
# poi avvia la Web UI su http://127.0.0.1:5000

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$env:DATABASE_URL = "sqlite:///demo.db"
$env:MONGO_URI = "mongodb://127.0.0.1:1"   # Mongo offline -> graceful degradation, demo pienamente offline

if (-not (Test-Path "demo.db")) {
    Write-Host "=== Prepariamo il DB dimostrativo (prime installazione) ===" -ForegroundColor Cyan
    python -m ariadne.main process "test_data/inkplate5_bom.csv" --brand "e-radionica" --model "Inkplate 5" --manufacturer "e-radionica"
    python -m ariadne.main process "test_data/hiltop_motherboard.ods" --brand "Devtank" --model "HILTOP Motherboard Rev D"
    Write-Host "=== DB pronto ===" -ForegroundColor Green
}

Write-Host "=== Avvio Web UI su http://127.0.0.1:5000 ===" -ForegroundColor Cyan
python -m ariadne.web
