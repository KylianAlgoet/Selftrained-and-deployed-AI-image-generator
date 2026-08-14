# M10 — the 20-minute restructuring

**Date:** 2026-08-14 · **Milestone:** M10 · **Decision record:** DR-017
**Supersedes:** the 26-slide deck in `build-record.md` beside this file

The authoritative presentation slot became known on 2026-08-14: **20:00 in total, including the live
demo.** The deck built earlier that day ran to 26 slides and an estimated 26.4 minutes of narration
plus a 4-minute demo. **It missed the slot by roughly 50 %.**

Everything below is the output of commands that ran in this environment on this date. The timing
figures are **estimates derived from speaker-note word counts**, and are labelled as estimates
wherever they appear. **No rehearsal has been run.**

## The finding that matters more than the deck

**Every structural check passed on a deck that did not fit.** 26 pages for 26 slides, 0 hard
validator failures, 0 advisories, 31 fact locks resolving, 29 tests green.

The checks were not wrong. **The binding constraint was absent from the repository, so nothing could
fail on it.** A validator enforces the requirements it has been told, and the one requirement that
disqualified the artifact had never been written down — it was recorded in DR-016 as an open item
and searched for twice.

This is the fourth instance of one pattern in this project, and the first where the missing check
was a *requirement* rather than a *method*:

| milestone | what passed | what it could not see |
|---|---|---|
| M8 | a dataset integrity hash | it had only ever run on its author's machine |
| M9 | a source-level report validator | a presentation-level bibliography defect |
| M10 | `git status`, showing a tracked PDF | the PDF did not match its sources |
| **M10** | **every structural deck check** | **the deck did not fit its slot** |

DR-016's `core`/`supporting` tiering was the response to *not knowing* the duration, and it was
**inadequate on its own**: only 4 of 26 slides were `supporting`, so cutting every cuttable slide
saved about 4 minutes against an overrun of about 11. **Tiering absorbs variation; it does not
absorb being wrong about the budget.**

## Commands

```
python scripts/validate_slides.py       # now includes the timing and layout-markup checks
python scripts/build_slides.py --strict
python scripts/build_report.py --strict # the deck and report share report/facts.yaml
python scripts/validate_report.py
python scripts/report_facts.py --check
python -m pytest
```

## Results

| check | result |
|---|---|
| slides authored | **15 of 15** |
| validator hard failures | **0** |
| validator advisories | **0** |
| PDF pages / slide count | **15 / 15** — the overflow test passes |
| page geometry | **960 × 540 pt = 16:9** |
| fact locks | **31 resolve** |
| pytest | **523** (489 pre-existing + 34 slide-source tests) |
| report | **91 pages**, unchanged in length |

## Timing — ESTIMATE, not a rehearsal

| | | |
|---|---:|---|
| slide narration | **14:56** | 14 non-demo slides at 130 wpm, **plus the 0:15 spoken demo handoff** |
| live demo | **4:00** | declared target, timed separately by `docs/presentation/demo-script.md` |
| **combined** | **18:56** | |
| **buffer** | **1:04** | against the 20:00 slot |

Target band was 14:30–15:00 of narration with at least 1:00 of buffer. Both are met.

**The demo is not counted as zero.** Its slide note is a set of directions rather than a script, so
the demo slide is excluded from the word-count total and its two real costs — the handoff and the
demo itself — are declared in `deck.yaml`.

### Per-slide

| # | id | tier | layout | chars | bullets | note words | est. |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | title | core | title | 117 | 0 | 33 | 0:15 |
| 2 | assignment | core | statement | 299 | 0 | 152 | 1:10 |
| 3 | method | core | figure | 232 | 0 | 154 | 1:11 |
| 4 | dataset | core | split | 364 | 4 | 125 | 0:58 |
| 5 | base-model | core | split | 326 | 4 | 178 | 1:22 |
| 6 | conditioning | core | split | 306 | 4 | 150 | 1:09 |
| 7 | lora | core | two-figures | 186 | 0 | 189 | 1:27 |
| 8 | limits | core | split | 434 | 4 | 183 | 1:24 |
| 9 | system | core | figure | 213 | 0 | 125 | 0:58 |
| 10 | testing | supporting | bullets | 380 | 4 | 122 | 0:56 |
| 11 | reproducibility | core | split | 436 | 4 | 142 | 1:06 |
| 12 | deployment | supporting | bullets | 489 | 5 | 137 | 1:03 |
| 13 | conclusions | core | statement | 420 | 0 | 122 | 0:56 |
| 14 | demo | core | demo | 262 | 0 | 250 | *excluded — directions* |
| 15 | close | core | bullets | 449 | 4 | 99 | 0:46 |

**13 core, 2 supporting. 881 s of slide narration + 15 s handoff = 896 s.**

Slides 3 and 9 carry inline SVG diagrams, which the character budget exempts because SVG cannot
reflow — it scales inside its `viewBox` rather than growing taller. Whether either diagram is
legible from the back of a room is a question only the human visual gate can answer.

## The guards were watched failing before they passed

A guard nobody has seen fail is not a guard. Both new checks were observed rejecting real drafts:

```
HARD  narration is ~1059s (17.7 min), outside the 870-900s target. Restructure the
      deck - do not plan to speak faster, and do not widen the band to fit the notes.
HARD  buffer is ~-99s against a 60s minimum. narration 1059s + demo 240s exceeds the
      1200s slot.
```

The first restructured draft was **still 3 minutes over** with a **negative** buffer. Two rounds of
note trimming brought it inside the band. The band is enforced **in both directions** — under the
minimum fails too, because it means the estimate has drifted from the design and in practice means a
note was gutted rather than deliberately cut.

## A rendering defect the budgets could not see

The `limits` slide was authored with two-column markup (`col-text` / `col-figure`) and **declared as
`bullets`**. That CSS grid is scoped to `.slide--split`, so the slide was valid HTML, passed every
character and bullet budget, produced exactly one PDF page — and **would have rendered with the
evidence figure stacked under the text instead of beside it.**

Caught by reading the per-slide table against the sources, not by any check. A `check_layout_markup`
guard now fails a build whose markup and declared layout disagree, with a test that watches it
reject the exact case. **A layout name is a promise about the markup, and it is now checked.**

## Artifacts

| file | bytes | sha256 |
|---|---:|---|
| `deliverables/DeckForge-AI-presentation.pdf` | 1 054 584 | `abaf12334813d73cd30459f8c9a16a64616794c643037d209ae5f77ca4d3a84a` |
| `deliverables/DeckForge-AI-presentation-notes.pdf` | 255 936 | `38d0c72475e5de2bd96cef02c31dd26894a5b28df311a9850c8db7d469d12bfb` |
| `deliverables/DeckForge-AI-research-report.pdf` | 2 772 732 | `4305d0bec9801d8e97ea3b469a1be935f4605342dc6e329b072512e5ddcb9710` |

Taken after the final build, with no rebuild between hashing and `git add`. **A rebuild changes every
digest** — Chrome embeds a creation timestamp (DR-015), which was tested in this milestone: three
builds of identical sources gave the same length and three different digests.

Writing DR-017 moved `decision_record_count` from 16 to 17, which added a row to the report's
Appendix B and required a report rebuild — the same self-referential cascade DR-016 caused, and the
fact lock caught it the same way.

## What this record does NOT establish

1. **That the deck fits in practice.** **No rehearsal has been run.** Every figure is an estimate at
   130 wpm — a deliberately slow chosen pace, not a measurement of how Kylian actually speaks.
2. **That 1:04 of buffer is comfortable.** It is 5 % of the slot. The estimate does not have to be
   wrong by much to consume it.
3. **That the deck reads well, or at all, on a projector.** Every check here is structural. **The
   human visual gate has still not been held.**
4. **That 15 is the right number of slides** — only that this 15 fits the budget while keeping every
   bounded claim. A rehearsal may move it again.
