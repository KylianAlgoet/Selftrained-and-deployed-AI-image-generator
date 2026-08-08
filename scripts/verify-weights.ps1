<#
.SYNOPSIS
    Verify the three production LoRA adapters, and optionally restore them first.

.DESCRIPTION
    Presence, then exact byte size, then SHA-256 - the same order and the same
    expectations the running service applies in `styles.verify_checkpoint()`.

    The expected values are READ FROM apps/api/styles.py rather than duplicated
    here. Hard-coding them in a second place is how a manifest drifts from the
    code it describes, and this script would then happily certify a machine the
    service will refuse to serve from.

    Risk R14: these files cannot be regenerated. A failure here means restore
    the file again - never retrain, never "regenerate", never relax the check.

.PARAMETER RestoreFrom
    A backup directory to copy the adapters from before verifying. The tree
    underneath it must mirror the layout in docs/deployment/weights-manifest.md.
    Omit to verify what is already on disk.

.PARAMETER CheckpointRoot
    Where the `outputs/lora/...` tree lives. Defaults to the repository root,
    matching the service's own CHECKPOINT_ROOT default.

.EXAMPLE
    .\scripts\verify-weights.ps1
    .\scripts\verify-weights.ps1 -RestoreFrom "E:\DeckForge-weights-backup"

.OUTPUTS
    Exit code 0 if all three verify, 1 otherwise.
#>
[CmdletBinding()]
param(
    [string]$RestoreFrom,
    [string]$CheckpointRoot
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $CheckpointRoot) { $CheckpointRoot = $repoRoot }

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Host "FAIL  the Python 3.11 virtual environment is missing at .venv\Scripts\python.exe" -ForegroundColor Red
    Write-Host "      create it with: py -V:3.11 -m venv .venv"
    exit 1
}

# Ask the code what it expects. One source of truth, queried - not restated.
$expectedJson = & $python -c @"
import json, sys
sys.path.insert(0, r'$repoRoot')
from apps.api.styles import PRODUCTION_STYLES
print(json.dumps([
    {
        'key': s.key,
        'run_id': s.run_id,
        'step': s.checkpoint_step,
        'sha256': s.sha256,
        'size': s.size_bytes,
        'relpath': str(s.adapter_path(__import__('pathlib').Path('ROOT')).relative_to('ROOT')),
    }
    for s in PRODUCTION_STYLES
]))
"@

if ($LASTEXITCODE -ne 0 -or -not $expectedJson) {
    Write-Host "FAIL  could not read the expected checkpoints from apps/api/styles.py" -ForegroundColor Red
    exit 1
}

$expected = $expectedJson | ConvertFrom-Json

Write-Host ""
Write-Host "DeckForge AI - production weight verification" -ForegroundColor Cyan
Write-Host "checkpoint root: $CheckpointRoot"
if ($RestoreFrom) { Write-Host "restoring from : $RestoreFrom" }
Write-Host ""

$failures = 0

foreach ($style in $expected) {
    $target = Join-Path $CheckpointRoot $style.relpath

    if ($RestoreFrom) {
        $source = Join-Path $RestoreFrom $style.relpath
        if (Test-Path $source) {
            $parent = Split-Path -Parent $target
            if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
            Copy-Item -Path $source -Destination $target -Force
        }
        else {
            Write-Host ("FAIL  {0,-18} not present in the backup: {1}" -f $style.key, $style.relpath) -ForegroundColor Red
            $failures++
            continue
        }
    }

    if (-not (Test-Path $target)) {
        Write-Host ("FAIL  {0,-18} missing" -f $style.key) -ForegroundColor Red
        Write-Host ("      expected at {0}" -f $style.relpath)
        $failures++
        continue
    }

    $actualSize = (Get-Item $target).Length
    if ($actualSize -ne $style.size) {
        Write-Host ("FAIL  {0,-18} is {1} bytes, expected {2}" -f $style.key, $actualSize, $style.size) -ForegroundColor Red
        $failures++
        continue
    }

    $actualHash = (Get-FileHash -Path $target -Algorithm SHA256).Hash.ToLower()
    if ($actualHash -ne $style.sha256) {
        Write-Host ("FAIL  {0,-18} sha256 mismatch" -f $style.key) -ForegroundColor Red
        Write-Host ("      expected {0}" -f $style.sha256)
        Write-Host ("      observed {0}" -f $actualHash)
        Write-Host  "      restore this file from backup. Do NOT retrain - R14 makes it unregenerable."
        $failures++
        continue
    }

    Write-Host ("PASS  {0,-18} {1} step {2}  {3}" -f $style.key, $style.run_id, $style.step, $actualHash.Substring(0, 16) + "...") -ForegroundColor Green
}

Write-Host ""
if ($failures -gt 0) {
    Write-Host "$failures of $($expected.Count) checkpoints FAILED. The service will return 503 for those styles." -ForegroundColor Red
    exit 1
}

Write-Host "All $($expected.Count) production checkpoints verified." -ForegroundColor Green
exit 0
