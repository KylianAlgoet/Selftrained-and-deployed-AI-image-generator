# M8 baseline — the four gates, re-measured before any M8 work

**Date:** 2026-08-09 · **Milestone:** M8 (phase M8.1) · **Commit:** `a355ffa` (M7 closure)
**Working tree:** clean at the time of measurement.

## Why this exists

M7 closed with recorded figures of 406 pytest, 165 vitest, eslint clean and a succeeding build.
Those are **records of a past run, not facts about the current machine.** M8 also discovered that
the Node toolchain had drifted from the audited v20.18.0 to v24.18.0 with no record of when, so
whether M7's frontend numbers were produced on Node 20 or Node 24 is genuinely unknown. Carrying
them forward untested would have made every later M8 claim rest on an unverified assumption.

Everything below is the output of a command that actually ran in this session.

## Results

| gate | command | result | matches M7 record |
|---|---|---|---|
| Python | `.venv/Scripts/python.exe -m pytest` | **406 passed**, 5 warnings, 46.94 s | **yes — exactly** |
| Frontend units | `npm run test` (vitest run) | **165 passed**, 11 files, 21.44 s | **yes — exactly** |
| Lint | `npm run lint` (eslint .) | **clean**, exit code 0, no output | yes |
| Build | `npm run build` (`tsc -b && vite build`) | **succeeds**, exit code 0, 606 modules, 9.63 s | yes |

**No regression, and no drift in either direction.** The Node 24 upgrade broke nothing.

### Two things in the output that are expected, not defects

1. **`npm run build` prints a PowerShell `NativeCommandError`.** Vite writes its chunk-size advisory
   to stderr, and PowerShell 5.1 wraps any native stderr line in an ErrorRecord. The build's own
   exit code is **0** and `dist/` is produced. This is a shell artifact, not a build failure.
2. **The 1,135.68 kB chunk-size warning** (316.39 kB gzipped) is Three.js and React Three Fiber in
   one bundle. It is an advisory, it predates M8, and code-splitting the viewer is a **feature
   change** — out of scope under the M8 feature freeze and not a defect to fix here.

## Warnings carried forward (both known and accepted)

- `DeprecationWarning: BPE.__init__ will not create from files anymore` — from the CLIP tokenizer
  inside transformers 5.14.1, hit by four `test_style_kit.py` tests. Library-internal.
- `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2`
  — documented and deliberately accepted in `apps/api/requirements.txt`. Installing `httpx2` risks
  moving a protected pin to silence a notice, and the tests pass without it.

## Measured environment

| component | version |
|---|---|
| OS | Windows 11 Home 10.0.26200 |
| Shell | Windows PowerShell 5.1 |
| Python (`.venv`) | 3.11.0 |
| **Node.js** | **v24.18.0** (audit recorded v20.18.0 — see the environment-audit M8 update) |
| **npm** | **11.16.0** (audit recorded 10.8.2) |
| Git | 2.42.0.windows.2 |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU, driver **610.88**, 8188 MiB |

### Protected ML pins — all intact

```
torch 2.13.0+cu126        torchvision 0.28.0+cu126   diffusers 0.39.0
transformers 5.14.1       accelerate 1.14.0          safetensors 0.8.0
peft 0.20.0               pillow 11.3.0              huggingface_hub 1.25.1
numpy 2.4.6
```

### API and frontend toolchain

```
fastapi 0.141.1   uvicorn 0.52.1   pydantic 2.13.4   starlette 1.4.1
httpx 0.28.1      pytest 8.4.2
vite 6.4.3        vitest 4.1.10    eslint 9.39.5     typescript 5.8.3   jsdom 26.1.0
```

## Scope of this run

- **No GPU inference.** No model was loaded and no generation was executed. The API tests run
  against a stubbed pipeline; the checkpoint-integrity tests read the three adapter files from disk
  and hash them, which touches no GPU.
- The three production adapters were present on disk during the run, which is why the
  checkpoint tests passed here. A clean clone without them will not — that is expected and is
  measured separately in the clean-clone validation.

## What this baseline binds

M8 must not reduce these numbers. Any later figure below 406 pytest or 165 vitest is a regression
and gets explained in the milestone report rather than absorbed.
