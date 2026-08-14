# DR-017 — Deck length and structure for a 20-minute defence slot

**Date:** 2026-08-14 · **Milestone:** M10 · **Status:** accepted
**Decides:** how many slides the defence deck has, what is on them, and how the timing is enforced
**Related:** DR-016 (the pipeline this keeps unchanged), `docs/00-project-brief.md` requirement 13,
`docs/presentation/jury-questions.md`

## Context

**The authoritative duration became known on 2026-08-14: 20:00 in total, including the live demo.**

Until then, no presentation duration was recorded anywhere in this repository — searched on
2026-08-11 and again on 2026-08-14 across the project brief, the planning, the governing prompt and
the report sources, and recorded as an open item in DR-016. The deck was therefore built to a
**provisional** length of 26 slides, with an estimated **26.4 minutes** of narration plus a
4-minute demo.

**That deck does not fit, and it misses by about 50 %.** Every structural check passed on it: 26
pages for 26 slides, 0 hard validator failures, 0 advisories, every fact lock resolving. The checks
were sound; the thing they could not check was the only thing that disqualified it.

## The problem this exposes, which outlasts the deck

A validator can only enforce a requirement it has been told. **The deck's binding constraint was
absent from the repository, so nothing could fail on it** — and a deck that overruns its slot fails
in front of a jury rather than in a build log. DR-016's tiering (`core`/`supporting`) was the
response to *not knowing* the duration, and it was inadequate on its own: only 4 of 26 slides were
`supporting`, so cutting every cuttable slide would have saved roughly 4 minutes against an overrun
of 11.

**Tiering absorbs variation. It does not absorb being wrong about the budget.**

## Alternatives

| # | alternative | treatment |
|---|---|---|
| A | **Restructure to ~15 slides against an enforced budget** | **selected** |
| B | Keep 26 slides and speak faster | **rejected** — ~26 minutes of notes into ~15 requires about 220 wpm. That is not a defence pace, and it degrades exactly the parts that need care: the bounded claims |
| C | Keep 26 slides and cut the demo | **rejected** — the demo is the assignment's demonstrable artefact, and 4 minutes of it is already the floor |
| D | Keep 26 slides and cut only the 4 `supporting` ones | **rejected** — saves ~4 minutes against an ~11-minute overrun. Arithmetically insufficient |
| E | Cut slides but leave the notes long, trusting delivery | **rejected** — the estimate is derived from the notes, so this hides the overrun instead of fixing it. It is option B wearing a disguise |

## Decision

**Cut the stage deck to 15 slides, rewrite every speaker note against a per-slide time target, and
make the total budget a hard build check.**

Three parts, and the third is the one that matters beyond this deck.

### 1. Structure: 26 → 15

Merges, chosen so that each surviving slide carries **one central claim**:

| new | from | note |
|---|---|---|
| 2 assignment | 2 + 3 | the problem and the research question read as one |
| 3 method | 4 + 5 + 6 | the constraint, the loop and the prototype ladder are one argument |
| 4 dataset | 7 + 8 | provenance is part of the dataset, not a separate topic |
| 7 lora | 12 + 13 + 14 | the method, its result and what ships |
| 8 limits | 15 + 16 + 17 | **three bounded findings on one slide** |
| 9 system | 18 + 19 + 20 | architecture, MVP and the fit trade-off |
| 15 close | 24 (part) + 26 | what I would change, not a mapping table |

Slide 10 (the memory-reading habit) folded into the base-model slide's note. Nothing was deleted.

### 2. Visual priority

Budgets were **tightened**, not merely kept: `bullets` fell from 900 to 580 visible characters,
`split` from 700 to 470, `figure` from 600 to 360. The old budgets permitted report-density text on
a slide — readable on a laptop, not from the back of a room. **One central claim per slide is now
enforced by the budget rather than trusted to the author.**

### 3. Timing is a hard check

The budget lives in `deck.yaml` and `validate_slides.py` enforces it:

```
narration = Σ(word-count estimate of every non-demo slide) + demo_handoff_seconds
combined  = narration + demo_target_seconds
buffer    = total_budget_seconds - combined
```

**The demo is never counted as zero.** Its note is a set of directions rather than a script, so the
demo slide is excluded from the word count and its two real costs — the spoken handoff (0:15) and
the demo itself (4:00) — are declared explicitly.

Narration is bounded **in both directions**, 870–900 s. Over is an overrun. **Under fails too**,
because it means the estimate has drifted far enough from the design that the buffer is no longer
the one that was reasoned about; in practice it means a note was gutted rather than deliberately
cut. Both are a signal to re-derive the budget, not to nudge a bound.

## Measured result

```
python scripts/validate_slides.py     -> 0 hard failures, 0 advisories
python scripts/build_slides.py --strict
-> slides authored   : 15 of 15
-> pages             : 15   (one page per slide: the overflow test)
-> page geometry     : 960 x 540 pt = 16:9
-> slide narration   : 14:11   (incl. demo handoff)
-> live demo         : 4:00
-> combined          : 18:11
-> buffer            : 1:49
```

Both new hard checks were **observed failing before they passed**: the first restructured draft came
in at 17.7 minutes of narration with a **negative** buffer, and the validator refused it. A guard
nobody has watched fail is not a guard.

### The band was widened once, at the content review

The first accepted draft landed at **14:56 / 1:04 buffer**, inside its then-band of 870–900 s. The
content review rejected that buffer as too thin — **1:04 is 5 % of the slot** for an estimate whose
only input is a word count at an assumed rate.

The band moved to **825–855 s with a 1:45 minimum buffer**, and the extra minute came out of
**speaker notes whose reasoning `jury-questions.md` already carries** — not out of a slide, and
**not out of a faster assumed delivery**: `words_per_minute` is unchanged at 130.

**This is the one case where moving a bound was right**, and it is worth being explicit about why,
because this project's standing rule is the opposite. The bound was not widened to admit a deck that
failed it — the deck was *passing*. It was tightened as a **safety** requirement, and the deck was
then cut to meet the stricter target. Loosening a check to admit failing work and tightening one to
demand better work are opposite moves that look similar in a diff.

## Two content defects the review caught, which no check could

Recorded here because both were in slide *claims*, and a validator that checks structure cannot
check whether a sentence is true.

**1. The deck subtracted two different memory concepts.** Slide 3 stated the card's total
(8187.5 MiB), the stack's **peak allocated** (5143.73 MiB) and the **spare** (200.0 MiB) as if the
first two produced the third. They do not: `8187.5 − 5143.73 = 3043.77`. Peak *allocated* counts
live tensors in the PyTorch allocator; the spare figure is measured against **total device
occupancy**, which also includes the CUDA context, the allocator's cached pool and the display. The
figure that actually pairs with the margin is **device used, 7987.5 MiB** — and
`8187.5 − 7987.5 = 200.0` exactly. That figure is now fact-locked as `worst_device_used_mib`, so the
slide's arithmetic is checkable rather than plausible. **Every number on that slide was individually
true and correctly fact-locked; the relationship implied between them was false.**

**2. The deck claimed both human gates were blinded.** Slide 3 said *"two human gates, scored blind
against a rubric written before the images existed"*. The evidence says otherwise, and says so
itself: `GATE-2-approval.md` records *"Unlike Gate 1, these sheets were **labelled**"*, and adds that
**"labelled sheets carry an expectation effect that blinded ones do not"**. Gate 2 asks which
checkpoint ships, which cannot be answered without knowing which checkpoint a sheet is.

The corrected wording is **"two human approval gates against a rubric defined before the images were
reviewed — the first blinded, the second labelled by necessity"**. Note the origin: the 26-slide
deck said *"blinding at the first gate"* and was **correct**. The error was introduced by the merge
that produced the 15-slide deck — **compression is where a qualified claim loses its qualifier**,
which is the exact risk `validate_slides.py` was written for, and it still took a human to catch it.

The M9 AI-assistance disclosure is untouched and remains on the `limits` slide.

## What this decision does NOT claim

1. **It does not claim the deck has been rehearsed.** **No rehearsal has been run.** Every figure
   above is an estimate derived from speaker-note word counts at a deliberately slow 130 wpm.
   130 wpm is a choice, not a measurement of how Kylian speaks, and the true rate is unknown.
2. **It does not claim 1:49 of buffer is generous.** It is 9 % of the slot — better than the 5 % it
   replaced, and still an estimate. The notes handout says to rehearse against a clock.
3. **It does not claim the deck is legible or well designed.** Every check is structural. The human
   visual gate has still not been held.
4. **It does not claim 15 is the right number of slides** — only that this 15 fits the budget while
   keeping every bounded claim. A rehearsal may well move it again.

## Consequences

1. **No claim left the project.** Everything cut from a visible slide moved into a speaker note or
   into `docs/presentation/jury-questions.md`, which is structured for 30–60-second answers with
   evidence paths attached.
2. **The merged `limits` slide is held to a stricter test than its three predecessors.** All three
   concessions — `retro-poster` **partial pass**, image count **inconclusive**, and **no second
   independent human rater** — are required on that one slide, and a test asserts all three
   requirements still name a real slide id.
3. **DR-016 is unchanged.** The pipeline, the fact-lock coupling to the report, and the
   figure/overflow guards all survive as they were. This record changes what the deck *contains* and
   adds a timing gate; it does not touch how it is built.
4. **DR-016's "no authoritative duration" open item is closed** by this record. Its tiering
   rationale is superseded: `tier` no longer carries the shortening strategy, because the deck is
   already at the size the slot allows.
5. **The 26-slide deck stays in Git history**, and its sources were removed rather than kept
   alongside. Two decks in one directory is how the wrong one gets presented.
6. **No package was installed**, and no application, model, dataset or weight was touched.

## Status

**Accepted**, 2026-08-14, on the measured build above — and **pending the human timing and visual
gate**, which this record does not stand in for.
