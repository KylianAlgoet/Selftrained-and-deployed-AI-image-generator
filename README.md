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

**M7 — Prototype 5, the integrated MVP: built and validated, awaiting the review gate**
(2026-08-06). Prototypes 0–4 are complete: the 3D viewer, the 148-item dataset, the base-model
benchmark (SD 1.5, DR-007), reference conditioning (IP-Adapter at 0.55, DR-008), the LoRA method
(DR-009) and three per-style adapters at weight 0.7 (DR-010). The MVP now serves them behind a
FastAPI service with a React UI and the 3D deck preview. See `docs/02-planning.md` for the
roadmap to submission (2026-08-17).

## Running it locally

The API and the frontend are two processes.

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

**Requirements:** the Python 3.11 virtual environment at the repository root (`.venv`), Node 20,
an NVIDIA GPU with 8 GB VRAM, and the three trained adapters under `outputs/lora/` — these are
git-ignored and are verified by sha256 on every request, so the service refuses to start
generating without them.

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
apps/api        FastAPI backend (planned)
apps/web        React + 3D frontend (planned)
ml/             Training, inference, dataset tooling, evaluation
data/           Dataset manifests and small licensed samples (raw data not committed)
experiments/    Experiment registry and configs
scripts/        Utility and validation scripts
tests/          Cross-cutting tests
docs/           Research, process, decisions, evidence, presentation
deliverables/   Final PDFs and submission artifacts
```

## Setup

Setup instructions will be added once the architecture decision (Phase 0) is executed and dependencies are pinned. Environment prerequisites are documented in [`docs/technical/environment-audit.md`](docs/technical/environment-audit.md).
