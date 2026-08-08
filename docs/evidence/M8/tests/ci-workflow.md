# CI workflow — added, and NOT YET RUN

**Date:** 2026-08-09 · **Milestone:** M8 (phase M8.6) · **File:** `.github/workflows/ci.yml`

## Status, stated before anything else

**This workflow has never executed.** It is committed locally and **not pushed**, per CLAUDE.md
rule 6 — remote operations need Kylian's explicit approval, and the first GitHub Actions run is
his decision, not mine.

Therefore:

- **There is no green badge, no run URL and no CI evidence to cite.** M8's test evidence is the
  **local** runs recorded in this directory.
- **The YAML has not been validated by a runner.** It is syntactically well-formed and every step
  mirrors a command that passes locally, but "it should work" is not "it worked" and this record
  will not say otherwise.
- The first run may well need fixes. That is expected for an untested workflow and will be
  recorded honestly when it happens.

## What it runs

| job | steps | runner |
|---|---|---|
| `python` | CPU torch, pinned deps, **assert no weights present**, `pytest -q` | windows-latest |
| `frontend` | `npm ci`, lint, vitest, `typecheck:e2e`, build | windows-latest |
| `e2e` | `npm ci`, Chromium only, `playwright test` (builds + previews) | windows-latest |

## Four decisions worth recording

### 1. No skip marker was needed — and finding that out changed the plan

The approved plan said checkpoint-dependent pytests would be **skipped in CI by an explicit
marker**, on the assumption that they read the three production adapters from `outputs/lora/`.

**That assumption was wrong, and it was checked rather than trusted.** `outputs/lora/` was moved
aside locally and the full suite re-run: **all tests still passed.** The checkpoint tests build
their own adapter files under `pytest`'s `tmp_path` — including the integrity-gate tests, which
corrupt a *copy* precisely because R14 makes the real files unregenerable.

So the entire pytest suite is already both GPU-free and weight-free, and **no marker, no skip and
no conditional was added.** Adding one would have created the appearance of reduced coverage in CI
where there is none.

The workflow instead asserts the **opposite**: it fails if `outputs/lora` exists on the runner. A
green build can then never be explained by weights having leaked into the repository.

### 2. Windows, not Ubuntu

Windows 11 + PowerShell 5.1 is the only platform this project has been validated on, and DR-014's
deployment is native Windows. A Linux CI would test a configuration nobody supports and would
quietly imply cross-platform support that was never established. Windows runners cost 2× minutes;
that is the right trade for not making an unearned claim.

### 3. CI installs CPU torch, so it does NOT validate the production dependency set

Production runs `torch 2.13.0+cu126` from PyTorch's own CUDA index. A runner has no GPU, so CI
installs the **CPU wheel of the same version** from PyPI.

This is a deliberate and stated difference. **CI validates the code against the same library
versions; it does not validate the production install.** The thing that validates the production
install is the clean-clone test, on the real hardware, with the real index URL.

### 4. CI can never substitute for the GPU evidence

A runner has no GPU and no adapters, so this workflow says nothing about generation quality, VRAM,
latency or adapter integrity. Those are measured in `experiments/registry.csv`, EXP-034, EXP-035
and `scripts/validate_p5_api.py`. A green CI badge is not evidence that DeckForge AI generates
anything, and the report must not present it as such.

## One risk carried

`ml/training/tests/test_style_kit.py` loads the **real CLIP tokenizer**, which transformers
downloads from Hugging Face on first use. That makes CI dependent on Hugging Face being reachable —
and **R11 records three separate occasions where third-party hosting became unavailable
mid-project**, including an HTTP 401 that blocked SD 2.1 entirely.

A red build caused by an unreachable tokenizer would be a CI failure with no defect behind it. The
tokenizer is small and cached by the runner where possible, so this is a known nuisance rather than
a blocker — but if it proves flaky, the honest fix is to mark those tests as requiring network,
not to delete the assertions they make about token ids.

## Local equivalents, which DID run

Every command in the workflow passes locally on 2026-08-09:

| command | result |
|---|---|
| `pytest -q` | **469 passed** |
| `pytest -q` with `outputs/lora` moved aside | **469 passed** — the basis for decision 1 |
| `npm run lint` | clean |
| `npm run test` | **169 passed** |
| `npm run typecheck:e2e` | clean |
| `npm run build` | succeeds |
| `npx playwright test` | **37 passed**, twice, no flakes |
