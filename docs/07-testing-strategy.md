# Testing strategy

**Created:** 2026-07-27 · **Status:** strategy defined; suites are built with the code they test (no application code exists yet).

## Layers

| Layer | Tool | What is tested |
|---|---|---|
| Dataset tooling | Pytest | Decode validation, hashing, duplicate detection, manifest completeness (licence fields present), split determinism |
| ML inference | Pytest | Pipeline loads, seed determinism (same seed → same output hash), LoRA loading, parameter validation |
| API | Pytest + FastAPI TestClient | Endpoint contracts, upload security (extension/MIME/size/path traversal rejection), error shapes, timeout behaviour |
| Frontend units | Vitest | Form validation, state management, API client, texture-update logic |
| End-to-end | Playwright | Full user flow: prompt + upload + style → generate (mocked model in CI-style runs; real model in the documented E2E evidence run) → 3D preview → download |

## Principles

- Tests accompany the unit they validate and must pass before that unit's commit (see commit protocol).
- GPU-dependent tests are marked/skipped on non-GPU contexts; the real-GPU E2E run is executed at least once and evidenced (final audit requirement).
- Security tests are first-class: malicious filename, oversized file, wrong MIME, non-image bytes each have explicit rejection tests.
- Test results cited in documentation are real runs; failing suites block commits rather than being commented out.

## Evidence

Test run outputs for milestone validations are captured in `docs/evidence/` and referenced in the process log and final report.
