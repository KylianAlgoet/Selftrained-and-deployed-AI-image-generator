# M11 — final GPU validation. The one authorised generation

**Date:** 2026-08-15 · **Milestone:** M11 (final submission audit) · **Result: PASS — byte-identical**
**Authorised by Kylian Algoet, explicitly, before it ran**, with the expected hash declared in
advance.

## Classification — read this before citing anything below

**This is M11 deployment and reproducibility validation. It is NOT a research experiment.**

- It has **no `EXP-###` id** and is **not** in `experiments/registry.csv`.
- It belongs to no frozen matrix, compares nothing, and evaluates no style.
- **No subjective quality scoring was performed**, deliberately. The run answers a reproducibility
  question, not a quality one.

### The generation total is now 28

| purpose | count |
|---|---:|
| research matrix (M3–M7), closed at its cap | 25 |
| Kylian's manual M7 human-review run | 1 |
| M8 deployment validation | 1 |
| **this M11 final-audit validation** | **1** |
| **total** | **28** |

**Generation count: 28** — 25 research (closed at cap) + 1 M7 human review + 1 M8 deployment
validation + 1 M11 final-audit validation. Never reported as 25 or 27.

**`docs/evidence/M8/README.md` still says 27 and is correct** — that is the state at the end of M8
and it was not rewritten. This document is the authoritative source for the current global total,
and `report/facts.yaml` now resolves `generations_total` from here.

## Preconditions

`preflight.ps1` returned **PASSED — 10 of 10**, the first full pass recorded on this machine. The
M11 clean clone had reported 9 of 10, blocked on port 8000.

```
PASS  Python virtual env           3.11 at .venv (3.11.0)
PASS  Python dependencies          torch 2.13.0+cu126, diffusers 0.39.0, fastapi 0.141.1
PASS  CUDA                         available - NVIDIA GeForce RTX 4060 Laptop GPU
PASS  nvidia-smi                   NVIDIA GeForce RTX 4060 Laptop GPU, 610.88, 8188 MiB
PASS  Node.js                      v24.18.0
PASS  Frontend dependencies        apps/web/node_modules present
PASS  API port 8000                free
PASS  Frontend port 5173           free
PASS  Preview port 4173            free
PASS  Production weights           all 3 adapters match their recorded sha256
```

### How port 8000 was freed, and what it turned out to be

M11's clean clone recorded port 8000 as held by `com.docker.backend` and called it Docker Desktop.
**That was incomplete.** The port was published by a **container belonging to an unrelated project**:

```
aegislab-api-1   image aegislab-api   127.0.0.1:8000->8000/tcp
```

`com.docker.backend` was only the proxy. Terminating it — the action the earlier record implied —
would have stopped **three** containers including a Postgres database. Instead **only
`aegislab-api-1` was stopped**, and it was **restarted immediately after this validation**; the web
and database containers were never touched. Recorded because the earlier description would have led
a reader to a heavier action than the situation required.

## Configuration — deliberately identical to M8's

| setting | value |
|---|---|
| style | `minimal-geometric` — EXP-027 step 300 |
| prompt (typed) | `a mountain and a rising sun` |
| prompt (assembled by the service) | `xgeo minimal geometric abstract style skateboard decal artwork, a mountain and a rising sun` |
| reference image | none · `ip_adapter_scale` **0** · `reference_present` false |
| seed | **42** |
| LoRA weight | 0.7 |
| steps / guidance | 30 of 30 · 7.5 |
| resolution | 512 × 1536 |
| scheduler | `DPMSolverMultistepScheduler` |
| base model | `stable-diffusion-v1-5/stable-diffusion-v1-5` rev `451f4fe16113bff5a5d2269ed5ad43b0592e9a14` |
| adapter sha256 | `2d425838cce59adc5c12b894e29439b695b98b9e40ef5d7ae667bd5216cb96a8` |
| live LoRA modules | 128 · active adapters `['minimal-geometric']` |

## The pre-declared comparison

The expected values were written down **before the run**, in the plan and in the driver script:

| | expected | actual | |
|---|---|---|---|
| bytes | 1 089 939 | **1 089 939** | **MATCH** |
| sha256 | `46bbf160e427…fb6d7f` | **`46bbf160e427…fb6d7f`** | **MATCH** |

Full digest, both sides:
`46bbf160e4270429e6692467dc6c59577e99bf3178dedd8d38193d0335fb6d7f`

**Verified three independent ways**, as M8's was: Node's `crypto` inside the driver, PowerShell
`Get-FileHash` afterwards, and the service's own `image_sha256` recorded in the metadata sidecar.

### What this establishes

The clean-clone reproduction is no longer a one-off. The same PNG has now come out of **four**
runs across **nine days**, two environments and a full dependency reinstall:

| run | date | environment |
|---|---|---|
| M7 Prototype 5, Phase A | 2026-08-06 | development machine |
| M8 clean clone | 2026-08-09 | freshly built environment |
| **M11 final audit** | **2026-08-15** | development machine, after the M11 clean clone |

**This does not contradict R14 and must not be quoted as if it did.** R14 concerns *training*, which
is not bit-reproducible from its recorded seed because LoRA initialisation drew from an unseeded
global RNG. This is *inference*: given a fixed adapter, seed and settings, generation is
deterministic and portable. Different halves of the pipeline; both statements stand.

It is also independent corroboration that the adapter on disk is the right file — a different
adapter could not produce these bytes.

## Measured result

| field | value |
|---|---|
| `generation_id` | `AHJ4-7Z-WT5W-uHrE1g1_g` |
| `created_utc` | 2026-08-15T21:42:54Z |
| HTTP status | **200** |
| `POST /api/generate` calls | **1** — asserted by the driver |
| `generate_seconds` | **16.419** |
| browser wall clock | **60.37 s** — includes the cold model load |
| `steps_run` | **30 of 30** |
| `peak_allocated_mb` | **5143.73** |
| `peak_device_used_mb` | 7969.5 of 8187.5 → **`spare_device_mb` 218.0** |
| console errors | **0** |
| warnings | **none** |

### Memory: a number that has not moved in four milestones

`peak_allocated_mb` **5143.73** is byte-identical to **EXP-019b (M5)**, **EXP-034 (M7)** and the
**M8 clean-clone run**. `allocated_mb` after the generation settled at **3316.64**, matching
EXP-034's figure across all thirteen of its runs.

**`spare_device_mb` 218.0 is the prompt-only figure and does NOT supersede the 200.0 MiB ceiling.**
That tighter worst case belongs to the *reference-conditioned* path, which this run deliberately did
not exercise. The operative production margin remains **200.0 MiB**.

## Device state, before and after

| | before | after |
|---|---|---|
| `/api/health` `pipeline_loaded` | `false` | `true` |
| `active_style` | `null` | `minimal-geometric` |
| `allocated_mb` | 0.0 | 3316.64 |
| `device_used_mb` | 1081.5 | 7969.5 |
| `nvidia-smi` memory.used | **83 MiB** | 6971 MiB |

The pre-run figures are the evidence that **no GPU work preceded the authorised generation**.

## The full browser path

Driven through a **real Chromium browser** against the **real frontend and the real API, with
nothing mocked**. This is the opposite of the Playwright suite, which answers every `/api/**` call
from frozen fixtures.

| link | result | evidence |
|---|---|---|
| app loads | **PASS** | `screenshots/00-app-loaded.png` |
| live WebGL context **before** generating | **PASS** — `true` | the deck renders on load, not as a result artefact |
| prompt entered, style selected, seed shown | **PASS** | read back as `a mountain and a rising sun` · `minimal-geometric` · `42` · strength `0.7` |
| Generate starts **exactly one** inference | **PASS** | POST count asserted = 1 |
| progress shown, honestly | **PASS** | see below |
| image returned and displayed | **PASS** | `screenshots/03-result-and-deck.png` |
| metadata accessible | **PASS** | `Reproducibility metadata` panel; sidecar downloaded through the app |
| **3D deck shows the generated texture** | **PASS** | `Applied to the deck preview →` visible; decal on the board |
| deck can be orbited | **PASS** | `screenshots/04-deck-orbited.png` |
| downloads work | **PASS** | PNG and metadata saved via the app's own buttons |
| WebGL context still live after | **PASS** — `true` | |

### Honest progress, captured mid-flight

Read from the live DOM 6 s in, during the cold model load:

```
GENERATING DECAL
Loading the local generation model…
No step percentage at this stage
Elapsed: 9 seconds
STYLE Minimal geometric · REFERENCE IMAGE No · SEED 42 · OUTPUT 512×1536 · GENERATION Local
```

**No percentage and no invented progress bar** — DR-013's rule observed in a real cold start rather
than in a fixture, exactly as M8 recorded it.

### One honest caveat about the driver

The browser was driven by **Playwright-controlled Chromium**, not by a human hand and not by the
Claude browser extension, which was **not connected** during this session. That is a real difference
from M8's run, which was hand-driven. It does not weaken the chain — the same real browser executes
the same real frontend against the same real API — but the run proves the *application* path, not a
human's experience of it. Recorded rather than smoothed over.

## Afterwards

`stop-demo.ps1` stopped both processes it had started; **ports 8000, 5173 and 4173 were all released
and no orphan uvicorn or vite process remained.** `aegislab-api-1` was restarted and all three of
that project's containers are running again.

## Artifacts

| file | tracked? | what it is |
|---|---|---|
| `gpu-validation/generation-record.json` | yes | the full run record, including the raw API response |
| `gpu-validation/metadata.json` | yes | the sidecar, downloaded through the application |
| `gpu-validation/screenshots/` | yes | five captures, ~112–186 KB each |
| `gpu-validation/run-validation.mjs` | yes | the driver, so the run is repeatable |
| `outputs/m11-gpu-validation/m11-gpu-validation.png` | **no** | the decal itself, 1 089 939 bytes |

**The PNG is deliberately not committed**, following the same policy as M8: generated images live in
git-ignored `outputs/`. Nothing is lost — its sha256 is recorded in three independent places, the
screenshots show the result and the deck, and the file is byte-identical to the already-recorded
`outputs/prototype-5/P5__minimal-geometric__promptonly__seed42.png`.
