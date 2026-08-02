[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "release\install_hmi_realtime_adb.sh"
$scriptPath = (Resolve-Path $scriptPath).Path
$rawScript = Get-Content -LiteralPath $scriptPath -Raw

if (!$rawScript.Contains("pm install -r -d -t") -or !$rawScript.Contains("vn.fpt.dms.hmi")) {
    throw "Invalid HMI installer: $scriptPath"
}

Set-Clipboard -Value $rawScript
Write-Host "Copied raw CarSky ADB installer to clipboard:" -ForegroundColor Green
Write-Host $scriptPath
Write-Host "Open DMS Android ADB, press Ctrl+V once, then Enter."
