# Process log

Newest entries first. Each entry: date, objective, plan, completed work, unfinished work, blockers, decisions, commands/tests, real results, evidence, commits, next step.

---

## 2026-07-27 — Dataset research and dataset pipeline (M2)

**Objective:** build the mandatory custom training dataset (≥3 distinct styles, documented provenance/licences) and its validation pipeline (RQ3; prep RQ4; part RQ11).

**Plan:** approved M2 plan — final style set retro-comic / minimal-geometric / ukiyo-e (DR-006), ~50 items/style, licence-safe sources, pure-function pipeline modules with pytest, human approval gate before any download.

**Completed work:** Python 3.11 venv (project's first) with pinned `ml/requirements.txt` (Pillow 11.3, imagehash 4.3.2, pytest 8.4.2; no torch yet). Pipeline in `ml/dataset/`: validate, hashing (SHA-256 + dHash near-dupe), manifest schema (licence/style/split allowlists), normalize, captions, deterministic split, stats, contact_sheet, seeded geometric generator — **34 pytest tests, all passing**. Collection (`scripts/collect_dataset_v1.py`) and build (`scripts/build_dataset_v1.py`) scripts. Dataset v1: **148 licence-verified items** (ukiyo-e 55 CC0 / retro-comic 41 public domain / minimal-geometric 52 project-original), train 124 / val 17 / holdout 7. Manifest `data/manifests/dataset-v1.csv`; evidence (statistics, 3 contact sheets, curation log) in `docs/evidence/dataset-v1/`.

**Source-registry approval & fallbacks (honest record):**
- Kylian approved the source registry with conditions A–D (2026-07-27) before any download.
- **Digital Comic Museum** (source #2, conditional): Cloudflare "Just a moment…" challenge blocked all programmatic access → **condition-B fallback applied**: its retro-comic share shifted to additional Library of Congress WPA posters (public domain). No new source added.
- **Art Institute of Chicago** (source #4): search API works, but its IIIF image CDN returned **HTTP 403 for every fetch** (default and browser user agents) → its ukiyo-e share shifted to the already-approved **Met Open Access** source #3. No new source added.
- **Manual visual review (condition C):** one Met item (`met-61658`, a 3D bodhisattva wood sculpture that passed the keyword filter) was rejected as off-style after inspecting the contact sheet; recorded in the curation log.

**Real results:** 162 candidates → 148 accepted. 14 rejections (13 LOC posters below the 512 px minimum; 1 manual off-style). 0 exact or near duplicates. Manifest passes schema validation (0 errors); 100% of items have provenance source, licence, and caption. Short-side range 512–3505 px. Every style ≥40 (condition D). Contact sheets ≤182 KB each; raw images git-ignored (verified with `git check-ignore`).

**Decisions:** DR-006 (style set + sourcing). Interpreted the "exclude persons" rule as the methodology's "identifiable living persons" (privacy) — figures in century-old public-domain art are in scope.

**Commits:** 8be587c DR-006/methodology · 58c472f python env · 22c36a0 validate/hash/manifest+tests · 7034e8f captions/splits/stats/sheets+tests · d79330b geometric generator+tests · 89f04ef collection+build scripts · 8b8e283 manifest+evidence · (process-docs commit follows).

**Blockers:** none. **Next step:** M2 milestone report + push, then M3 (Prototype 1: base-model benchmark) in Plan mode.

---

## 2026-07-27 — Prototype 0: static interactive 3D skateboard viewer (M1)

**Objective:** answer RQ9 (decal UV mapping, nose–tail orientation, dynamic textures) with a working viewer; validate DR-003.

**Plan:** approved M1 plan — procedural deck geometry in R3F (four alternatives compared, weighted matrix → DR-005), self-created assets only, Vitest coverage, evidence with correct + labelled-demonstration orientation states.

**Completed work:** `apps/web` scaffold (Vite 6.4.3 pinned for Node 20.18, React 19.2.8, three 0.185.1, R3F 9.6.1, drei 10.7.7, Vitest 4.1.10); `deckGeometry.ts` (concave, asymmetric nose/tail kicks, documented UV convention v=1=nose, material groups); `DeckViewer.tsx` (lights, OrbitControls, reset, preserveDrawingBuffer, dev-only evidence hook); `ViewerControls.tsx` (jsdom-testable, labelled inverted-UV demonstration toggle); two self-authored SVG decals; 13 passing tests; 5 evidence captures in `docs/evidence/prototype-0/`.

**Real results:** first render orientation **correct** (no fix needed — documented honestly; demonstration toggle provides the "defect" illustration). Orbit/zoom/reset verified in Chrome. Texture swap works without reload. `npm run test` 13/13, lint clean, build 1.11 MB minified.

**Failures/lessons (documented in prototype doc):** jsdom 27 requires Node ≥20.19 → pinned jsdom 26.1.0, Vitest default env `node` (R5); background-tab rAF pause caused hash-identical stale canvas captures → forced-render evidence hook; Chrome blocks repeated automatic downloads → local save-server for evidence export.

**Decisions:** DR-005 (procedural deck geometry, self-made UVs).

**Commits:** 36150ef scaffold · b10608c geometry+tests · 148a2c9 kick asymmetry · 634ff59 scene+decals · 2dba9d4 prototype docs/evidence · (process-docs commit follows).

**Blockers:** none. **Next step:** M1 milestone report + push, await visual sign-off, then M2 dataset milestone (Plan mode).

---

## 2026-07-27 — Public planning created (GitHub Project + issues)

**Objective:** fulfil the mandatory public-planning deliverable before Prototype 0, per approval of remote planning operations.

**Completed work:** created the public GitHub Project **DeckForge AI - Project Planning** (https://github.com/users/KylianAlgoet/projects/1; visibility changed private → public in project settings, confirmed "Changes saved"). Created repository issues #1–#12 mirroring milestones M0–M11 from `docs/02-planning.md`, each containing objective, acceptance criteria, planned start/end dates, priority, dependencies, expected evidence, and current status. The project's auto-add workflow adds repository issues to the board automatically (verified in issue #1's timeline). Closed issue #1 (M0) as completed — board shows M0 = Done, M1–M11 = Todo, matching reality. Added the planning URL to README, planning doc, process log, and session handoff.

**Method note:** GitHub CLI is not installed and no API token is available to the agent, so the project and issues were created through the authenticated browser session (Claude in Chrome) using prefilled issue URLs; no credentials were read or stored.

**Real results:** public URL https://github.com/users/KylianAlgoet/projects/1 renders the 12 milestones with correct statuses; issues #1–#12 exist at https://github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator/issues.

**Commits:** `docs(project): add public planning link to README and planning docs` (hash in session handoff), pushed to origin/main after the standard checks.

**Next step:** unchanged — Prototype 0 plan on approval.

---

## 2026-07-27 — Remote operations approved; Phase 0 pushed

**Objective:** publish the validated Phase 0 history to GitHub after explicit approval of remote operations.

**Completed work:** pre-push checklist executed with real outputs — clean working tree, branch `main`, 8 commits reviewed (`af4891b`…`673e540`), secret-pattern scan clean, tracked files all text (largest 23.1 KB, no binaries/weights/datasets), remote confirmed empty via `git ls-remote` (branch-creating push, no history rewrite). Pushed `main` → `origin/main` with upstream tracking.

**Real results:** `origin/main` = `673e5402fd3a20e2a35764b457705278484aa79e`; local and remote in sync.

**Decisions:** ongoing policy per user instruction — validated milestone commits are pushed to origin after each milestone, subject to the same security and file-size checks. No force-pushes, history rewrites, or settings changes.

**Next step:** unchanged — await Phase 0 review, then Prototype 0 plan. Public planning link (GitHub Project) still to be created.

---

## 2026-07-27 — Phase 0: research and repository foundation

**Objective:** establish the audited, documented, secure foundation required before any prototype work (Phase 0 of the master prompt).

**Plan:** approved Phase 0 plan (Plan mode): repository inspection → real environment audit → monorepo skeleton → security foundation → CLAUDE.md/rules → documentation foundation → research plan → planning v1 → risk register → architecture matrices + decision records → experiment registry → traceability → validation → atomic commit sequence → milestone report.

**Completed work:**
- Repository inspection: confirmed root `C:\Expert Lab\Selftrained-and-deployed-AI-image-generator`, branch `main` with zero commits, remote `origin` configured (untouched), only the prompt pack present.
- Environment audit with real commands (`docs/technical/environment-audit.md`). Key findings: RTX 4060 Laptop 8 GB VRAM (driver 610.74, CUDA UMD 13.3), 16 GB RAM, 228 GB free disk, Python 3.14 default **but PyTorch-incompatible** → Python 3.11 (installed) mandated for ML; Node 20.18.0; Docker 29.1.3; FFmpeg/nvcc/conda absent; `python`/`pip` not on PATH (use `py`).
- Monorepo skeleton with `.gitkeep` placeholders.
- Security foundation: `.gitignore` (secrets, weights, datasets, caches, large binaries), `.env.example` (placeholders only).
- `CLAUDE.md` + `.claude/rules/` (commit protocol, research process, security, documentation, honesty/evidence).
- Documentation foundation: `README.md`, docs 00–09, process docs, `docs/ai-usage.md`, `docs/learning-outcome-traceability.md`.
- Research plan with primary question + RQ1–RQ12 (`docs/01-research-plan.md`); LoRA direction recorded as hypothesis, not decision.
- Planning v1 with milestones M0–M11 to submission (`docs/02-planning.md`).
- Risk register R1–R10 (`docs/process/risk-register.md`).
- Architecture matrices + DR-001…DR-004 (`docs/03-architecture.md`, `docs/decisions/`): monorepo, FastAPI, React+Vite+TS+R3F, Diffusers+PEFT+Accelerate; ML method/base model deliberately left open for Prototypes 1–4.
- Experiment registry header (`experiments/registry.csv`).

**Unfinished work:** none within Phase 0 scope (Prototype 0 deliberately not started).

**Blockers:** none. Remote push not yet approved (expected; see risk R7).

**Decisions:** DR-001 monorepo · DR-002 FastAPI · DR-003 React+Vite+TS+R3F · DR-004 Diffusers toolchain. Process decision: use Python 3.11 for ML work (audit finding).

**Commands/tests:** environment audit commands (verbatim outputs in `docs/technical/environment-audit.md`); `git status --ignored` dry-run; staged-diff review before each commit. No application tests exist yet (no application code by design).

**Real results:** see environment audit; no dependencies installed; no fabricated measurements — PyTorch CUDA check explicitly deferred to first install.

**Evidence:** this repository state, `docs/technical/environment-audit.md`, decision records, planning v1, commit history of 2026-07-27.

**Commits:** listed in the Phase 0 milestone report (created at end of session; hashes recorded in session handoff).

**Next step:** await Phase 0 review, then Prototype 0 (static interactive 3D skateboard viewer) starting with its Plan-mode plan.
