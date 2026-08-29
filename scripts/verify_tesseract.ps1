$ErrorActionPreference = "Stop"
$tesseract = Get-Command tesseract -ErrorAction Stop
$version = & $tesseract.Source --version | Select-Object -First 1
$languages = & $tesseract.Source --list-langs
foreach ($language in @("srp", "srp_latn", "eng", "osd")) {
    if ($languages -notcontains $language) { throw "Missing Tesseract language: $language" }
}
Write-Host "Tesseract version: $version"
Write-Host "Executable path: $($tesseract.Source)"
Write-Host "Tessdata path: $env:TESSDATA_PREFIX"
Write-Host "Tesseract and required languages are available."
