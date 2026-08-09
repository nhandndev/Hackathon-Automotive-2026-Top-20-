[CmdletBinding()]
param(
    [ValidateSet("hybrid-live", "dataset-fleet")]
    [string]$Mode = "hybrid-live",
    [string]$TripDir,
    [string]$DataDir,
    [int]$Camera = 0,
    [string]$DriverId,
    [string]$DriverModel,
    [int]$MaxFrames = 0,
    [switch]$NoDisplay,
    [switch]$OpenDashboard,
    [switch]$SkipFrontend,
    [switch]$RequireCarSky,
    [switch]$SkipCarSkyPreflight
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$productRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$aiRoot = Join-Path $productRoot "AI"
$beRoot = Join-Path $productRoot "SE\BE"
$feRoot = Join-Path $productRoot "SE\FE"
$savedTripsDir = Join-Path $feRoot "src\data\saved_trips"
$aiScript = Join-Path $aiRoot "scripts\end_to_end_demo.py"
$fleetAiScript = Join-Path $aiRoot "scripts\dataset_fleet_demo.py"
$carSkyScript = Join-Path $beRoot "scripts\carsky_phase05.py"
$beEnvFile = Join-Path $beRoot ".env"
$tripPath = $null
$dataPath = $null
if ($Mode -eq "hybrid-live" -and $TripDir) {
    $tripPath = (Resolve-Path $TripDir).Path
}
if ($Mode -eq "dataset-fleet" -and $DataDir) {
    $dataPath = (Resolve-Path $DataDir).Path
}
$tripName = if ($tripPath) { Split-Path $tripPath -Leaf } else { "dataset-fleet" }
$runStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = Join-Path $aiRoot "artifacts\runtime_logs\$runStamp"
$predictionDir = Join-Path $aiRoot "artifacts\predictions"
$eventDir = Join-Path $aiRoot "artifacts\decision_events"
$driverModelPath = if ($DriverModel) {
    (Resolve-Path $DriverModel).Path
}
else {
    $null
}

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

function Test-BackendSnapshotContract {
    try {
        $schema = Invoke-RestMethod -Uri "http://127.0.0.1:8000/openapi.json" -TimeoutSec 2
        $props = $schema.components.schemas.LiveSnapshotPayload.properties
        return ($null -ne $props.safe_driving_score -and $null -ne $props.harsh_brake_count)
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

function Clear-SavedDemoTrips {
    $resolvedFeRoot = (Resolve-Path -LiteralPath $feRoot).Path
    if (!(Test-Path -LiteralPath $savedTripsDir)) { return }
    $resolvedSavedTripsDir = (Resolve-Path -LiteralPath $savedTripsDir).Path
    if (!$resolvedSavedTripsDir.StartsWith($resolvedFeRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-Warning "Skip saved trip cleanup because path is outside FE root: $resolvedSavedTripsDir"
        return
    }
    $jsonFiles = Get-ChildItem -LiteralPath $resolvedSavedTripsDir -Filter "*.json" -File -ErrorAction SilentlyContinue
    foreach ($file in $jsonFiles) {
        Remove-Item -LiteralPath $file.FullName -Force -ErrorAction SilentlyContinue
    }
    if ($jsonFiles.Count -gt 0) {
        Write-Host "Cleared saved demo trips: $($jsonFiles.Count) file(s)." -ForegroundColor DarkYellow
    }
}

try {
    Write-Step "Preflight local environment"
    if ($Mode -eq "hybrid-live" -and !$tripPath) {
        throw "Mode hybrid-live requires -TripDir."
    }
    if ($Mode -eq "dataset-fleet" -and !$dataPath) {
        throw "Mode dataset-fleet requires -DataDir."
    }
    $repoRoot = (Resolve-Path (Join-Path $productRoot "..")).Path
    $pythonCandidates = @(
        (Join-Path $repoRoot ".venv\Scripts\python.exe"),
        (Join-Path $productRoot ".venv\Scripts\python.exe")
    )
    $projectPython = $pythonCandidates |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
    if ($projectPython) {
        $pythonExe = $projectPython
    }
    else {
        $pythonExe = (Get-Command python -ErrorAction Stop).Source
    }
    Write-Host "Python: $pythonExe"
    & $pythonExe -c "import cv2, fastapi, httpx, onnxruntime, pydantic_settings, sklearn, torch, ultralytics, uvicorn, yaml; assert hasattr(cv2, 'STEREO_SGBM_MODE_SGBM_3WAY'); print('Python dependencies: OK')"
    if ($LASTEXITCODE -ne 0) { throw "Python dependency check failed in project .venv/current environment." }

    foreach ($requiredPath in @($aiScript, $fleetAiScript, $carSkyScript, $beEnvFile)) {
        if (!(Test-Path -LiteralPath $requiredPath)) { throw "Required path is missing: $requiredPath" }
    }
    if ($driverModelPath) {
        if (!(Test-Path -LiteralPath $driverModelPath)) {
            throw "DriverModel does not exist: $driverModelPath"
        }
        if ([System.IO.Path]::GetExtension($driverModelPath) -ne ".joblib") {
            throw "DriverModel must point to a .joblib artifact: $driverModelPath"
        }
        Write-Host "Driver model override: $driverModelPath"
    }
    else {
        Write-Host "Driver model: AI/configs/model_registry.yaml (production)"
    }
    New-Item -ItemType Directory -Force -Path $logDir, $predictionDir, $eventDir | Out-Null
    Write-Step "Clear saved demo trips before starting this run"
    Clear-SavedDemoTrips

    if (!$SkipCarSkyPreflight) {
        Write-Step "Preflight CarSky cloud deployment"
        $beEnv = Read-DotEnv $beEnvFile
        $carskyExternal = (
            $beEnv["CARSKY_ENABLED"] -eq "true" -and
            $beEnv["CARSKY_MODE"] -eq "external"
        )
        if (!$carskyExternal) {
            $message = "SE/BE/.env is not configured for CarSky external. Current: CARSKY_ENABLED=$($beEnv['CARSKY_ENABLED']), CARSKY_MODE=$($beEnv['CARSKY_MODE'])."
            if ($RequireCarSky) {
                throw "$message Set CARSKY_ENABLED=true and CARSKY_MODE=external, then fill CarSky credentials."
            }
            Write-Warning "$message Continue with local AI + SE Backend + Fleet Dashboard only. Add -RequireCarSky for full CarSky-gated demo."
        }
        else {
            foreach ($key in @("CARSKY_BASE_URL", "CARSKY_API_KEY", "CARSKY_ROOM_ID", "CARSKY_NODE_KEY")) {
                if (!$beEnv[$key]) {
                    if ($RequireCarSky) {
                        throw "SE/BE/.env is missing $key."
                    }
                    Write-Warning "SE/BE/.env is missing $key. Continue local dashboard demo without CarSky preflight."
                    $carskyExternal = $false
                    break
                }
            }
            if ($carskyExternal) {
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
        }
    }
    else {
        Write-Warning "CarSky preflight skipped. Publishing still follows SE/BE/.env."
    }

    $backendHealth = "http://127.0.0.1:8000/health"
    if (Test-Http $backendHealth) {
        if (!(Test-BackendSnapshotContract)) {
            throw "A stale SE Backend is already running on port 8000 and does not support the current AI snapshot contract. Stop that backend process, then rerun this script."
        }
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
    Write-Step $(if ($Mode -eq "dataset-fleet") {
        "Run AI pipeline: sequential BTC dataset fleet"
    } else {
        "Run AI pipeline: BTC road cameras + live driver webcam"
    })

    $outputCsv = Join-Path $predictionDir "$tripName-live-$runStamp.csv"
    $eventFile = Join-Path $eventDir "$tripName-live-$runStamp.events.jsonl"
    if ($Mode -eq "dataset-fleet") {
        $aiArguments = @(
            $fleetAiScript,
            "--data-dir", $dataPath,
            "--se-endpoint", "http://127.0.0.1:8000/api/v1/alerts",
            "--output-dir", (Join-Path $aiRoot "artifacts\fleet_demo\$runStamp"),
            "--runtime-mode", "fixed",
            "--road-interval-ms", "200",
            "--driver-interval-ms", "50",
            "--target-fps", "10",
            "--dashboard-stream-fps", "3",
            "--speed", "0.5"
        )
    }
    else {
        $aiArguments = @(
            $aiScript,
            "--trip-dir", $tripPath,
            "--driver-source", "webcam",
            "--camera", "$Camera",
            "--se-endpoint", "http://127.0.0.1:8000/api/v1/alerts",
            "--output-csv", $outputCsv,
            "--events", $eventFile,
            "--runtime-mode", "fixed",
            "--road-interval-ms", "200",
            "--driver-interval-ms", "50",
            "--target-fps", "10",
            "--dashboard-stream-fps", "3",
            "--speed", "0.5"
        )
        if ($DriverId) { $aiArguments += @("--driver-id", $DriverId) }
    }
    if ($driverModelPath) { $aiArguments += @("--driver-model", $driverModelPath) }
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
    if ($Mode -eq "dataset-fleet") {
        Write-Host "Fleet artifacts: $(Join-Path $aiRoot ('artifacts\fleet_demo\' + $runStamp))"
    }
    else {
        Write-Host "Prediction CSV: $outputCsv"
        Write-Host "Decision events: $eventFile"
    }
    Write-Host "Runtime logs:    $logDir"
    if ($Mode -eq "dataset-fleet" -and !$NoDisplay) {
        Write-Host "Dashboard is keeping all trip histories. Inspect them now." -ForegroundColor Cyan
        $null = Read-Host "Press Enter to stop Dashboard and Backend"
    }
}
catch {
    Write-Host "`nPRODUCT DEMO FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Show-LogTail (Join-Path $logDir "backend.stderr.log")
    Show-LogTail (Join-Path $logDir "frontend.stderr.log")
    $exitCode = 1
}
finally {
    Write-Step "Stop services started by this runner"
    Clear-SavedDemoTrips
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
