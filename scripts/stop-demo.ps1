<#
.SYNOPSIS
    Stop the demo processes this machine started, and confirm the ports are free.

.DESCRIPTION
    Stops ONLY the PIDs recorded in .run\demo.json by start-demo.ps1, plus their
    child processes. It deliberately does NOT kill by process name: `python.exe`
    and `node.exe` are not this project's to claim, and a stop script that
    killed every node process on a developer's machine would be a worse bug than
    the leak it was cleaning up.

    Verifying the ports afterwards matters as much as the stop itself. M7 closed
    by manually confirming both ports were released and no duplicate uvicorn
    remained; this turns that habit into a check.

.PARAMETER Force
    Also stop whatever holds ports 8000/5173/4173 when no run file exists - for
    recovering from a crashed session. Reports what it is about to stop.

.EXAMPLE
    .\scripts\stop-demo.ps1
    .\scripts\stop-demo.ps1 -Force
#>
[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = 'Continue'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot '.run\demo.json'

function Stop-Tree {
    param([int]$ProcessId, [string]$Label)

    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $process) {
        Write-Host ("  {0,-10} pid {1} was already gone" -f $Label, $ProcessId) -ForegroundColor Yellow
        return
    }

    # npm spawns vite as a child; stopping only the launcher would leave the
    # server holding its port.
    Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue |
        ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host ("  {0,-10} pid {1} stopped" -f $Label, $ProcessId) -ForegroundColor Green
}

Write-Host ""
Write-Host "DeckForge AI - stopping the demo" -ForegroundColor Cyan

if (Test-Path $pidFile) {
    $record = Get-Content $pidFile -Raw | ConvertFrom-Json
    Stop-Tree -ProcessId $record.api_pid -Label 'API'
    Stop-Tree -ProcessId $record.web_pid -Label 'frontend'
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}
elseif ($Force) {
    Write-Host "  no run file; -Force given, stopping whatever holds the demo ports" -ForegroundColor Yellow
    foreach ($port in @(8000, 5173, 4173)) {
        $held = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($connection in $held) {
            $owner = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
            Write-Host ("  port {0}: stopping pid {1} ({2})" -f $port, $connection.OwningProcess, $owner.ProcessName)
            Stop-Tree -ProcessId $connection.OwningProcess -Label "port$port"
        }
    }
}
else {
    Write-Host "  no .run\demo.json - nothing was started by start-demo.ps1" -ForegroundColor Yellow
    Write-Host "  use -Force to stop whatever is holding ports 8000/5173/4173"
}

# --- verify the ports actually came free -------------------------------------

Start-Sleep -Milliseconds 800
Write-Host ""
$stillHeld = 0
foreach ($port in @(8000, 5173, 4173)) {
    $held = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($held) {
        Write-Host ("  port {0,-5} STILL HELD by pid {1}" -f $port, $held[0].OwningProcess) -ForegroundColor Red
        $stillHeld++
    }
    else {
        Write-Host ("  port {0,-5} released" -f $port) -ForegroundColor Green
    }
}

Write-Host ""
if ($stillHeld -gt 0) {
    Write-Host "$stillHeld port(s) still held. Run with -Force, or stop them manually." -ForegroundColor Red
    exit 1
}

Write-Host "All demo ports released." -ForegroundColor Green
exit 0
