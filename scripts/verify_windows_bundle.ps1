param([string]$BundlePath)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $BundlePath) { $BundlePath = Join-Path $Root "dist\PDF-to-Excel" }
$BundlePath = (Resolve-Path $BundlePath).Path
$Application = Join-Path $BundlePath "PDF-to-Excel.exe"
if (-not (Test-Path $Application)) { throw "Packaged application missing: $Application" }
$Tesseract = Get-ChildItem $BundlePath -Filter tesseract.exe -Recurse | Where-Object FullName -Like "*vendor*tesseract*tesseract.exe" | Select-Object -First 1
if (-not $Tesseract) { throw "Packaged vendor/tesseract/tesseract.exe is missing." }
& (Join-Path $PSScriptRoot "verify_tesseract.ps1") -Source $Tesseract.FullName
$nativePatterns = @("*Qt6Core*", "*cv2*", "*fitz*")
foreach ($pattern in $nativePatterns) {
    if (-not (Get-ChildItem $BundlePath -Filter $pattern -Recurse | Select-Object -First 1)) { throw "Native bundle component missing: $pattern" }
}
$UnicodeDirectory = Join-Path $env:TEMP "PDF Excel čćžšđ ћирилица"
New-Item $UnicodeDirectory -ItemType Directory -Force | Out-Null
$Report = Join-Path $UnicodeDirectory "self-test.json"
$process = Start-Process $Application -ArgumentList @("--self-test", "--output", $Report) -PassThru
try {
    if (-not $process.WaitForExit(120000)) { throw "Packaged self-test timed out." }
    if ($process.ExitCode -ne 0) { throw "Packaged self-test failed with exit code $($process.ExitCode)." }
    $result = Get-Content $Report -Raw | ConvertFrom-Json
    if (-not $result.success -or -not $result.frozen) { throw "Packaged self-test report indicates failure: $Report" }
} finally {
    if (-not $process.HasExited) { Stop-Process $process -Force }
}
$smoke = Start-Process $Application -PassThru
try {
    Start-Sleep -Seconds 5
    if ($smoke.HasExited -and $smoke.ExitCode -ne 0) { throw "GUI smoke test exited with code $($smoke.ExitCode)." }
} finally {
    if (-not $smoke.HasExited) { Stop-Process $smoke -Force }
}
Write-Host "Verified packaged application: $BundlePath"
