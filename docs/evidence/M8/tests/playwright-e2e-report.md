# Playwright E2E — the suite M7 did not have

**Date:** 2026-08-09 · **Milestone:** M8 (phase M8.3) · **Result: 37 passed, 0 failed.**
**Runner:** `@playwright/test` 1.62.1, Chromium 151.0.7922.34, headless, one worker.
**Command:** `cd apps/web && npx playwright test`
**Runtime:** ~1.1 minutes, including a full production build.

M7 closed with the E2E layer explicitly outstanding: its end-to-end evidence was a real uvicorn
process driven by `scripts/validate_p5_api.py` plus manual browser checks, and the testing strategy
said so rather than claiming a suite existed. This closes that gap.

## Architecture

| decision | why |
|---|---|
| Runs against `npm run build && npm run preview` | The bundle that ships is the thing tested — production minification, real `import.meta.env`, real asset pipeline. A dev-server suite can pass while the built application is broken. |
| `/api/**` mocked at the network boundary | React, R3F, the WebGL canvas, the texture pipeline, the polling loop and the download paths all run for real. The mock sits exactly at the HTTP contract. |
| Fixtures are **JSON**, validated by pytest | `apps/api/tests/test_e2e_fixture_contract.py` (20 tests) validates every fixture against the real Pydantic models. Without it, a renamed backend field would leave this suite passing against a shape the server no longer sends. |
| Chromium only | Cross-browser rendering is not an M8 criterion; three browsers would cost ~900 MB to answer a question nobody asked. |
| No GPU, no model, no weights, no network | The suite passes on a machine that has never downloaded a checkpoint — which is what makes CI possible and what lets this criterion be met without spending generation budget. |

The browser binaries live in `C:\Users\kylia\AppData\Local\ms-playwright\`, outside the repository.
Reports, traces and screenshots are git-ignored.

## Results by file

| file | tests | covers |
|---|---:|---|
| `app.spec.ts` | 6 | shell, WebGL context, **production/review separation**, DR-012 disclosure, offline banner |
| `generate.spec.ts` | 8 | styles list, bounded settings, reference attach/remove, **multipart request body**, result, downloads, deck application, partial-pass warning |
| `progress.spec.ts` | 7 | waiting state, polling cadence, **real step counts**, estimate timing, **no percentage without a denominator**, finalising, telemetry loss |
| `decal-upload.spec.ts` | 6 | upload without `POST /api/generate`, no false metadata, decode failure preserves the decal, preflight, restore, **camera survives a texture swap** |
| `errors.spec.ts` | 6 | 409 busy, 504 with step counts, 503 with no path leak, 422 field binding, network abort, recoverable state |
| `viewport.spec.ts` | 3 | 1440×900 demo viewport, 390×844 narrow, result panel overflow |
| **total** | **37** | |

## The assertions that carry the most weight

1. **Review tools are absent from production.** Two controls behind DR-012 must stay in the codebase
   and never appear in the interface. `?review=1` restores them; the default build does not show
   them. "Hidden from production" decays silently unless something checks it.
2. **No percentage exists without a denominator.** With a cold-load fixture the panel shows a stage
   name, the words *"No step percentage at this stage"*, no `%` anywhere, and `aria-valuenow`
   unset. This is DR-013's rule, and the failure it guards against is not a crash — a fake
   percentage works perfectly and looks better.
3. **The fixtures cannot lie about it either.** A pytest asserts no fixture publishes
   `estimated_remaining_seconds` outside `denoising`. Otherwise assertion 2 could pass because the
   interface ignored data it should never have been handed.
4. **Uploading a decal issues no generation request.** Proven from a request log, not from
   behaviour that looks right. This is also the demo's live fallback if CUDA fails on stage.
5. **The multipart body is inspected directly.** A form that renders correctly but posts the wrong
   field names gives a 422 in production and a green suite otherwise.
6. **503 leaks no path.** The page body is searched for `outputs/lora`, `C:\` and `.safetensors`.

## Four defects found — all in the tests, none in the application

Every failure in the first run was a wrong assertion. **The application needed no change**, which
is the result worth recording rather than a silent green tick.

| # | first-run failure | cause | fix |
|---:|---|---|---|
| 1 | `getByLabel('Style')` matched 2 elements | "Style" also prefixes "Style strength" | `{ exact: true }` |
| 2 | expected `1.3008×` in the result panel | `fitDisclosure` rounds to 3 decimals → `1.301×`; only the static viewer note quotes `1.3008×` | assert what the component renders |
| 3 | expected "Ukiyo-e woodblock" in the progress panel | the form defaults to the **first** style; the test never selected one | select the style, then assert it |
| 4 | `Finalising…` matched 2 elements | the same sentence is also in the visually-hidden aria-live region | scope to `.progress-stage` |

### One assertion was deliberately removed rather than made to pass

The `DECAL GENERATED` headline renders only while the decoded PNG is being composed onto the deck —
about a second — and the panel unmounts as soon as that finishes. Asserting it is a race against
the application being fast.

**The fix was not to make the state linger.** M7 recorded that explicitly: padding a finished
result so a label can be read is the dishonesty the progress feature exists to avoid, and accepted
limitation 3 states the stage may be visible only briefly. The test asserts the durable outcome
instead — the result panel appears and the progress panel is gone — and a comment in the test
records why the obvious assertion is absent, so it does not read as an oversight.

## Scenario 19 from the plan: camera state

The plan flagged this as the one scenario that might not be automatable, and said it would be
reported as such rather than replaced by a weaker assertion that looked equivalent.

**It was automatable.** Reading the camera matrix out of the React tree proved unnecessary: the
test orbits the deck, screenshots the canvas, swaps the texture, and asserts the frame changed —
then presses **Reset view** and asserts the frame changed *again*. That second assertion is the
load-bearing one, because a reset that visibly moves the deck proves the deck was not already in
its default pose, which is what a texture swap resetting the camera would have caused.

## Stability

Run twice end to end; **37 passed both times, no flakes.** `retries: 0` deliberately — a suite that
retries hides exactly the timing bugs a browser suite is for.

## A dependency finding, recorded not fixed

`npm audit` reports **3 high-severity advisories**: `brace-expansion` (via `@typescript-eslint`),
`js-yaml` (via `eslint`) and `nanoid` (via `vite`/`postcss`). All three are **DoS issues in
dev-only build tooling**, and none reaches the shipped bundle.

**They are pre-existing, not introduced by Playwright.** Verified rather than assumed: the
`package-lock.json` diff is purely additive — four entries, all Playwright — and all three packages
were already present in the lockfile at `a355ffa`.

**Not fixed in M8, deliberately.** `npm audit fix` would move `vite`, `eslint` and
`typescript-eslint`, which the entire validated frontend and its 169 vitest tests rest on, during a
hardening milestone whose whole point is not to move things. This is Kylian's call and is listed as
an open decision.

## New dependencies

| package | scope | note |
|---|---|---|
| `@playwright/test` 1.62.1 | `apps/web` devDependency | pulls `playwright`, `playwright-core` |
| `@types/node` 26.2.0 | `apps/web` devDependency | needed by `tsconfig.e2e.json`; pulls `undici-types` |

Dry-run before each install confirmed **no production dependency moved**. The protected Python
stack was never touched.

## Suite totals after M8.3

| suite | M7 close | now |
|---|---:|---:|
| pytest | 406 | **461** |
| vitest | 165 | **169** |
| Playwright E2E | **0 (did not exist)** | **37** |
| eslint | clean | clean |
| build | succeeds | succeeds |

## What this suite does NOT prove

It never loads the model, so it says nothing about generation quality, VRAM, latency or adapter
integrity. Those are evidenced on the GPU by `scripts/validate_p5_api.py` (Phases A/B/C), EXP-034
and EXP-035, and by the clean-clone real-output run. **A mocked E2E suite proves the application
works against the contract — not that the contract is fulfilled by a real model.** Both kinds of
evidence exist for this project and neither is presented as the other.
