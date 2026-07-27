# Session handoff

**Last updated:** 2026-07-27 (Dataset / M2 session; part under Opus 4.8 after Fable 5 became unavailable)

## Current state

Phase 0, public planning (issues #1–#12), and **M1 (Prototype 0)** complete and pushed; issue #2 closed. **M2 (dataset) complete**: 148 licence-verified items (ukiyo-e 55 CC0 / retro-comic 41 public domain / minimal-geometric 52 project-original), splits train 124 / val 17 / holdout 7. Pipeline in `ml/dataset/` with 34 passing pytest tests. Manifest `data/manifests/dataset-v1.csv`; evidence in `docs/evidence/dataset-v1/` (statistics, 3 contact sheets, curation log). DR-006 recorded.

## Uncommitted changes

None expected at handoff — verify with `git status`. (Process-docs commit closes the M2 sequence.)

## Latest commits (M2 sequence, 2026-07-27)

```
(process-docs commit — see git log)
8b8e283 docs(data): record dataset v1 manifest, statistics, and contact sheets
89f04ef feat(dataset): add approved-source collection and manifest build scripts
d79330b feat(dataset): add seeded geometric decal generator with tests
7034e8f feat(dataset): add captioning, splits, statistics, and contact sheets with tests
22c36a0 feat(dataset): add validation, hashing, and duplicate detection with tests
58c472f chore(ml): set up python 3.11 environment with pinned dataset tooling
8be587c docs(dataset): record approved style set and sourcing decision
```

## Blockers

- None. Issue #3 to be closed at the end of the M2 push; board auto-moves M2 to Done.

## Facts a new session must know

- Repo root: `C:\Expert Lab\Selftrained-and-deployed-AI-image-generator`; 8 GB VRAM constraint.
- **Python:** `.venv` at repo root is **Python 3.11** (`.venv/Scripts/python.exe`); pinned tooling in `ml/requirements.txt` (Pillow, imagehash, pytest — no torch yet). Run tests with `.venv/Scripts/python.exe -m pytest` (config in `pytest.ini`, testpaths=ml). Set `PYTHONIOENCODING=utf-8` when printing Japanese romanization.
- **Dataset:** raw images in `data/raw/<style>/` are **git-ignored** (also `data/processed/`, `.venv/`, `data/raw/candidates.csv`). Only manifest + evidence are committed. To rebuild: `.venv/Scripts/python.exe scripts/collect_dataset_v1.py` then `scripts/build_dataset_v1.py` (downloads skip existing files; build is deterministic).
- **Sources actually used** (2 approved sources were blocked): ukiyo-e = Met Open Access (AIC dropped, 403); retro-comic = Library of Congress WPA posters (Digital Comic Museum dropped, Cloudflare); minimal-geometric = `ml/dataset/generate_geometric.py`. All within the approved registry (conditions A/B).
- `apps/web`: React 19 + Vite 6.4.3 + R3F viewer (M1); `npm run dev/test/build`.

## Next action

M3 — Prototype 1: local base-model benchmark (issue #4, planned Aug 2–4; can start early). Start in Plan mode. **This is the first milestone that installs torch/diffusers** — pin versions against the audited CUDA 13.3 / driver 610.74 / 8 GB VRAM, verify `torch.cuda.is_available()` before any run. No training in M3 (inference benchmark only).
