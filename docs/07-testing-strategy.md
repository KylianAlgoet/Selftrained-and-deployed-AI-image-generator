# Testing strategy

**Created:** 2026-07-27 · **Updated:** 2026-07-30 (Prototype 1) · **Status:** strategy defined; **66 pytest tests exist and pass** (dataset tooling + ML inference layers). API, frontend-unit, and E2E layers arrive with their code.

## Layers

| Layer | Tool | What is tested |
|---|---|---|
| Dataset tooling | Pytest | Decode validation, hashing, duplicate detection, manifest completeness (licence fields present), split determinism, **style-label regression guards** (`retro-comic` cannot return) |
| ML inference | Pytest | **Frozen-kit hash lock**, result-schema round-trip, output-filename encoding, memory-tier escalation, aggregation (median/min/max), resource-sampler lifecycle. Pipeline loads and seed→output-hash determinism are verified by real runs recorded in `experiments/registry.csv` rather than in CI, since they require the GPU. LoRA loading arrives with Prototype 3 |
| API | Pytest + FastAPI TestClient | Endpoint contracts, upload security (extension/MIME/size/path traversal rejection), error shapes, timeout behaviour |
| Frontend units | Vitest | Form validation, state management, API client, texture-update logic |
| End-to-end | Playwright | Full user flow: prompt + upload + style → generate (mocked model in CI-style runs; real model in the documented E2E evidence run) → 3D preview → download |

## Principles

- Tests accompany the unit they validate and must pass before that unit's commit (see commit protocol).
- GPU-dependent tests are marked/skipped on non-GPU contexts; the real-GPU E2E run is executed at least once and evidenced (final audit requirement).
- Security tests are first-class: malicious filename, oversized file, wrong MIME, non-image bytes each have explicit rejection tests.
- Test results cited in documentation are real runs; failing suites block commits rather than being commented out.

## Principles added from Prototype 1 experience

- **Pure logic is kept importable without torch or diffusers.** `ml/inference/bench_schema.py` deliberately imports neither, so the schema, filename, tier-escalation and aggregation tests run on any machine in under a second. Only the runner touches the GPU stack.
- **Frozen research artefacts get hash locks, not just review.** The evaluation kit is pinned by a SHA-256 fingerprint asserted in a test, with a companion test proving the lock is actually sensitive to change. A silent edit to a prompt or seed would otherwise invalidate every cross-prototype comparison without anything failing.
- **Guard against reporting what the code cannot know.** A test asserts the measurement summary contains no quality verdict ("winner", "best", "recommend", …), so the tooling cannot pre-empt the student's rubric scoring.
- **Terminology corrections get regression guards.** After the `retro-comic` → `retro-poster` relabel, two tests assert the old identifier is absent from `ALLOWED_STYLES` and `STYLE_PHRASES`.
- **A minimal end-to-end smoke test precedes every long run.** This is a testing requirement, not just a process nicety: the one-image smoke test caught a real defect in the resource sampler (an attribute shadowing `threading.Thread._stop()`) that destroyed the result row of a run which had already succeeded — before ~90 minutes of GPU time was committed.
- **Measurement validity is itself testable.** One configuration per OS process is mandatory whenever VRAM or timing is measured, after an incident where a shared process contaminated both. See `docs/evidence/EXP-005/measurement-methodology-correction.md`.

## Principles added from Prototype 2 experience

- **Measurement instrumentation must never enter the workload it measures.** Generation and metric
  computation are separate phases in separate processes. The CLIP encoder used for similarity
  indicators is 2.35 GiB; loading it inside a text-only or img2img process to compute a metric would
  have inflated exactly the VRAM figures the method comparison rests on. **This is enforced by a
  test, not by discipline:** a pytest parses the Phase-1 runner with `ast` and fails if it ever
  imports the similarity module, and a second test guards the reverse direction. The evidence is
  also visible in the data — `image_encoder_revision_sha` is empty on every text-only and img2img
  row, proving no encoder was resident there.
- **A tolerance is pre-declared in code before the measurement it judges.** The 2 % clean-process
  spot-check tolerance lives in `ml/inference/reference_schema.py` with a test asserting its value,
  so it cannot be tuned after seeing the result.
- **"Not measured" and "failed" are different states and must not share a code path.** The
  process-isolation report initially printed "REJECTED — a pair exceeded the tolerance" when the
  pairs were merely absent from a partial dataset. Reporting missing data as a failed check is a
  false claim; the three outcomes (accepted, rejected, not measured) are now distinct.
- **An untestable condition is reported as inapplicable, not as a failure.** IP-Adapter-Plus ran at
  one influence level by design, so monotonicity is untestable for it; labelling that "not met"
  would report a failure it never had.
- **Inverted parameters get an explicit regression guard.** img2img `strength` runs backwards
  (lower = stronger reference). A test asserts `level_for_value("img2img", 0.30) == "strong"`, so no
  chart or table can silently invert the entire conclusion.
- **Descriptive labels are verified against the artefact before anything is built on them.** The
  approved plan described a reference as a "cresting wave"; opening the image showed an interior
  scene, and that phrase belonged to a *prompt*. A regression test now guards the corrected label.
- **Interrupted runs restart their unit rather than resuming mid-file.** Each experiment runner
  deletes its own results file at start, so a killed run leaves no half-written evidence to be
  mistaken for a complete one.

## Evidence

Test run outputs for milestone validations are captured in `docs/evidence/` and referenced in the process log and final report.
