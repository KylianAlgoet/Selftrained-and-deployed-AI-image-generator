# M11 clean-clone validation — clone → documented restore → running system

**Date:** 2026-08-15 · **Milestone:** M11 (B13)
**Clone directory:** `C:\Expert Lab\DeckForge-M11-clean-clone` — **outside** the working repository
**Source:** the local repository as a Git remote, at `6bde9dc`
**Transcripts:** `transcripts/clean-clone-phase1.txt`, `clean-clone-phase2.txt`,
`clean-clone-preflight-after-restore.txt`, `clean-clone-backend.txt`, `clean-clone-frontend.txt`

## What this test was for

Not to prove that a clean clone notices its weights are missing — that is only the first result.
The question is whether **an evaluator can go from `git clone` to a running system** using the
procedure this repository documents. Both states are recorded below: the expected pre-restore
failure, and the post-restore pass.

## Why the local repository was the clone source

`git clone "C:\Expert Lab\Selftrained-and-deployed-AI-image-generator"` proves **what Git actually
contains**, which is the question. Cloning `origin` would prove something different and currently
false — `origin/main` is **19 commits behind** local `main`, so it would have tested stale code. A
clone from `origin` is a separate check and is **not claimed here**.

## Result

| # | step | result |
|---:|---|---|
| 1 | `git clone`; HEAD `6bde9dc`; clean tree | **PASS** |
| 2 | ignored trees absent (`outputs/`, `.venv`, `node_modules`, `data/raw`) | **PASS** |
| 3 | `py -V:3.11 -m venv .venv`; pip upgraded first | **PASS** — Python 3.11.0 |
| 4 | dependencies in the runbook's order, torch from the CUDA index | **PASS** |
| 5 | `pip check`; the ten protected pins verified by real import | **PASS** — see below |
| 6 | `npm ci` from the lockfile | **PASS**, 12.6 s |
| **7** | **`preflight.ps1` BEFORE restore** | **FAIL, as expected** — the adapters are not in Git |
| **8** | **`verify-weights.ps1 -RestoreFrom …`** | **PASS** — 3 of 3 restored and SHA-256 verified |
| **9** | **`preflight.ps1` AFTER restore** | **9 of 10 PASS** — one environmental failure, below |
| **10** | **backend from the clone, `--workers 1`** | **PASS** — `/api/health` and `/api/styles` |
| 11 | frontend: built bundle served from the clone | **PASS** — page and both assets HTTP 200 |
| 12 | pytest in the clone | **PASS** — **522 passed, 5 skipped** |
| 13 | eslint · vitest · build · Playwright in the clone | **PASS** — clean · **183** · succeeds · **38** |

## The protected pins, verified by import in the fresh environment

```
torch         2.13.0+cu126        transformers  5.14.1
torchvision   0.28.0+cu126        accelerate    1.14.0
diffusers     0.39.0              safetensors   0.8.0
peft          0.20.0              pillow        11.3.0
cuda available True               device  NVIDIA GeForce RTX 4060 Laptop GPU
```

`pip check`: **No broken requirements found.** The install moved none of the pins the project
protects, in an environment built from nothing.

## Step 7 — the expected failure

`preflight.ps1` failed on **Production weights** before the restore. That is the correct result and
the reason the check exists: `.gitignore` excludes `*.safetensors` and `outputs/`, the three
adapters **cannot be regenerated** (R14), and the service refuses to generate without them.

## Step 8 — the documented restore

The runbook's form is `.\scripts\verify-weights.ps1 -RestoreFrom "<your backup path>"`. The backup
source used here was the working repository's `outputs/` tree, which holds the authoritative
production adapters in exactly the layout `docs/deployment/weights-manifest.md` specifies. The
manifest states that the real backup lives on external storage and that **its path is Kylian's to
supply**, so no private absolute path is written into this record.

The script restored and verified all three by SHA-256, reading the expected values from
`apps/api/styles.py` rather than from a second copy. Confirmed again by preflight in step 9:

```
PASS  Production weights           all 3 adapters match their recorded sha256
```

**The restore mechanism is proven end to end.**

## Step 9 — the one failure, and what it is

```
PASS  Python virtual env           3.11 at .venv (3.11.0)
PASS  Python dependencies          torch 2.13.0+cu126, diffusers 0.39.0, fastapi 0.141.1
PASS  CUDA                         available - NVIDIA GeForce RTX 4060 Laptop GPU
PASS  nvidia-smi                   NVIDIA GeForce RTX 4060 Laptop GPU, 610.88, 8188 MiB
PASS  Node.js                      v24.18.0
PASS  Frontend dependencies        apps/web/node_modules present
FAIL  API port 8000                IN USE by pid 17668 (com.docker.backend) - a second API
                                   process would compete for the GPU
PASS  Frontend port 5173           free
PASS  Preview port 4173            free
PASS  Production weights           all 3 adapters match their recorded sha256
```

**Port 8000 is held by Docker Desktop**, an unrelated process that was already running on this
machine. This is an **environment condition, not a repository defect**, and preflight detecting it
is the check doing precisely its job — it exists so that two API processes never compete for one
8 GB device.

It was **not** resolved by stopping Docker: that is the user's running application, and killing it
to make a check go green would be the wrong trade. It is listed as a **human-only item**: a full
`preflight.ps1` PASS on this machine requires port 8000 to be free.

## Step 10 — the backend, from the clean clone

Started on **8001** because 8000 was occupied, `--workers 1`, no `--reload`. No generation was
requested, so the pipeline never loaded and **no GPU work was done**.

```json
{"status": "ok", "pid": 31040, "pipeline_loaded": false, "active_style": null,
 "generation_in_progress": false, "cuda_available": true,
 "device_name": "NVIDIA GeForce RTX 4060 Laptop GPU", "device_total_mb": 8187.5,
 "device_used_mb": 1081.5, "allocated_mb": 0.0, "single_worker_guard": "enforced"}
```

`GET /api/styles` returned all three production styles with the correct run ids and checkpoint
steps — `minimal-geometric` EXP-027 step 300, `ukiyo-e` EXP-028 step **600**, `retro-poster`
EXP-029 step 300 — and `retro-poster` carrying `"outcome": "PARTIAL PASS"` with its pseudo-text and
framing limitation in the payload. **The partial pass reaches the API contract, not only the
documentation.**

`uvicorn --workers 1` again started **two** processes; both were stopped and the port released with
no orphan, which is the M8 finding still holding.

## Step 11 — the frontend

`vite preview` binds to **`::1` only**, so it must be reached as `http://localhost:4173`; a
`127.0.0.1` probe fails and that is the probe's fault, not the application's. Ports were confirmed
free first, so the response could only come from this clone's `dist/`.

```
GET http://localhost:4173/            -> HTTP 200, 1 288 bytes
page title: DeckForge AI - skateboard decal studio
  /assets/index-DCQMOnWs.js           -> HTTP 200, 1 136 141 bytes
  /assets/index-DGRcUfrj.css          -> HTTP 200,    15 695 bytes
```

## Step 12 — the finding that matters for the report

**pytest in the clean clone: 522 passed, 5 skipped.** 522 + 5 = **527**, matching the development
machine exactly. The five are pre-existing conditional skips for git-ignored assets, each declaring
its reason.

`report/sources/15-testing.md` states, in the present tense, *"A clean clone runs **468 passed and
5 skipped** … 468 + 5 = 473, matching the development machine exactly."* That was true when M8
measured it. **It is no longer what the command prints.** The arithmetic is still internally
consistent — chapter 15 is scoped to the 473 **system** tests throughout — but the sentence
describes an observable command output, and the output changed when M9 and M10 added 54
document-validation tests. See `findings.md`.

## What this test still does not prove

- **Not a generation.** No model was loaded and no image was produced. Real-model behaviour is
  evidenced separately, and the M11 GPU gate is where that is decided.
- **Not the remote.** The clone came from the local repository. Nothing here says `origin/main` is
  current — it is 19 commits behind.
- **Not a preflight PASS.** Nine of ten checks pass; the tenth needs port 8000 free.
