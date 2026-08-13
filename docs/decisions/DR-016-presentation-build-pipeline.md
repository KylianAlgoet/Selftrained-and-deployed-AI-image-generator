# DR-016 — Presentation authoring format and slide build pipeline

**Date:** 2026-08-11 (implemented) · **Record written:** 2026-08-14 · **Milestone:** M10
**Status:** accepted
**Decides:** how the defence presentation is authored and how its two PDFs are produced
**Related:** DR-015 (which this extends), `docs/00-project-brief.md` mandatory requirement 13,
`docs/process/feature-freeze.md`

## A process note this record has to make first

**The pipeline was built on 2026-08-11 and this record was written on 2026-08-14, after the fact.**
That inverts the project's own decision loop, which puts the record before the implementation, and
`slides/deck.yaml`, `scripts/build_slides.py`, `slides/templates/slides.css` and `.gitignore` all
cited "DR-016" for three days while no such file existed. It is recorded here rather than quietly
back-dated, because a citation to a decision record that does not exist is exactly the kind of defect
this project documents instead of tidying away.

Nothing below is reconstructed from memory: the toolchain table was re-measured on 2026-08-14, and
the measured result is the build that produced the submitted artifacts.

## Context

The assignment requires **a presentation as PDF** (`docs/00-project-brief.md`, mandatory
requirement 13). It is the one mandatory requirement still outstanding after M9, and the defence is
on 2026-09-02.

Three constraints shape the decision:

1. **The feature freeze is in force** (2026-08-09 → submission). No installs without a decision
   record.
2. **The machine still has no document or presentation toolchain.** Measured on 2026-08-14, in this
   environment, not recalled from DR-015:

   | tool | state |
   |---|---|
   | `python-pptx` | **absent** from `.venv` |
   | `marp` | **absent** from PATH |
   | pandoc | **absent** from PATH |
   | soffice (LibreOffice) | **absent** from PATH |
   | weasyprint | **absent** from `.venv` |
   | `pypdf`, `fitz` (PyMuPDF) | **absent** from `.venv` |
   | Google Chrome | **present** — build prerequisite inherited from DR-015 |
   | Node / `npx` | present — but a Marp or reveal.js install is still a new dependency |

3. **A deck needs two different documents from one set of facts.** A 16:9 deck for the room, and a
   speaker-note handout for the presenter. Authoring those separately guarantees they drift.

## Alternatives and how each was treated

| # | alternative | treatment |
|---|---|---|
| A | **Extend the DR-015 chain: Markdown → markdown-it-py → Jinja2 + print CSS → headless Chrome** | **selected and measured** — the build below |
| B | PowerPoint / Google Slides | **screened out** — the source leaves version control, which breaks traceability to commits and fact locks; the same reason DR-015 rejected Word |
| C | Marp (npm) | **screened out** — absent; a new dependency under the freeze, and its theming would not reuse the report's fact-substitution stage |
| D | reveal.js (npm) | **screened out** — absent, new dependency, and it targets a browser presentation rather than the PDF the assignment requires |
| E | `python-pptx` | **screened out** — absent, and a `.pptx` still has to be converted to PDF by a tool that is also absent |
| F | A second, separate Chrome pipeline written for slides | **screened out** — it would duplicate the fact substitution, figure resolution and PDF validation stages, and duplicated stages drift apart |

**Only A was measured.** B–F were screened on criteria, and this record says so rather than implying
a comparison that did not happen — the same honesty DR-007, DR-009 and DR-015 carry.

## Criteria

| criterion | why it matters here |
|---|---|
| **Zero new dependencies** | the freeze forbids installs without a decision record |
| **Numbers cannot drift from the report** | a slide contradicting the report in the room is a defence failure |
| **Slide and speaker note cannot drift apart** | the deck is deliberately sparse; the note carries the argument |
| **Overflow must fail the build, not the presentation** | a fixed-height slide clips silently |
| **Diffable source** | 26 slides revised repeatedly before the defence |
| **Two outputs, one source** | deck and handout must stay in step |

## Decision

**Author each slide as one Markdown file under `slides/sources/`, holding the slide body and its
speaker note under a `## Speaker notes` heading, and render both PDFs through the DR-015 stages
imported directly from `build_report.py`.**

Configuration fixed by this record:

- **`scripts/build_slides.py` imports its stages from `build_report`** rather than copying them —
  `substitute_facts`, `check_figures`, `absolutise_figures`, `find_chrome`, `print_to_pdf`,
  `validate_pdf`, `make_markdown`. One pipeline, two documents.
- **There is no `slides/facts.yaml`.** Quantitative values resolve from `report/facts.yaml`, so a
  number corrected in the report is corrected on the slide by the same edit. This is the mechanism
  behind the "numbers cannot drift" criterion, and it is the main reason A beat C, D and E.
- **One file per slide**, body and note together, so a note cannot drift from its slide. A slide with
  no speaker note is a **build failure**, not a warning.
- **Per-layout text budgets** in `slides/deck.yaml`; exceeding one is a **hard build failure**. A
  slide is a fixed 190.5 mm box with `overflow: hidden`, so over-full content is clipped rather than
  reflowed and the loss is silent.
- **The page count is the direct overflow test**: the build fails if the PDF page count does not
  equal the slide count.
- **Captions, evidence pointers and inline SVG are exempt from the text budget.** Captions are set
  small and are there to be pointed at, not read aloud, and counting them would penalise naming the
  evidence under every figure. SVG is exempt on a stronger argument: the budget is a proxy for reflow
  overflow, and SVG cannot reflow — it scales down inside its `viewBox` rather than growing taller.
- **Two outputs:** `DeckForge-AI-presentation.pdf` (16:9, notes **excluded**) and
  `DeckForge-AI-presentation-notes.pdf` (A4 handout, one page per slide, notes **included**).
- **System fonts only, no external assets**, inherited from DR-015 for the same reason.

## Measured result

The build that produced the submitted artifacts, run on 2026-08-14 from commit `685664b`:

```
python scripts/build_slides.py --strict
-> slides authored   : 26 of 26
-> bytes             : 1,313,731
-> sha256            : 42c5e8e2927f7d8bc8d4663ae599025c7535a0e35abf84efdd5f4cfbb722a6e8
-> pages             : 26  (heuristic: page-tree /Count agrees with the /Type /Page object count)
-> page geometry     : 960 x 540 pt = 16:9
-> estimated speaking: 26.4 min, slides only (ESTIMATE from note word counts)
-> build time        : 2.94s
```

Notes handout: 380 486 bytes, sha256
`71442da253df9a0b0137328bca1c53c599ac6c0bc1e05737aa354743903d1658`.

Report, rebuilt in the same session for the reason in consequence 5: 2 769 385 bytes, sha256
`73f574158d83f7452a605d57b8c40541c45b2a0693fb69d66f280e9ea2677157`, **91 pages**. This
**supersedes** the M9 artifact (2 756 980 bytes, `5c394e7a…`, 90 pages) recorded in
`docs/evidence/M9/evidence-audit.md`.

**One report build in this session came out 800 KB short at the same page count and passed every
check.** It did not recur in 14 attempts and its cause is unknown. It is not a deck defect, but it
bears directly on what this pipeline's checks can and cannot prove, and it is recorded in
`docs/evidence/M10/build-record.md` rather than left to the next person to rediscover.

**26 pages for 26 slides is the overflow test passing, not a formatting detail.**

## The page geometry check, and why it is reported the way it is

`read_aspect()` is a regex over the raw PDF bytes for `/MediaBox`, for the same reason DR-015's page
counter is a heuristic: **no PDF parser is installed**, re-confirmed above. It succeeded here because
Chrome wrote no object streams for this deck, and it may fail once more photographs are embedded. An
unreadable box is reported as **unreadable**, and mixed page sizes are reported as `MIXED` — never
assumed correct. The human visual gate is what actually confirms the shape.

## What this decision does NOT claim

1. **It does not claim the PDF is byte-reproducible.** Chrome embeds a creation timestamp and its own
   version. Reproducible in **content**; the recorded SHA-256 identifies the **submitted artifact**.
   Identical to DR-015's position, and to the project's R14 distinction between reproducible
   inference and reproducible training.
2. **It does not claim the deck is the right length.** See below.
3. **It does not claim the text budgets are correct.** They are a crude, checkable proxy for
   overflow. They are the deterministic half of the defence; the human visual gate is the other half,
   and neither replaces the other.
4. **It does not claim alternative A is the best presentation pipeline** — only that it is the one
   that works here without touching a frozen dependency set, and the only one that inherits the
   report's fact locks for free.
5. **It does not claim the speaking estimate is a rehearsal time.** See below.

## Two open items, both deliberate

**1. No authoritative presentation duration is recorded anywhere in this repository.** Searched on
2026-08-11 and re-checked on 2026-08-14 across the project brief, the planning, the governing prompt
and the report sources: no duration is stated in any of them. **The slide count is therefore
provisional**, and the deck responds to that rather than guessing: every slide carries a `tier` of
`core` or `supporting`, and a `supporting` slide can be cut, with its content folding into the
adjacent `core` slide's speaker note rather than being deleted. **A shorter cut costs stage time; it
never costs a claim.** Of the 26 slides, **22 are `core` and 4 are `supporting`** — `memory-habit`,
`adapters`, `other-failures` and `texture-fit`. Note the implication: cutting every cuttable slide
removes only 4 of 26, so the tier mechanism absorbs a **modest** overrun, not a large one. If the
real duration turns out to be 15 or 20 minutes, the deck needs restructuring, not trimming.

**This needs Kylian to supply the real duration from the assessment material or the programme.**
Until then the length is unvalidated.

**2. The spoken time is an ESTIMATE and no rehearsal has been run.** It is derived from the speaker
notes' word count at a deliberately slow 130 wpm, and reported with that method attached every time.
The demo slide's note is excluded from the total, because it is a set of directions rather than a
script and the demo is budgeted separately at its own 4-minute target. **26.4 minutes of slides plus
a 4-minute demo target is roughly 30 minutes** — and an estimate from word counts is not a measured
rehearsal, which is why it is never called one.

## Consequences

1. **Chrome remains a build prerequisite**, unchanged from DR-015.
2. **Both presentation PDFs are tracked** via the same narrow ignore-exception mechanism the report
   uses, because requirement 13 puts them in the GitHub result. The intermediate HTML of both stays
   ignored and is rebuilt on every run.
3. **A change to `report/facts.yaml` now rebuilds the deck as well as the report.** That is the
   intended coupling, and it means the deck must be rebuilt whenever the report is.
4. **The report's fact locks gained a distinction M10 forced.** `pytest_tests` is the product/research
   count at the M8 close; M9 added tests that test the *report* rather than the system. Collapsing
   them into one ambiguous number would let a slide and a chapter mean different things by the same
   figure, so `pytest_report_tests` and `pytest_total` are locked separately and a slide has to choose
   which it means.
5. **Writing this record changed the report.** `decision_record_count` is extracted structurally by
   globbing `docs/decisions/DR-*.md`, so creating DR-016 moved it from 15 to 16 and the fact lock
   **failed the deck build** until `report/facts.yaml` and Appendix B were updated. The report was
   rebuilt, and the extra appendix row moved it from **90 to 91 pages**. This is the mechanism
   working as designed — a self-referential decision record is exactly the case where a hand-typed
   count would have gone stale silently.
6. **The report's page count is NOT fact-locked, and it drifted.** "90-page report" was a typed
   literal on slide 26 and in the traceability matrix, and the rebuild above made both wrong. They
   were corrected to 91. A page count cannot be extracted from the Markdown sources — it only exists
   after Chrome paginates — so no lock is possible with the current extractors, and **this remains a
   live drift risk**: any edit that changes the report's length silently invalidates that number in
   two places. Dated historical records that state 90 pages (the M9 process-log entry, the M9
   evidence audit, the planning row for 2026-08-11) are **correct for their date and were not
   rewritten**.
7. **No package was installed.** The `.venv` is unchanged by this decision.

## Status

**Accepted**, on the measured build above. The deck's *content* has not yet passed a human visual
gate, and this record does not stand in for one.
