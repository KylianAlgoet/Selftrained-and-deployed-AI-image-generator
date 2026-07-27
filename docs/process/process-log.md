# Process log

Newest entries first. Each entry: date, objective, plan, completed work, unfinished work, blockers, decisions, commands/tests, real results, evidence, commits, next step.

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
