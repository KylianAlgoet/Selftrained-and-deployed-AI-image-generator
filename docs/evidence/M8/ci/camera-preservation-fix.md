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

## Local validation, 2026-08-10

All run on the validated machine, against the built bundle.

| gate | command | result |
|---|---|---|
| camera test, repeated | `npx playwright test -g "replacing the decal..." --repeat-each=5` | **5 passed** (52.1 s total incl. build) |
| full E2E suite | `npx playwright test` | **38 passed** (1.2 m) |
| unit tests | `npm run test` | **181 passed**, 12 files |
| lint | `npm run lint` | clean |
| E2E typecheck | `npm run typecheck:e2e` | clean |
| production build | `npm run build` | succeeds |
| handle gate | `npm run verify:no-e2e-handle` | ok |
| backend | `.venv/Scripts/python.exe -m pytest` | **473 passed** |

**No GPU inference was run.** The generation total remains **27**.

## What this still does not prove

- **It has not been observed passing on a GitHub runner yet.** That is the whole point of the fix
  and the reason M8 stays open until the remote run is green. Nothing here may be reported as CI
  evidence before then.
- The damping trace was taken on the development machine. It establishes the decay's shape and the
  size of the signal, not the runner's frame rate — which is why sampling is per frame rather than
  per millisecond.
- The probe measures **camera state**. It says nothing about whether the decal renders correctly;
  that remains covered by the other viewer scenarios.
