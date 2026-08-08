# DeckForge AI

**Self-trained and deployed AI skateboard-decal generator** — final bachelor resit assignment, Multimedia & Creative Technologies (Erasmushogeschool Brussel), by Kylian Algoet.

## What it will do

A customer of a skateboard manufacturer can:

1. Enter a text prompt (with optional negative prompt)
2. Upload a reference image (PNG/JPG/WEBP)
3. Select a visual style (at least three distinct styles)
4. Generate new decal artwork with a **locally trained** model (text + reference-image conditioning)
5. Preview the decal on an **interactive 3D skateboard deck** (rotate/zoom/reset, correct nose–tail orientation)
6. Download the artwork

## Public planning

The public project planning (milestones M0–M11 with objectives, acceptance criteria, dates, priorities, dependencies, evidence, and live status) is maintained as a GitHub Project:
**https://github.com/users/KylianAlgoet/projects/1** — backed by [repository issues #1–#12](https://github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator/issues?q=is%3Aissue).

## Project status

**M7 — Prototype 5, the integrated MVP: COMPLETE** (approved at the final human visual gate,
2026-08-07). **M8 — testing, deployment and demo preparation: in progress.** Prototypes 0–4 are
complete: the 3D viewer, the 148-item dataset, the base-model benchmark (SD 1.5, DR-007),
reference conditioning (IP-Adapter at 0.55, DR-008), the LoRA method (DR-009) and three per-style
adapters at weight 0.7 (DR-010). The MVP serves them behind a FastAPI service with a React UI and
the 3D deck preview. See `docs/02-planning.md` for the roadmap to submission (2026-08-17).

## Running it locally

**Full instructions: [`docs/deployment/runbook.md`](docs/deployment/runbook.md).** Deployment
strategy and the alternatives considered: [`DR-014`](docs/decisions/DR-014-deployment-and-demo-strategy.md).

```powershell
.\scripts\preflight.ps1      # verify Python, Node, CUDA, ports and the three adapters
.\scripts\start-demo.ps1     # API + frontend; prints the URL
.\scripts\stop-demo.ps1      # stop what was started; confirm the ports are released
```

Or manually, as two processes:

```bash
# 1. API — ONE worker, no reload. This is a correctness requirement, not a preference:
#    the single-flight lock is process-local, and a second resident pipeline does not fit
#    in the 200 MiB of spare VRAM the stack leaves (see DR-011).
.venv/Scripts/python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1

# 2. Frontend
cd apps/web && npm run dev        # http://localhost:5173
```

The pipeline loads on the **first** generation request, so that one takes about 30 s and every
later one 12–13 s. `GET /api/health` reports the device, the process PID and whether the
pipeline is resident.

**Requirements:** Python 3.11 (`.venv` at the repository root), Node >= 20.19, an NVIDIA GPU with
~8 GB VRAM, and the three trained adapters under `outputs/lora/`. Those adapters are git-ignored,
**cannot be regenerated** (risk R14), and are verified by SHA-256 on every request — so the
service refuses to generate without them. What they are and how to restore them:
[`docs/deployment/weights-manifest.md`](docs/deployment/weights-manifest.md).

There is no CPU fallback and no container. Both are deliberate; DR-014 records why.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest    # 461 — API + ML tooling, pipeline stubbed, no GPU
cd apps\web
npm run test                          # 169 — vitest
npm run lint
npm run build
npx playwright test                   # 37 — browser E2E against the built frontend, no GPU
```

No test in any of these suites loads the model or runs a generation. Real-model behaviour is
evidenced separately by `scripts/validate_p5_api.py` against an actual uvicorn process, and by the
experiment registry.

## Why the process is visible

This assignment assesses the research process itself (learning outcomes D1–D7): iterative prototypes, compared alternatives, real experiments with recorded results, honest failure documentation, and full traceability. Key entry points:

| Document | Purpose |
|---|---|
| [`docs/00-project-brief.md`](docs/00-project-brief.md) | Assignment, requirements, learning outcomes |
| [`docs/01-research-plan.md`](docs/01-research-plan.md) | Primary research question and subquestions |
| [`docs/02-planning.md`](docs/02-planning.md) | Milestone planning to submission |
| [`docs/03-architecture.md`](docs/03-architecture.md) | Architecture alternatives and decisions |
| [`docs/06-prototype-overview.md`](docs/06-prototype-overview.md) | Prototype ladder (0–5) |
| [`experiments/registry.csv`](experiments/registry.csv) | Experiment registry |
| [`docs/learning-outcome-traceability.md`](docs/learning-outcome-traceability.md) | Evidence mapped to D1–D7 |
| [`docs/technical/environment-audit.md`](docs/technical/environment-audit.md) | Audited hardware/software environment |
| [`docs/ai-usage.md`](docs/ai-usage.md) | Honest AI-assistance documentation |

## Repository layout

```
apps/api        FastAPI backend — service, uploads, styles, progress telemetry
apps/web        React + Three.js frontend, and the Playwright E2E suite in apps/web/e2e
ml/             Training, inference, dataset tooling, evaluation
data/           Dataset manifests and small licensed samples (raw data not committed)
experiments/    Experiment registry and configs
scripts/        Utility and validation scripts, plus preflight/start/stop tooling
docs/           Research, process, decisions, evidence, deployment, presentation
```

`outputs/` and `deliverables/` are git-ignored: generated images, model adapters and derived
upload packages are regenerable or restorable, and model weights are never committed.

## Setup

See [`docs/deployment/runbook.md`](docs/deployment/runbook.md) for the full procedure, and
[`docs/technical/environment-audit.md`](docs/technical/environment-audit.md) for the audited
environment this was validated on.
