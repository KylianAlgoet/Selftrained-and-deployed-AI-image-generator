# DR-002: Backend framework — FastAPI

**Date:** 2026-07-27 · **Status:** accepted (implementation validated in Prototype 5)

## Context
The backend must expose generation endpoints, run the Python ML inference stack in-process, validate untrusted uploads rigorously, and be testable within the deadline.

## Alternatives
1. **FastAPI** (+ Pydantic)
2. **Flask**
3. **Node/Express** (separate Python worker required)

## Criteria and evaluation
Weighted matrix in `docs/03-architecture.md` (D-B): ML-stack fit (5), input validation (5), async/long requests (4), OpenAPI evidence (3), Pytest testability (4), time-to-productivity (4). FastAPI 121/125, Flask 81, Express 65.

## Decision
FastAPI with Pydantic models for all request/response validation.

## Consequences
- Upload security requirements (`.claude/rules/security.md`) implemented as Pydantic + explicit validators.
- Auto-generated OpenAPI docs serve as API evidence for the jury.
- Long generation calls need timeout and loading-state design from the start.
