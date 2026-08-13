# M10 — presentation build record

**Date:** 2026-08-14 · **Milestone:** M10 · **Decision record:** DR-016
**Built from commit:** `685664b` · **Environment:** Windows 11 Home, PowerShell 5.1, `.venv` Python
3.11, Google Chrome (headless)

Everything below is the output of commands that ran in this environment on this date. Nothing is
recalled or estimated except the speaking time, which is labelled as an estimate wherever it appears.

## Commands

```
python scripts/validate_slides.py       # read-only, hard checks vs advisories
python scripts/build_slides.py --strict # 26/26 required; Chrome is a prerequisite (DR-016)
python scripts/report_facts.py --check  # fact locks, shared with the report
python -m pytest tests/test_slides_sources.py -q
```

## Results

| check | result |
|---|---|
| slides authored | **26 of 26** |
| validator hard failures | **0** |
| validator advisories | **0** |
| fact locks | **31 resolve against their evidence** |
| `test_slides_sources.py` | **29 passed** |
| PDF pages / slide count | **26 / 26** — the overflow test passes |
| page geometry | **960 × 540 pt = 16:9** |
| build time | **3.28 s** |

## Artifacts

| file | bytes | sha256 |
|---|---:|---|
| `deliverables/DeckForge-AI-presentation.pdf` | 1 313 731 | `42c5e8e2927f7d8bc8d4663ae599025c7535a0e35abf84efdd5f4cfbb722a6e8` |
| `deliverables/DeckForge-AI-presentation-notes.pdf` | 380 486 | `71442da253df9a0b0137328bca1c53c599ac6c0bc1e05737aa354743903d1658` |
| `deliverables/DeckForge-AI-research-report.pdf` | 2 769 385 | `73f574158d83f7452a605d57b8c40541c45b2a0693fb69d66f280e9ea2677157` |

**These digests are of the artifacts as committed** — taken after the final build, with no rebuild
between hashing and `git add`. Any later rebuild changes them; see the reproducibility note below.

Both are tracked. The intermediate HTML of each is git-ignored and rebuilt on every run. **Neither
PDF is byte-reproducible** — Chrome embeds a creation timestamp and its own version — so these
digests identify **these artifacts**, not a recipe. Reproducible in content; see DR-015 and DR-016.

## The stale-PDF finding

**The PDFs committed to the working tree before this session did not match their sources.** They were
built at 05:00:44 on 2026-08-11; `slides/templates/slides.css` and `slides/sources/13-step-300.md`
were then edited at 05:03:57–58 and the deck was never rebuilt. The difference was not cosmetic:

| | bytes |
|---|---:|
| stale PDF on disk | 1 097 724 |
| rebuilt from the same sources | 1 313 730 |

**216 006 bytes — about 20 % — of the deliverable was missing**, and nothing in the repository would
have reported it. The build writes both HTML and PDF, so the HTML timestamps (05:04:11) were *newer*
than the PDFs, which is only possible if a later run rendered HTML without producing a PDF.

**Lesson, and it is the same one M8 and M9 already produced in different clothes:** a build artifact
committed alongside its sources is only evidence if something proves the two correspond. Nothing did
here. The file's presence in `git status` looked exactly like success. This is the presentation-layer
sibling of M8's dataset hash that had only ever passed on its author's machine, and of M9's
bibliography defect that the source-level validator could not see.

## The self-referential fact lock

Writing DR-016 **broke the deck build**, and correctly:

```
BUILD FAILED: fact locks failed, so the deck cannot be trusted:
1 fact lock(s) failed:
  - decision_record_count: declared 15 but docs/decisions states 16
```

`decision_record_count` is extracted by globbing `docs/decisions/DR-*.md`, so the act of recording
the presentation pipeline changed a number the report and two slides state. `report/facts.yaml` and
the report's Appendix B were updated to 16 and the report was rebuilt.

**The rebuild moved the report from 90 to 91 pages**, which in turn invalidated the typed literal
"90-page report" on slide 26 and in the traceability matrix. Both were corrected. The report's page
count is **not** fact-locked and cannot be with the current extractors — it exists only after Chrome
paginates — so it is recorded in DR-016 as a live drift risk.

Superseded artifact, recorded so the two are never confused:

| | bytes | sha256 | pages |
|---|---:|---|---:|
| M9 report (superseded) | 2 756 980 | `5c394e7a…` | 90 |
| **current report** | 2 769 385 | `73f574158d83f7452a605d57b8c40541c45b2a0693fb69d66f280e9ea2677157` | **91** |

## An unexplained one-off in the report build — OPEN, and it is not the deck's

While rebuilding the report for the reason above, **one build produced a PDF 800 KB smaller than
every other build of the same sources, and every check passed on it.**

| build | sources | bytes | pages |
|---|---|---:|---:|
| A | after the facts/Appendix B edit | 2 767 458 | 91 |
| **B** | after two small prose edits | **1 968 295** | **91** |
| C … M | **identical to B's sources, no edit between** | 2 769 385 | 91 |

Build B is **28 % smaller than the build immediately after it, from the same sources**. It passed the
structural check (`%PDF-1.4`, `%%EOF`, non-empty) and the page-count heuristic agreed at 91.

**Reproduction attempts: 14 consecutive builds, all 2 769 385 bytes, images 6, pages 91, no object
streams. The anomaly did not recur.** Build B was overwritten before it could be examined,
so **why it was smaller is unknown** — a figure that failed to load within the virtual-time budget is
the obvious hypothesis and it is a hypothesis, not a finding.

**What this does establish, and it is the part that matters:** the report build's existing checks —
structural validity plus page count — **cannot detect the loss of 800 KB of content**. A report with
missing figures would have shipped looking exactly like a correct one. This is the same defect class
as the stale deck PDF above, one level deeper.

**No mitigation was added, deliberately.** The obvious guard is a minimum-size or embedded-image-count
floor, but the cause was observed **once** and never reproduced, and a threshold chosen from a single
observation is guesswork dressed as a check — the project's own rule is that a hoped-for result is a
diagnostic, not a pass condition. Adding one also means editing `build_report.py` under an active
feature freeze. **This is Kylian's call**, and until it is taken the risk is live.

**DR-015's non-reproducibility claim was tested here, and it holds.** Three consecutive builds of
identical sources produced **the same length and three different SHA-256 digests**:

```
2769385  0a56eff53aed0422be7e4375c1f2387df2119fb4fe7a64b4297b3d0f0a4059ee
2769385  c1b11dfae0aedb1a21e9a0bd12aac93788380fdc85384fe9baf6ccd98b7fa43c
2769385  73f574158d83f7452a605d57b8c40541c45b2a0693fb69d66f280e9ea2677157
```

Consistent with Chrome embedding a creation timestamp: the *content* is stable, the bytes are not.

**This corrects a wrong inference made earlier in this same session.** The builds were first recorded
as "byte-identical" on the strength of their **matching sizes alone**, without hashing any of them.
Equal length is not equal content, and the digests above are what settled it. Worth stating plainly
because it is the identical mistake the project keeps meeting from the other direction — treating a
check that *passed* as evidence for a claim it never tested.

## Per-slide measurements

`chars` is visible body text after the budget exemptions (captions, evidence pointers, inline SVG —
see DR-016). `note words` is the speaker note's word count; `est. s` is that count at 130 wpm.

| # | id | tier | layout | chars | bullets | note words | est. s |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | title | core | title | 117 | 0 | 119 | 55 |
| 2 | assignment | core | bullets | 390 | 4 | 121 | 56 |
| 3 | research-question | core | statement | 241 | 0 | 110 | 51 |
| 4 | constraint | core | statement | 148 | 0 | 125 | 58 |
| 5 | method | core | bullets | 488 | 5 | 138 | 64 |
| 6 | ladder | core | figure | 0 | 0 | 136 | 63 |
| 7 | dataset | core | split | 257 | 4 | 118 | 54 |
| 8 | licensing | core | bullets | 504 | 5 | 131 | 60 |
| 9 | base-model | core | split | 355 | 4 | 141 | 65 |
| 10 | memory-habit | supporting | statement | 133 | 0 | 137 | 63 |
| 11 | conditioning | core | split | 324 | 4 | 125 | 58 |
| 12 | why-lora | core | bullets | 455 | 5 | 132 | 61 |
| 13 | step-300 | core | two-figures | 173 | 0 | 146 | 67 |
| 14 | adapters | supporting | table | 307 | 0 | 121 | 56 |
| 15 | retro-poster | core | split | 272 | 3 | 139 | 64 |
| 16 | rq4 | core | bullets | 334 | 4 | 148 | 68 |
| 17 | other-failures | supporting | bullets | 598 | 5 | 160 | 74 |
| 18 | architecture | core | figure | 0 | 0 | 135 | 62 |
| 19 | mvp | core | split | 362 | 4 | 156 | 72 |
| 20 | texture-fit | supporting | two-figures | 164 | 0 | 138 | 64 |
| 21 | testing | core | bullets | 431 | 5 | 158 | 73 |
| 22 | determinism | core | split | 434 | 4 | 152 | 70 |
| 23 | deployment | core | bullets | 563 | 5 | 150 | 69 |
| 24 | conclusions | core | bullets | 510 | 0 | 144 | 66 |
| 25 | demo | core | demo | 262 | 0 | 246 | 114 |
| 26 | close | core | bullets | 549 | 5 | 159 | 73 |

**22 core, 4 supporting. 3 685 note words in total.**

Slides 6 and 18 show 0 visible characters because both are inline SVG diagrams, which the budget
exempts on the grounds that SVG cannot reflow — it scales inside its `viewBox` rather than growing
taller. Whether either is legible from the back of a room is a question only the human visual gate
can answer.

## Timing — an ESTIMATE, not a rehearsal

**1 586 seconds = 26.4 minutes of slides**, excluding the demo, plus a **4-minute demo target**:
roughly **30 minutes**.

Its method: total speaker-note word count ÷ 130 wpm. 130 is a deliberately slow defence pace. The
demo slide's 246-word note is excluded from the slide total because it is a set of directions rather
than a script, and the demo is budgeted separately.

**No rehearsal has been run**, so no measured delivery time exists. A word-count estimate is not a
rehearsal time and is never reported as one. The estimate also cannot know pauses, questions, or the
demo running long.

## Two things this record does NOT establish

1. **That the deck is the right length.** **No authoritative presentation duration is recorded
   anywhere in this repository** — searched 2026-08-11 and re-checked 2026-08-14 across the project
   brief, the planning, the governing prompt and the report sources. The slide count is
   **provisional** until Kylian supplies the real duration. The `core`/`supporting` tiering is the
   response, but it only makes 4 of 26 slides cuttable, so it absorbs a modest overrun and not a
   large one.
2. **That the deck reads well, or at all, on a projector.** Every check above is structural. The
   budgets are a crude proxy for overflow, the page-count equality proves only that nothing spilled
   onto a second page, and the `/MediaBox` regex proves only the page shape. **Nothing here is a
   judgement about legibility, design, or whether the argument survives compression onto a slide.**
   That requires a human opening the PDF, and it has not happened yet.
