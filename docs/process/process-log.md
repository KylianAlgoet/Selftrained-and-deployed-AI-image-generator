# Process log

Newest entries first. Each entry: date, objective, plan, completed work, unfinished work, blockers, decisions, commands/tests, real results, evidence, commits, next step.

---

## 2026-08-10 (later) — the CI fix failed on CI, and what the runner taught

**Objective:** the first fix (`316b2cd`) passed every local gate and still failed remotely. Make the
measurement survive a runner instead of a laptop.

**Real CI result, run #5 on `316b2cd`:** pytest **PASS** (2m 31s) · vitest/eslint/build **PASS**
(59s, 181 vitest, and the new production-bundle handle guard passed) · playwright **FAIL** — **35
passed, 3 failed**, 16.8 m. The camera scenario exceeded the **60 s** test timeout inside the settle
loop; `errors.spec.ts` 409 and 504 failed immediately after it, and everything from scenario 15
onwards passed.

**Diagnosis.** Two mistakes, neither visible without a runner:

1. **The settle loop polled from Node** — up to 120 `waitForTimeout` + `page.evaluate` round trips
   per phase, four phases per test. Locally 6.6 s; on a runner where the WebGL scenarios are ~15x
   slower (scenario 11: 30.6 s against 2.1 s here) that is unaffordable.
2. **It waited in milliseconds for something that happens in frames.** Damping advances only on a
   rendered frame, so a wall-clock settle rule is a bet on the frame rate — and a software
   rasteriser is where that bet loses.

The two `errors.spec.ts` failures are **attributed, not diagnosed**: contiguous with the timed-out
test, untouched by the change, green in the previous run, and followed by a clean recovery, which is
what a poisoned context teardown looks like. Recorded as an inference. If they fail again once the
camera test passes, they are independent.

**Completed work:** the whole measurement moved inside the page — one `page.evaluate` per phase
waits a fixed number of **rendered frames**, reads the pose, waits a few more and reads again. Four
round trips instead of several hundred. The second read yields the **residual drift**, and the
comparison tolerance is derived from it (`max(drift x 20, 1e-3)`) rather than hard-coded, so the
rule adapts to whatever machine runs it. Drift above `MAX_RESIDUAL_DRIFT` fails the test as
**UNMEASURED** rather than blaming the texture swap. Two tolerance-independent assertions were added:
after the swap the camera must remain >1.0 from the opening pose, and after Reset view it must be
back at it. The probe now reports frames and elapsed ms, so a third failure would arrive with the
runner's frame rate attached instead of another guess.

**A second defect, caught by a unit test rather than by CI.** The first draft used
`MAX_RESIDUAL_DRIFT = 0.05`; with the factor of 20 that made the worst permitted tolerance exactly
**1.0**, which is `DISTINCT_VIEWPOINT` — wide enough to swallow an entire change of viewpoint, making
the comparison decorative. A vitest case asserting
`toleranceForDrift(MAX_RESIDUAL_DRIFT) < DISTINCT_VIEWPOINT` failed and caught it before the commit.
Tightened to **5e-3**: worst-case tolerance 0.1, a 10x margin under `DISTINCT_VIEWPOINT` and 37x
under the 3.7-unit move a reset makes. This is exactly the failure the unit tests are biased to
catch.

**Commands and real results** (2026-08-10, validated machine):

| gate | result |
|---|---|
| camera scenario x5 | **5 passed**, 40.3 s incl. build |
| full Playwright suite | **38 passed**, 1.2 m |
| `npm run test` | **183 passed** |
| `npm run lint` · `npm run typecheck:e2e` | clean |
| `npm run build` → `npm run verify:no-e2e-handle` | succeeds → ok |
| `.venv/Scripts/python.exe -m pytest` | **473 passed** |

**Lesson worth keeping for the report.** A green local sweep is not evidence about CI, and this
milestone has now produced that lesson twice — first as a dataset hash that only ever passed on its
author's machine, now as a test that only ever passed on its author's GPU. The fix in both cases was
to change the measurement, not the threshold.

**No GPU inference was run. The generation total remains 27.**

**Blockers:** the remote run for attempt 2 has not happened. **Nothing here is CI evidence yet.**

**Evidence:** `docs/evidence/M8/ci/camera-preservation-fix.md` (attempts 1 and 2, with the real run
#5 table).

**Next step:** commit, push, wait for the run. M8 closes only when all three jobs are green.

---

## 2026-08-10 — M8 REOPENED: the last red CI job, fixed at the measurement

**Objective:** make the remote CI run green. M8 was closed locally on 2026-08-09 and pushed; the
first GitHub Actions run then failed one Playwright scenario, so criterion 1 ("backend, frontend and
E2E suites pass") was evidenced locally but not remotely.

**Plan:** replace the screenshot-based camera-preservation measurement with read-only camera-state
instrumentation gated to E2E builds. Change no application behaviour, and do not solve it with a
larger timeout.

**Reported CI state for `68d1bf2`:** pytest **PASS** · vitest/eslint/build **PASS** ·
Playwright **37 passed, 1 failed** — `replacing the decal does not reset the camera`, timed out
after **300 000 ms** on the Windows runner.

**Completed work:**

- `src/viewer/e2eCameraState.ts` — pure, import-free camera-state helpers plus the handle name,
  shared by the app and the Playwright project.
- `src/viewer/E2ECameraProbe.tsx` — publishes `window.__deckforgeE2ECamera.cameraState()`. Read-only:
  it copies numbers out of the live camera and OrbitControls and writes nothing back.
- `vite.config.ts` — `__DECKFORGE_E2E__`, a literal-substituted `define`, so an ordinary build makes
  the probe dead code and the bundler removes it. `playwright.config.ts` sets `VITE_E2E=1` on its
  own `webServer` build and nothing else does.
- `scripts/assert-no-e2e-handle.mjs` + `npm run verify:no-e2e-handle`, wired into the `frontend` CI
  job after `npm run build`. It reads the handle name from the source, so a rename cannot leave it
  checking a dead string.
- The test now compares camera position, quaternion and orbit target structurally, keeps the real
  orbit drag and the precondition that the drag registered, and drops its `test.setTimeout` override.
- Twelve vitest cases for the comparison rule, biased towards proving it is not too lax.

**A defect found in my own work, recorded rather than hidden.** The first rewrite defined "at rest"
as two consecutive reads equal to within 1e-6 and failed 3/3. drei enables OrbitControls damping by
default, so the camera decays towards rest and **never exactly arrives**; that state does not exist.
A temporary diagnostic spec traced the real decay *before* any threshold was chosen, and was deleted
afterwards. The trace also exposed a second trap: damping only advances on a rendered frame, so a
stalled render loop on a software rasteriser can emit two identical reads mid-flight. Each sample
now waits for a real frame and two consecutive quiet samples are required.

**Decisions:** a `define` rather than `import.meta.env.VITE_E2E`, because only a define is
guaranteed to be substituted literally and therefore to remove the handle from the bundle rather
than merely disable it. Tolerances taken from the measured decay, not chosen: `SETTLE_EPSILON` 1e-5,
`CAMERA_EPSILON` 1e-3 — ~30x above damping residue and ~3700x below the 3.7-unit move the test must
catch. No decision record: this changes no architecture and no production behaviour.

**Commands and real results** (all 2026-08-10, validated machine):

| gate | result |
|---|---|
| `npx playwright test -g "replacing the decal..." --repeat-each=5` | **5 passed**, 52.1 s incl. build |
| `npx playwright test` | **38 passed**, 1.2 m (the scenario itself 6.6 s, was ~138 s) |
| `npm run test` | **181 passed** (169 + 12 new) |
| `npm run lint` · `npm run typecheck:e2e` | clean |
| `npm run build` → `npm run verify:no-e2e-handle` | succeeds → `ok: none of the 6 built assets contain "__deckforgeE2ECamera"` |
| `VITE_E2E=1 npm run build` → same guard | **FAIL**, as it must — the guard detects the handle |
| `.venv/Scripts/python.exe -m pytest` | **473 passed** |

The E2E build check is the load-bearing one: without it, "the production bundle is clean" would be a
check that passes on everything.

**Stronger, not merely faster.** The old pixel comparison could only say *the frame changed*, so
camera preservation was argued indirectly from Reset view still having work to do. The test now
asserts the pose is **identical** after the swap, and that Reset view returns to the **opening**
pose — an assertion that could not previously be written.

**No GPU inference was run. The generation total remains 27.**

**Unfinished work / blockers:** **the remote CI run has not happened yet.** Nothing here may be
reported as CI evidence until all three jobs are green. M8 stays open until then.

**Evidence:** `docs/evidence/M8/ci/camera-preservation-fix.md`,
`docs/evidence/M8/ci/camera-damping-trace.md`, updated `docs/evidence/M8/README.md`.

**Next step:** commit, push, and wait for GitHub Actions. If green, close M8 formally; only then
consider M9.

---

## 2026-08-09 — M8 CLOSED: all six acceptance criteria met

### Milestone report

**MILESTONE:** M8 — testing, deployment, clean-clone validation and demo preparation.

**STATUS:** **COMPLETE**, closed **locally only**. Nothing pushed; issue #9 and the project board
are untouched and remain Kylian's. **M9 has not begun.**

**BRANCH:** `main`.

**RESEARCH QUESTION (RQ12):** how is a locally trained, GPU-bound generator deployed so that it is
reproducible for a third party and reliable for a live demonstration? **Answered in DR-014:**
native local deployment on the validated machine plus backup demo assets, with Docker screened out
on measured constraints and cloud GPU rejected on cost and measurement validity.

**WORK COMPLETED:** baseline re-measured and an environment drift corrected · 35 backend and 4
frontend upload-security tests · `.env.example` rewritten and AST-guarded · **37 Playwright E2E
scenarios** with a pytest fixture-contract guard · DR-014 · weights manifest with an 8-test guard ·
four PowerShell scripts (verify-weights, preflight, start-demo, stop-demo) · deployment runbook ·
README rewritten · non-GPU CI workflow · a real clean-clone validation · the authorised clean-clone
generation · timed demo script · backup demo plan and asset builder · feature-freeze record.

**TESTS AND VALIDATION**

| gate | M7 close | M8 close |
|---|---:|---:|
| pytest | 406 | **473** |
| vitest | 165 | **169** |
| Playwright E2E | **0 — did not exist** | **37** |
| eslint | clean | clean |
| production build | succeeds | succeeds |

Clean clone: **468 passed, 5 skipped** (pre-existing conditional skips for git-ignored assets;
468 + 5 = 473). Playwright run twice end to end, no flakes, `retries: 0`.

**ACTUAL RESULTS**

- **The clean clone reproduced M7's Phase A output byte-for-byte** — sha256 `46bbf160e427…`,
  1 089 939 bytes, fresh environment, three days later, verified two independent ways.
- `peak_allocated_mb` **5143.73** — byte-identical across EXP-019b, EXP-034 and this run.
- Clone to running service in **~10 minutes**.
- The service starts with **`allocated_mb: 0.0`** — lazy loading measured, not asserted.
- The weight restore path fails loudly when weights are absent (3/3) and passes after restore (3/3).

**FIVE DEFECTS FOUND.** M8 was scoped to verify and it discovered — every one invisible on the
machine the code was written on. (1) The frozen dataset hash **failed on every clean clone**: it
hashed a CRLF working copy while Git stores LF, so an integrity control had only ever passed
locally. (2) `.env.example` documented five variables nothing reads, two implying upload security
rules were configurable. (3) The audited Node version was stale — 20.18.0 recorded, 24.18.0 actual.
(4) `apps/api/requirements.txt` claimed a pin it did not make. (5) `uvicorn --workers 1` starts two
processes, so a naive stop strands the worker on port 8000.

**DECISIONS:** DR-014 · seven at the human gates (Node re-baseline, deployment, Playwright scope,
CI not pushed, hash fix, generation authorised, requirements comment) · the two dataset constants
kept separate · the planned CI skip-marker **dropped** after checking disproved its premise · the
1 MB PNG kept out of Git per project policy.

**RISKS:** **R15** (live demo failure) and **R16** (checkpoints unrestorable) added. R12 updated
with the container-runtime rejection. R11 noted against CI's Hugging Face dependency.

**PLANNING CHANGES:** M8 complete 2026-08-09, planned Aug 13–15 — four days early on M7's buffer.
**~11 h actual vs 10 h estimated.**

**RISKS OR BLOCKERS:** none blocking. Open and deliberate: CI has never run · 3 pre-existing npm
advisories · transitive Python versions unpinned · no screen recording · the **external weight
backup has not been exercised** (the clone restored from the working repository).

**NEXT ACTION:** Kylian's — the push, issue #9, the board. Then **M9, the research report.**

---

## 2026-08-09 — M8.8: the human gate, the hash fix, and one authorised generation

**Objective.** Resolve the three decisions the clean clone surfaced, then satisfy the real-output
criterion with exactly one generation.

**Kylian's three decisions at the gate.**

1. **Frozen hash** — re-record against what Git actually stores.
2. **Generation** — **authorised**, one run.
3. **Transitive pins** — fix the misleading comment, move no versions.

### The hash fix, and the cascade that shaped it

Implementing decision 1 naively would have caused real damage, and the investigation caught it
before anything was changed. `DATASET_V1_SHA256` is **not only** used by the failing test: it is
mixed into `kit_fingerprint()` — locked at `fc11d828…` and cited across M6 evidence as unchanged —
and it is recorded as `dataset_version` in **every M6 training run**. Repointing it would have
moved the frozen fingerprint and desynchronised every recorded run, for what is only a line-ending
representation.

So the two questions were separated, because they are different questions:

| constant | answers | status |
|---|---|---|
| `DATASET_V1_SHA256` = `cd18cbb0…` | which dataset configuration was M6 run against? | **unchanged** — an identifier |
| `DATASET_V1_CONTENT_SHA256` = `b38996ae…` | has the content been modified? | **new** — the integrity check |

`sha256_dataset_content()` normalises line endings before hashing, so the check is **independent of
the checkout** — `core.autocrlf`, `.gitattributes` and the host platform cannot move it. The
working copy was normalised to LF, producing **zero Git diff** because the blob was already LF.

Four tests added: the check itself · one proving line-ending independence · one proving it **still
detects a real content edit**, so normalising did not make it blind · one asserting the two
constants have not been collapsed into one. Verified after: `kit_fingerprint()` still `fc11d828…`,
`dataset_version` still `cd18cbb05307`, **473 pytest locally**, and in the clean clone **468 passed,
5 skipped, 0 failed** (the skips are pre-existing conditional skips for git-ignored assets;
468 + 5 = 473).

### The authorised generation — PASS

Driven **from the browser**, not curl: a curl call proves prompt → API → model → PNG, but the
criterion is the whole chain, and only a browser run also proves PNG → frontend → 3D deck.
`minimal-geometric`, prompt-only, seed 42, defaults.

HTTP 200 · `MYOcI34c3yfyj2z1YtKAtA` · 30/30 steps · EXP-027 step 300, adapter hash matching the
gate-2 record · `generate_seconds` **16.649** · browser wall **63.16 s** including the cold load ·
peak allocated **5143.73 MiB** · spare **218.0 MiB** · 1 `POST /api/generate` · **0 console errors**.

**The strongest result of the milestone: the clean clone reproduced M7's Phase A output
byte-for-byte.** Same sha256 `46bbf160e427…`, same 1 089 939 bytes, a freshly built environment
three days later. Verified two ways — `sha256sum` on both files, and the service's own recorded
`image_sha256`.

**This does not contradict R14 and must never be quoted as if it did.** R14 is about *training* not
being bit-reproducible from seed. This is *inference*: a fixed adapter plus a fixed seed and
settings is deterministic and portable. Different halves of the pipeline; both statements true. It
is also independent corroboration that the restored adapter is the right file — a different adapter
could not have produced those bytes.

`peak_allocated_mb` 5143.73 is byte-identical to EXP-019b and EXP-034 across three milestones.
**`spare_device_mb` 218.0 does NOT supersede the 200.0 MiB ceiling** — 218.0 is the prompt-only
path, and 200.0 belongs to the reference-conditioned path this run deliberately did not use.

The cold-load screenshot captured DR-013's rule in a real cold start: stage name, *"No step
percentage at this stage"*, no invented bar.

**Generation count is now 27** — 25 research + Kylian's M7 review run + this deployment validation.
**Stated as 27, never rounded back to 25.** It has **no `EXP-###`** and is **not** in
`experiments/registry.csv`.

**Decisions taken here.**

1. **The two hash constants stay separate**, with a test asserting they are not merged.
2. **The 1 MB PNG is not committed.** Generated images live in git-ignored `outputs/` in this
   project and it would be larger than anything tracked under `docs/evidence/`. Its hash is
   recorded in three places, the screenshots show the result and the deck, and it is byte-identical
   to an already-recorded Phase A file.
3. **The original clean-clone failure is preserved in the evidence**, not edited out. It is the most
   valuable thing the test produced.

**Afterwards.** Both processes stopped, all ports released, no orphans, and the **4.9 GB clean-clone
directory deleted** — regenerable in ~10 minutes from the runbook, which is the point.

**Evidence.** `docs/evidence/M8/clean-clone/real-output.md` + `real-output/`, and the updated
`log.md`.

**Next step.** M8.10 — feature freeze, documentation, traceability and closure.

---

## 2026-08-09 — M8.7: the clean-clone test, and the defect it found on the first attempt

**Objective.** Prove a third party can clone the repository and reach a working system, using no
GPU and no generation.

**Completed work.** Full clone into `C:\Expert Lab\DeckForge-M8-clean-clone`, **outside** the
working repository, at commit `824838f`. Steps 1–15 and 18 executed with real output captured.

**Real results: 17 of 18 non-GPU steps PASS, 1 FAILS.** Clone to running service in **~10 minutes**.

| step | result |
|---|---|
| clone, ignored trees absent | PASS |
| venv, pinned install, `pip check` | PASS — 402 s |
| `npm ci`, build, lint, vitest, typecheck | PASS — 169 vitest, eslint clean |
| **pytest** | **FAIL — 1 test** |
| weight restore + verify | PASS — 3/3 FAIL before, 3/3 PASS after |
| preflight, start, health, styles | PASS |
| browser on the real backend, decal on the deck | PASS — 0 generate calls, 0 console errors |
| Playwright in the clone | PASS — 37/37 |
| stop, ports released, no orphans | PASS |

### The blocking defect — a frozen hash that fails on every clean clone

`test_dataset_v1_is_byte_identical_to_the_recorded_hash` fails. Diagnosed to certainty:

| | bytes | endings | sha256 |
|---|---:|---|---|
| dev-machine working copy | 63 152 | 149 × CRLF | `cd18cbb0…` ← the recorded constant |
| **the Git blob** | **63 003** | 149 × LF | `b38996ae…` |
| every clean clone | 63 003 | 149 × LF | `b38996ae…` |

**The content is identical** — normalising line endings makes them byte-for-byte equal, and the
149-byte difference is exactly the 149 lines.

`dataset-v1.csv` was committed **before** `.gitattributes` gained `data/manifests/*.csv -text`, so
Git normalised it to LF in the blob while the working copy kept CRLF and was never re-checked-out.
`DATASET_V1_SHA256` was then recorded from **the working copy**, not from what Git stores.

**This is an integrity control that has been pinned to a machine-local representation since M6.**
Its purpose is proving the dataset was never modified; it has only ever passed on the one machine
holding the stale bytes. M6 identified `core.autocrlf` as exactly this hazard and added
`.gitattributes` in response — the rule protects future checkouts, but nobody re-derived the
constant, and no clean clone had been attempted until now. **This is the class of defect a
clean-clone test exists to find, and it surfaced on the first attempt.**

**NOT FIXED.** The change is one constant, but it is a value documented as **frozen** across M6
evidence, so it is Kylian's decision and goes to the human gate with the generation authorisation.

### Two secondary findings, both recorded, neither changed

1. **`apps/api/requirements.txt` claims a pin it does not make.** `starlette==1.4.1` and three
   others sit under *"pinned here so the set is reproducible"* — **commented out.** The clone
   installed starlette **1.6.0** and numpy **2.4.4**. Everything passed and `pip check` was clean,
   but the file states something untrue. Pinning transitive deps is a dependency move under freeze,
   so it needs approval.
2. **`deliverables/` appears in a clean clone** despite being git-ignored, because
   `deliverables/.gitkeep` is tracked and `.gitignore` never affects tracked files. Harmless — an
   empty placeholder, no derived package — but worth recording so nobody thinks the rule failed.

**What the clone positively proved.** pip 22.3 shipped and could not resolve torch (the M3 finding
reproduced exactly, so the runbook's upgrade step is load-bearing) · the runbook's install order
works verbatim, CUDA index included · CUDA available in the clone · the restore path fails loudly
when weights are absent and passes after `-RestoreFrom` · the service is healthy with
`pipeline_loaded: false` and `allocated_mb: 0.0` · the real API served the real styles with
`retro-poster` marked PARTIAL PASS · and the **entire 3D path works with zero GPU cost**.

**Stated limitation.** The weights were restored from the working repository, **not** from the
external backup drive, which was unavailable this session and whose path is deliberately not
guessed. The *mechanism* was validated and it is source-agnostic; a restore from the real external
backup **is not claimed**.

**Commands run.** `git clone` · `py -V:3.11 -m venv` · `pip install` (4 requirement files + torch) ·
`pip check` · `npm ci` · `npm run lint/test/typecheck:e2e/build` · `pytest` (×2) ·
`verify-weights.ps1` (×2) · `preflight.ps1` · `start-demo.ps1` · health/styles/progress ·
a Playwright-driven browser check against the real backend · `npx playwright test` ·
`stop-demo.ps1`.

**Evidence.** `docs/evidence/M8/clean-clone/` — `log.md`, `environment.md`, `api-health.json`,
two screenshots.

**Blockers.** **The frozen-hash defect blocks the clean-clone acceptance criterion**, and its fix is
Kylian's decision. The clone is **retained** so the authorised generation can run in it without
repeating the ten-minute setup.

**No GPU inference ran**; the generation total stays at 26.

**Next step.** M8.8 — the human gate: the hash decision, and authorisation for one real generation.

---

## 2026-08-09 — M8.6: a CI workflow, and a planning assumption that was wrong

**Objective.** Add a non-GPU CI workflow, committed locally and not pushed.

**Completed work.** `.github/workflows/ci.yml` with three jobs (pytest · vitest/lint/typecheck/build
· mocked Playwright), all on `windows-latest`. Evidence written.

**The approved plan was wrong on one point, and checking is what caught it.** The plan said
checkpoint-dependent pytests would need an explicit **skip marker** in CI, assuming they read the
three production adapters. `outputs/lora/` was moved aside locally and the whole suite re-run:
**all 469 tests still passed.** The checkpoint tests build their own adapter files under `tmp_path`
— including the integrity-gate tests, which corrupt a *copy* precisely because R14 makes the real
files unregenerable.

So **no marker, no skip and no conditional was added.** Adding one would have implied reduced CI
coverage where there is none. The workflow asserts the opposite instead: it **fails if
`outputs/lora` exists on the runner**, so a green build can never be explained by weights having
leaked into the repository.

**Decisions.**

1. **`windows-latest`, not `ubuntu-latest`.** Windows 11 + PowerShell 5.1 is the only platform this
   project has been validated on and DR-014 deploys natively on it. Linux CI would test a
   configuration nobody supports and imply cross-platform support that was never established.
   Windows runners cost 2× minutes; that is the right price for not making an unearned claim.
2. **CI installs CPU torch, and the file says so.** Production is `torch 2.13.0+cu126` from
   PyTorch's own index. CI validates the **code against the same library versions**; it does not
   validate the production install. The clean-clone test does that, on the real hardware.
3. **CI is not a substitute for the GPU evidence, and the record says so in its first lines.** A
   runner has no GPU and no adapters, so a green badge says nothing about generation quality, VRAM,
   latency or adapter integrity.

**Status — stated plainly: the workflow has NEVER RUN.** It is committed locally and **not
pushed**; the first GitHub Actions run is Kylian's decision under CLAUDE.md rule 6. There is no
green badge and no run URL to cite, the YAML has been parsed but not executed by a runner, and the
first run may need fixes. M8's test evidence is therefore the **local** runs.

**One risk carried.** `test_style_kit.py` loads the real CLIP tokenizer, which transformers
downloads from Hugging Face. **R11 records three occasions where third-party hosting became
unavailable mid-project**, so a red build with no defect behind it is possible. If it proves flaky
the honest fix is a network marker, not deleting the token-id assertions.

**Commands run.** `pytest` with `outputs/lora` moved aside and restored · YAML parse check.

**Evidence.** `docs/evidence/M8/tests/ci-workflow.md`.

**Unfinished work / blockers.** Nothing pushed. **No GPU inference ran**; the total stays at 26.

**Next step.** M8.7 — the non-GPU clean-clone validation.

---

## 2026-08-09 — M8.5: deployment tooling, and what `--workers 1` really starts

**Objective.** Make the DR-014 deployment reproducible and hard to get wrong: verified weights, a
preflight that catches the known traps, and a start/stop pair that cannot leave orphans.

**Completed work.** `weights-manifest.md` with an 8-test pytest guard · `verify-weights.ps1` ·
`preflight.ps1` · `start-demo.ps1` · `stop-demo.ps1` · `runbook.md` · README setup section
rewritten · `.gitignore` gains `.run/`.

**Real results — all four scripts executed, output captured.**

| script | result |
|---|---|
| `verify-weights.ps1` | 3/3 PASS against the gate-2 hashes, exit 0 |
| `preflight.ps1` | 10/10 PASS, exit 0 |
| `start-demo.ps1` | API healthy, `cuda True`, `guard enforced`, exit 0 |
| `stop-demo.ps1` | both processes stopped, all three ports released, **no orphans**, exit 0 |

`pytest` 461 → **469**.

**The finding.** `uvicorn --workers 1` starts **two** processes — a supervisor and one worker:

```
19700  <- supervisor; loads no model
 8632  <- worker; serves requests and holds the pipeline (parent 19700)
```

This does **not** contradict the single-worker requirement and is not a duplicated API: there is
one worker, only the worker loads a model, and `allocated_mb` was **0.0** with
`pipeline_loaded: false` on a freshly started service — measured proof that lazy loading costs no
GPU memory, exactly as DR-011 describes. EXP-034's memory analysis is unaffected.

It has two practical consequences, both now handled rather than discovered mid-demo:
`/api/health` reports the **worker's** pid, which is *not* the pid `start-demo.ps1` launched; and
`stop-demo.ps1` must stop the tree, because stopping only the recorded PID would leave the worker
holding port 8000. M7's closure note recorded "API pid 25748" — that was a supervisor too. The
distinction had simply never come up, because nothing had needed to stop the pair programmatically.

**Decisions.**

1. **The scripts query `apps/api/styles.py` instead of restating its constants.** A verifier with
   its own copy of the hashes can certify a machine the service will then refuse to serve from.
2. **`start-demo.ps1` refuses to start when port 8000 is held.** `assert_single_worker` cannot
   catch a second API process — nothing inside one process can see another — and two resident
   pipelines do not fit in 8 GB. M7 closed by *manually* confirming no duplicate uvicorn remained;
   this makes it a check.
3. **`stop-demo.ps1` never kills by process name.** `python.exe` and `node.exe` are not this
   project's to claim; killing every `node.exe` on a developer's machine would be worse than the
   leak it was cleaning up. It stops recorded PIDs and their children, then verifies the ports.
4. **The restore path is a parameter, never a private absolute path.** `-RestoreFrom` plus
   `CHECKPOINT_ROOT`; a pytest asserts no personal path appears in the manifest.
5. **The manifest states R14 explicitly** — a failed hash means restore from backup, never
   retrain — and a pytest asserts that wording is present.

**One defect found and fixed in my own work:** a non-English string reached a `preflight.ps1`
failure message. Corrected immediately, and a scan of all six new files confirms no non-Latin
characters remain.

**Commands run.** `verify-weights.ps1` · `preflight.ps1` · `start-demo.ps1` · `/api/health` ·
`/api/styles` · `Get-CimInstance Win32_Process` · `stop-demo.ps1` · `pytest`.

**Evidence.** `docs/evidence/M8/deployment/preflight-and-lifecycle.md`.

**Unfinished work / blockers.** None. **No GPU inference ran** — `pipeline_loaded` stayed false
throughout and the generation total stays at 26.

**Next step.** M8.6 — the non-GPU CI workflow, committed locally and not pushed.

---

## 2026-08-09 — M8.3: the Playwright E2E suite M7 did not have

**Objective.** Build the automated browser suite M8's first acceptance criterion requires, without
a GPU, a model or a single generation.

**Completed work.** `@playwright/test` + Chromium installed as `apps/web` devDependencies; config,
JSON fixtures, a pytest contract guard and **37 scenarios across 6 spec files**; vitest scoped away
from `e2e/`; `.gitignore` and eslint updated.

**Real results.**

| suite | M7 close | now |
|---|---:|---:|
| pytest | 406 | **461** |
| vitest | 165 | **169** |
| **Playwright E2E** | **0 — did not exist** | **37 passed** |
| eslint / build | clean / succeeds | clean / succeeds |

Run twice end to end: 37 passed both times, **no flakes**, `retries: 0`.

**Decisions.**

1. **The suite runs against `npm run build && npm run preview`, never the dev server.** What ships
   is what is tested. A dev-server suite can pass while the built application is broken.
2. **The mock sits at the HTTP boundary and nowhere above it.** React, R3F, the WebGL canvas, the
   texture pipeline, the polling loop and the downloads all run for real.
3. **The fixtures are JSON, and a pytest validates them against the real Pydantic models.** This is
   the difference between mocked E2E and E2E theatre: without it, a field renamed in `schemas.py`
   would leave the browser suite happily passing against a shape the server stopped sending. A
   first attempt kept the fixtures as TypeScript literals and read them here with a regex; it broke
   on identifiers, template strings and spreads, and the honest conclusion was that **data should
   be data**. Both sides now load one JSON file and neither parses the other's language.
4. **A pytest also asserts no fixture publishes an estimate outside `denoising`.** Otherwise the
   E2E test proving "no percentage during model loading" could pass because the interface ignored
   data it should never have been given.

**Four defects found, all in the tests, none in the application.** Every first-run failure was a
wrong assertion: an ambiguous `getByLabel('Style')`, an expected `1.3008×` where `fitDisclosure`
rounds to `1.301×`, a style the test never selected, and a sentence that also appears in the
aria-live region. The application needed no change.

**One assertion was removed rather than made to pass.** The `DECAL GENERATED` headline renders only
while the PNG is composed onto the deck — about a second — so asserting it races the application
being fast. **The fix was NOT to make the state linger:** M7 recorded that padding a finished
result so a label can be read is exactly the dishonesty the progress feature exists to avoid. The
test asserts the durable outcome and a comment records why the obvious assertion is absent.

**Scenario 19 (camera state) was flagged in the plan as possibly not automatable. It was
automatable** — and without reading the camera matrix. The test orbits, swaps the texture, asserts
the frame changed, then presses **Reset view** and asserts it changed *again*; a reset that visibly
moves the deck proves the deck was not already in its default pose.

**A finding recorded but deliberately not fixed.** `npm audit` reports 3 high-severity advisories
(`brace-expansion`, `js-yaml`, `nanoid`) — all DoS issues in **dev-only build tooling**, none in
the shipped bundle. **Verified pre-existing, not introduced by Playwright:** the lockfile diff is
purely additive and all three were already present at `a355ffa`. `npm audit fix` would move
`vite`, `eslint` and `typescript-eslint` during a hardening milestone. **Kylian's call — open.**

**Commands run.** `npm install --dry-run` (twice, both confirmed no production dependency moved) ·
`npx playwright install chromium` · `npx playwright test` (×2) · `npm run typecheck:e2e` ·
`npm run lint` · `npm run test` · `npm run build` · `pytest`.

**Evidence.** `docs/evidence/M8/tests/playwright-e2e-report.md`.

**Unfinished work / blockers.** None. **No GPU inference ran**; the generation total stays at 26.

**Next step.** M8.4 — DR-014, the deployment and demo decision.

---

## 2026-08-09 — M8.2: upload-security gaps closed, and a lying settings file fixed

**Objective.** Close the real gaps in upload security without inflating the test count, and make
`.env.example` describe the configuration that exists.

**Plan.** Audit what M7 already proves, add tests only where they carry new evidence, and fix
anything the audit exposes.

**Completed work.** 35 backend and 4 frontend assertions added; `.env.example` rewritten and
guarded; `docs/evidence/M8/security/upload-security-matrix.md` written.

**The audit result, stated before the additions.** All three criteria named in issue #9 —
malicious filename, oversize file, wrong MIME — **were already met by M7**, along with
decompression-bomb, truncation, and content-vs-extension mismatch. Nothing there was rewritten.
Generation-id traversal was also already covered by `test_validation_and_errors.py`, so the two
tests the plan listed for it were **dropped as duplicates** rather than added for the count.

**Real results.**

| suite | before | after |
|---|---:|---:|
| pytest | 406 | **441** |
| vitest | 165 | **169** |
| eslint | clean | clean |

**No defect was found in the upload path.** All 35 new backend assertions passed on first run
against the existing implementation. That is worth stating plainly rather than hiding in a green
tick: the M7 code was already correct under conditions it had never been tested against.

**One real defect was found, outside the code.** `.env.example` documented five keys nothing
reads — `MODEL_CACHE_DIR`, `BASE_MODEL_ID`, `LORA_WEIGHTS_PATH`, `ALLOWED_UPLOAD_EXTENSIONS`,
`UPLOAD_TMP_DIR`. The last two are misleading in a security context: they imply the extension
allowlist and a temporary upload directory are configurable, when the allowlist is frozen in code
deliberately and no temporary upload directory exists at all.

**Decisions.**

1. **The strongest new test replaced a weaker claim rather than joining it.** M7's traversal test
   asserted an empty temporary directory, which only shows nothing landed in *one* place. The new
   test patches `builtins.open`, `Path.open`, `Path.write_bytes` and `Path.mkdir` to raise and
   runs 12 hostile filenames through validation, so **any** filesystem access fails it.
2. **That guard carries a sensitivity test.** A guard that cannot fail is not evidence — the same
   companion-assertion pattern the frozen-kit hash locks use.
3. **The temp-file close is asserted structurally, by AST.** No HTTP test can observe it: Starlette
   owns the `SpooledTemporaryFile`. Following the existing import-boundary precedent, a pytest
   parses `main.py` and asserts the `UploadRejected` handler's `try` has a `.close()` in its
   `finally`. A future edit moving it into the success branch would leak a temp file on every
   rejection while every other test still passed.
4. **Filename sanitisation was deliberately NOT added.** Sanitising a name implies it will be
   reused. It is not, and decision 1 is the evidence. A frontend test asserts a hostile *name* with
   a valid type passes preflight, so nobody later mistakes name-filtering for a real check.

**Commands run.** `pytest apps/api/tests/test_uploads.py` · `pytest apps/api/tests/test_env_example.py`
· `pytest` · `npm run test` · `npm run lint`.

**Evidence.** `docs/evidence/M8/security/upload-security-matrix.md` — 27 rules mapped to their
tests, including the three deliberately-not-tested items and why.

**Unfinished work / blockers.** None. **No GPU inference ran**; the generation total stays at 26.

**Next step.** M8.3 — the Playwright E2E suite.

---

## 2026-08-09 — M8.1: baseline re-measured, and a stale environment fact found

**Objective.** Establish a measured baseline before any M8 change, so every later claim in the
milestone rests on a number from this machine rather than on M7's record.

**Plan.** Re-run the four gates, capture the real toolchain versions, and record any drift.

**Completed work.** All four gates re-run. `docs/evidence/M8/baseline/test-baseline.md` written.
The environment audit corrected and the stale jsdom justification in `apps/web/vite.config.ts`
rewritten.

**Real results.**

| gate | result | vs M7 record |
|---|---|---|
| `.venv/Scripts/python.exe -m pytest` | **406 passed**, 46.94 s | identical |
| `npm run test` | **165 passed**, 11 files | identical |
| `npm run lint` | clean, exit 0 | identical |
| `npm run build` | succeeds, exit 0, 606 modules | identical |

**The finding.** `docs/technical/environment-audit.md` recorded **Node v20.18.0 / npm 10.8.2** from
the 2026-07-27 audit. The machine actually runs **Node v24.18.0 / npm 11.16.0**, confirmed in both
PowerShell and Bash. Node was upgraded between those dates and **nothing in this repository records
when**, so it is not possible to say whether M7's 165 vitest and its clean build were produced on
Node 20 or Node 24. That uncertainty is exactly what re-measuring removed: they pass on Node 24 now,
measured, today.

A second-order consequence: `apps/web/vite.config.ts` justified its jsdom 26.x pin with *"jsdom 27's
CSS chain requires Node >= 20.19 (audited Node is 20.18.0)"*. That constraint no longer binds.

**Decisions.**

1. **Re-baseline on Node 24 rather than reinstalling Node 20** (Kylian, this session). The demo runs
   on this machine, so the validated stack should be the one that will be demonstrated.
2. **The jsdom pin is NOT moved.** The rationale was stale, but a stale rationale is not a defect.
   Under an M8 feature freeze, moving a working dependency with no failure behind it would add risk
   for nothing. The comment was corrected to state the real reason — 26.1.0 is what the suite was
   validated against — instead of deleting a justification and leaving a bare pin.
3. **The original audit values are preserved, not overwritten.** The summary row is marked
   superseded and points at a dated update section, following the precedent set by the 2026-07-30
   driver correction.

**Commands run.** `pytest` · `npm run test` · `npm run lint` · `npm run build` · `pip list` ·
`npm ls` · `node -v` · `npm -v` · `nvidia-smi --query-gpu` · `git --version`.

**Evidence.** `docs/evidence/M8/baseline/test-baseline.md`.

**Unfinished work / blockers.** None. **No GPU inference ran**; the generation total stays at 26.

**Next step.** M8.2 — close the upload-security test gaps and align `.env.example` with the settings
`apps/api/config.py` actually reads.

---

## 2026-08-07 — M7 CLOSED: final human visual gate APPROVED

### Milestone report

**MILESTONE:** M7 — Prototype 5, the integrated MVP.

**STATUS:** **COMPLETE**, closed **locally only**. Nothing pushed; the remote GitHub issue and the
project board are untouched and remain Kylian's.

**BRANCH:** `main`, 18 commits ahead of `origin/main` at gate time.

**RESEARCH QUESTION:** can the measured stack — SD 1.5 + one per-style LoRA at 0.7 + IP-Adapter at
0.55 at 512×1536 — be exposed as a usable application on one 8 GB device without breaking the
margin it depends on? **Answered: yes.**

**WORK COMPLETED:** the FastAPI single-flight service with upload security, a checkpoint integrity
gate and an in-loop deadline · EXP-034 residency and EXP-035 reference neutralisation · the React
generate flow · both texture-fit modes, decided at a human gate · a professional interface pass ·
read-only progress telemetry with an honest ETA · `Upload your own decal` as a production feature ·
DR-011, DR-012, DR-013 · eleven evidence screenshots.

**FILES CHANGED:** 41 files across the interface pass and 5 more for the upload feature; full list
in the two entries below.

**TESTS AND VALIDATION:** `pytest` **406** · `vitest` **165** · eslint clean · `npm run build`
succeeds · `git diff --check` clean · no tracked model weights · frozen dataset and evaluation
kits unchanged · all three production LoRA sha256 values re-verified on disk.

**ACTUAL RESULTS:** residency accumulates nothing (allocated after generation **3316.64 MiB in all
13 runs**, growth **0.00 MiB**); peak allocated **5143.73 MiB**, byte-identical to M5's EXP-019b;
worst spare **200.0 MiB**, *tighter* than the 202.0 MiB carried since M5; 6 of 6 repeated cases
byte-identical; a 504 stops the loop at **14 of 30 steps**; the grey placeholder is inert at scale
0.0 (EXP-035, byte-identical output).

**EVIDENCE:** `docs/evidence/prototype-5/` — `FINAL-GATE-approval.md` (12/12 PASS),
`GATE-approval.md`, `GATE-handover.md`, `api-validation.jsonl`, `screenshots/` and
`screenshots/ui/`; `docs/evidence/EXP-034/`, `docs/evidence/EXP-035/`.

**DECISIONS:** DR-011 accepted · DR-012 `full-surface`, Kylian's, re-confirmed at this gate ·
DR-013 progress telemetry, approved at this gate.

**COMMITS:** 18 M7 commits, listed in the session handoff, plus the closure commits from this
entry.

**RISKS OR BLOCKERS:** none blocking. **R12 stands at 200.0 MiB** and is the operative production
ceiling for M8.

**PLANNING CHANGES:** M7 delivered 2026-08-06/07 against a planned Aug 10–13. **The GPU budget
closed at 26 total generations, not 25** — see below.

**NEXT ACTION:** Kylian's push, GitHub issue and project board. Then **M8**, which has not begun.

### The gate

**Reviewer and approver: Kylian Algoet. Result: APPROVED. Final visual gate PASSED, 12 of 12
manual acceptance items.** He approved the redesigned production interface, the real progress and
ETA implementation, `Upload your own decal` as a production feature, and re-confirmed
`full-surface`. Full record with his findings: `docs/evidence/prototype-5/FINAL-GATE-approval.md`.

### Generation budget — final wording

**26 total generations.** The research budget closed at **25 / 25**. **Generation 26 was a manual
human-review run**, performed by Kylian himself during the final interface review, **outside the
frozen research matrix**.

It is deliberately **not** added to EXP-034, **not** registered in `experiments/registry.csv`, and
**not** treated as a new experiment: it produced no research result and was not run under the
pre-declared measurement conditions. Registering it would have contaminated a frozen matrix with a
run that answers a different question. Its telemetry is cited only as evidence that the interface
behaved correctly. **No further GPU generation is authorised for M7 closure.**

### Accepted limitations — approved, not deferred

Cold model loading has no honest percentage · the ETA is approximate and mainly covers denoising ·
finalising may be visible only briefly and **must not be artificially delayed** · prompt adherence
can be weaker than style adherence · the physical GPU margin remains ~200 MiB · one API process and
one worker only.

### Closure housekeeping

Both local servers were stopped cleanly (API pid 25748, frontend pid 476); ports 8000 and 5173
released; a process scan confirmed **no duplicate uvicorn or vite process** remained. **No GPU
inference was run for closure.**

**Next step:** M8 has not begun. The push, the issue and the board are Kylian's.

---

## 2026-08-07 — M7 visual review: progress verified from telemetry, and decal upload shipped

**Objective:** answer, from real telemetry rather than by inference, what Kylian's live generation
displayed; then add "upload your own decal" as a production feature.

**Completed work.** Verification of the live run against the retained telemetry and the uvicorn
access log. Then the upload feature: a production control in the deck workspace, a shared image
preflight, provenance state tracked explicitly (`starter` / `generated` / `upload`), replace,
remove, return-to-generated, and a result panel that stops claiming the deck shows the generation
when it does not. **13 new frontend tests.** The superseded review-only "Load decal" control was
removed.

**Unfinished by design:** M7 not closed · nothing pushed · issue and board untouched · M8 not
begun.

**Decisions:** none of mine. The product decision — keep local decal upload as a normal feature,
clearly separate from the AI reference upload — is Kylian's.

**Real results — what the live run establishes.** Operation `cHWlV0J6Qgh2BKze`:
`current_step 30 / total_steps 30`, `denoising_fraction 1.0`, `elapsed_seconds 40.83`, status
`completed`. Access log: **1** `POST /api/generate` → 200 and **48** progress polls, i.e.
continuous polling across the whole request. **Real diffusion steps were tracked and delivered.**

**What it does not establish, stated rather than smoothed over:** the server logs requests, not
rendered text, so it cannot confirm which strings the browser painted. No defect was found in the
render path and it is covered by tests, but "produced and delivered" is not "observed", and the
two are kept apart. Two measured reasons a stage could be present and missed: the request was a
**cold start** (≈28 s of its 40.83 s was model loading, so denoising was only the last ~12 s), and
**`Finalising the decal…` lasts about a second** — the VAE decode plus PNG encode. **No fix was
made because no defect was found**, and the finalising stage will not be padded: delaying a
finished result to make a label linger is exactly the dishonesty the feature exists to avoid.

**Real results — the upload feature.** **vitest 152 → 165**, all pass; eslint clean; build
succeeds; pytest **406** unchanged. Verified live in Chrome with a PNG drawn in the browser and
fed through the real control: provenance strip reads `User-uploaded artwork · my-own-artwork.png`,
no AI metadata panel, no AI downloads. A file declaring `image/png` whose bytes are not an image
was rejected by the **decode** with the previous decal left on the board; a GIF declaring
`image/gif` was rejected by the preflight before decoding.

**The check that matters, taken from the server rather than asserted:** across every upload the
access log's `POST /api/generate` count stayed at **1** and the poll count at **48**, and
`/api/health` still reported `allocated_mb: 3316.64`. **The upload path made no API request and
no GPU work happened.**

**Planning change:** the M7 GPU cap of 25 was exceeded — Kylian ran a **26th** generation during
his review. His decision, recorded rather than absorbed.

**Evidence:** `docs/evidence/prototype-5/screenshots/ui/10-upload-own-decal.jpg` and
`11-upload-failure-preserves-decal.jpg`. **Unlike states 02–06 these two involve no mock at all**,
and the README says so.

**Next step:** Kylian's final visual review of the upload feature.

---

## 2026-08-07 — M7 interface pass: a deck studio and real generation progress; M7 still OPEN

**Objective:** one focused professional UI/UX pass and an honest generation-progress experience,
without restarting model research, changing generated output, or spending GPU budget.

**Plan:** baseline → inspect the whole frontend and the relevant backend → progress telemetry
behind one read-only endpoint → rebuild the workspace → tests → browser verification with mocked
telemetry → documentation → commits → stop at a visual review gate.

**Completed work.** Backend: `apps/api/progress.py` (thread-safe tracker, opaque operation ids,
EMA estimate on a monotonic clock), `GET /api/generation-progress`, and `compose_step_callbacks`
so progress reporting is threaded through the existing deadline callback instead of replacing it.
Frontend: a token system, a studio layout, one status-message system, a four-step form, a
compacted result panel, review-only controls moved behind `?review=1`, and the print-progress
panel with its pure presentation model and single polling loop. **82 new frontend tests and 35 new
backend tests.**

**Unfinished by design:** M7 is **not** closed · nothing pushed · issue and board untouched · M8
not begun · **no generation ran** and the cap stands at 25 of 25.

**Blockers:** none. The pass stops at Kylian's visual review, which is the intended state.

**Decisions:** **DR-013 — read-only progress endpoint polled by the client.** SSE, WebSocket and
an async job id were screened and rejected without implementation; the reasons are recorded. The
rule the decision turns on: **only denoising has a real denominator**, so every other stage gets a
stage name and no number, and no weighted overall percentage exists anywhere.

**Commands and tests:** `.venv/Scripts/python.exe -m pytest -q` · `npm run test -- --run` ·
`npm run lint` · `npm run build` · `git diff --check` · tracked-weight, large-file, secret and
frozen-artifact scans · a real `uvicorn --workers 1` process with a browser-side interceptor.

**Real results.** **pytest 371 → 406**, all pass. **vitest 70 → 152**, all pass. eslint clean;
build succeeds in 5.65 s. The three production checkpoints re-hashed on disk and **match** their
gate-2 values, 6 414 480 bytes each. 38 frozen-artifact tests pass. No tracked model weights; the
largest tracked file is the pre-existing 316 KB `EXP-031/final-matrix.jsonl`. **No GPU work ran:**
`POST /api/generate` was intercepted in the browser, and the API's own endpoint still reported
`pipeline_loaded: false` afterwards — an independent check that the model was never loaded.

**Responsive readings (measured in real nested viewports).** 1920 px and 1440 px: two columns,
viewer 722 px and 631 px. 1024 px, 768 px and 390 px: single column, viewer 360 px. **No
horizontal scroll at any width**, and no vertical page scroll on desktop.

**Three defects found in my own work.** (1) The desktop shell overflowed the viewport by 70 px —
`min-height: 100vh` let the flex column grow past the viewport, putting the deck below the fold.
(2) A horizontal scrollbar on every page: `.generate-form input[type='file'] { width: 100% }` beat
`.visually-hidden` on specificity and stretched the hidden file input to 1992 px. **Neither was
visible to any test** — both were found only by measuring the live document, which is the argument
for browser verification over screenshots alone. (3) The poll loop restarted on every render when
the hook received inline options, firing a request per render instead of one per interval; the
collaborators now live in refs.

**A defect the browser also surfaced:** Chrome renders the native file input's text in the OS
language, which put Dutch ("Bestand kiezen") into an English-only interface. The native control is
kept for accessibility and visually replaced.

**Evidence:** `docs/evidence/prototype-5/screenshots/ui/` — nine states, **all with mocked
telemetry and labelled as interface verification, not measurements**, with the reason the numbers
in them must never be quoted.

**Worth recording.** `resize_window` could not produce narrow viewports: the window was maximised
on a 1536 px screen at 80 % zoom, so the CSS viewport stayed at 1920 px whatever was requested.
The narrow layouts were rendered in **iframes of the exact target widths** instead — an iframe is
a real viewport, so its media queries are the genuine ones, unlike a scaled screenshot.

**Next step:** Kylian's final visual review of the nine states and the running application.

---

## 2026-08-07 — M7 review gate: the texture-fit default decided; M7 still OPEN

**Objective:** put the one open decision to Kylian, implement whichever mode he selects, and
record the decision — without closing the milestone on the strength of that single answer.

**Plan:** present the measured trade-off and both screenshots → take the decision → implement the
default and replace the test that asserted no default existed → ask for the rationale rather than
write one → DR-012 and a gate approval record → documentation → commit → stop.

**Completed work:** `DEFAULT_TEXTURE_FIT_MODE = 'full-surface'` exported from
`apps/web/src/deck/textureFit.ts`; `App.tsx` reads it for its initial state; the texture-fit
selector is no longer badged *review control* (that badge moved to the "Load decal" control,
which really is one) and the footer now states the default and its cost. The
"exposes no exported default mode" test was replaced by five tests: the default is
`full-surface`, it is one of the offered modes, the rejected mode survives, its stretch is
disclosed, and the export is real rather than a stub. **DR-012** written and **DR-011's**
"deliberately left open" section closed against it; `docs/evidence/prototype-5/GATE-approval.md`
added; the handover, prototype report, evidence README, testing strategy, planning log,
traceability matrix and `ai-usage.md` updated.

**Unfinished by design:** M7 is **not** closed · the 12-item manual acceptance checklist is
**unwalked** · nothing pushed · the GitHub issue and board untouched · M8 not begun · no 26th
generation.

**Blockers:** none. M7's closure waits on Kylian's checklist walk, which is the intended state.

**Decisions:** **DR-012 — `full-surface` is the production texture-fit default.** Kylian's, at the
gate, with his rationale quoted verbatim rather than paraphrased: the bare ends made the deck look
unfinished and the artwork look like a centred rectangular sticker, and the measured 1.3008×
stretch was acceptable on the selected production styles. Asked separately whether M7 could be
declared complete, he answered **"Not yet — I'll walk the checklist"**, and the milestone stayed
open.

**Commands and tests:** `.venv/Scripts/python.exe -m pytest -q` · `npm run test -- --run` ·
`npm run lint` · `npm run build`.

**Real results:** **371 pytest passed**, exit 0 — unchanged by this edit, as expected for a
frontend-only change. **70 vitest passed** (66 before: five tests added, one removed). eslint
clean. `npm run build` succeeded in 5.80 s. **No GPU work ran**; the cap stands at 25 of 25.

**Evidence:** `docs/evidence/prototype-5/GATE-approval.md`,
`docs/evidence/prototype-5/screenshots/`, `docs/decisions/DR-012-deck-texture-fit.md`.

**Worth recording.** The technique from the previous session — *a test that asserts a decision has
not been made* — is what forced this to be a documented decision. Selecting the default meant
deleting an assertion that said "nobody has selected the default", which cannot be done absently.
Two further options were screened and recorded rather than silently ignored: regenerating at
512×1998 to match the deck (rejected — it changes the DR-007 generation geometry every memory
figure from EXP-016 onward was taken at, and the LoRAs were trained at 1:3) and reshaping the deck
to 1:3 (rejected — distorting the board to suit the image inverts the problem).

**Next step:** Kylian walks `GATE-handover.md` §12 against the running app. If it passes, M7 closes
with the standard milestone report; if an item fails, it becomes a defect to fix before closure.

---

## 2026-08-06 — M7 built and validated: the integrated MVP; STOPPED at the review gate

**Objective:** put the measured generation stack behind a usable application on one 8 GB device,
measure what nothing had measured about running it as a service, build both answers to the
deck-geometry mismatch, and stop without choosing between them.

**Plan:** approved M7 plan (Plan mode, revised twice on Kylian's corrections) — inspect the
optional-reference path → resolver-gated dependency install → FastAPI service → API tests →
EXP-034 residency → frontend and both texture-fit modes → capped GPU validation → evidence,
documentation, commits → gate.

**Completed work:** `apps/api` (config with a single-worker guard, production style table with a
sha256 integrity gate, frozen upload limits, resident pipeline with a verified LoRA lifecycle,
single-flight generation service, FastAPI app) with **82 tests**; the React generate flow with
loading/error/busy states, reproducibility metadata, PNG + JSON download and **both texture-fit
modes**, with **66 web tests**; **EXP-034** and **EXP-035**; end-to-end validation against a real
uvicorn process; browser evidence; DR-011; `docs/prototypes/prototype-5.md`; the gate handover.

**Two things were genuinely unknown and are now measured.**

**1. Residency costs nothing, and the margin is tighter than advertised.** EXP-034 ran a frozen
12-request matrix — six cases twice — through one long-lived process, deliberately breaking the
one-config-per-process rule because that is the question. Allocated memory after generation was
**3316.64 MiB in all 13 runs**: not "within the 64 MiB tolerance declared in advance", identical.
Six unload/load cycles across three adapters left the allocator exactly where it started. Peak
allocated was **5143.73 MiB, byte-identical to M5's EXP-019b**, so a resident service and a
one-shot process reach the same peak. All six repeated cases were **byte-identical**. But the
worst spare device memory is **200.0 MiB**, not the 202.0 MiB quoted from EXP-032 — every
reference-conditioned request sits there. The margin got *tighter* under real serving, and it is
recorded that way rather than rounded toward comfort.

**2. Prototype 0's decals hid a geometry problem for four milestones.** The bundled test decals
are **512×2000** — 1:3.906, effectively the deck's own aspect. The generator produces 512×1536,
which is 1:3. The mismatch could not surface until real generated artwork reached the deck.
Neither fit is correct: `full-surface` stretches by **1.3008×**, `fit-without-stretch` leaves
**23.12 %** of the length bare (11.56 % per end). Both are built, both disclose their cost
numerically, and **neither is selected** — a test asserts the code exports no default.

**A third finding, from reading the library rather than assuming.** "Prompt-only" is not simply
"omit the reference": with IP-Adapter resident, diffusers 0.39.0 sets `added_cond_kwargs` to
`None` and the UNet then **raises**. The service keeps the adapter at scale 0.0 with a
constructed grey placeholder, and **EXP-035** tested the claim that rests on — a grey placeholder
and real holdout artwork produced **byte-identical** output, and the same bytes as EXP-034's
prompt-only result. It is recorded that this does *not* re-establish text-only equivalence, which
still rests on M4's separate 12/12 measurement.

**Three defects found in my own work.**

1. **A wrong measurement, not a wrong service.** The deadline check asserted an early stop by
   wall clock and failed at 25.69 s — but that was a *cold* request, and nearly all of it was the
   model load. The 504 now reports how far the loop got, so the early stop is provable from the
   response (14 of 30 steps) independent of loading time; warmed, it returns in 6.33 s against
   ~13 s unaborted.
2. **A blank-deck screenshot that was not a bug.** A capture taken in the same second the scene
   finished initialising showed an empty viewer; three seconds later it rendered correctly, with
   no console errors on either load. Recorded because "the screenshot looks wrong" is exactly
   what gets reported as a defect without verification.
3. **`<output>` inside a `<label>`** is itself a labelable element, which made a control
   ambiguous to assistive technology and to the tests. Replaced with a `<span>`.

**Commands and tests:** `.venv/Scripts/python.exe -m pytest` → **371 passed** (289 pre-existing,
unchanged, plus 82 new). `npm run test` → **66 passed**; `npm run lint` clean; `npm run build`
succeeds. `scripts/measure_service_residency.py`, `scripts/validate_p5_api.py`,
`scripts/measure_reference_neutralisation.py`.

**Dependency gate:** `fastapi`, `uvicorn`, `python-multipart`, `pydantic` installed only after a
parsed `--dry-run --report` proved the resolver would move **none** of torch, torchvision,
diffusers, transformers, accelerate, safetensors, peft, pillow, typing-extensions or httpx.
Verified afterwards by `pip check` and real imports. A starlette deprecation warning about
`httpx2` in TestClient is accepted rather than chased, because silencing it risks a protected pin.

**Budget:** the plan declared a hard cap of **25 real generations** before any ran. Final count:
**25 of 25**, exactly. When the fit-mode screenshots were needed after the cap was reached, an
existing decal was loaded from disk through a review control instead of generating a 26th.

**Unfinished by design:** no texture-fit default chosen · M7 not declared complete · nothing
pushed · the GitHub issue and board untouched (`gh` unavailable, and those are Kylian's) · M8 not
begun.

**Blockers:** none technical. The review gate is the intended stopping point.

**Evidence:** `docs/evidence/prototype-5/` (GATE-handover.md, README.md, api-validation.jsonl,
screenshots/), `docs/evidence/EXP-034/`, `docs/evidence/EXP-035/`, DR-011,
`docs/prototypes/prototype-5.md`, registry rows EXP-034 and EXP-035.

**Next step:** Kylian's review. The one decision required is the **production texture-fit mode**;
the manual acceptance checklist is in the gate handover.

---

## 2026-08-05 — M6 COMPLETE: gate 2 passed, production checkpoints selected, DR-010 finalised

**Objective:** verify the completed Gate-2 scoring artifact, record Kylian's decisions and their provenance, resolve the selected production checkpoints from evidence, apply the authorised forward-only reproducibility fix, finalise DR-010, and close M6 in documentation.

**Completed work:** Gate-2 artifact verified (`835488f3…`, exact match, 21/21 score rows, 15/15 failure-mode rows) and pinned in `.gitattributes` with a pytest asserting the hash; `GATE-2-approval.md` written with explicit provenance; the three selected checkpoints resolved, re-hashed on disk and confirmed against their recorded values; the R14 runner fix with four regression tests; DR-010 moved from draft to **accepted**; registry, planning, architecture, dataset methodology, experiment methodology, testing strategy, risk register, traceability, AI-usage, the Prototype-4 report and this log updated; M6 marked complete.

**Real results — the selected production artifacts.** All three: rank 8 / alpha 8, 256 tensors, 256 LoRA keys, **zero base-model keys**, 6 414 480 bytes, sha256 matching the value recorded at training time.

| style | run | step | sha256 | outcome |
|---|---|---:|---|---|
| minimal-geometric | EXP-027 | **300** | `2d425838cce59adc…` | PASS |
| ukiyo-e | EXP-028 | **600** | `52381b6052ad71f1…` | PASS |
| retro-poster | EXP-029 | **300** | `70d2afbfb3c09aff…` | PARTIAL PASS |

**Decisions (all Kylian's).** Three separate per-style adapters at a **default weight of 0.7** (optional 0.4–1.0). **RQ5:** the multi-style adapter is **viable but not selected** — competitive at 512×512 with no severe cross-style bleed, and explicitly **not recorded as a failure**; per-style adapters win on flexibility, since each style needs a different checkpoint. **H4 confirmed** — `retro-poster` bakes in pseudo-text and framing, so it is a **partial pass, not upgraded**. **H5 supported** — 0.7 is a compromise, not a universal optimum. **No contingency authorised; both slots unused at 10 of 12 runs.**

**The most informative result is one nobody would have seen without per-style gating.** Two of the three selected checkpoints are **step 300**, not the 600 the runs trained to: prompt adherence fell from 4 to 3 at step 600 for both `minimal-geometric` and `retro-poster` while style consistency held at 5. Training longer made the style stronger and the model less obedient. Only `ukiyo-e` improved.

**R14 handled as authorised — forward-only.** `seed_everything()` now seeds Python `random`, the global torch RNG and CUDA **before** adapter construction, keeping the explicitly seeded `Generator`. Four tests: same seed gives identical initial weights; a different seed does not; the seeding happens before `add_adapter`; and the docstring still states the M6 artifacts are not bit-reproducible. **EXP-027…EXP-030 were not rerun or replaced**, and the historical finding is unchanged — the selected checkpoints are authoritative as files, not as a recipe.

**Commands and tests:** `.venv/Scripts/python.exe -m pytest` → **289 passed**.

**Unfinished work, deliberately:** the GitHub issue and project-board status are **not** updated — `gh` is unavailable and those browser actions are Kylian's. Nothing is pushed. M7 has not begun.

**Blockers:** none. M6 is complete.

**Evidence:** `docs/evidence/prototype-4/GATE-2-approval.md`, `gate-2-scoring-form-completed.md`, `docs/decisions/DR-010-style-learning-configuration.md` (accepted), `experiments/registry.csv` rows EXP-020…EXP-033.

**Next step:** Kylian's push approval, then M7 (Prototype 5 — integrated MVP), which must begin 2026-08-10 to 08-12.

---

## 2026-08-05 — M6 Phase B complete: approved full runs, multi-style, final matrix; STOPPED at gate 2

**Objective:** execute Phase B exactly as Kylian's gate-1 approval authorised it, produce the gate-2 review package, and stop without selecting anything.

**Plan:** verify the gate-1 artifact → three 600-step per-style runs in fresh processes → validate every gate and checkpoint → balanced multi-style run only if all three passed → capped final matrix on approved candidates only → combined-stack checks → offline indicators → gate-2 package → documentation → atomic commits → stop.

**Completed work:** gate-1 scoring artifact verified (`cf6bf260…`, matching, 15/15 rows filled) and an approval record written; `.gitattributes` added to stop line-ending normalisation from breaking that hash; balanced multi-style training implemented with asserted exposure; **EXP-027/028/029** at 600 steps and **EXP-030** at 1800; **EXP-031** final matrix, 252 generations against a cap of 432; **EXP-032** combined stack, 8 runs; **EXP-033** offline indicators; 21 labelled contact sheets; a blank gate-2 form; a review-only ZIP; seven registry rows; DR-010 opened as a draft; `docs/prototypes/prototype-4.md`.

**Real results.** Four runs, four passes, tier 0, no escalation. Peak allocated **3133.4 MiB in all four — and in all ten runs of the milestone**, so training memory is set by geometry alone. Multi-style exposure asserted at exactly `minimal-geometric:600; retro-poster:600; ukiyo-e:600`. The combined stack fits at 512×1536 with **202.0 MiB spare** for every candidate, identical to M5's EXP-019b, and the WDDM spill signature is **absent** — device used is near the ceiling but peak RSS at the deck format is *lower* than at 512×512. **0 of 252** near-copy flags, with the holdout control at a comparable distance.

**Three defects found in my own work, all recorded rather than patched away.**

1. **Training is not bit-reproducible from the recorded seed.** The LoRA initialisation draws from the global torch RNG, which the runner never seeds. Diagnosed from the *shape* of the discrepancy rather than guessed: same-step adapters differ by an L2 of ~158 against a norm of ~112, a ratio of √2 — the signature of two independent draws, not floating-point drift. The data pipeline was verified deterministic in the same pass, and I did **not** fix it mid-milestone, because seeding the initialisation would alter every run the gate-1 arms were compared against. Recorded as risk **R14**.

2. **24 duplicate generations in my own matrix.** Two blocks of the plan overlap at weight 0.7. The duplicates were byte-identical, so nothing looked broken — but each one put a self-pair into a diversity cell and dragged it toward zero, which reads as mode collapse. EXP-027@300 moved from 0.3302 to **0.4067** once the repeats were excluded. Found by noticing a `seeds=5` count where the design allowed at most 3. Fixed in the plan, in the diversity computation, and guarded by a regression test; the matrix was not regenerated, because its evidence is a valid superset of the fixed plan.

3. **A line-ending rule that would have broken a hash lock.** `core.autocrlf` is true and no `.gitattributes` existed, so committing Kylian's scored form would have rewritten it to CRLF on checkout and silently invalidated the sha256 that proves no score was edited after unblinding.

**Also corrected:** two L2 figures I mis-transcribed into a draft DR-010 table, caught by re-reading the recorded rows rather than trusting the draft.

**Commands and tests:** `.venv/Scripts/python.exe -m pytest` → **284 passed**. Training via `ml.training.train_lora` (one fresh process per run); matrix via `scripts/run_final_matrix.py` (21 processes); validation via `scripts/validate_p4_full_runs.py`; indicators via `scripts/evaluate_p4_final_indicators.py` (CPU, separate process).

**Unfinished work, deliberately:** no production checkpoint selected; no style declared a winner; no default LoRA weight chosen; RQ5, H4 and H5 without verdicts; DR-010 without a conclusion or consequences section; M6 issue open; nothing pushed.

**Blockers:** none technical. Gate 2 is a human gate and is the intended stopping point. `gh` remains unavailable, so issue state stays Kylian's.

**Decisions:** all six gate-1 decisions were Kylian's and are recorded in `docs/evidence/prototype-4/GATE-1-approval.md`. No decision was made in Phase B.

**Evidence:** `docs/evidence/EXP-027…EXP-033/`, `docs/evidence/prototype-4/` (approval, full-run validation, final sheets, gate-2 form and handover), `experiments/registry.csv` rows EXP-027…EXP-033.

**Budget:** 10 of 12 authorised training runs used; both contingency slots preserved. 252 of 432 allowed generations.

**Next step:** Kylian's gate-2 review. Nothing proceeds until the eight decisions in `docs/evidence/prototype-4/GATE-2-handover.md` come back.

---

## 2026-08-04 — M6 Phase A complete: pilots, caption A/B and dataset-size arms; STOPPED at gate 1

**Objective:** complete the autonomous pre-review half of Prototype 4 — freeze the style datasets, train the pilots, gather automated evidence, and hand Kylian a blinded scoring package — then stop.

**Completed work:** style kit frozen and hash-locked (`fc11d828…`); five per-style manifests; caption and source-image audit; the M5 runner extended for per-style training; **six 300-step pilot runs**; the capped 108-image pilot review matrix; offline memorisation indicators; the blinded review package; eight registry rows; the gate-1 handover.

**Two findings that came from verifying rather than assuming.**

**1. The trigger tokens named in the approved plan were wrong.** Checked against the pinned CLIP tokenizer before freezing anything: `dfukiyo` splits into **four** pieces `['d','fu','ki','yo</w>']` and loses the shared `df` prefix, so the family was not even internally consistent; `dfposter` contains `poster</w>`, a piece sitting inside its own style phrase and across the caption corpus — exactly the ordinary-word collision a trigger must avoid. A replacement candidate `xuki` also failed, because several ukiyo-e captions contain the literal words *"uki e"*. The frozen family is **`xgeo` / `xkyo` / `xpst`** — each exactly two pieces, sharing a leading piece, with **zero** overlap against the style phrases, the frozen prompt kit, or all 148 dataset captions. A test asserts the recorded ids against the live tokenizer, and another asserts the vocabulary size is unchanged: **no new vocabulary is added**, because the text encoder is frozen and an added embedding would never receive a gradient.

**2. The caption defects are worse than the M2 note implied, and the frame evidence is now quantified.** Rule-based audit over the training captions: `retro-poster` has **only 14 of 36** captions describing anything visible — 16 are authorship credits, 6 name venues; `ukiyo-e` has **7 of 44** truncated mid-phrase; `minimal-geometric` has **6 distinct** content phrases across 44 items. Separately, an objective border-darkness measurement with a threshold fixed before any image was read puts `retro-poster` at **median −73.5 with 35 of 36 items flagged (97 %)**, against **+29.7 and 2 of 44** for `ukiyo-e`. That is far more specific than "most items", and the `ukiyo-e` figure being *positive* matches the M4 observation about light paper margins. **It is recorded as an indicator, not proof** — a dark border can be a framed scan or simply dark artwork — and **H4 remains unanswered** until Kylian's failure-mode probe.

**Real results — six runs, six passes, tier 0 throughout, no escalation:**

```
             images  pres./item  s/step   wall    first -> last loss   L2
EXP-020         44      6.818    0.284   90.4 s   0.0780 -> 0.0044   3.449
EXP-021         44      6.818    0.408  127.6 s   0.6583 -> 0.0302   2.737
EXP-022         36      8.333    0.294   93.3 s   0.4973 -> 0.0351   3.534
EXP-023         44      6.818    0.294   93.1 s   0.0781 -> 0.0045   3.559
EXP-024n12      12     25.000    0.296   93.4 s   0.0648 -> 0.0042   3.831
EXP-024n24      24     12.500    0.331  104.6 s   0.0849 -> 0.0052   3.406
```

Peak allocated is **3133.4 MiB in all six** — neither style nor set size moves training memory; only geometry does, as EXP-016/017 measured. `ukiyo-e` is slowest per step because its sources run to 4000 px, so decode and crop dominate — a **data-loading** cost, not a model-side one.

**The RQ4 presentation counts landed exactly where the plan predicted** — 25.000 / 12.500 / 6.818 — which is the equal-compute confound made visible in the record rather than left to be inferred from steps ÷ items.

**EXP-025 pilot matrix:** 108 of 108 generations, at exactly the declared cap, one process per checkpoint. **EXP-026 memorisation:** **0 of 108** near-copy flags at `dHash ≤ 6`; median nearest-training distance 20.5–27.0, with the holdout control at a comparable 25.0–28.0 — which is what the control is for.

**Commands and tests:**

```
.venv/Scripts/python.exe scripts/build_style_manifests.py      -> 5 manifests, 148/148 accounted for
.venv/Scripts/python.exe scripts/build_caption_audit.py        -> caption + border audit
.venv/Scripts/python.exe -m ml.training.train_lora --style ... -> 6 runs
.venv/Scripts/python.exe scripts/run_pilot_matrix.py           -> 108/108 images
.venv/Scripts/python.exe scripts/evaluate_p4_memorisation.py   -> 0/108 flagged, 315.1 s CPU
.venv/Scripts/python.exe scripts/build_p4_review_package.py    -> 15 sheets, blinded form, mapping
.venv/Scripts/python.exe -m pytest                             -> 260 passed
```

**Unfinished by design:** no checkpoint selected · no step count chosen · no style called recognisable · no hyperparameter changed · no full, contingency or multi-style run · no final matrix · no DR-010 · no push. **No visual-quality claim anywhere in Phase A.**

**Blockers:** none. `gh` is not on PATH, so issue #7 state could not be verified.

**Evidence:** `docs/evidence/prototype-4/GATE-1-handover.md`, `caption-audit.md`, `pilot-sheets/`, `pilot-scoring-form.md`; `docs/evidence/EXP-020…EXP-026/`.

**Next step:** **STOP at gate 1.** Phase B begins only when Kylian returns scores and six decisions: checkpoint per style, full-run step count per style, caption verdict, dataset-size verdict, contingency authorisation, and whether the multi-style run proceeds.

---

## 2026-08-04 — M5 step 1: PEFT pinned under dependency-stack protection

**Objective:** add the LoRA training dependency required by Prototype 3 **without moving any part of the inference stack that M3 and M4 measurements depend on.**

**Plan:** M5 was planned in Plan mode and approved by Kylian after three rounds of correction. Two decisions were taken before planning: the smoke test **measures both training geometries** (512×512 and native 512×1536) in separate processes, and M5 uses **automated technical gates only — no human rubric gate**, deferring all visual judgement to Prototype 4.

**Completed work:** pre-flight (clean tree at `f1eba54`, in sync with `origin/main`, **123 passed**); protected baseline versions recorded; PEFT version chosen from published metadata (`diffusers 0.39.0` declares `peft>=0.17.0` for its `training` extra; `MIN_PEFT_VERSION` in `diffusers/utils/constants.py:24` is the older `0.6.0` loader floor); resolver **dry-run inspected before any write to the venv**; `peft==0.20.0` installed `--no-deps`; post-install verification; `ml/requirements-training.txt` written with the full rationale.

**Decision — dependency gating.** Installing a training package is treated as a gated step with its own evidence file, not a routine `pip install`. The stop-and-ask condition (any of torch / diffusers / transformers / accelerate / safetensors being upgraded, downgraded or reinstalled) was checked against the machine-readable `--report` JSON and **did not trigger**, so the install proceeded under the approved plan.

**Commands and tests:**

```
.venv/Scripts/python.exe -m pytest                                   -> 123 passed in 1.06s (pre)
.venv/Scripts/python.exe -m pip index versions peft                  -> latest 0.20.0
.venv/Scripts/python.exe -m pip install --dry-run peft==0.20.0 --report <json>
.venv/Scripts/python.exe -m pip install --no-deps peft==0.20.0
.venv/Scripts/python.exe -m pip check                                -> No broken requirements found.
.venv/Scripts/python.exe -m pytest                                   -> 123 passed in 1.09s (post)
```

**Real results:** the resolver report resolved to **exactly one package to install (peft 0.20.0)** and **touched none of the five protected packages** — peft's floors (`torch>=1.13.0`, `accelerate>=0.21.0`) sit far below the pinned versions and its `transformers` / `safetensors` requirements carry no upper bound, so the resolver had no reason to move anything. After install, all five protected versions are unchanged, `torch.cuda.is_available()` is `True` on the RTX 4060 Laptop GPU, and the only functional change is `diffusers.utils.USE_PEFT_BACKEND` flipping to `True`. Test count identical before and after (**123**), so nothing regressed.

**`bitsandbytes` and `xformers` confirmed ABSENT and deliberately not installed.** bitsandbytes is tier 3 of the M5 training memory ladder and requires Kylian's explicit approval; no 8-bit-optimizer support is claimed anywhere until it has actually installed and run on this machine.

**Unfinished work:** everything from plan step 2 onward — freezing the smoke-test manifest and validation kit, the training schema and runner, and experiments EXP-016…EXP-019.

**Blockers:** none. Note that **`gh` is not on PATH in this session**, so issue #6 state cannot be verified or changed from here.

**Evidence:** `docs/evidence/EXP-016/dependency-resolution.md` (protected baseline, version selection from metadata, real resolver output, install log, post-install verification, optional-tool absence).

**Next step:** plan step 2 — freeze `data/manifests/smoke-test-p3.csv` (12 `minimal-geometric` train-split items) and the validation kit **before any GPU work**, with a pytest proving no holdout item is included.

---

## 2026-08-04 — M5 complete: LoRA trains, reloads, and the combined stack fits by 202 MiB (DR-009)

**Objective:** answer RQ1 with measured data — does a LoRA actually train, save, reload and measurably change generation on 8 GB, and what does it cost? — and discharge the mandatory R12 combined-stack acceptance item.

**Completed work:** all thirteen plan steps. PEFT pinned under dependency gating; the smoke subset and validation kit frozen and hash-locked before any GPU work; a training schema with its own tier ladder; a training runner plus a process-isolating, gate-enforcing orchestrator; eight experiments across thirteen runs; a load-and-generate verifier split into two phases; the combined-stack runner; DR-009; eight registry rows; and the documentation set.

**Real results — all at training tier 0, no escalation anywhere:**

```
                geometry     peak alloc   peak device   spare     s/step
EXP-016a  1 step   512x512     3114.09      4267.5      3920.0    1.9344
EXP-016b  10 step  512x512     3133.40      4285.5      3902.0    0.4340
EXP-016   300 step 512x512     3133.40      4285.5      3902.0    0.2854
EXP-017a  1 step   512x1536    5160.96      6429.5      1758.0    2.5533
EXP-017b  10 step  512x1536    5182.58      6449.5      1738.0    1.1223
```

**Native deck-format LoRA training FITS**, which the plan treated as genuinely uncertain. Because tier 0 passed everywhere, deeper tiers were **not** executed — the ladder guard forbids collecting extra results for their own sake.

**The mechanism was measured, not assumed.** Post-load allocation is byte-identical at both geometries (2066.56 MiB) and the optimizer-step peak barely moves (2108.93 → 2118.76), while the forward/backward peak rises 3114.09 → 5182.58. **Activations scale with geometry; optimizer state does not.** This vindicates Kylian's thirteenth correction — he removed "increase gradient accumulation" from the memory ladder on the reasoning that at micro-batch 1 it changes training semantics but not micro-step peak memory — and it establishes gradient checkpointing as the correct tier-1 escalation, with a lower-memory optimizer as the wrong first move.

**EXP-018 (load and generate).** Reload proven from the **live UNet**: 0 LoRA modules before load, **128 after**. Lower bound at weight 0.0: **4/4 byte-identical** to the no-adapter baseline (mean absolute pixel difference 0.0, dHash 0, CLIP cosine 1.0) — recorded as a **diagnostic, not a pass condition**, because loading an inactive adapter can legitimately alter the execution graph. Changed output at weight 1.0: **4/4 beyond a noise floor declared before any result was read** (mean abs difference 51.89–66.33, dHash 20–28, CLIP cosine 0.4796–0.7247). The baseline peak of **2675.38 MiB is byte-identical to Prototype 1's EXP-002**, giving cross-milestone continuity for a third milestone running.

**EXP-019 (the R12 acceptance item).** Ran in the fixed order, 512×512 first. Both adapters live simultaneously, read back from the UNet: 128 LoRA modules + 16 IP-Adapter attention processors. At the deck format: **5143.73 MiB allocated, 7985.5 MiB device used of 8187.5 — 202.0 MiB spare, 2.5 % of the device.** It fits. **It is not comfortable headroom**, and it is *less* margin than IP-Adapter alone had in EXP-013 (222 MiB). Geometry was never reduced and no tier escalated.

**The LoRA's marginal cost is +3.04 MiB allocated at both geometries**, measured independently in EXP-018 and EXP-019 and matching the arithmetic for 1 594 368 fp16 parameters. It does not scale with output size.

**Decision — DR-009:** **LoRA selected** for Prototypes 4–5, rank 8 / alpha 8, UNet attention, text encoder and VAE frozen, tier 0. The record states explicitly that from-scratch, full fine-tuning, DreamBooth and Textual Inversion were **screened, not measured**, and that no superiority claim is made over them — the same honest limitation DR-007 carries for the gated SD 2.1.

**Commands and tests:**

```
.venv/Scripts/python.exe -m pytest                                    -> 210 passed
.venv/Scripts/python.exe scripts/build_smoke_test_manifest.py         -> 12 rows, full palette/shape coverage
.venv/Scripts/python.exe -m ml.training.train_lora --exp-id ...       -> 5 training runs
.venv/Scripts/python.exe scripts/run_lora_training.py --stage ...     -> gate-enforced staging
.venv/Scripts/python.exe -m ml.training.verify_lora --arm ...         -> 3 arms, 12 images
.venv/Scripts/python.exe scripts/evaluate_lora_effect.py              -> Phase 2, CPU, 29.7 s
.venv/Scripts/python.exe -m ml.training.combined_stack --exp-id ...   -> EXP-019a/b
```

**Failures recorded honestly.** The first EXP-019a attempt is preserved with `status: failed`. It was a defect in this milestone's own runner — `preprocess_for_adapter` returns `(image, note)` and the caller unpacked one value — **not** a finding about the stack. It is kept rather than deleted because deleting failed rows is how a record stops being a record, and it still carries one real measurement: the full stack loaded at 3308.33 MiB before failing in preprocessing.

**Unfinished work / deliberately out of scope:** no long *native* 512×1536 training run (a separate Prototype 4 decision); no trigger-token design (M5 used dataset captions verbatim, deliberately, so the smoke test carried one variable); no human rubric gate and **no style-quality claim anywhere** — that is Prototype 4's question.

**Blockers:** none. **`gh` is not on PATH in this session**, so issue #6 state could not be verified or changed from here.

**Evidence:** `docs/evidence/EXP-016/`, `EXP-017/`, `EXP-018/`, `EXP-019/`, `docs/evidence/prototype-3/` (training summary, two contact sheets), `docs/decisions/DR-009-fine-tuning-method.md`.

**Next step:** **M6 — Prototype 4: style-learning experiments** (issue #7, planned Aug 8–11). Per-style vs multi-style LoRAs (RQ5), dataset-size/rank/learning-rate variations (RQ4), and the human rubric evaluation that M5 deliberately deferred.

---

## 2026-08-01 — M4 closed: human review passed, standard IP-Adapter selected (DR-008)

**Objective:** complete M4 after the human-review gate by recording Kylian's scores, deciding the reference-conditioning method, and finalising the milestone.

**Completed work:** Kylian inspected the eight contact sheets, approved the evidence, and supplied aggregate rubric scores plus failure-mode observations. Scores recorded **at the granularity actually used** — aggregate per (method × influence level × resolution), which is exactly the granularity of the form's own rows, so unlike M3 they are entered directly rather than marked "not individually scored". `human-scores.csv` is authoritative; the form and probe are generated from it by joining onto the inventory of what was actually generated, and the generator warns on any approved row matching no generated unit. All 22 rows matched with no orphans.

**Blanks preserved as not scored — 29 cells.** A blank is never a zero and is never back-filled: blanks are excluded from every mean and the surviving `n` is printed beside each figure. `reference_influence` and `copy_or_overfitting_risk` are blank for text-only, which uses no reference. `diversity_across_seeds` carries **n=1 per method** and is flagged as not load-bearing. **`text-only` at 512×1536 is entirely unscored** — it was not visually rescored from the M4 sheets, and **no M3 value was substituted**, because the M3 review used different sheets and answered a different question.

**Decision — DR-008:** **standard IP-Adapter selected** as the primary reference-conditioning method for Prototypes 3–5 (`h94/IP-Adapter`, `ip-adapter_sd15.safetensors` @ `018e402774`), **default scale 0.55**, user-adjustable **0.40–0.60**, higher values only with an explicit warning that prompt authority falls and pseudo-text / source-like composition increase. **img2img is retained as a documented zero-extra-VRAM fallback, not the default path.** IP-Adapter-Plus not selected (no decisive advantage, slightly more VRAM). ControlNet stays criteria-only and screened out for M4 — a scope decision, not a quality judgement, deferred to Prototype 5 for layout control.

**Human scores (aggregate means at 512×512, blanks excluded, n stated):**

```
                     prompt style ref  quality decal comp artef orig  divers copy
text-only            3.00   3.00  n/s  4.00    2.00  3.00 4.00  4.00  4.00   n/s   (n=1)
img2img              3.00   4.12  3.75 4.00    3.75  4.00 3.38  3.12  3.00   3.12  (n=8)
ip-adapter           3.11   4.44  3.44 4.00    3.56  3.89 3.44  4.11  4.00   4.33  (n=9)
ip-adapter-plus      3.00   5.00  4.00 4.00    4.00  4.00 3.00  4.00  4.00   4.00  (n=1)

Deck format 512x1536:  img2img 0.65  originality 1, copy risk 1  -> REJECTED as primary
                       ip-adapter 0.55 originality 4, copy risk 4
                       text-only      NOT SCORED (deliberately)
```

**Why the decision went this way.** Both measured methods met all four controllability conditions, so RQ6 has a **positive** answer and the choice is about cost, not capability. The decisive evidence is the near-copy count: **all six copy-risk flags in the milestone (dHash ≤ 6) are img2img at 512×1536**, three at **dHash 0–1** — perceptually indistinguishable from the reference — at the very geometry the product ships. IP-Adapter produced **zero** near-copy flags at any scale or geometry, and scored higher on originality (4.11 vs 3.12) and copy risk (4.33 vs 3.12).

**Two risks stated prominently rather than softened:**

- **R13 (occurred, mitigated by method selection):** img2img reproduces the reference at the deck format. Mechanism is mechanical — img2img forces the reference into the output resolution, so when the aspect already matches nothing is cropped and denoising at `strength=0.65` starts from an essentially intact copy. Median dHash for img2img at medium is 27 @512×512 but **5 @512×1536**.
- **R12 (open, high/high):** **IP-Adapter at 512×1536 peaks at 7965.5 MiB of 8187.5 MiB physical — about 222 MiB spare.** Never to be described as comfortable headroom. **A combined SD 1.5 + LoRA + IP-Adapter smoke test at 512×1536 is now a mandatory acceptance item for M5**, added to the planning row and the risk register. If it fails, the failure is recorded as its own result row and approved memory tiers are tested in separate runs — **geometry is never silently reduced to make it pass**.

**Objective measurements and human scores are reported in separate sections** in DR-008, `prototype-2.md` and `human-scores.md`, and are never blended into a single number.

**Docs updated:** DR-008 (new); `experiments/registry.csv` (**EXP-007…EXP-014**, all mandated fields, unmeasured written as "not measured"); `docs/prototypes/prototype-2.md` (new); `docs/03-architecture.md` (**new section D-F**, the second weighted matrix populated with measured hardware data); `docs/06-prototype-overview.md`; `docs/02-planning.md` + change log (~9 h actual vs 10 h estimated) and the M5 acceptance item; `docs/process/risk-register.md` (**R12 and R13 added**; R1 gains the adapter figure, R8 its first conditioning evidence); `docs/07-testing-strategy.md` (**seven principles from Prototype 2**, headed by "measurement instrumentation must never enter the workload it measures"); `docs/04-dataset-methodology.md` (the imprecise "to be resolved in M4" heading corrected — M4 produced *evidence*, the mitigation decision stays in Prototype 4/M6 — plus the C6 frame/pseudo-text evidence table); `docs/learning-outcome-traceability.md` (D1, D4, D5, D6); `docs/ai-usage.md`; this log; session handoff.

**Blockers:** none. **Next step:** issue #5 closure, board → Done, validated push, M4 milestone report. **Then stop before M5.**

---

## 2026-08-01 — M4 Phase-1 measurements: EXP-007 to EXP-013 complete, 299 runs, zero failures

**Objective:** produce the measured evidence for RQ6 — how text and reference conditioning combine, and what each method costs — up to the mandatory human-review gate.

**Plan:** approved M4 plan, execution steps 2–6. One fresh OS process per method × adapter variant × resolution × memory tier, launched by `scripts/run_reference_conditioning.py`. Influence levels share a process by design, with clean-process spot checks to verify that sharing.

**Completed work:** 16 processes, 299 generation rows, **0 failures, 0 timeouts, no memory-tier escalation anywhere**. EXP-007 gate · EXP-008/008b img2img sweep + spot check · EXP-009/009b IP-Adapter sweep + spot check · EXP-010 baseline and scale-0.0 diagnostic (512×512 and the deck format) · EXP-011 conflict and difficult reference · EXP-012 IP-Adapter-Plus · EXP-013 deck format.

**Interruption, recorded rather than smoothed over.** The first orchestrator invocation was killed mid-EXP-009 by a usage-limit cutoff. Stages 1–4 had completed; EXP-009's 77 partial rows were **discarded and the experiment re-run from scratch**, because each runner deletes its own results file at start rather than appending twice. `--start-at` was added for clean resumption. No partial data was kept and nothing was reconstructed by hand.

**Real results — VRAM (peak allocated, per run, tier 0, fp16):**

```
512x512      text-only      2675.38 MiB     img2img         2675.38 MiB  (+0.00)
             ip-adapter     3924.07 MiB     ip-adapter-plus 3978.87 MiB
512x1536     text-only      3892.01 MiB     img2img         3892.01 MiB  (+0.00)
             ip-adapter     5140.69 MiB
```

**img2img costs exactly zero extra VRAM** — byte-identical to the text-only baseline at both geometries, which is what `AutoPipelineForImage2Image.from_pipe` sharing the already-loaded components should produce, and it is now measured rather than projected. **IP-Adapter costs +1248.69 MiB at 512×512 and +1248.68 MiB at 512×1536** — the same fixed resident cost at both geometries, consistent with its scale acting on attention rather than on output size. IP-Adapter-Plus adds a further 54.80 MiB over base IP-Adapter.

**Headroom warning for the deck format.** IP-Adapter at 512×1536 reached **7965.5 MiB peak device used against 8187.5 MiB physical — roughly 222 MiB spare**. No overflow flag was raised (allocated and reserved both stayed below physical) and all 9 runs succeeded, but this is not headroom to describe as comfortable, and adding a LoRA on top in Prototype 3–4 cannot be assumed to fit.

**Real results — latency (median seconds):**

```
512x512    text-only 3.248 | img2img 3.021 (s=0.90) ... 1.208 (s=0.30) | ip-adapter ~3.35-3.47 | plus 3.436
512x1536   text-only 11.837 | img2img 7.980 (s=0.65) | ip-adapter 12.022
```

**The img2img latency trap is confirmed, not assumed.** Wall-clock falls as reference influence rises (3.021 s at strength 0.90 → 1.208 s at 0.30) purely because diffusers runs `int(steps × strength)` steps. Seconds per effective step stays flat at 0.112–0.134, so the apparent speed advantage is fewer steps, not faster ones. Every row carries `effective_steps` and the summaries report s/eff step alongside wall-clock.

**Process isolation — ACCEPTED in full.** All **6 of 6** clean-process spot-check pairs agree with their shared-process counterparts at **+0.000 %**, against a 2 % tolerance pre-declared in code before any measurement. Sharing a process across influence levels did not distort `peak_vram_allocated_mb`; no method needed re-running one level per process. Recorded as a confirmation precisely because it could have gone the other way, as EXP-005's allocator contamination did one milestone earlier.

**EXP-010 lower-bound diagnostic — both comparisons maximally positive:**

- **12 of 12** IP-Adapter runs at `scale=0.0` are **byte-identical** to the text-only baseline at the same prompt and seed. At zero scale the cross-attention path contributes nothing, so the method's lower bound is the baseline *exactly*, not approximately.
- **12 of 12** M4 baseline outputs are **byte-identical to Prototype 1's EXP-002 hashes**. Cross-milestone repeatability holds, and the M4 baseline is provably the M3 baseline, so the two milestones' figures are directly comparable.

Both were tested rather than promised; the diagnostic was written to report a mismatch honestly, and the "hash inequality alone does not fail the lower bound" caveat remains in the document because it governs how the result would have been read had it come out differently.

**Measurement separation verified from data:** `image_encoder_revision_sha` is **empty on every text-only and img2img row**, which is positive evidence that no CLIP encoder was resident in those measured processes. A pytest parses the Phase-1 runner with `ast` and fails if it ever imports `ml.evaluation.similarity`.

**Defect found in my own analysis script and fixed:** the process-isolation report initially printed "REJECTED — at least one pair exceeded the tolerance" when the pairs were merely *absent* from a partial dataset. Reporting missing data as a failed check is exactly the kind of false claim the honesty rules forbid, so the three outcomes are now distinguished: accepted, rejected, and not measured.

**Unfinished work:** Phase-2 similarity evaluation (running), contact sheets, the scoring form, and the gate handoff.

**Blockers:** none.

**Commands/tests:** `.venv\Scripts\python.exe scripts\run_reference_conditioning.py --start-at 5` → `12/12 processes exited 0 in 1200.87s`. `.venv\Scripts\python.exe -m pytest` → 123 passed; frozen-kit fingerprint `c40749bc…` unchanged.

**Evidence:** `docs/evidence/EXP-007/` … `EXP-013/`, and `docs/evidence/prototype-2/` (`measurement-summary.md`, `process-isolation-check.md`, `lower-bound-diagnostic.md`, `all-generation-results.csv`, `process-run-manifest.json`).

**Next step:** Phase-2 similarity, contact sheets, blank scoring form, then **stop at the human-review gate**. No scores, no method selection, no DR-008 conclusion, no push.

---

## 2026-08-01 — M4 foundation: Prototype 2 reference-conditioning schema, kit and Phase-1 runner

**Objective:** build and validate the reference-conditioning foundation for Prototype 2 (RQ6, RQ7) before spending any GPU time — the data model, the frozen reference kit, and the Phase-1 generation runner.

**Plan:** approved M4 plan (`docs/prompts/` planning session, 2026-07-31), steps 1–3 of its safe execution order. Measured arms: text-only baseline, img2img, IP-Adapter, IP-Adapter-Plus at medium only. ControlNet compared on criteria but **not implemented**. No LoRA training, no dataset modification, no edit to the frozen prompt kit.

**Completed work:**

- `ml/inference/reference_schema.py` — pure data model (no torch/diffusers import): method registry, reference registry R1–R5, condition table C1–C6, the shared influence-level mapping, `effective_steps`, `retained_area_fraction`, `process_config_key`, the Phase-1 `ReferenceResultRow` and the **separate** Phase-2 `SimilarityRow`, aggregation and the unscored summary renderer.
- `scripts/build_reference_kit.py` — verifies every dataset-derived reference against `data/manifests/dataset-v1.csv` (holdout membership, dimensions, licence, SHA-256 of the file on disk), regenerates R4 from seed 9001, copies the two project-original references into `data/references/` with a byte-identity check, computes retained-area fractions, and writes the registry plus a contact sheet.
- `ml/inference/reference_conditioning.py` — Phase-1 runner. Imports **no** similarity or metric code. Reuses Prototype 1's `load_pipeline`, `ResourceSampler`, `resolve_revision` and `sha256_bytes` unchanged, derives the img2img pipeline through `AutoPipelineForImage2Image.from_pipe` so both SD 1.5-native arms provably share identical weights, and works around the diffusers 0.39.0 pinning gap by loading and registering the CLIP image encoder itself at the pinned revision before calling `load_ip_adapter`.
- Tests: `test_reference_schema.py` (schema, level mapping, arithmetic, registry integrity, process boundary, similarity join, monotonicity, unscored summary) and `test_reference_conditioning.py` (run plan, preprocessing geometry, failure recording).

**Measurement-validity correction preserved from the plan:** generation measurement is separated from similarity evaluation. A pytest parses the runner with `ast` and asserts it never imports `ml.evaluation.similarity`, so the 2.35 GiB CLIP metric encoder can never be resident in a process whose VRAM figure describes a generation method — the same class of error as the EXP-005 allocator contamination.

**Correction made against the approved plan, after inspecting the actual images:** the plan describes condition **C5** as "reference says cresting wave, prompt says minimal geometric". *Cresting wave* is the wording of prompt **P3-ukiyo**, not the content of **R3** (`DS-0103`, `met-37129.jpg`), which is a landscape ukiyo-e print of a seated figure at a low desk in an interior. The conflict C5 tests is real and unchanged — a figurative ukiyo-e scene against a minimal-geometric prompt — but it is now described accurately, C3 is relabelled *style-matched on style, subject-mismatched*, and a pytest guards against the old label reappearing. Recorded also: **R1 is likewise a framed, text-dominated poster scan**; R5 is the harder case because it adds landscape orientation, not because it is the only framed reference.

**Defects found and fixed while validating the resumed working tree** (three real, one test-side):

1. `resolve_levels("text-only", "sweep")` raised `KeyError` — the control arm owns no sweep values. EXP-010 runs the baseline through that entry point, so it would have failed at launch. It now returns the single `none` level.
2. Failure handlers used `str(err).splitlines()[0]`, which raises `IndexError` on an exception with an empty message — destroying the very failure row the honesty rules require. Replaced with `_first_line`, which never returns empty.
3. The `--gate` JSON did not record the UNet attention-processor evidence its own docstring promised. It now records the IP-Adapter processor names, the adapter/total processor counts read back from the live UNet, and post-load VRAM.
4. The Phase-1/Phase-2 import guard forbade the whole `ml.evaluation` package, which would have banned the frozen prompt kit. Narrowed to fully-qualified names so `from ml.evaluation import similarity` is still caught, plus a positive assertion that the frozen kit *is* imported.

**Unfinished work:** EXP-007…EXP-014 (all GPU runs), the Phase-2 similarity evaluator, the orchestrator, contact sheets, and the scoring form.

**Blockers:** none.

**Commands/tests (real output):**

```
.venv\Scripts\python.exe -m pytest
113 passed in 0.99s

.venv\Scripts\python.exe -c "from ml.evaluation import prompt_kit; print(prompt_kit.kit_fingerprint())"
c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228

.venv\Scripts\python.exe scripts\build_reference_kit.py
  R1: OK - DS-0077 holdout, SHA-256 matches manifest and file on disk
  R2: OK - DS-0048 holdout, SHA-256 matches manifest and file on disk
  R3: OK - DS-0103 holdout, SHA-256 matches manifest and file on disk
  R4: n/a - generated from seed, not a manifest item
  R5: OK - DS-0088 holdout, SHA-256 matches manifest and file on disk
  5 references verified against the manifest and materialised.
```

66 pre-existing tests plus 47 new ones pass, and the frozen prompt-kit fingerprint is **unchanged**. No linter is installed in this environment (`ruff` absent), so pytest is the validation gate; this is stated rather than a lint step being claimed.

**Real results:** the reference kit is frozen and provenance-verified; no GPU measurement has been taken yet, and none is claimed.

**Evidence:** `docs/evidence/prototype-2/reference-kit.md`, `reference-kit.csv`, `reference-kit-sheet.jpg`; `docs/evidence/EXP-007/cuda-gate-recheck.json` and `pip-freeze.txt`.

**Next step:** EXP-007, the IP-Adapter environment gate — a hard gate. Nothing downstream runs until the adapter loads at the pinned revision with its attention processors verifiably present in the UNet.

---

## 2026-07-30 — M3 closed: human review passed, SD 1.5 selected (DR-007)

**Objective:** complete M3 after the human-review gate by recording Kylian's scores, deciding the base model, and finalising the milestone.

**Completed work:** Kylian manually inspected the three contact sheets, approved the evidence as visually usable, and supplied rubric scores. Scores recorded **at the granularity actually used** — aggregate per model/track — in `docs/evidence/EXP-006-scoring/human-scores.md` and `.csv`. On his explicit instruction, the per-unit cells in `scoring-form.md`/`.csv` now read **"not individually scored"** rather than being back-filled with the aggregates, since presenting one aggregate judgement as 28 independent judgements would misrepresent the review. `reference_influence` is **N/A** (no reference image until Prototype 2) and `diversity_across_seeds` is recorded as **not manually scored**, because the supplied sheets showed the fixed seed-42 comparison rather than a multi-seed comparison — **no value was invented for either**.

**Human scores (1–5):**

```
Track A (both @512x512)   SD 1.5  3/3/4/3/3/4/3      SDXL  3/3/4/3/3/4/3   <- IDENTICAL
Track B (native)          SD 1.5  3/3/4/3/3/4/3      SDXL  4/5/5/4/4/4/3   <- SDXL wins
  (prompt_adherence / style_consistency / visual_quality / decal_suitability /
   composition / artefacts / originality)

Aspect ratio (visual_quality / decal_suitability / composition)
  direct-1x1  4/2/3   direct-1x2  4/4/4   direct-1x3  4/5/4 SELECTED   square-crop  3/2/3 REJECTED
```

**Decision — DR-007:** **Stable Diffusion 1.5 selected as the base model for Prototypes 2–5** (pinned `451f4fe1`). SDXL is the **visual-quality winner at native 1024×1024** and is retained as a benchmark, not as the production model. **Deck format: direct 1:3 at 512×1536**; square-crop rejected. The Track A result is what made this clear-cut: at the same resolution the student scored both candidates identically, so SDXL's quality advantage exists only at a resolution this 8 GB GPU cannot hold, and its native inference only completed because Windows WDDM silently spilled into shared host RAM. **"30/30 successful" is explicitly not described as SDXL fitting comfortably on this hardware.**

**Limitations stated, not hidden:** the decision rests on **two** measured candidates because SD 2.1 base is gated (HTTP 401, EXP-003); candidate B cannot be reproduced today without authenticating. EXP-005's contaminated first run is retained as a **documented failed measurement design**, with its refuted thermal hypothesis, rather than deleted.

**Docs updated:** DR-007 (new); `experiments/registry.csv` (evaluation + next_action for EXP-002/004/005); `docs/prototypes/prototype-1.md` (status → complete, human scores, conclusion); `docs/03-architecture.md` (**new section D-E**, the first weighted matrix populated with measured hardware data); `docs/06-prototype-overview.md`; `docs/02-planning.md` + change log (~8 h actual vs 10 h est); `docs/process/risk-register.md` (R1 → mitigating, R5 → closed, R10 → closed, **R11 added** for third-party hosting availability); `docs/07-testing-strategy.md` (six principles added from Prototype 1 experience); `docs/learning-outcome-traceability.md` (D1/D2/D4/D5/D6); `docs/ai-usage.md`; this log; session handoff.

**Blockers:** none. **Next step:** issue #4 closure, board → Done, validated push, M3 milestone report. Then stop before M4.

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
