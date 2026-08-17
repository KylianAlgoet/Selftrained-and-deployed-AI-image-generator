# DeckForge AI — Second-sit Submission

**Student:** Kylian Algoet
**Programme:** Multimedia & Creative Technologies
**Institution:** Erasmushogeschool Brussel
**Submission date:** 17 August 2026

This file is the index for the five official deliverables. It does not repeat their contents.

---

## 1. Planning

**https://github.com/users/KylianAlgoet/projects/1/views/1**

Public GitHub Project board covering milestones M0–M12 with objectives, acceptance criteria, dates,
priorities, dependencies, evidence and live status. Backed by
[repository issues](https://github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator/issues?q=is%3Aissue).

## 2. Research documentation

**`deliverables/DeckForge-AI-research-report.pdf` — 91 pages, 26 chapters.**

Covers context and assignment, research questions, methodology, planning, architecture research,
model selection and fine-tuning, dataset and licences, prototypes, failed experiments, results, the
integrated MVP, testing, deployment and reproducibility, ethics, limitations, conclusions,
reflection, lessons learned, future work, references, appendices, and D1–D7 traceability.

## 3. Result / source code

**https://github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator**

Public repository; the submitted state is the tip of `origin/main`. The final application is a
validated local GPU deployment, not a publicly hosted web application.

## 4. Prototype documentation

**[README.md — Prototype documentation](https://github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator#readme)**

The root README is the main prototype documentation. It is written for a reader opening the
repository for the first time, and it contains or links to:

- **Images** — tracked screenshots of the 3D viewer prototype (including a controlled inverted-UV
  demonstration showing what an incorrect UV orientation would look like), cross-model comparison
  sheets, checkpoint comparison sheets, the dataset contact sheet, the production interface, and the
  final 3D deck result. Every image is committed to the repository and renders on GitHub.
- **Prototype iterations and intermediate results** — prototypes 0 through 5 in order, each with
  what was tested, what worked, what failed, what was learned, and which decision record followed.
- **Code** — direct links to `apps/api/`, `apps/web/`, `ml/`, `scripts/`, `experiments/`,
  `data/manifests/`, `report/` and `docs/`, each with a description of what it contains.
- **Architecture** — the system design and how the components fit together.
- **Dataset and provenance** — sources, licensing, and what "self-trained" means in this project.
- **Experiment evidence** — the tracked evidence directories for prototypes 0, 1, 2, 4 and 5, the
  M11 submission audit, the M12 demo-rehearsal record, and the experiment registry.
- **Generated-output evidence and failures** — tracked generation results alongside the recorded
  failed attempts.
- **Final MVP, testing, reproducibility and limitations** — the integrated result, the test figures,
  the reproduction steps and setup, and the known limitations.

Generated images live in `outputs/`, which is git-ignored by policy; the tracked evidence
directories linked from the README are therefore the public record.

## 5. Presentation

**`deliverables/DeckForge-AI-presentation.pdf` — 16 pages**, including a dedicated Project Planning
slide.

Speaker notes accompany it as `deliverables/DeckForge-AI-presentation-notes.pdf`.

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
| Lessons learned / reflection | Report ch. 20–23, `docs/09-final-reflection.md` |
| What would be done differently | Report ch. 20–23, `docs/09-final-reflection.md` |
| Next steps | Report ch. 20–23, `docs/09-final-reflection.md` |
| Sources and references | Report ch. 24, appendices ch. 25 |
| D1–D7 | `docs/learning-outcome-traceability.md`, report ch. 26 |

## Project facts

**31** completed real GPU generations · **1** separate failed GPU inference attempt (no completed
image, recorded separately and not counted in the 31) · **148** dataset images across **3** styles ·
**40** experiments · **17** decision records · latest final validation: **528** pytest passed ·
**183** Vitest · **38** Playwright E2E.

---

Live defence: 2 September 2026.
