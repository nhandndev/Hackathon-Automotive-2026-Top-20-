[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TripDir,
    [int]$Camera = 0,
    [string]$DriverId,
    [int]$MaxFrames = 0,
    [switch]$NoDisplay,
    [switch]$OpenDashboard,
    [switch]$SkipFrontend,
    [switch]$SkipCarSkyPreflight
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$productRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$aiRoot = Join-Path $productRoot "AI"
$beRoot = Join-Path $productRoot "SE\BE"
$feRoot = Join-Path $productRoot "SE\FE"
$aiScript = Join-Path $aiRoot "scripts\end_to_end_demo.py"
$carSkyScript = Join-Path $beRoot "scripts\carsky_phase05.py"
$beEnvFile = Join-Path $beRoot ".env"
$tripPath = (Resolve-Path $TripDir).Path
$tripName = Split-Path $tripPath -Leaf
$runStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = Join-Path $aiRoot "artifacts\runtime_logs\$runStamp"
$predictionDir = Join-Path $aiRoot "artifacts\predictions"
$eventDir = Join-Path $aiRoot "artifacts\decision_events"

$backendProcess = $null
$frontendProcess = $null
$ownsBackend = $false
$ownsFrontend = $false
$exitCode = 1

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Http([string]$Url) {
    try {
        $null = Invoke-RestMethod -Uri $Url -TimeoutSec 2
        return $true
    }
    catch { return $false }
}

function Wait-Http(
    [string]$Url,
    [string]$ServiceName,
    [System.Diagnostics.Process]$Process,
    [int]$TimeoutSeconds = 45
) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Http $Url) {
            Write-Host "$ServiceName ready: $Url" -ForegroundColor Green
            return
        }
        if (($null -ne $Process) -and $Process.HasExited) {
            throw "$ServiceName exited before becoming ready. See $logDir"
        }
        Start-Sleep -Milliseconds 500
    }
    throw "Timed out waiting for $ServiceName at $Url. See $logDir"
}

function Read-DotEnv([string]$Path) {
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (!$trimmed -or $trimmed.StartsWith("#") -or !$trimmed.Contains("=")) { continue }
        $pair = $trimmed.Split("=", 2)
        $values[$pair[0].Trim()] = $pair[1].Trim().Trim('"').Trim("'")
    }
    return $values
}

function Show-LogTail([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        Write-Host "`n--- $(Split-Path $Path -Leaf) ---" -ForegroundColor Yellow
        Get-Content -LiteralPath $Path -Tail 35
    }
}

try {
    Write-Step "Preflight local environment"
    if ($env:CONDA_DEFAULT_ENV -ne "automotive") {
        throw "Activate the expected environment first: conda activate automotive"
    }

    $pythonExe = (Get-Command python -ErrorAction Stop).Source
    Write-Host "Python: $pythonExe"
    & $pythonExe -c "import cv2, fastapi, httpx, onnxruntime, pydantic_settings, sklearn, torch, ultralytics, uvicorn, yaml; assert hasattr(cv2, 'STEREO_SGBM_MODE_SGBM_3WAY'); print('Python dependencies: OK')"
    if ($LASTEXITCODE -ne 0) { throw "Python dependency check failed in conda environment automotive." }

    foreach ($requiredPath in @($aiScript, $carSkyScript, $beEnvFile)) {
        if (!(Test-Path -LiteralPath $requiredPath)) { throw "Required path is missing: $requiredPath" }
    }
    New-Item -ItemType Directory -Force -Path $logDir, $predictionDir, $eventDir | Out-Null

    if (!$SkipCarSkyPreflight) {
        Write-Step "Preflight CarSky cloud deployment"
        $beEnv = Read-DotEnv $beEnvFile
        if ($beEnv["CARSKY_ENABLED"] -ne "true" -or $beEnv["CARSKY_MODE"] -ne "external") {
            throw "SE/BE/.env must set CARSKY_ENABLED=true and CARSKY_MODE=external."
        }
        foreach ($key in @("CARSKY_BASE_URL", "CARSKY_API_KEY", "CARSKY_ROOM_ID", "CARSKY_NODE_KEY")) {
            if (!$beEnv[$key]) { throw "SE/BE/.env is missing $key." }
        }
        Push-Location $beRoot
        try {
            & $pythonExe $carSkyScript status
            if ($LASTEXITCODE -ne 0) { throw "CarSky deployment status check failed." }
            & $pythonExe $carSkyScript nodes
            if ($LASTEXITCODE -ne 0) { throw "CarSky node check failed." }
            Write-Host "CarSky deployment and nodes: OK" -ForegroundColor Green
        }
        finally { Pop-Location }
    }
    else {
        Write-Warning "CarSky preflight skipped. Publishing still follows SE/BE/.env."
    }

    $backendHealth = "http://127.0.0.1:8000/health"
    if (Test-Http $backendHealth) {
        Write-Host "Backend already running; reusing it." -ForegroundColor Yellow
    }
    else {
        Write-Step "Start SE Backend"
        $backendStdout = Join-Path $logDir "backend.stdout.log"
        $backendStderr = Join-Path $logDir "backend.stderr.log"
        $backendProcess = Start-Process -FilePath $pythonExe `
            -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
            -WorkingDirectory $beRoot -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $backendStdout -RedirectStandardError $backendStderr
        $ownsBackend = $true
        Wait-Http $backendHealth "SE Backend" $backendProcess
    }

    if (!$SkipFrontend) {
        $frontendHealth = "http://127.0.0.1:3000/api/health"
        if (Test-Http $frontendHealth) {
            Write-Host "Fleet Dashboard already running; reusing it." -ForegroundColor Yellow
        }
        else {
            Write-Step "Start Fleet Dashboard"
            $nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
            if ($null -eq $nodeCommand) { $nodeCommand = Get-Command node -ErrorAction Stop }
            if (!(Test-Path -LiteralPath (Join-Path $feRoot "node_modules"))) {
                throw "Frontend dependencies are missing. Run npm install once in $feRoot"
            }
            $tsxCli = Join-Path $feRoot "node_modules\tsx\dist\cli.mjs"
            if (!(Test-Path -LiteralPath $tsxCli)) {
                throw "Frontend runtime is missing: $tsxCli. Run npm install once in $feRoot"
            }
            $frontendStdout = Join-Path $logDir "frontend.stdout.log"
            $frontendStderr = Join-Path $logDir "frontend.stderr.log"
            $oldPort = $env:PORT
            $oldWsUrl = $env:VITE_ALERTS_WS_URL
            $env:PORT = "3000"
            $env:VITE_ALERTS_WS_URL = "ws://127.0.0.1:8000/api/v1/alerts/live"
            try {
                $frontendProcess = Start-Process -FilePath $nodeCommand.Source `
                    -ArgumentList @($tsxCli, "server.ts") -WorkingDirectory $feRoot `
                    -WindowStyle Hidden -PassThru `
                    -RedirectStandardOutput $frontendStdout -RedirectStandardError $frontendStderr
            }
            finally {
                $env:PORT = $oldPort
                $env:VITE_ALERTS_WS_URL = $oldWsUrl
            }
            $ownsFrontend = $true
            Wait-Http $frontendHealth "Fleet Dashboard" $frontendProcess 60
        }
        Write-Host "Fleet Dashboard: http://127.0.0.1:3000" -ForegroundColor Green
        if ($OpenDashboard) { Start-Process "http://127.0.0.1:3000" }
    }

    Write-Host "Backend API docs: http://127.0.0.1:8000/docs"
    Write-Host "Recent events:    http://127.0.0.1:8000/api/v1/alerts/recent"
    Write-Step "Run AI pipeline: BTC road cameras + live driver webcam"

    $outputCsv = Join-Path $predictionDir "$tripName-live-$runStamp.csv"
    $eventFile = Join-Path $eventDir "$tripName-live-$runStamp.events.jsonl"
    $aiArguments = @(
        $aiScript,
        "--trip-dir", $tripPath,
        "--camera", "$Camera",
        "--se-endpoint", "http://127.0.0.1:8000/api/v1/alerts",
        "--output-csv", $outputCsv,
        "--events", $eventFile
    )
    if ($DriverId) { $aiArguments += @("--driver-id", $DriverId) }
    if ($MaxFrames -gt 0) { $aiArguments += @("--max-frames", "$MaxFrames") }
    if ($NoDisplay) { $aiArguments += "--no-display" }

    Write-Host "Press Q or Esc in the AI window to stop." -ForegroundColor Yellow
    Push-Location $productRoot
    try {
        & $pythonExe @aiArguments
        $exitCode = $LASTEXITCODE
    }
    finally { Pop-Location }
    if ($exitCode -ne 0) { throw "AI pipeline exited with code $exitCode." }

    Write-Host "`nDemo completed." -ForegroundColor Green
    Write-Host "Prediction CSV: $outputCsv"
    Write-Host "Decision events: $eventFile"
    Write-Host "Runtime logs:    $logDir"
}
catch {
    Write-Host "`nPRODUCT DEMO FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Show-LogTail (Join-Path $logDir "backend.stderr.log")
    Show-LogTail (Join-Path $logDir "frontend.stderr.log")
    $exitCode = 1
}
finally {
    Write-Step "Stop services started by this runner"
    if ($ownsFrontend -and $null -ne $frontendProcess -and !$frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Fleet Dashboard stopped."
    }
    if ($ownsBackend -and $null -ne $backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "SE Backend stopped."
    }
}

exit $exitCode
