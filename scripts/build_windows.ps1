$ErrorActionPreference = "Stop"
python -m PyInstaller --noconfirm --clean --windowed --name PDF-to-Excel --paths src --collect-all pytesseract app.py
Write-Host "Build complete: dist/PDF-to-Excel"
