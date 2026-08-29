param([string]$Source)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $Source) {
    $candidates = @($env:TESSERACT_SOURCE, (Join-Path $env:ProgramFiles "Tesseract-OCR")) | Where-Object { $_ }
    $Source = $candidates | Where-Object { Test-Path (Join-Path $_ "tesseract.exe") } | Select-Object -First 1
}
if (-not $Source -or -not (Test-Path (Join-Path $Source "tesseract.exe"))) {
    throw "Trusted Tesseract source not found. Pass -Source 'C:\Program Files\Tesseract-OCR'."
}
$Destination = Join-Path $Root "vendor\tesseract"
$Readme = Join-Path $Destination "README.md"
$Temporary = Join-Path $Root "build\tesseract-prepared"
Remove-Item $Temporary -Recurse -Force -ErrorAction SilentlyContinue
New-Item $Temporary -ItemType Directory -Force | Out-Null
Copy-Item (Join-Path (Resolve-Path $Source).Path "*") $Temporary -Recurse -Force
foreach ($language in @("eng", "srp", "srp_latn", "osd")) {
    if (-not (Test-Path (Join-Path $Temporary "tessdata\$language.traineddata"))) {
        throw "Trusted source is incomplete: missing tessdata\$language.traineddata"
    }
}
& (Join-Path $Temporary "tesseract.exe") --version
if ($LASTEXITCODE -ne 0) { throw "Prepared tesseract.exe --version failed." }
$languages = & (Join-Path $Temporary "tesseract.exe") --list-langs
if ($LASTEXITCODE -ne 0) { throw "Prepared tesseract.exe --list-langs failed." }
foreach ($language in @("eng", "srp", "srp_latn", "osd")) {
    if ($languages -notcontains $language) { throw "Prepared runtime does not report language: $language" }
}
Get-ChildItem $Destination -Force -ErrorAction SilentlyContinue | Where-Object Name -ne "README.md" | Remove-Item -Recurse -Force
Copy-Item (Join-Path $Temporary "*") $Destination -Recurse -Force
if (Test-Path $Readme) { Write-Verbose "Preserved bundle documentation." }
Write-Host "Prepared and verified Tesseract bundle: $Destination"
