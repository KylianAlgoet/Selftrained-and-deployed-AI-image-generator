# Process log

Newest entries first. Each entry: date, objective, plan, completed work, unfinished work, blockers, decisions, commands/tests, real results, evidence, commits, next step.

---

## 2026-07-30 — Prototype 1: local base-model benchmark (M3) — measurements complete, awaiting scoring

**Objective:** install the project's first ML runtime, verify the GPU, and produce the first measured evidence so the base-model choice for Prototypes 2–5 rests on numbers (RQ2, RQ8, RQ10).

**Plan:** approved M3 plan — two-track benchmark (Track A all candidates at 512×512; Track B each at its designed resolution), pinned immutable model revisions, numbered memory tiers escalated only after a recorded failure, one candidate per fresh process, and a mandatory human-review gate before any conclusion.

**Completed work:** `ml/requirements-inference.txt` (torch 2.13.0+cu126, torchvision 0.28.0+cu126, diffusers 0.39.0, transformers 5.14.1, accelerate 1.14.0, safetensors 0.8.0, huggingface_hub 1.25.1, psutil 7.2.2). CUDA smoke test (EXP-001), hash-locked frozen prompt kit, benchmark schema + runner, aspect-ratio experiment, two orchestrators, and the blank scoring-form generator. **66 pytest tests pass, all CPU-only.** Registry rows EXP-001…EXP-005 written; `docs/prototypes/prototype-1.md` records the full prototype.

**Real results** (all at memory tier 0; no escalation needed anywhere):

```
EXP-001 gate: torch 2.13.0+cu126, bundled CUDA runtime 12.6, driver 610.88,
  RTX 4060 Laptop GPU sm_89, 8187.5 MiB VRAM. Relative error 6.32e-07 fp32,
  5.22e-04 fp16, 4.28e-03 bf16. VERDICT: PASS

EXP-002 SD 1.5 @ 451f4fe1   30/30 ok
  512x512  median  4.069s  alloc 2675 / reserved 3246 / device 4360 MiB
  512x768  median  6.811s  alloc 2979 / reserved 3864 / device 4978 MiB

EXP-004 SDXL base @ 46216598  30/30 ok
  512x512   median  16.512s  alloc  7859 / reserved  9030 / device 8188 MiB
  1024x1024 median 118.733s  alloc 10738 / reserved 14510 / device 8188 MiB, RSS 6807 MiB

EXP-005 aspect ratio (SD 1.5), one geometry per fresh process, 24/24 ok
  512x512   median  4.111s (spread 0.08)  alloc 2675 MiB
  512x1024  median  8.962s (spread 0.09)  alloc 3284 MiB
  512x1536  median 15.244s (spread 0.20)  alloc 3892 MiB
  square-crop -> 170x512 usable, median 4.281s, alloc 2675 MiB
```

**Key finding — "30/30 ok" is misleading for SDXL.** SDXL reported zero failures at every resolution, but at 1024×1024 peak allocated (10738 MiB) and reserved (14510 MiB) both **exceed the 8187.5 MiB of physical VRAM**. Windows WDDM spilled silently into shared host memory rather than raising a CUDA OOM, so no exception existed for the tier-escalation logic to catch: the model degraded quietly instead of failing loudly. About 29× SD 1.5's cost per 512 px image. Only recording three VRAM figures instead of one made this visible.

**RQ8 hypothesis refuted on memory/reliability.** Direct 1:3 generation reached 512×1536 in 3892 MiB — under half the budget — with no failures, while `square-crop`'s real cost is resolution: a 1:3 strip from 512×512 leaves only 170×512 usable pixels. 1:3 is a stated approximation of ~1:3.6 (dimensions must be multiples of 64). Composition quality remains Kylian's to judge.

**Failures and corrections (first-class results):**
- **EXP-003 BLOCKED:** `stabilityai/stable-diffusion-2-1-base` returns HTTP 401, as do `-2-1` and `-2-base`, while SDXL from the same org returns 200 → repository gating, not an outage. Per the approved plan Kylian was **asked** rather than authenticating or substituting a model, and chose to proceed with two candidates. Three declined alternatives recorded, including an ungated community mirror rejected because its fidelity cannot be verified while the original is gated.
- **Instrumentation bug caught by the mandated smoke test:** the resource sampler stored its stop flag as `self._stop`, shadowing `threading.Thread._stop()`, so every `join()` raised `'Event' object is not callable` and destroyed the result row of a run that had already succeeded. Found on the first one-image run, before ~90 min of GPU time was committed. Fixed, hardened, four regression tests added.
- **Measurement-methodology correction with a refuted hypothesis:** EXP-005's first run put all four geometries in one process, contaminating the reserved/device VRAM figures and inflating `square-crop` to 7.96 s for provably identical work. Thermal throttling was **tested and ruled out** — a hotter, more throttled card ran the same work *faster* (4.10 s). Cause was in-process caching-allocator state; one process per strategy cut timing spread ~20×. Documented in `docs/evidence/EXP-005/measurement-methodology-correction.md`.

**Audit corrections:** driver is 610.88, not the 610.74 recorded 2026-07-27 (updated in between). `nvidia-smi`'s CUDA 13.3 is the driver's maximum supported API, not a toolkit PyTorch must match — a CUDA 12.6 wheel runs correctly on it. Also: the venv shipped pip 22.3, which could not resolve torch at all; upgrading to pip 26.2 was a prerequisite.

**Factual observation for the gate (not a quality judgement), corrected after inspecting the Track B sheet:** the phrase "skateboard decal artwork" is often read literally, yielding an image *of a deck* rather than flat printable artwork — but this is **resolution-dependent, not universal**. SD 1.5 at its native 512 px produces predominantly photographic product mockups (decks on concrete/floors/doors, a sticker beside a potted plant); SDXL at 512 px produces deck-shaped panels; **SDXL at its native 1024 px produces flat artwork with no mockup framing** (medallion, flat geometric composition, Great Wave, tiled skull patterns). An earlier draft of this entry asserted the behaviour was uniform across both models — that was an overgeneralisation from the Track A sheet alone and is corrected here. It is also a concrete vindication of the two-track design: scoring only at 512 px would have mis-described SDXL.

**Unfinished work — deliberately gated:** DR-007 (base-model selection), planning/traceability finalisation, issue #4 closure, board move, and the milestone push all wait for Kylian's rubric scores and visual approval. **No winner has been chosen and no quality score has been assigned by the assistant.**

**Evidence:** `docs/evidence/EXP-001…EXP-005/`, `docs/evidence/prototype-1/` (Track A and Track B cross-model sheets, combined CSV, unscored summary), `docs/evidence/EXP-006-scoring/` (blank rubric + form), `experiments/registry.csv`, `docs/prototypes/prototype-1.md`. 84 full-resolution PNGs in git-ignored `outputs/`.

**Commits:** e5684f1 style relabel · 37650b6 pinned deps · 1d51ccc CUDA smoke test · f646ee9 frozen kit · eae6e41 benchmark runner · e25f1e0 orchestrator + scoring form · 8829664 benchmark measurements · (aspect-ratio + prototype doc commit follows).

**Blockers:** none technical. **Next step:** Kylian scores the contact sheets using `docs/evidence/EXP-006-scoring/`, then DR-007, issue #4, and the validated milestone push.

---

## 2026-07-30 — M3 pre-check: dataset style relabelled `retro-comic` → `retro-poster`

**Objective:** before starting Prototype 1, verify that the M2 dataset's style identifiers actually describe the collected material, and correct them if not.

**Plan:** approved M3 plan, step 0 (hard gate before any runtime work): inspect the evidence, choose an accurate stable English identifier, rename it consistently across manifest, schema, captions, tests, scripts, evidence, and documentation, verify that nothing but the label changed, and document the correction without reopening M2.

**Completed work:** Kylian flagged that the `retro-comic` label conflicted with the evidence, which describes WPA posters. Re-inspection of the contact sheet and all 41 manifest rows confirmed the material is **Library of Congress WPA / Federal Theatre Project silkscreen theatre posters** (Carmen, Alien Corn, The Chocolate Soldier, Counsellor at Law, Dracula, Day Is Darkness) with flat silkscreen colour fields, Art Deco/Moderne figures, and dominant display typography — and **no halftone, comic panels, speech balloons, or sequential art whatsoever**. The label was wrong.

Renamed the identifier to **`retro-poster`** and the caption phrase from `"retro comic poster style"` to `"retro silkscreen poster style"` across: `ml/dataset/manifest.py` (`ALLOWED_STYLES`), `ml/dataset/captions.py` (`STYLE_PHRASES`), `ml/dataset/tests/` (captions, manifest, stats), `scripts/collect_dataset_v1.py`, git-ignored `data/raw/candidates.csv` and the `data/raw/retro-comic/` → `data/raw/retro-poster/` directory, `data/manifests/dataset-v1.csv`, regenerated `docs/evidence/dataset-v1/` (statistics, contact sheet renamed to `contact-sheet-retro-poster.jpg`, curation log), `docs/04-dataset-methodology.md`, and this log. Added two regression tests asserting `retro-comic` is gone from `ALLOWED_STYLES` and `STYLE_PHRASES`.

**Why this mattered beyond naming:** the inaccurate label had already propagated into the draft M3 benchmark prompt kit, which asked for *"halftone shading and bold ink outlines"*. Freezing that kit would have prompted for a style absent from the training data and invalidated every later LoRA comparison built on it as a pre-training baseline. Hence the hard gate before any experiment.

**Commands/tests and real results:**

```
> .venv/Scripts/python.exe scripts/build_dataset_v1.py
candidates: 162 / after validation: 148 / after dedupe: 148
manifest written: data\manifests\dataset-v1.csv (148 rows)
contact sheet: contact-sheet-minimal-geometric.jpg (80 KB, 52 items)
contact sheet: contact-sheet-retro-poster.jpg (151 KB, 41 items)
contact sheet: contact-sheet-ukiyo-e.jpg (177 KB, 55 items)
curation log: 14 rejections recorded
splits: {'train': 124, 'val': 17, 'holdout': 7}

> manifest before/after diff check
columns that changed: {'style': 41, 'caption': 41}
UNEXPECTED column changes: {}   id mismatches: 0
sha256 identical: True   split identical: True   filename identical: True
validate_manifest errors: 0
VERDICT: PASS - only style+caption changed

> .venv/Scripts/python.exe -m pytest
36 passed in 1.09s
```

**Decisions:** `retro-poster` chosen over `wpa-poster` (style-descriptive and UI-safe; precise provenance belongs in the manifest and DR text). No image was altered, re-collected, or removed to fit either name. **M2 not reopened** — its acceptance criteria are intact (three styles still defined, licence-verified, deduplicated, split); only the label was imprecise, so issue #3 gets a traceability comment and stays closed. Recorded as a dated correction section in DR-006 with the original decision text preserved.

**Two dataset findings recorded, not silently fixed** (see `docs/04-dataset-methodology.md`, to be resolved with evidence in M4): most `retro-poster` items are **framed/matted scans**, which a LoRA could learn as style; and the material is **text-dominated**, which risks teaching garbled pseudo-lettering since diffusion models render text poorly.

**Evidence:** DR-006 correction section, `data/manifests/dataset-v1.csv`, regenerated `docs/evidence/dataset-v1/`, the diff-check output above.

**Blockers:** none. **Next step:** M3 step 1 — pin the PyTorch/Diffusers inference dependencies (resolved from the official index at execution time), then the CUDA smoke-test hard gate.

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
