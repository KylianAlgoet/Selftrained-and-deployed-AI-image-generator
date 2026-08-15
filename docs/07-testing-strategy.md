# Testing strategy

**Created:** 2026-07-27 · **Updated:** 2026-08-15 (M11 audit) · **Status:** **527 pytest, 183 vitest and 38 Playwright E2E tests exist and pass**, measured 2026-08-15. All four layers now exist: the API and frontend-unit layers arrived with M7, the E2E layer with M8, and M9/M10 added validation suites for the report and the deck.

The 527 is not one homogeneous number: **473 system + 16 report-validation + 38 deck-validation**. Only the first 473 test the application. The suite sizes recorded further down are the figures measured at each milestone's closure and are deliberately left as history.

## Layers

| Layer | Tool | What is tested |
|---|---|---|
| Dataset tooling | Pytest | Decode validation, hashing, duplicate detection, manifest completeness (licence fields present), split determinism, **style-label regression guards** (`retro-comic` cannot return) |
| ML inference | Pytest | **Frozen-kit hash lock**, result-schema round-trip, output-filename encoding, memory-tier escalation, aggregation (median/min/max), resource-sampler lifecycle. Pipeline loads and seed→output-hash determinism are verified by real runs recorded in `experiments/registry.csv` rather than in CI, since they require the GPU |
| ML training (Prototype 3, M5) | Pytest | **Smoke-kit hash lock** (`a8052f44…`), **holdout-exclusion proof** joined against `dataset-v1` rather than against the smoke manifest's own split column, deterministic sample order and its fingerprint, source-transform correctness (centre-crop geometry; `none` refuses a mismatched source), **training tier ladder** escalation/termination and its distinctness from the inference ladder, a guard that **gradient accumulation never appears as a memory tier**, gate logic (unmeasured sentinels must never satisfy a gate; `loss_decreased` must never gate), adapter artefact rejection when base-model keys are present, and **AST-parsed import boundaries** in both directions — the schema must import no torch, and neither training runner may import the CLIP similarity evaluator. Actual training, adapter reload and the combined-stack fit are verified by real GPU runs recorded in `experiments/registry.csv` (EXP-016…EXP-019), not in CI |
| API (Prototype 5, M7) | Pytest + FastAPI TestClient, **pipeline stubbed — no GPU, no model, no network** | Endpoint contracts and every status code (422/409/503/504/500); upload security with one negative test per frozen rule (bad extension, MIME/extension mismatch, undecodable bytes, truncated file, oversize, **decompression bomb**, traversal filename, a GIF renamed to `.png`); **generation-id resolution is a registry lookup, never a path join**, so traversal strings have nothing to traverse; the **single-worker guard** rejects a detectable worker count above 1; **lock discipline** — the lock is released only after the generation call returns, a second request is blocked while work is active, a later request succeeds after a controlled abort or failure, and a client disconnect does not free it; **LoRA lifecycle** across `minimal-geometric → ukiyo-e → retro-poster → minimal-geometric` asserting exactly one live adapter each time, plus a style switch after a failed generation; **reference → no-reference → reference** leaving no stale conditioning; the checkpoint integrity gate against missing, wrong-size and **same-size-wrong-content** adapters; and that metadata never contains a filesystem path. Real serving, real aborts and the real integrity gate are verified on the GPU by `scripts/validate_p5_api.py` against an actual uvicorn process, recorded in `docs/evidence/prototype-5/` |
| Frontend units | Vitest | API client (multipart fields, busy/timeout/unavailable classification, non-JSON error bodies); form validation and the DR-008/DR-010 bounded controls; reference preflight; **decal provenance** — that `Upload your own decal` is a production control distinct from the AI reference input, that it calls no generation API, that uploaded artwork gets no reproducibility metadata, and that a failed decode preserves the previous texture; **texture-fit geometry** — both modes' stretch factor, uncovered fraction, canvas size and that the decal is drawn once, upright and unmirrored, plus the **DR-012 production default** (`full-surface`, still one of the two offered modes, with its stretch disclosed); **texture swapping** — the replaced texture is disposed, an object URL is revoked only *after* the replacement resolves, and a failed load keeps the previous decal; **colour space and flipY** on every deck texture |
| End-to-end (M8) | Playwright + Chromium | **37 scenarios** against the **built** frontend (`npm run build && npm run preview`), with every `/api/**` call answered from frozen JSON fixtures — no model, no GPU, no weights. Covers: the shell and a live WebGL context; the **production/review separation**; the styles list and the PARTIAL PASS notice; bounded DR-008/DR-010 controls; reference attach and remove; the **multipart request body itself**; the waiting state; polling cadence; **real denoising step counts**; that a stage with no denominator shows **no percentage**; finalising; the result, both downloads and the decal on the deck; **decal upload issuing no `POST /api/generate`**; a failed decode preserving the previous texture; 409/504/503/422 and a network abort; **camera state surviving a texture swap**; and two viewports. The fixtures are validated against the real Pydantic models by `apps/api/tests/test_e2e_fixture_contract.py`, so a backend field rename breaks a Python test instead of leaving the browser suite passing against a stale shape |

## Suite sizes now (measured 2026-08-15, M11 audit)

| suite | count | gate |
|---|---:|---|
| pytest, whole repository | **527** | all pass — 473 system + 16 report-validation + 38 deck-validation |
| vitest (`apps/web`) | **183** | all pass, 12 files |
| **Playwright E2E** (`apps/web/e2e`) | **38** | all pass, `retries: 0` |
| eslint | — | clean |
| `npm run build` | — | succeeds, 608 modules |

Transcript: `docs/evidence/M11/transcripts/b5-suites.txt`.

## Suite sizes at M8 closure (2026-08-09) — historical

| suite | count | gate |
|---|---:|---|
| pytest (`ml` + `apps/api`) | **473** | all pass; **no Python linter is installed**, so pytest is the Python gate |
| vitest (`apps/web`) | **169** | all pass |
| **Playwright E2E** (`apps/web/e2e`) | **37** | all pass, twice, no flakes, `retries: 0` |
| eslint | — | clean |
| `npm run build` | — | succeeds |

Growth: M7 closed at **406** pytest / **165** vitest / **0** E2E. M8 added +35 upload-security,
+5 `.env.example` guards, +20 E2E fixture-contract, +8 weights-manifest and +4 dataset-integrity
tests on the Python side, +4 preflight tests on the frontend, and the E2E suite from nothing.

**A clean clone runs 468 passed / 5 skipped.** The five are pre-existing conditional skips for
git-ignored assets (raw dataset images, the reference kit), each declaring its reason; 468 + 5 =
473, matching the development machine exactly.

## What the automated suites deliberately do NOT prove

**No test in any of the three suites loads the model or runs a generation.** They prove the code,
the contracts, the upload rules and the interface. Generation quality, VRAM, latency and adapter
integrity under real serving are evidenced separately by `experiments/registry.csv`, EXP-034,
EXP-035, `scripts/validate_p5_api.py` against a real uvicorn process, and the single authorised
clean-clone generation. **A green suite is not evidence that DeckForge AI generates anything**, and
neither kind of evidence is presented as the other.

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

- **Caps are asserted before the work, not tallied after it.** The final validation matrix
  computes its exact total and checks it against the pre-declared 432 *before the first image*.
  A matrix that discovers it overran once it has overrun is not capped.
- **A balanced sampler asserts the balance it claims.** The multi-style run checks the achieved
  per-style exposure and fails loudly, because an unbalanced run would still produce a plausible
  adapter and would silently make the RQ5 comparison meaningless.
- **A generation plan may not contain the same cell twice.** Two overlapping blocks of the final
  matrix repeated 24 configurations. They were byte-identical, so nothing looked wrong - but each
  repeat put a self-pair into a diversity cell and dragged it toward zero, which reads as mode
  collapse. A regression test now forbids a duplicated cell in any arm.
- **Hash-locked evidence is protected from line-ending normalisation.** `core.autocrlf` is true
  here, so without a `.gitattributes` rule Git would rewrite the Gate-1 scoring artifact to CRLF
  on checkout and invalidate the sha256 that proves no human score was edited after unblinding.
  A pytest asserts that hash on every run.

- **Both human scoring artifacts are hash-locked in the test suite.** The Gate-1 and Gate-2
  completed forms are asserted by sha256 on every pytest run and pinned in `.gitattributes`, so
  "no score was edited after approval" is a check rather than a promise.
- **A reproducibility fix is tested in both directions.** The R14 seeding fix has a test proving
  the same seed gives identical initial LoRA weights *and* one proving a different seed does not
  - seeding that pinned every run to one adapter would otherwise pass the first test. A third
  test asserts the seeding happens *before* adapter construction, since seeding afterwards would
  leave the initialisation unseeded and still satisfy the first two.
- **A forward-looking fix must not be allowed to imply a retroactive one.** A test asserts the
  `seed_everything` docstring still states that the M6 artifacts are not bit-reproducible.

## Evidence

Test run outputs for milestone validations are captured in `docs/evidence/` and referenced in the process log and final report.

## Principles added from M8 (testing, deployment, clean-clone)

- **A hash lock over a text file must hash the CONTENT, not the checkout.** The frozen
  `dataset-v1.csv` check compared raw bytes against a constant taken from a CRLF working copy,
  while Git stores LF — so an integrity control intended to prove the dataset was never modified
  **failed on every clean clone** and had only ever passed on its author's machine. The fix hashes
  the content with line endings normalised, and carries a companion test proving it still detects a
  real content edit, because normalising must not buy portability at the cost of sensitivity.
- **Separate an identifier from an integrity check when one value is doing both jobs.**
  `DATASET_V1_SHA256` also feeds `kit_fingerprint()` and every run's recorded `dataset_version`.
  Repointing it would have moved a frozen fingerprint that M6 evidence cites as unchanged. Two
  questions, two constants, and a test asserting they have not been merged back.
- **A mocked E2E suite needs a contract test or it is theatre.** Fixtures are a copy of the API
  contract, and copies rot. A pytest validates every fixture against the real Pydantic models, so a
  renamed backend field breaks a Python test instead of leaving the browser suite green against a
  shape the server stopped sending.
- **Prove a negative with a request log.** "Uploading your own decal never calls the model" is the
  feature's entire value and the demo's fallback. It is asserted by counting `POST /api/generate`
  calls, not by observing that the behaviour looks right.
- **Test the filesystem boundary, not one directory.** The old traversal test asserted a temporary
  directory stayed empty, which shows nothing landed in *one* place. The replacement patches
  `open`, `Path.open`, `Path.write_bytes` and `Path.mkdir` to raise, so **any** filesystem access
  fails — plus a companion test proving that guard can actually fail.
- **A settings file that lies is worse than one that is incomplete.** `.env.example` documented five
  variables nothing read, two of which implied upload security rules were configurable. The
  permitted set is now derived from `config.py` by AST, so it cannot drift again.
- **An assertion that races the implementation should be removed, not slowed down.** The
  "DECAL GENERATED" headline is visible for about a second by design. The fix was never to pad the
  state so a test could read it — that is precisely the dishonesty the progress feature exists to
  avoid — so the test asserts the durable outcome and a comment records why the obvious assertion
  is absent.
- **A clean-clone test is a test, and it finds things.** This one found five real defects on its
  first run, none of which any existing suite could have caught, because every one of them was
  invisible on the machine where the code was written.

## Principles added from Prototype 5 experience

- **Test the claim a design rests on, not the fact that it runs.** The prompt-only path keeps
  IP-Adapter resident at scale 0.0 with a constructed placeholder, which is only sound if the
  reference content cannot influence the result. EXP-035 generated from a grey placeholder and
  from real holdout artwork and required **byte-identical** output. "No exception was raised" would
  have proved nothing about the thing that mattered.
- **Verify live state instead of trusting a call that returned.** `load_lora_weights` returning
  without raising does not mean the requested adapter is the one that will generate. Every style
  switch re-reads the live adapter list and live module count and refuses to proceed if they
  disagree, because generating with the previous style's adapter is indistinguishable from success
  in the response and silently misattributes an image to a style that never produced it.
- **A guard must be proved against a copy, never against the artifact it protects.** The checkpoint
  integrity gate is demonstrated by corrupting a *copy* of an adapter to the same length with
  different content. Damaging a real checkpoint to test the check would destroy a file that R14
  makes unregenerable.
- **Prefer evidence the measurement cannot fake over timing.** The deadline check first asserted an
  early stop by wall clock and failed at 25.69 s on a *cold* request, where nearly all the time was
  the model load — the service was correct and the assertion was wrong. The 504 now reports how far
  the denoising loop got, which no amount of loading time can imitate.
- **A suspicious screenshot is a hypothesis, not a defect.** A capture taken in the same second the
  R3F scene finished initialising showed an empty viewer; three seconds later it rendered correctly
  and the console was clean across both loads. Verify before reporting.
- **Assert that a decision has NOT been made.** Where a choice belongs to the human gate, a test
  asserts the code exports no default. Until 2026-08-07 `textureFit.ts` deliberately had no
  `DEFAULT_TEXTURE_FIT_MODE`, so a default could not appear by accident and quietly pre-empt the
  reviewer. **The technique worked and then retired itself:** once Kylian selected `full-surface`
  at the gate, that test was replaced by tests asserting the *chosen* default (DR-012), that the
  rejected mode still exists rather than being deleted, and that the accepted 1.3008× stretch is
  disclosed in the UI. The negative assertion is what made the replacement a recorded decision
  instead of a silent code change.
