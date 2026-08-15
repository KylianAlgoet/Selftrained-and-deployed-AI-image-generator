# M11 — official assignment audit

**Date:** 2026-08-15 · **Source of requirements:** `docs/00-project-brief.md`
**Method:** each requirement checked against repository evidence that was opened, run or measured
during this audit. Compliance is **not** inferred from a similar feature existing.

## Mandatory requirements

| # | requirement | status | repository evidence | report | presentation | blocker |
|---:|---|---|---|---|---|---|
| 1 | Collect and create a custom training dataset | **PASS** | `data/manifests/dataset-v1.csv` — **148 rows** re-derived this session; ukiyo-e 55 / minimal-geometric 52 / retro-poster 41; `docs/evidence/dataset-v1/` | §10 | slide 4 | — |
| 2 | Document dataset provenance and permitted usage | **PASS** | every row carries `source`, `licence`, `collection_date`, `permitted_use`, `sha256`; licences CC0 55 / public domain 41 / project-original 52; no unknown or restrictive licence; `DR-006` | §10.2 | slide 4 | — |
| 3 | Support multiple visual styles (≥ 3 visually distinct) | **PASS**, one qualified | three adapters served live from the clean clone: `minimal-geometric` (EXP-027 s300), `ukiyo-e` (EXP-028 s600), `retro-poster` (EXP-029 s300). `GET /api/styles` returns `retro-poster` as **`"outcome": "PARTIAL PASS"`** with its limitation in the payload | §13.3 | slide 7 | — |
| 4 | Train or fine-tune the model locally | **PASS** | 10 training runs on the audited RTX 4060; `experiments/registry.csv`; `DR-009` selects LoRA on **measured feasibility** and explicitly does not claim superiority over the four methods never run | §9.2 | slide 7 | — |
| 5 | Combine text prompting and a reference image | **PASS** | IP-Adapter at scale 0.55 (`DR-008`), chosen over tested img2img because img2img produced every near-copy flag at the deck geometry; bounds enforced in `apps/api/schemas.py` and asserted by E2E | §13.4 | slide 6 | — |
| 6 | Generate new decal artwork | **PASS** | **27** real GPU generations (25 research + 1 M7 review + 1 M8 deployment validation); `docs/evidence/prototype-5/`, `EXP-031`, `EXP-033` | §13 | slide 9 | — |
| 7 | Map it onto a 3D skateboard | **PASS** | `apps/web/src/viewer/`, `src/deck/`; `DR-005` geometry, `DR-012` texture fit; 38 Playwright scenarios exercise a live WebGL context, texture swap and camera preservation | §14.4 | slide 9 | — |
| 8 | Provide a reproducible deployment or demonstration setup | **PASS** | `docs/deployment/runbook.md` + `weights-manifest.md`; **M11 clean clone re-run today**: fresh venv, `npm ci`, documented restore, 3/3 adapters SHA-256 verified, backend serving, built frontend serving, 522 passed / 5 skipped | §16 | slide 12 | one **environmental** item: `preflight.ps1` needs port 8000 free (Docker Desktop holds it) |
| 9 | Maintain a public planning link | **PASS** | `https://github.com/users/KylianAlgoet/projects/1` — **HTTP 200 verified this session**; mirrors M0–M11 as issues #1–#12 | §7 | — | — |
| 10 | Provide research documentation as PDF | **PASS** | `deliverables/DeckForge-AI-research-report.pdf` — **91 pages**, 2 772 732 B, `3d439a5e…`; validated: no blank page, no raw markup, 9 embedded fonts, uniform A4 | — | slide 2 | two stale sentences, below |
| 11 | Provide prototype evidence | **PASS** | `docs/prototypes/prototype-0…5.md` and `docs/evidence/` — 35 EXP folders plus per-prototype evidence; none skipped | §11 | slide 3 | — |
| 12 | Provide the final GitHub result | **PARTIAL** | the repository is complete and clean locally at `6bde9dc`; **`origin/main` is 19 commits behind** | §26.2 | — | **the push has not happened** — see below |
| 13 | Provide a presentation as PDF | **PARTIAL** | `deliverables/DeckForge-AI-presentation.pdf` — **15 pages**, 960×540 pt, 1 052 201 B, `a11646b4…`; notes handout 16 pages. Validator: 0 hard failures, 0 advisories | §26.2 | itself | **no human visual gate, no rehearsal** — every timing figure is an estimate |

**11 of 13 PASS. 2 PARTIAL, and neither is a defect in the work:**

- **#12** needs a `git push`. That is a deliberate protocol decision, not an omission — remote
  operations are shown before they are taken, and 19 commits are waiting.
- **#13** needs two things only a human can do: look at the slides, and speak them against a clock.
  The report already refuses to call this met (§26.2: *"'Built' is therefore not 'met', and this row
  says so"*).

## Requirement 12 in detail

```
$ git rev-list --left-right --count origin/main...HEAD
0       19
```

Zero behind, **19 ahead**. Everything the assignment asks to be "the final GitHub result" exists in
Git and is committed; none of it has been published. Until it is pushed, an evaluator visiting the
repository sees the state as of M9, without: the 15-slide deck, both presentation PDFs, DR-016,
DR-017, the M10 evidence, and this audit.

**This is the single highest-impact open item in the submission.**

## Requirement 13 in detail

The deck's own timing check, run today with the project's own `note_seconds`:

| figure | value | bound |
|---|---:|---|
| narration | **854 s = 14:13** | band 825–855 s |
| combined (+ 4:00 demo) | **1 094 s = 18:13** | slot 1 200 s |
| buffer | **106 s = 1:46** | minimum 105 s |

Every figure is an **estimate from speaker-note word counts at an assumed 130 wpm**. No rehearsal
has been run, so none of these is a measured delivery time. The buffer clears its own hard minimum
by **one second**, which is worth knowing before the deck is edited again.

## Explicit non-goals — confirmed still out of scope

Accounts, payments, social features, a webshop, native apps and production-scale infrastructure are
absent, as `docs/00-project-brief.md` requires. No scope addition was found that lacks a
planning change-log entry.
