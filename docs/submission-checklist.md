# Submission checklist

**Created:** 2026-08-15 (M11) · **Deadlines:** feature freeze **2026-08-15** · final content
**2026-08-16 18:00** · submission **2026-08-17 06:00** (Europe/Brussels) · presentation
**2026-09-02**

Every row is either verified against evidence produced by the M11 audit, or named as outstanding
with the person who owns it. **Nothing here is marked done on the strength of a feature existing.**
Full audit: `docs/evidence/M11/assignment-audit.md` · findings: `docs/evidence/M11/findings.md`.

## 1. The thirteen mandatory requirements

**11 of 13 PASS. 2 PARTIAL, both waiting on a human action, neither a defect in the work.**

| # | requirement | state | owner |
|---:|---|---|---|
| 1 | custom training dataset | **PASS** — 148 rows re-derived this session | — |
| 2 | dataset provenance and permitted usage | **PASS** — CC0 55 / PD 41 / project-original 52, no unknown licence | — |
| 3 | ≥ 3 visually distinct styles | **PASS** — three adapters served live; `retro-poster` carries its PARTIAL PASS into the API payload | — |
| 4 | trained or fine-tuned locally | **PASS** — 10 runs on the audited RTX 4060 | — |
| 5 | text + reference-image conditioning | **PASS** — IP-Adapter at 0.55 (DR-008) | — |
| 6 | generates new decal artwork | **PASS** — **28** real GPU generations; re-validated live on 2026-08-15, byte-identical to a hash declared before the run | — |
| 7 | mapped onto a 3D skateboard | **PASS** — 38 Playwright scenarios against a live WebGL context | — |
| 8 | reproducible deployment/demo setup | **PASS** — M11 clean clone: clone → restore → running system | — |
| 9 | public planning link | **PASS** — HTTP 200 verified this session | — |
| 10 | research documentation as PDF | **PASS** — 91 pages, rebuilt and re-verified 2026-08-15 | — |
| 11 | prototype evidence | **PASS** — prototypes 0–5, none skipped | — |
| 12 | final GitHub result | **PARTIAL** — **19 commits unpushed** | **Kylian** |
| 13 | presentation as PDF | **PARTIAL** — **no visual gate, no rehearsal** | **Kylian** |

## 2. What only Kylian can do, in priority order

| # | action | why it cannot be done here | blocks |
|---:|---|---|---|
| **1** | **`git push`** — 19 commits | remote operations need his explicit approval; `origin/main` is 19 behind | **requirement 12** |
| **2** | **Open the 15-slide deck and review every slide** | every check that has run is *structural*; nothing says the deck is legible or that the argument survives compression | **requirement 13** |
| **3** | **Rehearse against a clock** | 14:13 is a word count at an assumed 130 wpm, not a measured delivery | **requirement 13** |
| 4 | Comment on and close **GitHub issue #10**; move the project board | `gh` is absent from this machine, and closing a public issue is his action regardless | public planning state |
| ~~5~~ | ~~Free **port 8000** before demoing~~ | **DONE 2026-08-15** — the holder was an unrelated project's container (`aegislab-api-1`), not Docker Desktop; stopped, preflight passed **10 of 10**, container restarted. **It will hold 8000 again after a reboot**, so free it before the demo | — |
| 6 | Decide whether to **gate** the report build on the TOC-leader check | it edits the build under a freeze for a cosmetic defect | nothing — informational |
| 7 | Write the **M9 entry in `docs/ai-usage.md`**, or leave it absent | reconstructing it from commits days later is the plausible-but-unwitnessed account that log exists to guard against | completeness of the AI-usage record |

## 3. Artifacts, as measured on 2026-08-15

| artifact | pages | bytes | sha256 |
|---|---:|---:|---|
| `deliverables/DeckForge-AI-research-report.pdf` | **91** | 2 773 114 | `5f2fe9c494d4978e…` |
| `deliverables/DeckForge-AI-presentation.pdf` | **15** | 1 052 201 | `a11646b4ce7a9f13…` |
| `deliverables/DeckForge-AI-presentation-notes.pdf` | **16** | 251 823 | `d9c3275e07293970…` |

**Rebuilding changes every hash** — Chrome embeds a timestamp. If anything is rebuilt before
submission, re-hash and update this table, `docs/evidence/M11/assignment-audit.md` and the session
handoff. **After any report rebuild, run
`.venv\Scripts\python.exe docs\evidence\M11\check_report_leaders.py`** — the build intermittently
drops the table-of-contents dot leaders (findings F1); text, figures and page count are unaffected,
but a short build looks correct to every other check.

## 4. Repository hygiene — verified this session

| check | result |
|---|---|
| secrets scan, 9 patterns, all history | **clean** — no weights or secrets path ever added in any commit |
| tracked size | 14.9 MB across 584 files; only the two PDFs exceed 1 MB |
| ignored trees absent from Git | `outputs/`, `.venv`, `node_modules`, `data/raw`, `__pycache__` |
| markdown links and written paths | **every one resolves**; 7 non-resolving paths each carry a recorded reason |
| dataset manifest vs `facts.yaml` | every count matches |

## 5. Suites — measured 2026-08-15

| suite | count | note |
|---|---:|---|
| pytest | **527** | 473 system + 16 report-validation + 38 deck-validation |
| pytest, clean clone | **522 passed / 5 skipped** | 522 + 5 = 527, matching this machine |
| vitest | **183** | 12 files |
| Playwright E2E | **38** | `retries: 0` |
| eslint · build | clean · succeeds | 608 modules |

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
8. **Do not run GPU inference.** The total is **28** and no further generation is authorised. The
   M11 final-audit validation on 2026-08-15 was the last one Kylian approved.
