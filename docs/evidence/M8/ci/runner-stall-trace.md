# What the runner is actually doing during a stall

**Date:** 2026-08-10 · **Milestone:** M8 · **Source:** the `playwright-report` artifact from
**CI run #7** (`b09035a`), 1 190 234 bytes, downloaded from GitHub Actions and expanded outside the
repository. **Related:** [`camera-preservation-fix.md`](camera-preservation-fix.md)

## Why this was taken

Three CI runs had failed with different subsets of scenarios, and the working explanation was "the
runner stalls". That was an inference from timing tables, not a measurement. Before changing any
test budget, the trace of an actual failure was read.

The subject is `generate.spec.ts:121 a completed generation shows the image, the duration and the
metadata`, retry #2 — the attempt that failed last, in a test that failed all three attempts.

## The action timeline

From `test.trace` inside the retry-2 trace archive:

```
   0.36s  Navigate to "/"
  21.58s  Fill "a mountain and a rising sun"   getByLabel('Describe the artwork')
  37.15s  Click                                getByRole('button', { name: 'Generate decal' })
  14.03s  Expect "toBeVisible"                 ERROR
   0.00s  Fulfill request
  12.78s  Fulfill request
  60.02s  After Hooks                          ERROR
  47.23s  Fixture "context"                    ERROR
```

**`fill` took 21.58 s and `click` took 37.15 s.** These are a keystroke into a textbox and a click on
a button — no WebGL, no network, no application logic worth the name. Together with the navigation
they consumed **59.1 s of the 60 s budget before the assertion under test even began**.

A Node-side `Fulfill request` — the mock answering from a frozen fixture, entirely inside the test
process — took **12.78 s**.

## The network timeline

From `0-trace.network`:

| started | duration | request |
|---|---:|---|
| 01:31:13.503 | 17.2 ms | `GET /` |
| 01:31:13.529 | 111.6 ms | `GET /assets/index-DCQMOnWs.js` |
| 01:31:13.530 | 26.3 ms | `GET /assets/index-DGRcUfrj.css` |
| 01:31:13.827 | 76.7 ms | `GET /api/styles` |
| **01:32:12.393** | **2391.7 ms** | `POST /api/generate` |
| 01:32:12.482 | 105.1 ms | `GET /api/generation-progress` |
| 01:32:13.397 | never completed | `GET /api/generation-progress` |
| 01:32:14.960 | never completed | `GET /api/generated/e2e_fixture_generation` |

The page finished loading at **01:31:13.6** and the generate POST was not sent until **01:32:12.4** —
a **59 second gap** containing nothing but a `fill` and a `click`.

The POST itself took **2391.7 ms against a 300 ms mock delay**. The image request that the result
region waits on was issued at 01:32:14.96 and was still being fulfilled when the test was torn down,
which is exactly the 12.78 s `Fulfill request` above.

## What this rules in and out

**Ruled out.** The application is not at fault: it never received a response to act on. The
assertion is not wrong — `getByRole('region', { name: 'Generation result' })` is the same locator
that passes in three neighbouring scenarios in the same run. The mock is not misconfigured; it is
the same `generateDelayMs: 300` used by those neighbours. None of the camera or E2E-probe work is
involved — this test does not touch the viewer beyond loading the page.

The DOM snapshot in `error-context.md` agrees: at the moment of failure the button reads
`Generating…` and the panel is still on the **first** progress stage, `Loading the trained style…`.
The UI was correct about its own state. It had not been told anything else yet.

**Ruled in.** The Playwright-to-Chromium control channel, and the runner underneath it, stall for
tens of seconds at a time. Every measurement above is of infrastructure, not of DeckForge AI.

## A hypothesis about the mechanism — NOT measured

Every scenario in this suite loads the application, and the application mounts an R3F canvas that
renders continuously (`frameloop` is R3F's default `always`). On a runner with no GPU that is
software rasterisation through SwiftShader, running for the whole life of every test, including the
many that never look at the canvas. On a two-core shared runner that is a plausible way to starve
the browser's main thread and with it the CDP channel.

**This is a hypothesis. No CPU measurement was taken on the runner, and none is available from the
artifact.** It is recorded because it fits, not because it was proven, and it must not be reported
as a finding.

## What it means for the test budget

The numbers set the floor, rather than being guessed at:

- A `fill` and a `click` cost **59 s** here. A 60 s per-test timeout cannot survive that, whatever
  the assertions do.
- A single mocked response took **12.78 s** to fulfil. A 10 s `expect` timeout cannot survive that
  either, and the result region genuinely could not have appeared before the image arrived.

So the observed failure would very likely have passed under a larger budget: the work was
progressing, just far slower than the budget allowed. That is a different situation from a test
that is wrong.

## The decision taken on this evidence

Approved by Kylian on 2026-08-10, after the trace above and with the alternatives stated:

**CI budgets become `timeout: 180 s` and `expect.timeout: 45 s`; local stays 60 s / 10 s.**
Both CI numbers are floors read off the measurements — 60 s cannot survive a 59.1 s fill-and-click,
10 s cannot survive a 12.78 s fulfilment. The `e2e` job's wall-clock guard moves 45 → 60 minutes,
because a job killed halfway produces nothing to act on and wastes more runner minutes than a
generous guard does.

Local values are deliberately untouched. The whole suite runs in ~1.2 minutes on the validated
machine, and a scenario needing more than 60 s here has found something worth reading; a CI-sized
local budget would remove the suite's only performance signal.

**This is an accommodation, not a fix, and must not be reported as one.** The stall is real and its
cause is unproven. Raising a budget lets a slow environment finish; it does not make the environment
better, and it does mean the suite can no longer detect a genuine performance regression on CI.

Rejected alternatives, with reasons: lifting only `expect` would probably not have saved this run,
since 59.1 s was gone before the first assertion; making the R3F canvas render on demand in E2E
builds attacks the *suspected* cause but changes rendering behaviour under test, needs its own
decision record under the freeze, and rests on a hypothesis this document explicitly refuses to
treat as a finding.

## Honest limits of this evidence

- **One trace, one attempt, one run.** The stall's shape is measured; its frequency and its cause are
  not.
- The 12.78 s fulfilment and the 59 s gap are **symptoms observed together**, not shown to have one
  cause.
- Nothing here says the suite would be green under a larger budget. It says this failure is
  environmental and not a defect in the application or the test.
