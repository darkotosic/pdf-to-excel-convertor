$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing .venv. Run scripts\setup_dev.ps1 first." }
& $python -m ruff check $Root
& $python -m ruff format --check $Root
& $python -m mypy (Join-Path $Root "src")
