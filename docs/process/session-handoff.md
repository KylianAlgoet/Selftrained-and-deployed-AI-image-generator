# Session handoff

**Last updated:** 2026-07-30 (M3 / Prototype 1 session, under Opus 5)

## Current state

Phase 0, public planning (issues #1–#12), **M1 (Prototype 0)**, and **M2 (dataset)** complete and pushed.

**M3 (Prototype 1 — base-model benchmark): measurements COMPLETE, milestone deliberately PAUSED at the mandatory human-review gate.** All code, tests, experiments, and evidence are committed locally. Nothing is pushed.

**Awaiting Kylian:** rubric scores + visual approval. Until those arrive, do **not** write DR-007's conclusion, choose a base model, close issue #4, mark M3 Done, or push. This is a standing instruction from the approved M3 plan, not a temporary state.

## Uncommitted changes

None expected at handoff — verify with `git status`.

## Latest commits (M3 sequence, 2026-07-30)

```
(aspect-ratio + prototype-1 doc commit — see git log)
8829664 docs(experiments): record base-model benchmark measurements for prototype 1
e25f1e0 feat(benchmark): add benchmark orchestrator and blank rubric scoring form
eae6e41 feat(benchmark): add base-model benchmark runner with vram and timing measurement
f646ee9 feat(evaluation): add frozen prompt and seed kit with hash-locked tests
1d51ccc feat(inference): add cuda environment smoke test with json evidence
37650b6 chore(ml): pin pytorch and diffusers inference dependencies for prototype 1
e5684f1 fix(dataset): rename retro-comic style to retro-poster to match wpa poster evidence
```

## What Kylian needs to do to unblock M3

1. Open `docs/evidence/prototype-1/cross-model-track-A-seed42.jpg` (controlled, all candidates at 512×512) and `cross-model-track-B-seed42.jpg` (each candidate at its native resolution).
2. Open `docs/evidence/EXP-005/aspect-ratio-comparison-seed42.jpg` for the deck-geometry comparison.
3. Read `docs/evidence/EXP-006-scoring/rubric.md`, then fill in `scoring-form.md` (or the `.csv`). **28 scoring units, all cells blank by design.**
4. Confirm visual approval. Then DR-007, issue #4, board move, and push follow.

## Measured results so far (no quality verdict assigned)

All at memory tier 0; no tier escalation was needed anywhere.

| Experiment | Result |
|---|---|
| EXP-001 | CUDA PASS. torch 2.13.0+cu126, bundled runtime 12.6, driver 610.88, RTX 4060 Laptop sm_89, 8187.5 MiB |
| EXP-002 SD 1.5 | 30/30 ok. 512×512 median **4.07 s**, alloc 2675 MiB. 512×768 median 6.81 s, alloc 2979 MiB |
| EXP-003 SD 2.1 base | **BLOCKED** — HTTP 401, repository gated. Two candidates by Kylian's decision |
| EXP-004 SDXL base | 30/30 ok. 512×512 median 16.51 s, alloc 7859 MiB. 1024×1024 median **118.73 s**, alloc **10738 MiB** |
| EXP-005 aspect ratio | 24/24 ok. 512×1536 median 15.24 s in 3892 MiB; square-crop leaves only **170×512 usable** |

**Do not report SDXL as "works on 8 GB".** Its 1024×1024 peak allocated (10738 MiB) and reserved (14510 MiB) exceed the 8187.5 MiB physical VRAM; WDDM spilled silently into host RAM instead of raising a CUDA OOM, so nothing failed and no tier escalated. It degraded quietly. ~29× SD 1.5's cost per 512 px image.

## Facts a new session must know

- Repo root: `C:\Expert Lab\Selftrained-and-deployed-AI-image-generator`; **8 GB VRAM** is the hard constraint.
- **Python:** `.venv` at repo root is **Python 3.11** (`.venv/Scripts/python.exe`). Never use system Python 3.14. Run tests with `.venv/Scripts/python.exe -m pytest` (66 tests, `pytest.ini`, testpaths=ml). Set `PYTHONIOENCODING=utf-8` for scripts that print non-ASCII.
- **pip 22.3 shipped in the venv cannot resolve torch** (rejects underscore-normalised wheel metadata). It was upgraded to 26.2; do not downgrade.
- **PyTorch install is NOT from PyPI:** `--index-url https://download.pytorch.org/whl/cu126`, `torch==2.13.0+cu126 torchvision==0.28.0+cu126`. See `ml/requirements-inference.txt` for the full rationale. `nvidia-smi`'s CUDA version is the **driver's max supported API**, not a toolkit to match. No xformers (torch SDPA is the Diffusers default). No nightlies.
- **Frozen evaluation kit** in `ml/evaluation/prompt_kit.py`, fingerprint `c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228`, hash-locked by pytest. **Never edit it to fix a benchmark** — record deviations per run instead. Changing it invalidates comparability with every earlier experiment.
- **One configuration per OS process** whenever VRAM or timing is measured. Adopted after a real contamination incident: the caching allocator retains its pool across `reset_peak_memory_stats()`, which corrupted EXP-005's first run. See `docs/evidence/EXP-005/measurement-methodology-correction.md`.
- **Model revisions are pinned to commit SHAs:** SD 1.5 `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`, SDXL `462165984030d82259a11f4367a4eed129e94a7b`. HF cache lives outside the repo at `C:\Users\kylia\.cache\huggingface` (~14 GB for SDXL alone).
- **`outputs/` is git-ignored** — 84 full-resolution PNGs live there. Only manifests, summaries, and contact sheets (≤300 KB) are committed.
- **Style identifiers** are `retro-poster`, `minimal-geometric`, `ukiyo-e`. `retro-poster` was renamed from `retro-comic` on 2026-07-30 because the material is WPA silkscreen posters, not comics. Never reintroduce `retro-comic`; pytest regression guards enforce this.
- **Dataset:** 148 items, splits 124/17/7, manifest `data/manifests/dataset-v1.csv`, raw images git-ignored.
- `apps/web`: React 19 + Vite 6.4.3 + R3F viewer (M1); `npm run dev/test/build`.

## Blockers

- **M3 is gated on Kylian's rubric scores and visual approval.** Nothing technical is blocking.

## Next action

Collect Kylian's scores from `docs/evidence/EXP-006-scoring/scoring-form.md`, then: record the scores, write **DR-007** (base-model selection, reporting Track A and Track B separately and explaining the trade-off, plus the two-candidate limitation), finalise planning/traceability/prototype-overview, update issue #4 and close it, verify the board shows M3 Done, run the pre-push checks, and push the validated milestone. Then the M3 milestone report, and stop before M4.
