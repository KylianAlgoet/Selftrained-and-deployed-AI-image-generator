<#
.SYNOPSIS
    Start the DeckForge AI demo: one API worker and the frontend.

.DESCRIPTION
    Runs preflight, then starts exactly two processes and records their PIDs so
    `stop-demo.ps1` can stop what it started rather than killing processes by
    name.

    THE REFUSAL IS THE POINT. If port 8000 is already held, this script stops
    instead of starting a second API process. `config.assert_single_worker`
    cannot catch that case - nothing inside one process can see another - and
    two resident pipelines do not fit in 8 GB. The failure mode without this
    check is a CUDA OOM in whichever request happens to be running, which is an
    awful way to discover a duplicated terminal mid-demonstration.

    `--workers 1` and no `--reload`, both correctness requirements rather than
    preferences: the busy lock is process-local, and the reloader runs a second
    process that would hold the same GPU.

    THE MODEL IS NOT LOADED HERE. The pipeline loads lazily on the first
    generation request, so starting the demo costs no GPU memory and runs no
    generation. Expect the first generation to take about 30 s and later ones
    about 13 s.

.PARAMETER SkipPreflight
    Start without running preflight. Not recommended before a demonstration.

.PARAMETER Preview
    Serve the built frontend (`npm run preview`, port 4173) instead of the dev
    server (port 5173). Closer to what ships; requires a build first.

.EXAMPLE
    .\scripts\start-demo.ps1
    .\scripts\stop-demo.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipPreflight,
    [switch]$Preview
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $repoRoot '.run'
$pidFile = Join-Path $runDir 'demo.json'

# --- refuse a duplicate API process ------------------------------------------

$held = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($held) {
    $owner = Get-Process -Id $held[0].OwningProcess -ErrorAction SilentlyContinue
    Write-Host ""
    Write-Host "REFUSING TO START." -ForegroundColor Red
    Write-Host "Port 8000 is already held by pid $($held[0].OwningProcess) ($($owner.ProcessName))."
    Write-Host ""
    Write-Host "DeckForge AI supports exactly ONE API process. A second resident pipeline does"
    Write-Host "not fit - the stack leaves about 200 MiB spare on an 8 GB device (EXP-034) - and"
    Write-Host "the single-flight lock is process-local, so it would not span both."
    Write-Host ""
    Write-Host "Stop the existing one first:  .\scripts\stop-demo.ps1"
    exit 1
}

if (Test-Path $pidFile) {
    Write-Host "A previous run file exists at .run\demo.json." -ForegroundColor Yellow
    Write-Host "Run .\scripts\stop-demo.ps1 first, or delete it if those processes are gone."
    exit 1
}

# --- preflight ----------------------------------------------------------------

if (-not $SkipPreflight) {
    & (Join-Path $PSScriptRoot 'preflight.ps1')
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Preflight failed - not starting." -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path $runDir)) { New-Item -ItemType Directory -Force -Path $runDir | Out-Null }

# --- API ----------------------------------------------------------------------

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
Write-Host ""
Write-Host "Starting the API (one worker, no reload)..." -ForegroundColor Cyan

$api = Start-Process -FilePath $python `
    -ArgumentList @('-m', 'uvicorn', 'apps.api.main:app',
                    '--host', '127.0.0.1', '--port', '8000', '--workers', '1') `
    -WorkingDirectory $repoRoot -PassThru

# --- wait for health ----------------------------------------------------------

$healthy = $false
foreach ($attempt in 1..40) {
    Start-Sleep -Milliseconds 500
    try {
        $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
        if ($response.status -eq 'ok') {
            $healthy = $true
            Write-Host ("API ready - pid {0}, cuda {1}, guard {2}" -f `
                $response.pid, $response.cuda_available, $response.single_worker_guard) -ForegroundColor Green
            break
        }
    }
    catch { }
    if ($api.HasExited) {
        Write-Host "The API process exited during startup (exit code $($api.ExitCode))." -ForegroundColor Red
        exit 1
    }
}

if (-not $healthy) {
    Write-Host "The API did not become healthy within 20 seconds." -ForegroundColor Red
    Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# --- frontend -----------------------------------------------------------------

$webDir = Join-Path $repoRoot 'apps\web'
$npmCommand = if ($Preview) { 'preview' } else { 'dev' }
$url = if ($Preview) { 'http://localhost:4173' } else { 'http://localhost:5173' }

Write-Host "Starting the frontend (npm run $npmCommand)..." -ForegroundColor Cyan
$web = Start-Process -FilePath 'cmd.exe' `
    -ArgumentList @('/c', 'npm', 'run', $npmCommand) `
    -WorkingDirectory $webDir -PassThru

Start-Sleep -Seconds 3
if ($web.HasExited) {
    Write-Host "The frontend process exited during startup." -ForegroundColor Red
    Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

@{
    api_pid   = $api.Id
    web_pid   = $web.Id
    url       = $url
    started   = (Get-Date -Format 'o')
} | ConvertTo-Json | Set-Content -Path $pidFile -Encoding utf8

Write-Host ""
Write-Host "  DeckForge AI is running at $url" -ForegroundColor Green
Write-Host ""
Write-Host "  API pid $($api.Id) - frontend pid $($web.Id) - recorded in .run\demo.json"
Write-Host "  The model loads on the FIRST generation (~30 s); later ones take ~13 s."
Write-Host "  Stop with: .\scripts\stop-demo.ps1"
Write-Host ""
exit 0
