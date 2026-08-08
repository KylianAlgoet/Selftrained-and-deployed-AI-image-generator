<#
.SYNOPSIS
    Check everything the demo needs BEFORE anything is started.

.DESCRIPTION
    Every check here is one that has actually cost time on this project, or one
    whose failure mode is confusing rather than obvious:

      - the wrong Python (3.14 is the default `py` version and PyTorch does not
        support it; the venv must be 3.11);
      - Node below 20.19, which the frontend toolchain needs;
      - node_modules missing, which produces a build error that reads like a
        code error;
      - port 8000 already held, which is how you end up with TWO API processes
        competing for one 8 GB device - the in-process worker guard CANNOT
        detect that, because nothing inside one process can;
      - a worker-count environment variable above 1, which the service refuses
        at startup and which is better caught here with an explanation;
      - missing or corrupted adapters, which otherwise surface as a 503 mid-demo.

    NOTHING HERE TOUCHES THE GPU. No model is loaded and no generation runs.
    `nvidia-smi` is queried for presence and driver only.

.PARAMETER SkipWeights
    Skip the SHA-256 checkpoint verification (it reads ~19 MB and hashes it).
    Use only when weights are known good and you want a fast port/tooling check.

.EXAMPLE
    .\scripts\preflight.ps1

.OUTPUTS
    Exit code 0 if every check passes, 1 otherwise.
#>
[CmdletBinding()]
param(
    [switch]$SkipWeights
)

$ErrorActionPreference = 'Continue'
$repoRoot = Split-Path -Parent $PSScriptRoot

$script:Failures = 0
$script:Warnings = 0

function Report {
    param(
        [ValidateSet('PASS', 'FAIL', 'WARN')][string]$Status,
        [string]$Check,
        [string]$Detail
    )
    $colour = switch ($Status) { 'PASS' { 'Green' } 'FAIL' { 'Red' } 'WARN' { 'Yellow' } }
    Write-Host ("{0,-5} {1,-28} {2}" -f $Status, $Check, $Detail) -ForegroundColor $colour
    if ($Status -eq 'FAIL') { $script:Failures++ }
    if ($Status -eq 'WARN') { $script:Warnings++ }
}

Write-Host ""
Write-Host "DeckForge AI - preflight" -ForegroundColor Cyan
Write-Host "repository: $repoRoot"
Write-Host ""

# --- Python -------------------------------------------------------------------

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (Test-Path $python) {
    $pyVersion = (& $python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
    if ($pyVersion -like '3.11.*') {
        Report PASS 'Python virtual env' "3.11 at .venv ($pyVersion)"
    }
    else {
        Report FAIL 'Python virtual env' "found $pyVersion, requires 3.11 - PyTorch has no 3.14 wheels"
    }
}
else {
    Report FAIL 'Python virtual env' 'missing - create with: py -V:3.11 -m venv .venv'
}

# --- The imports that actually matter ----------------------------------------

if (Test-Path $python) {
    $probe = & $python -c @"
import json, sys
sys.path.insert(0, r'$repoRoot')
result = {}
try:
    import torch
    result['torch'] = torch.__version__
    result['cuda'] = bool(torch.cuda.is_available())
    result['device'] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
except Exception as err:
    result['error'] = str(err)
try:
    import fastapi, diffusers
    result['fastapi'] = fastapi.__version__
    result['diffusers'] = diffusers.__version__
except Exception as err:
    result.setdefault('error', str(err))
print(json.dumps(result))
"@ 2>$null

    if ($probe) {
        $info = $probe | ConvertFrom-Json
        if ($info.error) {
            Report FAIL 'Python dependencies' $info.error
        }
        else {
            Report PASS 'Python dependencies' "torch $($info.torch), diffusers $($info.diffusers), fastapi $($info.fastapi)"
            if ($info.cuda) {
                Report PASS 'CUDA' "available - $($info.device)"
            }
            else {
                Report FAIL 'CUDA' 'torch.cuda.is_available() is False - generation cannot run'
            }
        }
    }
    else {
        Report FAIL 'Python dependencies' 'could not import torch/diffusers/fastapi'
    }
}

# --- GPU ----------------------------------------------------------------------

$smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($smi) {
    $gpu = (& nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader) -join '; '
    Report PASS 'nvidia-smi' $gpu
}
else {
    Report FAIL 'nvidia-smi' 'not on PATH - no NVIDIA driver tooling found'
}

# --- Node ---------------------------------------------------------------------

$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVersion = (& node -v).TrimStart('v')
    $major = [int]($nodeVersion.Split('.')[0])
    $minor = [int]($nodeVersion.Split('.')[1])
    if ($major -gt 20 -or ($major -eq 20 -and $minor -ge 19)) {
        Report PASS 'Node.js' "v$nodeVersion"
    }
    else {
        Report FAIL 'Node.js' "v$nodeVersion is below the required 20.19"
    }
}
else {
    Report FAIL 'Node.js' 'not on PATH'
}

if (Test-Path (Join-Path $repoRoot 'apps\web\node_modules')) {
    Report PASS 'Frontend dependencies' 'apps/web/node_modules present'
}
else {
    Report FAIL 'Frontend dependencies' 'missing - run: cd apps/web; npm ci'
}

# --- Ports --------------------------------------------------------------------
#
# THE CHECK THAT MATTERS MOST. `config.assert_single_worker` rejects a
# multi-worker configuration, but it cannot see a second API process someone
# started in another terminal - nothing inside one process can. Two resident
# pipelines do not fit in 8 GB, and the first symptom would be an OOM in
# whichever request happened to be running.

foreach ($port in @(8000, 5173, 4173)) {
    $inUse = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    $label = switch ($port) { 8000 { 'API port 8000' } 5173 { 'Frontend port 5173' } 4173 { 'Preview port 4173' } }
    if ($inUse) {
        $owner = (Get-Process -Id $inUse[0].OwningProcess -ErrorAction SilentlyContinue)
        $detail = "IN USE by pid $($inUse[0].OwningProcess) ($($owner.ProcessName))"
        if ($port -eq 8000) {
            Report FAIL $label "$detail - a second API process would compete for the GPU"
        }
        else {
            Report WARN $label $detail
        }
    }
    else {
        Report PASS $label 'free'
    }
}

# --- Worker-count environment -------------------------------------------------

foreach ($name in @('WEB_CONCURRENCY', 'UVICORN_WORKERS', 'GUNICORN_WORKERS')) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if ($value -and [int]$value -gt 1) {
        Report FAIL "$name" "$value - the service supports exactly one worker (DR-011)"
    }
}

# --- Weights ------------------------------------------------------------------

if ($SkipWeights) {
    Report WARN 'Production weights' 'SKIPPED by -SkipWeights'
}
else {
    # 6> redirects the information stream: Write-Host does not go to stdout, so
    # `| Out-Null` would let the nested script's whole report through.
    & (Join-Path $PSScriptRoot 'verify-weights.ps1') 6>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Report PASS 'Production weights' 'all 3 adapters match their recorded sha256'
    }
    else {
        Report FAIL 'Production weights' 'verification failed - run scripts\verify-weights.ps1 for detail'
    }
}

# --- Verdict ------------------------------------------------------------------

Write-Host ""
if ($script:Failures -gt 0) {
    Write-Host "PREFLIGHT FAILED - $($script:Failures) blocking issue(s), $($script:Warnings) warning(s)." -ForegroundColor Red
    exit 1
}

if ($script:Warnings -gt 0) {
    Write-Host "PREFLIGHT PASSED with $($script:Warnings) warning(s)." -ForegroundColor Yellow
}
else {
    Write-Host "PREFLIGHT PASSED - the demo can start." -ForegroundColor Green
}
exit 0
