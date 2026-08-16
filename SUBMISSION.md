# DeckForge AI — Second-sit Submission

**Student:** Kylian Algoet
**Course:** Multimedia & Creative Technologies, Erasmushogeschool Brussel
**Submitted:** 2026-08-17

This file is the index for the five official deliverables. It does not repeat their contents.

---

## 1. Planning

**https://github.com/users/KylianAlgoet/projects/1**

Public GitHub Project board covering milestones M0–M12 with objectives, acceptance criteria, dates,
priorities, dependencies, evidence and live status. Backed by
[repository issues](https://github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator/issues?q=is%3Aissue).
Verified reachable (HTTP 200) on 2026-08-16.

## 2. Research documentation

**`deliverables/DeckForge-AI-research-report.pdf`**

| | |
|---|---|
| Pages | **91** |
| Size | 2 773 108 bytes |
| SHA-256 | `b02c37bd724d8f8cd90fadefa9850f8c7b01f3f7554471795fbeaa16dda889b9` |

26 chapters covering context and assignment, research questions, methodology, planning,
architecture research, model selection and fine-tuning, dataset and licences, prototypes, failed
experiments, results, the integrated MVP, testing, deployment and reproducibility, ethics,
limitations, conclusions, reflection, lessons learned, future work, references, appendices, and
D1–D7 traceability.

## 3. Result / source code

**https://github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator**

Public repository. Verified reachable (HTTP 200) on 2026-08-16. The submitted state is the tip of
`origin/main`; the submission baseline is pinned by artifact hashes in
[`docs/submission-checklist.md`](docs/submission-checklist.md) §7.

## 4. Prototype documentation

**[`README.md`](README.md) — the root README of the GitHub repository.**

The README is the main prototype documentation. It is written for a reader opening the repository
for the first time, and it provides directly:

- **Images** — tracked screenshots of the 3D viewer prototype (including its inverted-UV failure),
  cross-model comparison sheets, checkpoint comparison sheets, the dataset contact sheet, the
  production interface, and the final 3D deck result. Every image is committed to the repository and
  renders on GitHub.
- **Code** — direct links to `apps/api/`, `apps/web/`, `ml/`, `scripts/`, `experiments/`,
  `data/manifests/`, `report/` and `docs/`, each with a description of what it contains.
- **Outputs and evidence** — links to the tracked evidence directories for prototypes 0, 1, 2, 4
  and 5, the M11 submission audit, the M12 demo-rehearsal record, and the experiment registry.
- **Prototype iterations** — prototypes 0 through 5 in order, each with what was tested, what
  worked, what failed, what was learned, and which decision record followed.

It also covers the research goal, dataset provenance and licensing, what "self-trained" means in
this project, the architecture, testing figures, reproducibility, known limitations, and setup.

Generated images live in `outputs/`, which is git-ignored by policy; the tracked evidence
directories linked from the README are therefore the public record.

## 5. Presentation

**`deliverables/DeckForge-AI-presentation.pdf`**

| | |
|---|---|
| Pages | **15** |
| Size | 1 052 201 bytes |
| SHA-256 | `a11646b4ce7a9f13955ba378a69b03828063cbf9d444377d889d8a1600846471` |

Speaker notes accompany it as `deliverables/DeckForge-AI-presentation-notes.pdf`
(16 pages · 251 823 bytes · `d9c3275e07293970ed1f6fcf82503bff767b469a275e5c8166bbf32d4094ce54`).

---

## Assessment coverage

| assessed element | where it is |
|---|---|
| Process overview | README §4, `docs/process/process-log.md`, report ch. 6–7 |
| Research | Report ch. 5–13, `docs/01-research-plan.md`, `experiments/registry.csv` |
| Planning | Public board above, `docs/02-planning.md`, report ch. 7 |
| Intermediate results | README §4, `docs/evidence/prototype-0…5/`, report ch. 11 |
| Approach and decisions | 17 records in `docs/decisions/`, report ch. 8–10 |
| Final result | README §3, `docs/evidence/prototype-5/`, report ch. 14 |
| Lessons learned / reflection / next steps | Report ch. 20–23, `docs/09-final-reflection.md` |
| Sources and references | Report ch. 24, appendices ch. 25 |
| D1–D7 | `docs/learning-outcome-traceability.md`, report ch. 26 |

## Project facts

**31** completed real GPU generations · **1** failed GPU inference attempt (driver crash, no image
produced, recorded separately) · **148** dataset images across 3 styles · **40** experiments ·
**17** decision records · **527** pytest · **183** vitest · **38** Playwright E2E.
