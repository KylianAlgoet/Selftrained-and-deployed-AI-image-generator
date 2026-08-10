# The one remote CI failure, and how it was fixed

**Date:** 2026-08-10 · **Milestone:** M8 (reopened) · **Commit under test:** `68d1bf2`
**Related:** [`camera-damping-trace.md`](camera-damping-trace.md), `docs/process/feature-freeze.md`

## What CI reported

The first GitHub Actions run of the M8 work returned two green jobs and one red one.

| job | result |
|---|---|
| `pytest (no GPU, no weights)` | **PASS** |
| `vitest, eslint, build` | **PASS** |
| `playwright (mocked API, no model)` | **37 passed, 1 failed** |

The single failure was `e2e/decal-upload.spec.ts › user decal upload › replacing the decal does not
reset the camera`, which **timed out after 300 000 ms** on the Windows runner.

## Why it failed there and not here

The test asked a structural question — *does swapping the decal texture move the camera?* — and
answered it photographically. It settled the WebGL canvas four times, and each settle took up to
twenty screenshots at 250 ms intervals.

On the validated machine that is slow but survivable. On a GitHub runner there is no GPU: Chromium
falls back to SwiftShader and every capture is software-rasterised. The test's own comment recorded
the local cost as ~2.3 minutes and set a 300 s budget against it. The runner exceeded even that.

Two things were wrong, and only one of them was the clock.

1. **The measurement was disproportionate.** Rendering a full frame and comparing PNG bytes is an
   extremely expensive way to locate a camera.
2. **The measurement could not express the claim.** A pixel diff can only conclude *the frame
   changed*. It can never conclude *the camera is in the same place*, which is the actual assertion.
   The old test had to prove camera preservation indirectly, by showing that **Reset view still had
   work to do** afterwards.

Raising the timeout was rejected: it would have bought a green tick without addressing either
point, and the suite would have stayed the slowest and least informative part of CI.

## What replaced it

Narrowly gated, **read-only** instrumentation that reports the live camera pose, and assertions
that compare that pose structurally.

- `src/viewer/e2eCameraState.ts` — pure functions and the handle name. No imports at all, so the
  Playwright project and the application can share it under different tsconfigs.
- `src/viewer/E2ECameraProbe.tsx` — mounts inside the R3F canvas and publishes
  `window.__deckforgeE2ECamera.cameraState()`, returning camera position, camera quaternion and the
  OrbitControls target. It reads; it never writes.
- `vite.config.ts` — the gate: `__DECKFORGE_E2E__`, a `define` replaced with a literal boolean.
- `playwright.config.ts` — sets `VITE_E2E=1` on the `webServer` build, and nothing else does.

**No application behaviour was changed.** Camera defaults, OrbitControls defaults, the texture swap
path, the Reset view control and the production UI are byte-for-byte what they were.

## Why a `define` and not `import.meta.env.VITE_E2E`

Only a `define` is guaranteed to be substituted **literally**. That makes `false && <Probe />` dead
code, so the probe, the module and the handle name are dropped from the bundle rather than merely
switched off inside it. An env lookup would have left the string in the shipped JavaScript.

## The gate, verified in both directions

Neither direction is assumed; both were run on 2026-08-10.

| build | command | result |
|---|---|---|
| ordinary production | `npm run build` then `npm run verify:no-e2e-handle` | `ok: none of the 6 built assets contain "__deckforgeE2ECamera"` |
| E2E | `VITE_E2E=1 npm run build` then the same guard | `FAIL: the production bundle contains the E2E handle ... dist\assets\index-DCQMOnWs.js` |

The second row is the important one: it proves the guard actually detects the handle, so the first
row is a real result and not a check that passes on everything. The guard now runs in the
`frontend` CI job, immediately after `npm run build`, and reads the handle name out of the source so
a rename cannot leave it silently checking a dead string.

## The false start, recorded rather than hidden

The first version of the rewritten test defined "the camera has come to rest" as **two consecutive
reads equal to within 1e-6**. It failed three times out of three with *"the camera never came to
rest"*.

That rule was wrong. drei enables OrbitControls damping by default, so the camera **decays towards
rest and never exactly arrives** — two identical reads are a state this scene does not reach. A
temporary diagnostic spec traced the real decay before any threshold was chosen; the trace is in
[`camera-damping-trace.md`](camera-damping-trace.md) and the diagnostic was deleted once it had
served its purpose.

The trace also produced the second failure mode: damping only advances on a **rendered frame**, so
on a software rasteriser a stalled render loop can emit two identical reads while the camera is
still in flight. Each sample therefore waits for a real frame, and two consecutive quiet samples
are required.

## The test is now stronger, not just faster

| | before | after |
|---|---|---|
| after the texture swap | *the frame differs from before* | **the pose is identical** to within 1e-3, against a 3.7-unit move |
| after Reset view | *the frame differs from after the swap* | that, **and the pose equals the opening pose** |
| drag precondition | frame differed | pose differed |
| local runtime | ~138 s | **6.6 s** |
| whole Playwright suite | — | **1.2 min**, 38/38 |

The "Reset view returns to the opening pose" assertion did not exist before and could not have: the
old measurement had no way to say where the camera was, only that something on screen had changed.

## Attempt 1 went to CI and failed. What it taught.

`316b2cd` was pushed and produced **CI run #5**. It is the first real measurement of this suite on a
runner, and it invalidated part of the reasoning above.

| job | result |
|---|---|
| `pytest (no GPU, no weights)` | **PASS**, 2m 31s |
| `vitest, eslint, build` | **PASS**, 59s — 181 vitest, and the new handle guard passed |
| `playwright (mocked API, no model)` | **FAIL** — 35 passed, **3 failed**, 16.8 m |

The camera scenario no longer took 300 s, but it still **exceeded the 60 s test timeout**, at
`readCameraState`. Two neighbouring scenarios failed with it:

| # | scenario | symptom |
|---:|---|---|
| 12 | replacing the decal does not reset the camera | test timeout 60 s, inside the settle loop |
| 13 | 409 is presented as busy, not as a failure | test timeout 60 s, "tearing down context exceeded" |
| 14 | 504 reports how far the generation actually got | `stopped after 14 of 30 steps` not found in 10 s |

**Scenarios 13 and 14 are most likely collateral, not independent regressions.** They are
immediately contiguous with the timed-out test, they touch none of the changed code, they passed in
the previous run, and everything from scenario 15 onwards passed. The camera test's context
teardown also timed out, which is the usual way a hung page poisons the next couple of tests. This
is a **reasoned inference, not a proven one** — the next run is what settles it.

### Why it still timed out

Two mistakes, both mine, both invisible without a runner.

1. **The settle loop polled from Node.** Every sample was `waitForTimeout(100)` plus a
   `page.evaluate`, and the loop allowed up to 120 of them per phase — roughly 120 round trips
   across the CDP boundary, four times per test. Locally that is 6.6 s. On a runner where the
   WebGL-heavy scenarios run about **15x slower** (scenario 11 took 30.6 s against 2.1 s here) it is
   not affordable.
2. **It waited in milliseconds for something that happens in frames.** Damping advances only when a
   frame renders. A wall-clock settle rule is therefore a bet on the frame rate, and a software
   rasteriser is exactly where that bet loses.

Raising the timeout was still not on the table.

## Attempt 2: the tolerance is measured, not assumed

The measurement moved **inside the page**. One `page.evaluate` per phase waits a fixed number of
**rendered frames**, reads the pose, waits a few more, and reads again. Four round trips for the
whole test instead of several hundred.

The second read is the important one. It gives the **residual drift** — how far the camera is still
moving on its own, on the machine actually running the test — and the comparison tolerance is
derived from that number rather than hard-coded:

```
tolerance = max(drift x 20, 1e-3)
```

If the drift is larger than `MAX_RESIDUAL_DRIFT`, the test fails as **UNMEASURED** with that word in
the message, rather than reporting a still-coasting camera as a texture swap that moved it. "Not
measured" and "failed" keep separate code paths, which is this project's rule.

Two further assertions make the claim decisive rather than tolerance-dependent: after the swap the
camera must still be **more than 1.0 away** from the opening pose (a reset would put it back
exactly), and after **Reset view** it must be back **at** the opening pose.

### A second defect, caught by a unit test rather than by CI

The first draft set `MAX_RESIDUAL_DRIFT = 0.05`. With a factor of 20 that makes the worst permitted
tolerance exactly **1.0** — precisely `DISTINCT_VIEWPOINT`. At the worst drift the test would accept,
the tolerance would have been wide enough to swallow an entire change of viewpoint, and the
comparison would have been decorative.

A vitest case asserting `toleranceForDrift(MAX_RESIDUAL_DRIFT) < DISTINCT_VIEWPOINT` failed on the
first run and caught it. `MAX_RESIDUAL_DRIFT` is now **5e-3**, so the worst-case tolerance is 0.1 —
a 10x margin under `DISTINCT_VIEWPOINT` and 37x under the 3.7-unit move a reset makes. The measured
drift at 90 frames is ~1.3e-3, so the limit is reached with room to spare.

This is the failure mode the unit tests were written to catch, and it is why they are biased towards
proving the rule is not too lax.

## Local validation, 2026-08-10

All run on the validated machine, against the built bundle.

Attempt 2, after the CI failure above.

| gate | command | result |
|---|---|---|
| camera test, repeated | `npx playwright test -g "replacing the decal..." --repeat-each=5` | **5 passed** (40.3 s total incl. build) |
| full E2E suite | `npx playwright test` | **38 passed** (1.2 m) |
| unit tests | `npm run test` | **183 passed**, 12 files |
| lint | `npm run lint` | clean |
| E2E typecheck | `npm run typecheck:e2e` | clean |
| production build | `npm run build` | succeeds |
| handle gate | `npm run verify:no-e2e-handle` | ok |
| backend | `.venv/Scripts/python.exe -m pytest` | **473 passed** |

**No GPU inference was run.** The generation total remains **27**.

Attempt 1 recorded 181 vitest and a 6.6 s scenario; the counts differ because the rewrite replaced
the `cameraStatesEqual` cases with `maxComponentDelta` and `toleranceForDrift` cases.

## Attempt 2 also failed on CI — and revealed that the camera test was never the whole problem

**CI run #6, `f409b65`:** pytest **PASS** (2m 39s) · vitest/eslint/build **PASS** (1m 1s, 183
vitest) · playwright **FAIL — 32 passed, 6 failed**, 18.0 m.

The camera scenario timed out again, but *where* it timed out is the finding. It failed at the
**third** probe — the cheap one, asking for 7 frames. The expensive 94-frame probe before it
**completed, and its drift precondition passed**. The measurement was no longer the bottleneck; the
test simply ran out of wall clock on everything around it.

And the failing set moved wholesale.

| scenario | run #5 | run #6 |
|---|---|---|
| `?review=1` restores both review tools | 2.6 s pass | **56.8 s** pass |
| production interface exposes no review controls | 3.1 s pass | 20.6 s pass |
| 409 is presented as busy | **FAIL** (2.2 m) | 6.4 s pass |
| 504 reports how far the generation got | **FAIL** (2.1 m) | 19.1 s pass |
| submits the bounded settings as multipart fields | 5.9 s pass | **FAIL** |
| offers a PNG download and a metadata download | 20.9 s pass | **FAIL** |

Run #4 failed 1 scenario, #5 failed 3, #6 failed 6, and the subsets barely overlap. The same code
path swings **22x between runs**. Five of run #6's failures are the `Generation result` region never
appearing after a **mocked** 4-second response — no GPU, no model, no network, nothing the camera
work touches, and nothing the probe could slow down (it mounts inside the canvas and does no
per-frame work).

**Conclusion: this is a CI capacity problem, not a camera-measurement problem.** The cascade theory
from run #5 is now supported — 409 and 504 recovered on their own once the camera test failed
earlier — but it was only ever half the story. Making the camera test cheaper a third time could not
turn CI green, because the other five would still be red.

## The decision: retries on CI, recorded as a limitation

Approved by Kylian on 2026-08-10 after the three options were put to him: retries, a larger suite
timeout, or disabling OrbitControls damping in E2E builds.

`playwright.config.ts` now sets **`retries: process.env.CI ? 2 : 0`**. Locally it stays 0 — a test
that fails here has found something. The `e2e` job's `timeout-minutes` moved 30 → 45 so a retrying
run can finish and report instead of being killed halfway; that is the **job's** wall-clock guard,
and **no per-test budget was changed to make anything pass**.

**This masks genuine flakiness. That is a limitation, not a fix, and it belongs in the report as
one.** What it does not mask is a deterministic defect, which still fails all three attempts. The
trade being made is between a suite whose red/green carries no information because the environment
is noisy, and one where red means something.

The alternatives were rejected for stated reasons: a larger suite timeout accepts ~20-minute
feedback and still loses to a 22x swing; disabling damping in E2E builds would fix the camera
scenario decisively but would stop the suite exercising the production control configuration — and
would not have fixed the five unrelated failures at all.

## CI run #7: the camera fix is confirmed, and the remaining failure is not it

**`b09035a`:** pytest **PASS** (2m 26s) · vitest/eslint/build **PASS** (1m 0s, 183 vitest) ·
playwright **36 passed, 1 flaky, 1 failed**, 15.6 m.

**`replacing the decal does not reset the camera` PASSED — 40.2 s, first attempt, no retry.** That is
the claim this whole document exists to establish, and it is now established on a GitHub runner
rather than only on its author's machine. Three measurements, same scenario:

| version | local | CI |
|---|---|---|
| screenshot comparison | ~138 s | **timeout at 300 000 ms** |
| structural, Node-side polling | 6.6 s | **timeout at 60 000 ms** |
| structural, in-page, frame-counted | ~4 s | **40.2 s, passing** |

### What retries actually did, quoted rather than rounded

- `offers a PNG download and a metadata download` — failed, then **passed on retry #1 in 9.1 s**.
  Reported as **flaky**. This is exactly the case retries exist for.
- `a completed generation shows the image, the duration and the metadata` — **failed all three
  attempts** (2.3 m, 2.4 m, 2.0 m). Retries did **not** mask it, which is the property that was
  claimed for them.

### The runner stalls in multi-minute windows

The failing test is pre-existing, untouched by any of this work, and passed in 11.4 s in run #5. Its
setup is identical to three neighbours that passed in the same run:

| # | scenario | same mock, same flow | result |
|---:|---|---|---|
| 22 | submits the bounded settings as multipart fields | `generateDelayMs: 300` | **5.6 s pass** |
| 24 | a completed generation shows the image… | `generateDelayMs: 300` | **2.3 m fail x3** |
| 27 | offers a PNG download… | `generateDelayMs: 300` | 1.8 m fail → **9.1 s pass** |
| 29 | applies the generated artwork to the deck | `generateDelayMs: 300` | **8.0 s pass** |

The same code path takes 5.6 s, then over two minutes, then 8.0 s, inside one run. **The runner
degrades for a window of minutes and every test inside that window fails, whatever it is.** Because
Playwright retries immediately, all three attempts of scenario 24 landed inside the same window —
while scenario 27's retry fell outside it and passed in 9 seconds.

That is why retries rescued one and not the other, and it is a property of the stall, not of the
tests.

### What this means for the remaining red

Retries were the right call and are doing their job. They cannot help a stall that outlasts a whole
retry cycle. The remaining lever is the per-test budget — the thing deliberately left alone until
the measurement had been fixed, which it now demonstrably has. **That decision is open and is
Kylian's**, and this document does not pre-empt it.

## CI runs #8 and #9: green, and what that is and is not worth

| run | commit | what changed | result |
|---:|---|---|---|
| #8 | `d29fba8` | docs only — **old budgets**, retries on | **Success** |
| #9 | `e9c9fb4` | CI budgets 180 s / 45 s | **Success**, 18m 56s |

Run #9, job by job: pytest **PASS** 2m 30s · vitest/eslint/build **PASS** 1m 0s with **183/183**
vitest · playwright **PASS** 18m 50s, the E2E step 14m 45s. `Upload the report on failure` was
skipped and the run produced **no artifacts**.

**All three jobs are green. That was the condition for M8, and it is met.**

### Three honest qualifications

1. **Run #8 passed under the OLD budgets.** It ran with retries but with 60 s / 10 s, and it went
   green anyway. So run #9's green **cannot be attributed to the budget change alone** — the stall
   is intermittent, and run #8 simply got a better runner. The budget change removes a known failure
   mode; it is not proven to be what turned CI green.
2. **The per-scenario retry counts could not be read.** The E2E step's log would not expand through
   the interface available here, so it is **not known** whether any scenario passed only on a retry.
   The absence of artifacts does not settle it either, because the upload step is `if: failure()`
   and a flaky-but-passing scenario produces none. This is recorded as unread rather than assumed to
   be zero.
3. **A green run under `retries: 2` and a 180 s budget is weaker evidence than a first-attempt green
   under 60 s**, and the report must say so rather than presenting a tick.

What *is* solidly established is narrower and still worth having: **the camera scenario passed on
CI on its first attempt, in 40.2 s, in run #7 — before any budget was raised.** That result stands
on its own and is the one this document was opened to obtain.

## What this still does not prove

- **Nothing here has been observed passing on a GitHub runner.** Attempts 1 and 2 both passed every
  local gate and both failed remotely. A green local sweep is explicitly not evidence in this
  document. M8 stays open until the remote run is green.
- **Retries do not make the runner faster.** If the suite is over budget systematically rather than
  intermittently, three attempts fail three times — and the honest reading of that would be that the
  timeout or the environment has to change after all.
- **A green run under `retries: 2` is weaker evidence than a green run without them.** It means
  every scenario passed within three attempts, not that every scenario passed first time. The retry
  counts appear in the run output and should be quoted rather than rounded away.
- **The five generate/progress failures were never reproduced locally**, across many repeated runs.
  They are attributed to the runner on the strength of the cross-run variance table, not on a
  reproduction.
- **The runner's frame rate is still unknown.** The probe reports it in its failure message, so a
  future failure arrives with the number attached instead of requiring another guess.
- The damping trace was taken on the development machine. It establishes the decay's shape and the
  size of the signal, not the runner's frame rate — which is why sampling is per frame rather than
  per millisecond.
- The probe measures **camera state**. It says nothing about whether the decal renders correctly;
  that remains covered by the other viewer scenarios.
