# Project planning

**Created:** 2026-07-27 · **Deadlines:** feature freeze 2026-08-15 · final content 2026-08-16 18:00 · submission 2026-08-17 06:00 (Europe/Brussels) · presentation 2026-09-02.

Rules: the **original plan (v1) below is never rewritten**. Adjustments are appended in the change log with reasons. Status values: `not started / in progress / done / blocked / dropped`. Effort in focused hours; actuals filled only when true.

## Original plan v1 (2026-07-27)

| # | Milestone | Key tasks | Dates | Priority | Depends on | Evidence | Est. effort | Actual effort | Completed | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| M0 | Phase 0 foundation | Repo inspection, environment audit, architecture matrices + DRs, research plan, planning, risk register, skeleton, security, CLAUDE.md/rules, docs foundation, experiment registry, traceability, validation, atomic commits | Jul 27–28 | critical | — | This repo state + commits + milestone report | 6 h | | | in progress |
| M1 | Prototype 0: 3D skateboard viewer | Deck model sourcing/licence, R3F scene, orbit/zoom/reset, test-texture swap, nose–tail orientation, evidence | Jul 28–30 | critical | M0 | `docs/prototypes/prototype-0.md`, screenshots, commits | 10 h | | | not started |
| M2 | Dataset research + pipeline | Style definitions (3), source/licence audit, manifest schema, collection, validation/hash/dedupe/caption/split scripts, statistics, contact sheets | Jul 30 – Aug 3 | critical | M0 | `docs/04-dataset-methodology.md`, manifests, script tests | 16 h | | | not started |
| M3 | Prototype 1: base-model benchmark | Python 3.11 venv, pinned installs, CUDA smoke test, SD 1.5 vs. SDXL inference benchmark (VRAM/speed/rubric), aspect-ratio test | Aug 2–4 | critical | M0 | EXP records, benchmark grids | 10 h | | | not started |
| M4 | Prototype 2: text + reference conditioning | img2img vs. IP-Adapter (vs. ControlNet) comparison, strength sweeps, fixed-seed grids | Aug 4–6 | critical | M3 | EXP records, comparison grids | 10 h | | | not started |
| M5 | Prototype 3: LoRA smoke test | Minimal LoRA train on tiny set, VRAM/duration measurements, load-and-generate verification | Aug 6–8 | critical | M2, M3 | EXP records, training logs | 10 h | | | not started |
| M6 | Prototype 4: style-learning experiments | Per-style LoRAs vs. multi-style LoRA, dataset-size/rank/LR variations, rubric evaluation, method comparison conclusions | Aug 8–11 | critical | M5 | EXP records, evaluation grids, RQ1/4/5 conclusions | 14 h | | | not started |
| M7 | Prototype 5: integrated MVP | FastAPI endpoints + validation/security, React UI, 3D texture pipeline, download, reproducibility metadata, error/loading states | Aug 10–13 | critical | M1, M4, M6 | Working MVP, API docs, commits | 18 h | | | not started |
| M8 | Testing, deployment, demo | Pytest/Vitest/Playwright suites, deployment setup + clean-clone test, demo script + backup plan | Aug 13–15 | high | M7 | Test reports, deployment docs | 10 h | | | not started |
| M9 | Research report PDF | Full report per assignment structure, references, PDF build, spelling/link validation | Aug 12–16 | critical | M6 (results) | `deliverables/` report PDF | 14 h | | | not started |
| M10 | Presentation + jury prep | Presentation PDF, speaker notes, timed demo script, backup demo, jury Q&A | Aug 14–16 | critical | M9 | `deliverables/` presentation PDF, `docs/presentation/` | 8 h | | | not started |
| M11 | Final submission audit | Prompt 6 audit: clean clone, secret/large-file scans, E2E, PDF/link/spelling validation, submission checklist | Aug 16 – 17 06:00 | critical | all | Audit results, checklist | 6 h | | | not started |

**Total estimated effort:** ~132 focused hours over 21 days (~6.3 h/day average — feasible but with little slack; see risk R4).

Public planning link: required deliverable; will be set up as a GitHub Project when remote operations are approved (see `docs/process/risk-register.md` R7).

## Milestone overlap notes

- M2 (dataset) overlaps M3 (benchmark): benchmark needs no custom data.
- M9 (report) starts before M8 finishes: methodology/dataset/early-prototype chapters can be written from completed evidence while later milestones run.
- Aug 16 is reserved exclusively for M11 validation, exports, and submission preparation.

## Change log

| Date | Change | Reason | Impact |
|---|---|---|---|
| — | (none yet) | | |
