# DR-001: Repository structure — monorepo

**Date:** 2026-07-27 · **Status:** accepted

## Context
The project combines ML training, a FastAPI backend, a React frontend, dataset tooling, experiments, and jury-assessed process documentation. The assignment requires visible, traceable process evidence in a single GitHub result.

## Alternatives
1. **Monorepo** (single repository, mandated layout)
2. **Multi-repo** (separate ml / api / web / docs repositories)
3. **Flat single folder** (no structural separation)

## Criteria and evaluation
Weighted matrix in `docs/03-architecture.md` (D-A): jury traceability (5), tooling simplicity (4), deadline risk (4), reproducibility (4), separation of concerns (3). Monorepo 93/100, flat 69, multi-repo 51.

## Decision
Monorepo with the master-prompt layout (`apps/`, `ml/`, `data/`, `experiments/`, `scripts/`, `tests/`, `docs/`, `deliverables/`).

## Consequences
- One Git history documents the entire process (D3/D7 evidence).
- Clean-clone validation tests everything at once.
- Requires discipline in `.gitignore` to keep datasets/weights out of the shared history.
