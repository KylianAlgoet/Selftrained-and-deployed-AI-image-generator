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

## What this still does not prove

- **Attempt 2 has not been observed passing on a GitHub runner.** Attempt 1 passed every local gate
  and still failed remotely, so a green local sweep is explicitly not evidence here. M8 stays open
  until the remote run is green.
- **The two error-handling failures are attributed, not diagnosed.** The cascade explanation fits
  every observation but was not reproduced. If they fail again once the camera test passes, they are
  independent and need their own investigation.
- **The runner's frame rate is still unknown.** Attempt 2 reports it in the failure message
  precisely so that a third failure would arrive with the number attached instead of requiring
  another guess.
- The damping trace was taken on the development machine. It establishes the decay's shape and the
  size of the signal, not the runner's frame rate — which is why sampling is per frame rather than
  per millisecond.
- The probe measures **camera state**. It says nothing about whether the decal renders correctly;
  that remains covered by the other viewer scenarios.
