$ErrorActionPreference = "Stop"
$Python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Development environment not found. Run .\scripts\setup_dev.ps1 first."
}
& $Python (Join-Path $PSScriptRoot "..\app.py")
