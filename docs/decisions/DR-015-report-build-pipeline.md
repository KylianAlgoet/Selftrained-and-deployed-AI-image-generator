# DR-015 — Report authoring format and reproducible PDF build pipeline

**Date:** 2026-08-10 · **Milestone:** M9 · **Status:** accepted
**Decides:** how the bachelor research report is authored and how its PDF is produced
**Related:** issue #10 (criteria 2 and 4), `docs/process/feature-freeze.md`, DR-001

## Context

The assignment requires **research documentation as PDF**
(`docs/00-project-brief.md`, mandatory requirement 10) and issue #10 requires a **reproducible PDF
build process**. The report is ~26 mandated sections and roughly 45–60 pages, drawing on 40
experiment rows, 15 decision records, 6 prototype documents and 77 tracked evidence images.

Two constraints shape the decision:

1. **A feature freeze is in force** (2026-08-09 → submission). Dependency upgrades and installs are
   *"not allowed without an explicit new decision record"*. Any pipeline needing a new package
   would have to be justified here rather than assumed.
2. **The machine has no document toolchain.** Measured on 2026-08-10, not recalled:

   | tool | state |
   |---|---|
   | pandoc | **absent** |
   | pdflatex, xelatex, tectonic | **absent** |
   | wkhtmltopdf | **absent** |
   | soffice (LibreOffice) | **absent** |
   | weasyprint | **absent** |
   | Google Chrome | **present** — `C:\Program Files\Google\Chrome\Application\chrome.exe` |
   | Microsoft Edge | present (Chromium, usable as a fallback engine) |
   | `markdown-it-py` | **4.2.0**, already in `.venv` |
   | `Jinja2` | **3.1.6**, already in `.venv` |
   | `Pygments` | **2.20.0**, already in `.venv` |
   | `PyYAML` | 6.0.3, already in `.venv` |
   | `mdit-py-plugins` | **absent** |
   | `linkify-it-py` | **absent** |

## Alternatives and how each was treated

| # | alternative | treatment |
|---|---|---|
| A | **Markdown → markdown-it-py → Jinja2 HTML+CSS → headless Chrome → PDF** | **measured** — probe run on 2026-08-10 |
| B | pandoc (+ a LaTeX engine) | **screened out** — pandoc is absent *and* would need a LaTeX engine that is also absent; two installs under a freeze |
| C | WeasyPrint | **screened out** — absent; a new dependency, and it pulls a native rendering stack |
| D | Hand-written HTML → Chrome | **screened out** — produces the same PDF but the source stops being reviewable, diffable or reusable; a 60-page report becomes unmaintainable |
| E | Manual browser "Print to PDF" | **screened out** — not scriptable, not reproducible, and it cannot satisfy issue #10 criterion 2 |
| F | Word / Google Docs | **screened out** — the source leaves version control, which breaks traceability to commits |

**Only A was measured.** B–F were screened on criteria, and this record says so rather than
implying a comparison that did not happen — the same honesty DR-007 and DR-009 carry for candidates
that were never run.

## Criteria

| criterion | why it matters here |
|---|---|
| **Zero new dependencies** | the freeze forbids installs without a decision record |
| **Reproducible on a clean clone** | issue #10 criterion 2; the project already proved a clean-clone test finds what local runs hide |
| **Diffable source** | 26 sections written over several days need reviewable increments |
| **Professional print output** | it is a bachelor research report, not a web page |
| **Build time** | fast enough to rebuild on every correction |
| **Failure behaviour** | a broken build must name the failing stage, not emit a silently wrong PDF |

## Measured result

The probe ran on 2026-08-10 against a three-page sample exercising `@page` sizing, a forced page
break, a repeating table header and the intended type stack:

```
chrome.exe --headless --disable-gpu --no-sandbox --no-pdf-header-footer
           --virtual-time-budget=5000 --print-to-pdf=probe.pdf probe.html
-> 43 514 bytes written
-> header %PDF-1.4, trailer %%EOF present
-> 3 pages, matching the 3 pages authored
```

**Chrome produces a real, structurally valid, multi-page PDF from CSS paged media.** Alternative A
is viable.

## Decision

**Author the report as Markdown under `report/sources/`, render it with `markdown-it-py`, template
it with Jinja2 into a single self-contained HTML, and print that to PDF with headless Chrome.**

Configuration fixed by this record:

- **markdown-it-py preset `commonmark`, with `table` and `strikethrough` enabled.** Both are core
  rules and need no plugin.
- **No footnote and no definition-list syntax** — those need `mdit-py-plugins`, which is absent.
  This is why the report uses **numbered `[n]` citations** rather than footnotes: the citation style
  follows the toolchain rather than fighting it.
- **Autolinking disabled** — `linkify-it-py` is absent; every URL is an explicit link.
- **Pygments** for code highlighting, with a light print theme.
- **System fonts only.** No web fonts and no external assets of any kind: Chrome renders offline and
  a missing remote font would change the layout silently.
- Figures are referenced **in place** under `docs/evidence/…` and resolved to absolute `file://`
  URLs at build time, so a figure cannot drift from the evidence it documents.

## What this decision does NOT claim

1. **It does not claim the PDF is byte-reproducible.** Chrome embeds a creation timestamp and its
   own version, so two builds of identical sources produce different bytes. The report is
   reproducible in **content**; the recorded SHA-256 identifies the **submitted artifact**, and no
   more. This project already distinguishes carefully between reproducible inference and
   reproducible training (R14), and the same care applies here.
2. **It does not claim Chrome implements all of CSS paged media.** Only the features the probe
   exercised are evidenced.
3. **It does not claim page counting is solved.** See below.
4. **It does not claim alternative A is the best pipeline** — only that it is the one that works
   here without touching a frozen dependency set. With pandoc available the comparison could have
   come out differently, and it was never run.

## Page counting — an explicit limitation

**No reliable PDF reader is available.** Probed on 2026-08-10: `pypdf`, `PyPDF2`, `PyMuPDF`/`fitz`,
`pdfminer`, `pikepdf` are all **absent from the venv**, and `pdfinfo` (poppler) is **absent from
PATH**.

A regex over `/Type /Page` objects is **not** an acceptable substitute: PDF object streams and
compression make it unreliable as a general parser, and a page count that is silently wrong is worse
than no page count at all.

**Decision: page count is optional build metadata.** The build reports it as a **clearly labelled
heuristic** — the page-tree `/Count` and the number of `/Type /Page` objects are both read, and a
count is reported **only if the two agree** and the file contains no object streams; otherwise the
build reports `not measured` and continues. The authoritative page count is obtained by a human
opening the PDF at the M9.12 visual gate, which happens anyway.

**No dependency will be installed for page counting without Kylian's approval.**

## Structural PDF validation is NOT optional

Independently of page counting, every build asserts the output exists, is non-empty, begins with
`%PDF-` and ends with `%%EOF`. A build that cannot assert those fails.

## Consequences

1. **Chrome becomes a build prerequisite** and is documented as such. A clean clone without Chrome
   can render the HTML but not the PDF — an honest limitation, recorded rather than hidden.
2. **The final PDF is tracked** at `deliverables/DeckForge-AI-research-report.pdf`, via the
   narrowest possible ignore exception. The intermediate HTML stays ignored and is rebuilt every
   time. Note the Git semantics this required: `deliverables/` would exclude the *directory*, and
   Git does not descend into an excluded directory, so the negation would have been unreachable;
   `deliverables/*` ignores the contents and keeps the directory traversable.
3. **Quantitative values in the report come from fact placeholders**, never typed literals, so a
   number cannot be current in one chapter and stale in another. Their extraction is defined in
   `report/facts.yaml` and asserted by `tests/test_report_facts.py`.
4. **The cover page is swappable.** `report/templates/cover.html.j2` and the `document:` block of
   `report/metadata.yaml` are the only two places that know what the cover looks like — it has no
   Markdown source at all. A school template supplied before submission replaces those two, and no
   chapter, cross-reference or validation check is affected.
5. **No package was installed.** The `.venv` is unchanged by this decision.

## Status

**Accepted**, 2026-08-10, on the measured probe above.
