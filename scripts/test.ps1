$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing .venv. Run scripts\setup_dev.ps1 first." }
& $python -m pytest (Join-Path $Root "tests") --cov=pdf_to_excel --cov-report=term-missing --cov-fail-under=85
