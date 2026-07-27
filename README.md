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

## Project status

**Phase 0 — research and repository foundation** (started 2026-07-27). No application code exists yet; the research framework, planning, environment audit, and documentation system are being established first. See `docs/02-planning.md` for the roadmap to submission (2026-08-17).

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
