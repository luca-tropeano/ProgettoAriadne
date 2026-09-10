# Ariadne — Prepara il DB dimostrativo e avvia la Web UI per la presentazione.
# Uso:  powershell -ExecutionPolicy Bypass -File run_demo.ps1
# La prima esecuzione importa 2 BOM reali (71 + 160 componenti) + materiali MDF
# (JSON campione + dichiarazione IPC-1752 Class D in XML + PDF Material Declaration
# ZVEI). Il sourcing MDF è AUTOMATICO all'import (MDF_AUTO=true di default):
# le Material Composition Declaration per-famiglia (MCD-Ceramic.pdf, KEMET/YAGEO
# MLCC) vengono linkate alle BOMEntry, e le BOMEntry non coperti vengono annotate
# con la pagina di conformità del produttore. (+ IBOM Oric se presente in Downloads)
# Poi avvia la Web UI su http://127.0.0.1:5000

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$env:DATABASE_URL = "sqlite:///demo.db"
$env:MONGO_URI = "mongodb://127.0.0.1:1"   # Mongo offline -> graceful degradation, demo pienamente offline
$env:MDF_AUTO = "true"                    # sourcing MDF automatico all'import BOM (default)

if (-not (Test-Path "demo.db")) {
    Write-Host "=== Prepariamo il DB dimostrativo (prime installazione) ===" -ForegroundColor Cyan
    python -m ariadne.main process "test_data/inkplate5_bom.csv" --brand "e-radionica" --model "Inkplate 5" --manufacturer "e-radionica"
    python -m ariadne.main process "test_data/hiltop_motherboard.ods" --brand "Devtank" --model "HILTOP Motherboard Rev D"
    # Il sourcing MDF automatico (MDF_AUTO=true) ha già linkato i KEMET/YAGEO
    # MLCC del HILTOP da MCD-Ceramic.pdf e annotato i riferimenti di conformità.
    # I passi seguenti mostrano la pipeline MDF manuale con altri formati:
    Write-Host "=== MDF sample (materials) ===" -ForegroundColor Cyan
    python -m ariadne.main mdf-ingest "test_data/mdf_sample.json"
    # MDF IPC-1752 Class D (XML): dichiarazione materiale omogeneo dello
    #   MLCC 2.2uF Murata — il part number matcha la BOM Inkplate (C14/C15)
    Write-Host "=== MDF IPC-1752A/B Class D (XML) ===" -ForegroundColor Cyan
    python -m ariadne.main mdf-ingest "test_data/mdf_class_d_sample.xml"
    # MDF PDF (Material Declaration ZVEI): 4 sostanze dichiarate (nessun part
    #   number nel file → materials inseriti, warning "non collegati")
    Write-Host "=== MDF PDF (dichiarazione materiale ZVEI) ===" -ForegroundColor Cyan
    python -m ariadne.main mdf-ingest "test_data/mdf_zvei_mlcc_example.pdf"
    # BONUS: se il file IBOM KiCad di Oric è presente, lo importa (demo formato HTML)
    $oric = Join-Path $env:USERPROFILE "Downloads\Oric-Remix-Issue_A_v1_2_ibom.html"
    if (Test-Path $oric) {
        Write-Host "=== Import IBOM Oric (.html) ===" -ForegroundColor Cyan
        python -m ariadne.main process $oric --brand "Oric" --model "Oric Remix Issue A v1.2"
    }
    Write-Host "=== DB pronto ===" -ForegroundColor Green
}

Write-Host "=== Avvio Web UI su http://127.0.0.1:5000 ===" -ForegroundColor Cyan
python -m ariadne.web
