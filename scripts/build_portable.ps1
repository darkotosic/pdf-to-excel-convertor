param([string]$Version, [switch]$SkipVerification)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not $Version) {
    $Version = & $Python -c "import tomllib,pathlib; print(tomllib.loads(pathlib.Path(r'$Root\pyproject.toml').read_text(encoding='utf-8'))['project']['version'])"
}
$env:PDF_TO_EXCEL_VERSION_FILE = Join-Path $Root "build\windows-version.txt"
$Company = if ($env:APP_COMPANY) { $env:APP_COMPANY } else { "" }
$Copyright = if ($env:APP_COPYRIGHT) { $env:APP_COPYRIGHT } else { "" }
& $Python (Join-Path $Root "scripts\generate_version_info.py") --pyproject (Join-Path $Root "pyproject.toml") --output $env:PDF_TO_EXCEL_VERSION_FILE --company $Company --copyright $Copyright
& $Python -m PyInstaller --noconfirm --clean --distpath (Join-Path $Root "build\portable") (Join-Path $Root "packaging\pdf_to_excel_portable.spec")
if ($LASTEXITCODE -ne 0) { throw "Portable PyInstaller build failed." }
$Built = Join-Path $Root "build\portable\PDF-to-Excel-Portable.exe"
$Artifact = Join-Path $Root "release\PDF-to-Excel-Portable-$Version-x64.exe"
Copy-Item $Built $Artifact -Force
if (-not $SkipVerification) {
    $Report = Join-Path $env:TEMP "pdf-to-excel-portable-self-test.json"
    & $Artifact --self-test --output $Report
    if ($LASTEXITCODE -ne 0) { throw "Portable self-test failed." }
}
Write-Host "Portable artifact (onefile; temporary extraction and slower startup): $Artifact"
