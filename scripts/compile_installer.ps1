param([Parameter(Mandatory)][string]$Version, [string]$IsccPath)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$candidates = @($IsccPath, $env:ISCC_PATH, "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { $_ }
$Compiler = $candidates | Where-Object { Test-Path $_ -PathType Leaf } | Select-Object -First 1
if (-not $Compiler) { throw "Inno Setup 6 ISCC.exe was not found. Install Inno Setup 6 or set ISCC_PATH/pass -IsccPath." }
$arguments = @("/DAppVersion=$Version")
if ($env:APP_PUBLISHER) { $arguments += "/DAppPublisher=$env:APP_PUBLISHER" }
$arguments += Join-Path $Root "installer\pdf_to_excel.iss"
& $Compiler @arguments
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed with exit code $LASTEXITCODE." }
