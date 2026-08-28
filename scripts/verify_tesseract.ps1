$ErrorActionPreference = "Stop"
$tesseract = Get-Command tesseract -ErrorAction Stop
$languages = & $tesseract.Source --list-langs
foreach ($language in @("srp", "srp_latn", "eng")) {
    if ($languages -notcontains $language) { throw "Missing Tesseract language: $language" }
}
Write-Host "Tesseract and required languages are available."
