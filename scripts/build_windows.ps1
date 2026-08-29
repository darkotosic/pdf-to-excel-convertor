$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing .venv. Run scripts\setup_dev.ps1 first." }
& (Join-Path $PSScriptRoot "quality_gate.ps1")
& $python -m PyInstaller --noconfirm --clean --onedir --windowed --name PDF-to-Excel --paths src --collect-all pytesseract app.py
Write-Host "Build complete: dist/PDF-to-Excel"
