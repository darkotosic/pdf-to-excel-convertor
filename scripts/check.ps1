$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing .venv. Run scripts\setup_dev.ps1 first." }
& $python -m ruff check .
& $python -m ruff format --check .
& $python -m mypy src
