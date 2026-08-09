# Clean-clone validation — real output

**Date:** 2026-08-09 · **Milestone:** M8 (phase M8.7)
**Clone directory:** `C:\Expert Lab\DeckForge-M8-clean-clone` — **outside** the working repository
**Source:** the local repository as a Git remote, at commit `824838f`
**Result: ALL 18 non-GPU steps PASS, plus the authorised real-output run.**

> **Updated 2026-08-09, after the human gate.** The first pass recorded **17 of 18** steps passing,
> with `test_dataset_v1_is_byte_identical_to_the_recorded_hash` failing. That defect was diagnosed,
> taken to Kylian, fixed on his decision, and **re-verified in this same clone: 468 passed, 5
> skipped, 0 failed.** The five skips are pre-existing conditional skips for git-ignored assets
> (raw dataset images, the reference kit), each declaring its reason; 468 + 5 = 473, matching the
> development machine exactly. The original failure is preserved below rather than edited out — it
> is the most valuable thing this test produced.
>
> The one authorised generation then ran and passed. See
> [`real-output.md`](real-output.md).

## Why the local repository was the clone source

`git clone "C:\Expert Lab\Selftrained-and-deployed-AI-image-generator"` proves **what Git actually
contains**, which is the question this test exists to answer, and it needs no network. A clone from
`origin` would additionally prove the push is current; that is a separate check requiring remote
access and is **not claimed here**.

## Step-by-step

| # | step | result |
|---:|---|---|
| 1 | clone; HEAD `824838f`; `git status` clean | **PASS** |
| 2 | ignored trees absent | **PASS** (one note below) |
| 3 | `py -V:3.11 -m venv .venv`; upgrade pip | **PASS** |
| 4 | install pinned dependencies | **PASS**, 402 s total |
| 5 | `pip check`; verify protected pins | **PASS** (two drifts, below) |
| 6 | `npm ci` from the lockfile | **PASS**, 306 packages, 15.7 s |
| 7 | `npm run build` | **PASS**, 606 modules, 11.31 s |
| 8 | `npm run lint`, `npm run test`, `npm run typecheck:e2e` | **PASS** — eslint clean, **169 vitest** |
| **9** | **`pytest` (before weights)** | **FAIL — 1 test.** See "The blocking defect". **Fixed; now PASS.** |
| 10 | restore weights; `verify-weights.ps1` | **PASS** — fails loudly before, 3/3 after |
| 11 | `pytest` (after weights) | same single failure — **unrelated to weights**; after the fix, **468 passed, 5 skipped, 0 failed** |
| 12 | `preflight.ps1` | **PASS**, 10/10 |
| 13 | `start-demo.ps1`; health; styles; progress | **PASS** |
| 14 | browser: real backend, decal on the 3D deck | **PASS** |
| 15 | `npx playwright test` in the clone | **PASS**, 37/37, 76.5 s |
| — | **HUMAN GATE** | **passed** — Kylian authorised the fix and the generation |
| 16–17 | **one authorised real generation** | **PASS** — see [`real-output.md`](real-output.md) |
| 18 | `stop-demo.ps1`; ports released; no orphans | **PASS** (run again after the generation) |

## The blocking defect: a frozen hash that fails on every clean clone

```
FAILED ml/training/tests/test_style_kit.py::test_dataset_v1_is_byte_identical_to_the_recorded_hash
  assert 'b38996ae44d8...' == 'cd18cbb05307...'
```

### Diagnosis — measured, not inferred

| | bytes | line endings | sha256 |
|---|---:|---|---|
| working copy on the dev machine | 63 152 | **149 × CRLF** | `cd18cbb0…` ← the recorded constant |
| **the Git blob** (`faf1fbee`) | **63 003** | **149 × LF** | `b38996ae…` |
| every clean clone | 63 003 | 149 × LF | `b38996ae…` |

**The content is identical.** Normalising line endings makes the two byte-for-byte equal — verified
directly, and the 149-byte difference is exactly the 149 lines (148 dataset items + header).

### What actually happened

`core.autocrlf` is true on this machine. `dataset-v1.csv` was committed **before**
`.gitattributes` gained its `data/manifests/*.csv -text` rule, so Git normalised it to LF in the
blob while the working copy kept its CRLF bytes and was never re-checked-out. The recorded constant
`DATASET_V1_SHA256` was then taken from **the working copy**, not from what Git stores.

The `-text` rule works correctly — it is why the clone gets the blob verbatim. It was simply added
after the constant had already been pinned to the wrong representation.

### Why this matters more than a failing test

This check is one of the project's **integrity controls**. Its stated purpose is proving that
`dataset-v1.csv` was never modified during M6. In fact it has been pinned to a **machine-local
representation** since M6 and **fails on every clean clone** — so it has only ever passed on the
one machine holding the stale CRLF bytes.

The irony is recorded honestly: M6 identified `core.autocrlf` as exactly this hazard and added
`.gitattributes` in response. The rule protected future checkouts; nobody re-derived the constant
afterwards, and no clean clone had been attempted until now. **This is precisely the class of
defect a clean-clone test exists to find, and it was found on the first attempt.**

### How it was fixed — and the cascade that shaped the fix

Kylian's decision at the gate: **re-record against what Git actually stores.** Implementing it
naively would have caused real damage, which the investigation caught first.

`DATASET_V1_SHA256` is not only used by this test. It is mixed into `kit_fingerprint()` — locked at
`fc11d828…` and cited across M6 evidence as unchanged — and it is recorded as `dataset_version` in
**every M6 training run**. Repointing it would have moved the frozen fingerprint and desynchronised
every recorded run's dataset version, for what is only a line-ending representation.

So the two questions were separated, because they are genuinely different questions:

| constant | answers | status |
|---|---|---|
| `DATASET_V1_SHA256` = `cd18cbb0…` | *which dataset configuration was M6 run against?* | **unchanged** — an identifier |
| `DATASET_V1_CONTENT_SHA256` = `b38996ae…` | *has the content been modified?* | **new** — the integrity check |

The check now hashes the content with line endings normalised to LF, via
`style_kit.sha256_dataset_content()`, so it is **independent of the checkout** — `core.autocrlf`,
`.gitattributes` and the host platform cannot move it. The working copy was also normalised to LF,
which produced **zero Git diff** because the blob was already LF.

Four tests were added: the content check itself, one proving the hash is line-ending independent,
one proving it still detects a real content edit (so normalising did not make it blind), and one
asserting the two constants have **not** been collapsed into one. `kit_fingerprint()` verified
still `fc11d828…`; `dataset_version` still `cd18cbb05307`.

**Re-verified in this clone: 468 passed, 5 skipped, 0 failed.**

## Note on step 2: `deliverables/` appears in the clone

`.gitignore` lists `deliverables/`, yet the directory exists in a fresh clone — because
`deliverables/.gitkeep` is **tracked**, and `.gitignore` never affects already-tracked files. Same
for `tests/.gitkeep`.

**Harmless, and not a leak:** both are empty placeholders, and no derived package or binary is
tracked. Recorded because a reader comparing `.gitignore` to a clone would otherwise think the
ignore rule had failed.

## Note on step 5: two transitive versions drifted

| package | dev machine | clean clone |
|---|---|---|
| `starlette` | 1.4.1 | **1.6.0** |
| `numpy` | 2.4.6 | **2.4.4** |

`apps/api/requirements.txt` lists `starlette==1.4.1` under the heading *"Pulled in by the four above
and pinned here so the set is reproducible"* — **but those lines are commented out, so they are not
pinned at all.** The file claims a reproducibility property it does not implement.

Everything passed on 1.6.0, so this is not currently breaking anything, and `pip check` reported no
broken requirements. It is still a false statement in a requirements file and is listed as an open
item. **Not changed here:** pinning transitive dependencies during a feature freeze is a dependency
move, and the protected-stack rule says that needs approval.

The six protected packages are all **exactly** as pinned: torch 2.13.0+cu126, torchvision
0.28.0+cu126, diffusers 0.39.0, transformers 5.14.1, accelerate 1.14.0, safetensors 0.8.0, plus
peft 0.20.0 and pillow 11.3.0.

## What the clean clone proved works

- **`pip 22.3` shipped in the venv and could not have resolved torch** — the M3 finding reproduced
  exactly, and the runbook's "upgrade pip first" step is therefore load-bearing, not a precaution.
- **The runbook's install order works verbatim**, including the PyTorch CUDA index URL.
- **CUDA is available in the clone** on the same GPU: `torch.cuda.is_available() → True`.
- **The weight restore path fails loudly when weights are absent** (3/3 FAIL, exit 1, each with its
  expected path) and passes after `-RestoreFrom` (3/3 PASS against the gate-2 hashes).
- **The service starts and is healthy with no model loaded**: `pipeline_loaded: false`,
  `allocated_mb: 0.0`, `cuda_available: true`, `single_worker_guard: enforced`.
- **The real API served the real styles** — `retro-poster` arriving marked `PARTIAL PASS`.
- **The 3D path works end to end with zero GPU cost.** In a real browser against the real backend:
  three styles listed, WebGL context live, decal uploaded and mapped to the deck, **0 calls to
  `POST /api/generate`**, and **no console errors**. Screenshots in `screenshots/`.
- **Shutdown is clean**: both processes stopped, all three ports released, no orphans.

### Backup source used, stated plainly

The weights were restored from the working repository, **not** from the external backup drive —
that drive was not available in this session and its path is deliberately not guessed. The
mechanism (`-RestoreFrom <path>`) is what was validated, and it is source-agnostic. **A restore
from the real external backup has not been performed and is not claimed.**

## Timings

| step | time |
|---|---:|
| torch + torchvision (CUDA index) | 214.6 s |
| remaining Python dependencies | 187.0 s |
| `npm ci` | 15.7 s |
| `npm run build` | 11.3 s |
| pytest | 26.6 s |
| Playwright (37, incl. build) | 76.5 s |
| **total, clone to running service** | **≈ 10 minutes** |

## Environment measured inside the clone

Python 3.11.0 · Node v24.18.0 · npm 11.16.0 · Git 2.42.0.windows.2 ·
NVIDIA GeForce RTX 4060 Laptop GPU, driver 610.88, 8188 MiB · Windows 11 Home 10.0.26200

## Status

**Complete.** The clean-clone directory has been **deleted**. It is regenerable in ~10 minutes by
following `docs/deployment/runbook.md`, which is the entire point of the exercise.

The one authorised generation ran inside it before deletion and reproduced M7's Phase A output
**byte-for-byte** — see [`real-output.md`](real-output.md).
