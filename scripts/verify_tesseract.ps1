param([string]$Source, [switch]$Vendored)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($Vendored) { $Executable = Join-Path $Root "vendor\tesseract\tesseract.exe" }
elseif ($Source) {
    $Executable = if (Test-Path $Source -PathType Container) { Join-Path $Source "tesseract.exe" } else { $Source }
} else { $Executable = (Get-Command tesseract -ErrorAction Stop).Source }
if (-not (Test-Path $Executable -PathType Leaf)) { throw "Tesseract executable not found: $Executable" }
$version = & $Executable --version | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw "tesseract --version failed: $Executable" }
$languages = & $Executable --list-langs
if ($LASTEXITCODE -ne 0) { throw "tesseract --list-langs failed: $Executable" }
foreach ($language in @("eng", "srp", "srp_latn", "osd")) {
    if ($languages -notcontains $language) { throw "Missing Tesseract language '$language' in $Executable" }
}
Write-Host "Tesseract version: $version"
Write-Host "Executable path: $Executable"
Write-Host "Tesseract and required languages are available."
