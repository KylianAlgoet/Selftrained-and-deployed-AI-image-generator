# Prototype 5 — M7 review gate approval record

**Milestone:** M7 (Prototype 5 — integrated MVP) · **Gate:** 1 of 2 · **M7 was not closed here**

> **SUPERSEDED for milestone status 2026-08-07:** the final visual gate passed and M7 is now
> closed locally. See `FINAL-GATE-approval.md`. Everything below remains accurate as the
> record of the texture-fit decision.
**Final human approver:** Kylian Algoet · **Date:** 2026-08-07

## 1. What the gate asked

One decision, posed in `GATE-handover.md` §1: **which texture-fit mode becomes the production
default.** Nothing else was left open, and nothing in the code picked one — a test asserted that
no default was exported.

## 2. What was returned

**Option A — `full-surface`.** Rationale, in Kylian's own words:

> "In the live comparison, fit-without-stretch left large black areas at the nose and tail, making
> the deck look unfinished and the artwork look like a centred rectangular sticker. Full-surface
> produced a coherent full-deck graphic. The measured 1.3008x lengthwise stretch was acceptable
> and not visually objectionable for the selected production styles."

Recorded as **DR-012**.

## 3. Review material

| item | path |
|---|---|
| handover | `docs/evidence/prototype-5/GATE-handover.md` |
| mode A screenshot | `docs/evidence/prototype-5/screenshots/fit-full-surface.jpg` |
| mode B screenshot | `docs/evidence/prototype-5/screenshots/fit-without-stretch.jpg` |
| orientation control | `docs/evidence/prototype-5/screenshots/orientation-reference.jpg` |

Both screenshots use the **same decal** (`P5__ukiyo-e__ref__seed42.png`) and the **same camera**;
only the mode differs. **No new generation was run for the gate** — the GPU budget was exhausted
at 25 of 25 before it opened.

## 4. What this approval does NOT cover

- **M7 is not complete.** Asked directly whether the milestone could be declared complete, Kylian
  answered **"Not yet — I'll walk the checklist"**. The 12-item manual acceptance checklist in
  `GATE-handover.md` §12 is **unwalked**, and no claim is made here about the items in it.
- **Nothing was pushed**, the GitHub issue and project board were not touched, and M8 has not
  begun.
- **No 26th generation was run.**
- No visual-quality claim beyond the quoted rationale is made, and it is scoped to the three
  selected production styles at 512×1536.

## 5. What was implemented against this approval

| change | file |
|---|---|
| `DEFAULT_TEXTURE_FIT_MODE = 'full-surface'` | `apps/web/src/deck/textureFit.ts` |
| the app's initial fit mode reads the exported default | `apps/web/src/App.tsx` |
| the fit selector is no longer badged as a review-only control | `apps/web/src/App.tsx` |
| the "no default is exported" test is replaced by five tests asserting the chosen default, that both modes survive, and that the stretch is disclosed | `apps/web/src/deck/textureFit.test.ts` |

**Validation run after the change** (2026-08-07):

| gate | result |
|---|---|
| `.venv/Scripts/python.exe -m pytest` | **371 passed**, exit 0 — unchanged by this edit |
| `npm run test -- --run` (vitest) | **70 passed** (was 66: five added, one removed) |
| `npm run lint` (eslint) | clean |
| `npm run build` | succeeds |

**No Python linter is installed**; pytest remains the Python validation gate.
