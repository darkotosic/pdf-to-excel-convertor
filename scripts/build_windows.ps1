param([switch]$Portable)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "build_release.ps1") -Portable:$Portable
