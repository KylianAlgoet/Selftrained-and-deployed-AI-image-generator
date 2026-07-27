# Project brief

**Project:** DeckForge AI (working title) · **Student:** Kylian Algoet · **Programme:** Multimedia & Creative Technologies, final bachelor resit assignment · **Created:** 2026-07-27

## Assignment

The client is a skateboard manufacturer. The system must let a customer enter a text prompt, upload a reference image, select a visual style, generate a new skateboard decal with a **self-trained (locally fine-tuned) model**, view the result on an interactive 3D skateboard deck, and download the artwork.

## Mandatory requirements

1. Collect and create a custom training dataset
2. Document dataset provenance and permitted usage
3. Support multiple visual styles (≥ 3 visually distinct)
4. Train or fine-tune the model locally
5. Combine text prompting and a reference image
6. Generate new decal artwork
7. Map it onto a 3D skateboard
8. Provide a reproducible deployment or demonstration setup
9. Maintain a public planning link
10. Provide research documentation as PDF
11. Provide prototype evidence
12. Provide the final GitHub result
13. Provide a presentation as PDF

## Deadlines

| Event | Date |
|---|---|
| Feature freeze | 2026-08-15 |
| Final-content deadline | 2026-08-16 18:00 |
| Submission | 2026-08-17 06:00 (Europe/Brussels) |
| Presentation | 2026-09-02 |

## Learning outcomes (assessed)

| ID | Outcome | Primary evidence location |
|---|---|---|
| D1 | Independent applied research | Research plan, experiments, prototypes |
| D2 | Independent professional functioning | Planning, process log, risk register |
| D3 | Iterative planning and professional methodology | Planning change log, Git history, decision records |
| D4 | Comparison and application of multiple solution methods | Architecture matrices, method comparisons (RQ1/5/6) |
| D5 | Complex problem solving through multiple prototypes and new technologies | Prototypes 0–5 |
| D6 | Justified research conclusions | Experiment registry, rubric evaluations, report |
| D7 | Professional multimedia documentation and presentation | Docs, report PDF, presentation PDF |

Full mapping: `docs/learning-outcome-traceability.md`.

## MVP scope

**Inputs:** prompt, optional negative prompt, PNG/JPG/WEBP reference image, style, reference strength, seed, generate action.
**Generation:** locally trained LoRA (hypothesis, see research plan), text + image conditioning, input validation, loading state, useful errors, reproducibility metadata, deterministic seeds.
**Output:** generated decal, settings, interactive 3D skateboard with dynamic texture update and correct nose–tail orientation, rotate/zoom/reset, download.

## Explicit non-goals

Accounts, payments, social features, a full webshop, native apps, production-scale infrastructure. Any scope addition requires a planning change-log entry (risk R6).
