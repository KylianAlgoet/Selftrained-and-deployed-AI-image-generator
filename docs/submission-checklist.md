# Submission checklist

**Created:** 2026-08-15 (M11) · **Deadlines:** feature freeze **2026-08-15** · final content
**2026-08-16 18:00** · submission **2026-08-17 06:00** (Europe/Brussels) · presentation
**2026-09-02**

Every row is either verified against evidence produced by the M11 audit, or named as outstanding
with the person who owns it. **Nothing here is marked done on the strength of a feature existing.**
Full audit: `docs/evidence/M11/assignment-audit.md` · findings: `docs/evidence/M11/findings.md`.

## 1. The thirteen mandatory requirements

**13 of 13 PASS for submission.** One defence-preparation action remains outstanding (a full timed
rehearsal); it is not a submission requirement and is tracked separately in §2.

| # | requirement | state | owner |
|---:|---|---|---|
| 1 | custom training dataset | **PASS** — 148 rows re-derived this session | — |
| 2 | dataset provenance and permitted usage | **PASS** — CC0 55 / PD 41 / project-original 52, no unknown licence | — |
| 3 | ≥ 3 visually distinct styles | **PASS** — three adapters served live; `retro-poster` carries its PARTIAL PASS into the API payload | — |
| 4 | trained or fine-tuned locally | **PASS** — 10 runs on the audited RTX 4060 | — |
| 5 | text + reference-image conditioning | **PASS** — IP-Adapter at 0.55 (DR-008) | — |
| 6 | generates new decal artwork | **PASS** — **31** completed real GPU generations (current total); re-validated live on 2026-08-15, byte-identical to a hash declared before the run. Plus **1 failed GPU inference attempt** on 2026-08-16, counted separately — `docs/evidence/M12/demo-rehearsal.md` | — |
| 7 | mapped onto a 3D skateboard | **PASS** — 38 Playwright scenarios against a live WebGL context | — |
| 8 | reproducible deployment/demo setup | **PASS** — M11 clean clone: clone → restore → running system | — |
| 9 | public planning link | **PASS** — `https://github.com/users/KylianAlgoet/projects/1/views/1`, HTTP 200 verified | — |
| 10 | research documentation as PDF | **PASS** — **91 pages**, final externally reviewed artifact installed 2026-08-17 | — |
| 11 | prototype evidence | **PASS** — prototypes 0–5, none skipped; `README.md` is the prototype documentation | — |
| 12 | final GitHub result | **PASS** — the M11 backlog was pushed 2026-08-15 23:55; the M12 submission commits are pushed on top. **Submission baseline: the tip of `origin/main`** — see §7 | — |
| 13 | presentation as PDF | **PASS** — final **16-page** presentation PDF supplied, `deliverables/DeckForge-AI-presentation.pdf`. *A full timed rehearsal remains defence preparation and is **not** claimed complete; the live defence has not happened. Neither is a submission requirement — see §2.* | — |

## 2. What only Kylian can do, in priority order

| # | action | why it cannot be done here | blocks |
|---:|---|---|---|
| ~~1~~ | ~~**`git push`** — 19 commits~~ | **DONE 2026-08-15 23:55** — reflog records `update by push` and `.git/FETCH_HEAD` confirms it. The M12 submission commits were pushed on 2026-08-16 | — |
| **2** | **Open the final 16-slide deck and review every slide** | every check that has run is *structural*; nothing says the deck is legible or that the argument survives compression | defence preparation |
| **3** | **Rehearse against a clock** | **no measured full-presentation duration is claimed anywhere.** The 20-minute slot includes the demo | defence preparation |
| 4 | Comment on and close **GitHub issue #10**; move the project board | `gh` is absent from this machine, and closing a public issue is his action regardless | public planning state |
| ~~5~~ | ~~Free **port 8000** before demoing~~ | **DONE 2026-08-15** — the holder was an unrelated project's container (`aegislab-api-1`), not Docker Desktop; stopped, preflight passed **10 of 10**, container restarted. **It will hold 8000 again after a reboot**, so free it before the demo | — |
| 6 | Decide whether to **gate** the report build on the TOC-leader check | it edits the build under a freeze for a cosmetic defect | nothing — informational |
| 7 | Write the **M9 entry in `docs/ai-usage.md`**, or leave it absent | reconstructing it from commits days later is the plausible-but-unwitnessed account that log exists to guard against | completeness of the AI-usage record |

## 3. Artifacts, as measured on 2026-08-17 (final externally reviewed artifacts installed)

| artifact | pages | bytes | sha256 | origin |
|---|---:|---:|---|---|
| `deliverables/DeckForge-AI-research-report.pdf` | **91** | 1 948 005 | `2cd07def657e4358…` | externally finalised |
| `deliverables/DeckForge-AI-presentation.pdf` | **16** | 1 540 784 | `3d3f77f00170d5ee…` | externally finalised |
| `deliverables/DeckForge-AI-presentation-notes.pdf` | **16** | 251 823 | `d9c3275e07293970…` | **unchanged**, still the repository build |

**The research report and the presentation are no longer repository builds.** Both were finalised
externally and installed verbatim on 2026-08-17; both are `%PDF-1.6` (Acrobat Distiller), where the
repository pipeline emits `%PDF-1.4` (Skia/PDF). **Do not rebuild either from source to "refresh"
them** — `scripts/build_report.py` and `scripts/build_slides.py` would overwrite the submitted
artifacts with different documents.

**The presentation source in `slides/` is stale and is knowingly retained as historical.** It
authors **15** slides and cannot reproduce the submitted 16-slide deck, which carries a dedicated
Project Planning slide that has no counterpart in the source. `scripts/validate_slides.py` and the
38 deck-validation tests still describe that 15-slide source, not the submitted PDF. Reconstructing
a matching source would have meant authoring slide content, so it was not attempted.

The speaker notes were **not** replaced and are not claimed to be. They remain the repository build
and still correspond one-page-per-slide to the **15**-slide deck.

### ⚠️ `audit_pdfs.py` no longer applies to two of the three PDFs

It reports **14 failures** against the installed artifacts. **Every one is a tooling mismatch, not a
content defect.** Its extractor (`docs/evidence/M11/pdf_text.py`) decodes text through per-font
`/ToUnicode` CMaps as the Chrome build emits them; the installed `%PDF-1.6` files carry
`/ToUnicode` for only 8 of 41 fonts, so the extractor recovers nothing and **every text assertion
then fails vacuously** — including "no blank page", which reports all 91 pages blank.

The report's content was verified independently, by extracting literal strings from its content
streams: 91 pages, 3 118 text-showing operators, and the required statements all present —
planning `/views/1`, **17** decision records, total **31**, "not bit-reproducible", RQ4
"inconclusive", retro-poster "PARTIAL PASS", SD 2.1 gated, and **no** occurrence of "15 slides",
"14:56" or "1:04".

**Do not read that FAIL as a defect in the deliverables, and do not "fix" the PDFs to satisfy it.**
The honest fix would be to teach the extractor this producer's encoding, which is out of scope
under a submission freeze.

If the report is ever rebuilt from source, re-run
`.venv\Scripts\python.exe docs\evidence\M11\check_report_leaders.py` — the Chrome build
intermittently drops the table-of-contents dot leaders (findings F1); text, figures and page count
are unaffected, but a short build looks correct to every other check. **That check does not apply to
the installed `%PDF-1.6` report**, which is not produced by Chrome and legitimately contains none of
the 1×1 leader fills the check counts.

## 4. Repository hygiene — verified this session

| check | result |
|---|---|
| secrets scan, 9 patterns, all history | **clean** — no weights or secrets path ever added in any commit |
| tracked size | 14.9 MB across 584 files; only the two PDFs exceed 1 MB |
| ignored trees absent from Git | `outputs/`, `.venv`, `node_modules`, `data/raw`, `__pycache__` |
| markdown links and written paths | **every one resolves**; 7 non-resolving paths each carry a recorded reason |
| dataset manifest vs `facts.yaml` | every count matches |

## 5. Suites

### Latest final validation — measured 2026-08-17

| suite | count | note |
|---|---:|---|
| **pytest** | **528 passed** | 473 system + 16 report-validation + 38 deck-validation + 1 added in M12 |
| vitest | **183** | 12 files |
| Playwright E2E | **38** | `retries: 0` |
| eslint · build | clean · succeeds | — |

### Historical M11 baseline — measured 2026-08-15, not restated

| suite | count | note |
|---|---:|---|
| pytest | **527** | 473 system + 16 report-validation + 38 deck-validation |
| pytest, clean clone | **522 passed / 5 skipped** | 522 + 5 = **527**, matching that machine |

**527 is correct for 2026-08-15 and is deliberately left alone.** The single test added in M12 —
which keeps the failed GPU attempt counted separately from the completed generations — is the whole
difference between 527 and 528. Rewriting the M11 figure to 528 would make a dated measurement
describe a suite that did not exist yet.

**No test in any suite loads the model or runs a generation.** A green suite is not evidence that
DeckForge AI generates anything, and this project does not present it as such.

## 6. Things that must not be "fixed" before submission

1. **Do not upgrade `retro-poster` to a full pass.** It is a PARTIAL PASS, and it is also not dropped.
2. **Do not report ten of twelve research questions as answered.** Eight answered within scope, four
   bounded, RQ4's image-count component explicitly inconclusive.
3. **Do not describe the ~200 MiB GPU margin as comfortable headroom.**
4. **Do not restore "both gates scored blind."** The first was blinded, the second labelled by
   necessity.
5. **Do not put `peak_allocated_mib` next to `worst_spare_mib` as if they subtract.** The margin is
   `8187.5 − 7987.5 = 200.0`.
6. **Do not solve a presentation overrun by speaking faster**, and do not widen the narration band.
7. **Do not retrain, and do not delete `outputs/lora/`.** R14 means the three production adapters
   cannot be regenerated; they are authoritative as files, by sha256.
8. **Do not run GPU inference.** The current total is **31** and no further generation is
   authorised. The three M12 demo-rehearsal runs on 2026-08-16 were the last Kylian approved.
   Historical records keep their historical numbers — M8 reads 27, M11 reads 28 — and must not be
   "corrected" to 31. See `docs/evidence/M12/demo-rehearsal.md`.
9. **Do not fill in the missing metadata for the three M12 outputs.** Seed, scheduler, guidance
   and adapter checkpoint were never captured and cannot be recovered. They are recorded as
   unknown on purpose; a plausible reconstruction would be indistinguishable from a measurement.

## 7. The submission baseline

**The submitted state is the tip of `origin/main` on branch `main`.**

A commit cannot contain its own hash, so this file does not quote the final SHA — that would
either be wrong or force an amend-and-repush cycle. The baseline is instead pinned by things that
*are* stable inside the commit:

| anchor | value |
|---|---:|
| research report | 91 pages · 1 948 005 B · `2cd07def657e4358…` |
| presentation | **16** pages · 1 540 784 B · `3d3f77f00170d5ee…` |
| speaker notes | 16 pages · 251 823 B · `d9c3275e07293970…` |
| current generation total | **31** completed, **1** failed attempt |
| latest validation | **528** pytest · 183 vitest · 38 Playwright |
| planning | `https://github.com/users/KylianAlgoet/projects/1/views/1` |

To confirm what was submitted: `git log -1` on `main`, with `git status` clean and the branch
level with `origin/main`. The three artifact hashes above are reproducible with `Get-FileHash`
and must match; **if a hash differs, an artifact was replaced after this file was written** —
re-measure and update the table rather than trusting it.

**The report and the presentation must not be rebuilt.** Both installed artifacts were finalised
externally and are not reproducible from this repository: the build scripts would emit different
documents, and in the presentation's case a **15**-slide one. The historical Chrome-build caveat
still applies to anything genuinely rebuilt from `report/sources/` — that build intermittently drops
the TOC dot leaders (F1); on 2026-08-16 it hit the short build on the first attempt (1 971 962 B,
34 729 fills) and needed a second run to land healthy (2 773 108 B, 1 500 559 fills).
