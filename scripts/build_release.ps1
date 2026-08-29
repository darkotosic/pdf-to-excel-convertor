param([switch]$Portable, [string]$IsccPath)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $IsWindows -or $env:PROCESSOR_ARCHITECTURE -ne "AMD64") { throw "Release builds require Windows 10/11 x64 architecture." }
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Missing repository .venv. Run scripts\setup_dev.ps1 first." }
$architecture = & $Python -c "import platform,struct; print(f'{platform.python_version()}|{struct.calcsize(chr(80))*8}')"
if ($architecture -notmatch '^3\.12\..*\|64$') { throw "Python 3.12 x64 is required; detected $architecture." }
$Version = & $Python -c "import tomllib,pathlib; print(tomllib.loads(pathlib.Path(r'$Root\pyproject.toml').read_text(encoding='utf-8'))['project']['version'])"
if (-not $Version) { throw "Unable to read project.version from pyproject.toml." }
Push-Location $Root
try {
    Remove-Item build, dist, release -Recurse -Force -ErrorAction SilentlyContinue
    New-Item build, release -ItemType Directory -Force | Out-Null
    & $Python -m pip install --requirement requirements-windows.lock
    & (Join-Path $PSScriptRoot "quality_gate.ps1")
    & (Join-Path $PSScriptRoot "verify_tesseract.ps1") -Vendored
    $VersionFile = Join-Path $Root "build\windows-version.txt"
    $Company = if ($env:APP_COMPANY) { $env:APP_COMPANY } else { "" }
    $Copyright = if ($env:APP_COPYRIGHT) { $env:APP_COPYRIGHT } else { "" }
    & $Python scripts\generate_version_info.py --pyproject pyproject.toml --output $VersionFile --company $Company --copyright $Copyright
    $env:PDF_TO_EXCEL_VERSION_FILE = $VersionFile
    if (-not (Test-Path assets\app.ico)) { Write-Warning "assets/app.ico is absent; artifacts will use the default application icon." }
    & $Python -m PyInstaller --noconfirm --clean packaging\pdf_to_excel.spec
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path dist\PDF-to-Excel\PDF-to-Excel.exe)) { throw "PyInstaller did not create PDF-to-Excel.exe." }
    & scripts\verify_windows_bundle.ps1
    $signing = $env:SIGNTOOL_PATH -and $env:WINDOWS_CERTIFICATE -and $env:TIMESTAMP_URL
    function Sign-Artifact([string]$Path) {
        & $env:SIGNTOOL_PATH sign /sha1 $env:WINDOWS_CERTIFICATE /fd SHA256 /tr $env:TIMESTAMP_URL /td SHA256 $Path
        if ($LASTEXITCODE -ne 0) { throw "Signing failed: $Path" }
        & $env:SIGNTOOL_PATH verify /pa $Path
        if ($LASTEXITCODE -ne 0) { throw "Signature verification failed: $Path" }
    }
    if ($signing) { Sign-Artifact (Join-Path $Root "dist\PDF-to-Excel\PDF-to-Excel.exe") }
    else { Write-Warning "release artifacts are unsigned." }
    & scripts\compile_installer.ps1 -Version $Version -IsccPath $IsccPath
    $Installer = Join-Path $Root "release\PDF-to-Excel-Setup-$Version-x64.exe"
    if (-not (Test-Path $Installer)) { throw "Expected installer was not produced: $Installer" }
    if ($signing) { Sign-Artifact $Installer }
    $Zip = Join-Path $Root "release\PDF-to-Excel-$Version-x64.zip"
    Compress-Archive -Path dist\PDF-to-Excel\* -DestinationPath $Zip
    if ($Portable) { & scripts\build_portable.ps1 -Version $Version }
    $artifacts = Get-ChildItem release -File | Where-Object Name -ne "SHA256SUMS.txt"
    $checksums = foreach ($artifact in $artifacts) { $hash = Get-FileHash $artifact -Algorithm SHA256; "$($hash.Hash)  $($artifact.Name)" }
    $checksums | Set-Content release\SHA256SUMS.txt -Encoding ascii
    Write-Host "`nRELEASE SUCCESS`n`nVersion: $Version`n`nArtifacts:"
    Get-ChildItem release -File | ForEach-Object { Write-Host "release\$($_.Name)" }
} finally { Pop-Location }
