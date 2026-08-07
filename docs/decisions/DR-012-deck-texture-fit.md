# DR-012 — Production texture-fit mode for the deck preview

**Status:** accepted · **Date:** 2026-08-07 · **Milestone:** M7 (Prototype 5)
**Re-confirmed** at the final visual gate on 2026-08-07 with the mode running in the
production interface (`docs/evidence/prototype-5/FINAL-GATE-approval.md`).
**Answers:** how a 1:3 generated decal is mapped onto a 1:3.902 deck surface by default.
**Related:** DR-005 (deck geometry), DR-007 (512×1536 generation format), DR-011 (service
architecture, which left exactly this item open)
**Evidence:** `docs/evidence/prototype-5/GATE-approval.md`, `docs/evidence/prototype-5/screenshots/`,
`apps/web/src/deck/textureFit.ts`

## Context

The two formats were fixed by earlier decisions and do not agree.

- **Generation format:** 512×1536, exactly **1:3**. Selected in DR-007 after EXP-005, and it is
  the geometry every memory measurement from M5 onward was taken at. Changing it invalidates
  those measurements.
- **Deck UV domain:** `DECK_LENGTH / DECK_WIDTH = 3.2 / 0.82 = ` **1:3.9024…**, a property of the
  Prototype-0 deck asset.

`3.9024 / 3 = 1.3008`. The mismatch is unavoidable at the mapping stage; it can only be paid for
in stretch or in coverage. It stayed invisible until M7 because **Prototype 0's bundled decals are
512×2000 (1:3.906)** — they happened to match the deck, so no generated artwork had ever reached it.

## Alternatives

| # | option | measured cost |
|---|---|---|
| **A** | **`full-surface`** — artwork covers the whole UV domain | stretched **1.3008×** lengthwise; **0 %** bare |
| B | `fit-without-stretch` — artwork composed centred on a deck-shaped canvas | no stretch; **23.12 %** of deck length bare (**11.56 % per end**, `#242424`) |
| C | regenerate at 512×1998 to match the deck | rejected before implementation: changes the generation geometry fixed in DR-007, invalidates the memory figures from EXP-016 onward, and the LoRAs were trained at the 1:3 format |
| D | change the deck geometry to 1:3 | rejected before implementation: the deck is a self-created project asset whose proportions come from a real skateboard; distorting the *board* to suit the image inverts the problem |

C and D were **screened, not measured** — both change an input that earlier milestones' evidence
depends on, which is why the trade-off was posed as A vs. B.

## Criteria

Selection was **visual and human**, deliberately: nothing measurable distinguishes A from B — the
numbers above are the trade-off itself, not a score. The criterion was which result reads as a
finished skateboard deck.

## Decision

**Option A, `full-surface`, is the production default.** Selected by Kylian Algoet at the M7
review gate on **2026-08-07**, in his own words:

> "In the live comparison, fit-without-stretch left large black areas at the nose and tail, making
> the deck look unfinished and the artwork look like a centred rectangular sticker. Full-surface
> produced a coherent full-deck graphic. The measured 1.3008x lengthwise stretch was acceptable
> and not visually objectionable for the selected production styles."

Implemented as `DEFAULT_TEXTURE_FIT_MODE` in `apps/web/src/deck/textureFit.ts`.

## Consequences

- **The stretch is disclosed, never hidden.** `fitDisclosure` prints "Stretched 1.301× along the
  deck to cover the whole surface" beside every result, and a test asserts the default mode
  produces a disclosure containing it.
- **`fit-without-stretch` is not removed.** It stays selectable and tested; a test asserts both
  modes remain and that the default is one of them.
- The 1.3008× figure applies to a 1:3 source. Any future change to the generation geometry
  changes the stretch, and `describeFit` derives it from the geometry constants rather than
  hard-coding it.
- **Scope of the justification:** it is stated for *the three selected production styles*
  (`minimal-geometric`, `ukiyo-e`, `retro-poster`) at 512×1536. It is not a general claim that a
  1.3× stretch is imperceptible.
- **A caveat that belongs to neither mode and did not decide it:** the Prototype-0 UV convention
  already compresses the texture horizontally toward the tapered nose and tail, because `u` is
  normalised across the profiled half-width. That is pre-existing geometry and applies to both
  modes equally.

## Limitations

- **One reviewer, one decal.** The comparison used a single generated image
  (`P5__ukiyo-e__ref__seed42.png`) at a fixed camera, judged by one person. That is the honest
  scope of the evidence; it was not a scored rubric or a multi-observer comparison.
- The GPU budget for M7 was **exhausted at 25 of 25 generations before this gate**, which is why
  the comparison reused an existing decal loaded from disk rather than generating fresh artwork
  per mode. Same image, same camera, one variable — but not a fresh sample.
