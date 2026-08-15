# M11 — audit findings

**Date:** 2026-08-15 · **Milestone:** M11 (final submission audit)
**Scope:** findings raised by the B1–B9 checks and the B13 clean-clone run. Each states what was
measured, what it means, and whether it was fixed or is being carried.

| # | finding | class | state |
|---:|---|---|---|
| **F1** | the 800 KB short report build — **cause identified** | build | **DIAGNOSED, not a content defect** |
| **F2** | the clean-clone test count was stale in three documents | documentation | **FIXED** |
| F3 | `preflight.ps1` cannot reach a full PASS while Docker Desktop holds port 8000 | environment | carried — human-only |
| F4 | `origin/main` is 19 commits behind local `main` | submission | carried — Kylian's |
| F5 | the deck has had no human visual gate and no rehearsal | submission | carried — Kylian's |
| F6 | the report does not print `worst_device_used_mib` (7987.5) | omission | carried, deliberate |
| F7 | 42 dataset items carry no `author` | provenance | not a defect — documented behaviour |

---

## F1 — the 800 KB short report build. Cause found: it is decoration, not content

### What was carried into this session

M10 recorded an **open, unexplained** risk: one report build came out ~800 KB short at the same 91
pages and passed every check. It did not recur in 14 attempts and **the file was overwritten before
it could be examined**, so the cause was unknown. The risk was stated at its worst plausible
reading: *"the report build cannot detect the loss of 800 KB of content, so a report with missing
figures would ship looking correct."*

### It recurred, and this time the artifact was preserved

The first M11 rebuild reproduced it. The short build was **copied aside before rebuilding**, which
is the step M10 could not take, and the two files were compared directly.

| build | bytes | sha256 | pages | build time |
|---|---:|---|---:|---:|
| **short** | **1 971 967** | `41cb8ad077fb9c85…` | 91 | 2.76 s |
| **full** | **2 773 114** | `5f2fe9c494d4978e…` | 91 | 3.48 s |
| delta | **+801 147** | — | **0** | — |

### What is identical between them

| property | short | full | identical |
|---|---:|---:|:--:|
| text-drawing operations | 19 434 | 19 434 | **yes** |
| sha256 of every glyph operation, in order | `02b77dcf6047995e…` | `02b77dcf6047995e…` | **yes** |
| embedded images | 6 | 6 | **yes** |
| image dimensions | 512×2048, 1024×896, 1098×692, 1280×512, 1903×980 | same | **yes** |
| embedded fonts (`/FontDescriptor`) | 9 | 9 | **yes** |
| PDF objects | 7 032 | 7 032 | **yes** |
| pages | 91 | 91 | **yes** |

**Not one glyph, figure, font or page differs.** The ordered hash of all 19 434 text operations is
byte-identical, which is a stronger statement than "the same words appear": the same glyphs are
drawn in the same order at the same positions.

### What actually differs

Exactly one thing — **1×1 pixel filled rectangles**:

| | short | full | delta |
|---|---:|---:|---:|
| `re` + `f` fills, all sizes | 36 199 | **1 502 029** | **+1 465 830** |
| of those, fills of exactly 1×1 | 34 729 | **1 500 559** | **+1 465 830** |

Sampling one page's content stream (object 27) shows the run directly:

```
115 0 1 1 re f      117 0 1 1 re f      119 0 1 1 re f      121 0 1 1 re f  …
```

One-unit squares at a two-unit pitch, filled `.7882 .8118 .8314`. That colour is
**`#c9cfd4`**, which is `--rule` in `report/templates/report.css`, and the only dotted rule in the
stylesheet is at **`report.css:170`**:

```css
.toc__dots {
  flex: 1 1 auto;
  border-bottom: 1px dotted var(--rule);
}
```

**The 800 KB is the table-of-contents dot leaders.** Chrome rasterises the dotted border into
individual 1×1 px fills instead of emitting a dash pattern.

### Why it costs 800 KB, and why it lands on all 91 pages

Chrome's paged output puts the **whole document** in every page's content stream and clips a window
into it (`237.5 284.375 2007.959 2988.1836 re W* n`, with a large negative `cm` offset per page).
The TOC leaders are therefore replicated into **all 91 page streams**, even though they are only
visible on the TOC pages. 91 objects differ, each by ~9 KB compressed:

```
object 27 inflated:   15 766 bytes (short)  ->  273 179 bytes (full)
object 27 compressed:  3 050 bytes (short)  ->   12 058 bytes (full)
```

The rectangles are near-identical, so they compress ~23:1 — 1.47 M drawing operations for 801 KB.

### What this changes

**The risk as written was wrong in its consequence.** The feared failure — a report shipping with
missing figures and looking correct — **cannot** be what was observed, because the short build's
figures, text and fonts are provably identical. The observable difference is that **some or all of
the TOC dot leaders do not render**.

It is not nothing: the short build still had 36 199 fills, so it is a **partial** rasterisation, not
a clean absence. That signature — some leaders drawn, most not — is consistent with the print being
taken while paint is still in progress, which also matches the shorter build time (2.76 s vs 3.48 s).
**The race itself is not proven, and is not claimed here.** What is proven is the content identity
and the identity of the missing marks.

### What was done about it

- **The shipped PDF is the full build** (`5f2fe9c494d4978e…`, 2 773 114 B, 1 502 029 fills). It was
  verified after building, not assumed.
- **A detector was written, but no gate was added to `build_report.py`.**
  `docs/evidence/M11/check_report_leaders.py` reports on any PDF and exits non-zero on a short
  build; it does not run inside the build and changes nothing about how the report is produced.
  M10 declined a guard because a threshold from one unreproduced observation is guesswork — that is
  no longer the objection, since the cause is known and the threshold is now derived from two
  measured builds. The remaining objection is only that **gating** the build means editing it under
  a freeze for a **cosmetic** defect. **Whether to gate is Kylian's call, and it is now an informed
  one.**
- **The CSS was not changed either.** Replacing the dotted border with a background gradient would
  remove 1.47 M drawing operations and the whole failure mode, but it changes the report's
  appearance under a freeze.

**How to check any future build:**

```powershell
.venv\Scripts\python.exe docs\evidence\M11\check_report_leaders.py
```

It counts the 1×1 fills and exits non-zero below a threshold of 750 000, halfway between the two
measured builds. It was verified against **both** artifacts on 2026-08-15:

```
deliverables\DeckForge-AI-research-report.pdf   2,773,114 B   91 pages   1,500,559 fills   PASS (0)
<preserved short build>                         1,971,967 B   91 pages      34,729 fills   FAIL (1)
```

The script deliberately lives in the evidence folder, not in the build: it **reports**, it does not
gate, so it changes nothing about how the report is produced. Byte size is a proxy for the same
thing and is easier to read — **≥ 2.7 MB is healthy, ~1.97 MB is short** — but the fill count is
what actually identifies the defect.

---

## F2 — the clean-clone test count was stale in three documents. FIXED

The B13 clean clone printed **522 passed, 5 skipped** (522 + 5 = 527, matching this machine). Three
documents still stated the M8 figure of **468 passed / 5 skipped**, in the present tense, as a
description of what the command prints:

| file | state |
|---|---|
| `README.md` | **corrected** to 522 / 5, with the superseded M8 figure named |
| `report/sources/15-testing.md` | **corrected**, and the report **rebuilt** — the sentence is in the shipped PDF |
| `docs/07-testing-strategy.md` | **left as written** — it sits under a heading now marked *"Suite sizes at M8 closure (2026-08-09) — historical"*, so it is correct for its date |

The arithmetic was never internally inconsistent: chapter 15 is scoped to the **473 system tests**
throughout, and `facts.pytest_tests` resolves to 473, so the page read `468 + 5 = 473`. What was
wrong is that a clean clone **no longer prints that**, because M9 and M10 added 54
document-validation tests. The corrected sentence states the whole-repository figure and names the
473 it contains.

Verified in the rebuilt PDF: `522 passed` appears **once**, `468 passed` appears **zero** times.

**This is the same class as M10's compression defect and M9's bibliography defect:** a sentence that
was true when written, describing an output that later changed, in a document no check reads as a
claim about live output.

---

## F3 — port 8000, and why it was not "fixed"

`preflight.ps1` reports 9 of 10 PASS in the clean clone. The failure is **API port 8000 IN USE by
pid 17668 (com.docker.backend)** — Docker Desktop, already running, unrelated to this project.

The check is doing its job: it exists so two API processes never compete for one 8 GB device. It was
**not** resolved by stopping Docker, because that is the user's running application and killing it to
turn a check green is the wrong trade. The clean-clone backend was started on **8001** instead, which
is why step 10 could still pass.

**A full `preflight.ps1` PASS on this machine requires port 8000 to be free.** Human-only item.

---

## F4 and F5 — the two PARTIAL requirements

Both are recorded in `assignment-audit.md` and neither is a defect in the work:

- **F4 — requirement 12.** `git rev-list --left-right --count origin/main...HEAD` → `0  19`. Zero
  behind, **19 ahead**. Everything the assignment calls "the final GitHub result" is committed and
  none of it is published. An evaluator visiting the repository today sees the M9 state. **This is
  the single highest-impact open item in the submission.**
- **F5 — requirement 13.** The deck builds, validates and fits its slot *on paper*. Every timing
  figure is an estimate from speaker-note word counts at an assumed 130 wpm. **No human has looked
  at the 15 slides and no rehearsal has been run.** The report already refuses to call this met.

---

## F6 — an omission the audit chose not to close

B7 records: the report states peak allocated (5143.73) and the one-shot device peak (7985.5), but
**does not print `worst_device_used_mib` (7987.5)** — its serving row shows `-` for peak device.

This is **not a false claim**; it is a gap where a fact-locked measurement now exists. It is the
figure the deck needs for its margin arithmetic to be checkable (`8187.5 − 7987.5 = 200.0`), and the
deck does print it. Adding it to the report is a content change under the freeze for a number the
report does not currently rely on, so it is **carried, not closed**.

---

## F7 — 42 dataset items with no author. Not a defect

B4 passed every licence and provenance check, and noted that 42 of 148 items carry no `author`: **41
Library of Congress WPA posters and 1 Met open-access item**. Both collections publish these as
anonymous. `docs/04-dataset-methodology.md` already documents the field as *"author (where known)"*,
so this is the documented behaviour rather than missing provenance.

Licence spread is unchanged and complete: **CC0 55 / public domain 41 / project-original 52**, no
unknown and no restrictive licence.
