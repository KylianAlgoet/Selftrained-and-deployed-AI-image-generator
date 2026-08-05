# Experiment methodology

**Created:** 2026-07-27 · Answers RQ10; governs all experiments from Prototype 1 onward.

## Registry

All experiments live in `experiments/registry.csv` with IDs `EXP-001`, `EXP-002`, … Fields: `id, date, prototype, research_question, hypothesis, dataset_version, model, config, rank, learning_rate, steps, batch_size, grad_accum, resolution, seed, gpu, peak_vram, duration, output_path, evaluation, conclusion, next_action, commit`.

Rules:
- A row is created when the experiment **runs**, never retroactively invented.
- `peak_vram` and `duration` are measured (`nvidia-smi`, timestamps), not estimated; unmeasured = "not measured".
- `commit` links the experiment to the code/config state that produced it.
- Failed experiments get rows too, with the failure documented per `.claude/rules/honesty-and-evidence.md`.

## Fixed-comparison protocol

Comparisons vary **one factor at a time** against a frozen kit:
- Fixed prompt set (defined at Prototype 1, reused verbatim afterwards)
- Fixed reference images (defined at Prototype 2)
- Fixed seeds (e.g. 42, 1337, 2026 — final set frozen at Prototype 1)
- Fixed resolution and sampler settings per comparison

## Evaluation rubric (1–5 per dimension)

| Dimension | 1 | 5 |
|---|---|---|
| Prompt adherence | ignores prompt | matches all stated elements |
| Style consistency | style unrecognizable | unmistakably the target style |
| Reference influence | no visible relation to reference | clear, controllable influence |
| Visual quality | broken/blurry | clean, coherent |
| Decal suitability | unusable on a deck | print-ready composition for a deck |
| Composition | chaotic/cropped badly | balanced for the deck format |
| Artefacts | dominant artefacts | none visible |
| Originality | near-copy of a source | clearly new artwork |
| Diversity (across seeds) | mode-collapsed | varied yet on-style |

Scores are recorded per output grid in the experiment's evidence folder; the registry stores the summary. Scoring is done by the student; the rubric's fixed anchors and fixed-seed grids limit (but do not eliminate) subjectivity — this limitation is reported honestly (risk R9).

## Evidence

Each experiment stores under `docs/evidence/EXP-###/` (or the prototype folder): the exact config, output images/grids, relevant logs, and `nvidia-smi` readings. Reports may only cite conclusions that trace to these artifacts.

## Two-gate human review (established in M6)

Prototype 4 used **two** human review gates rather than one, and they ask different questions,
which changes how each is run:

| | Gate 1 (pilots) | Gate 2 (production selection) |
|---|---|---|
| question | which configuration to take forward | which checkpoint ships |
| sheets | **blinded** within style | **labelled** |
| why | the arms differed in one hidden variable each (captions, set size, step count), so the label would have leaked the answer | the question cannot be answered without knowing which checkpoint a sheet is |
| known cost | none beyond the reduced context | **labelled sheets carry an expectation effect that blinded ones do not**, and this is stated rather than left implicit |

**Both gates hash the completed score file.** The Gate-1 hash was supplied *before* the blinding
map was opened; both hashes are asserted by pytest and both files are pinned in `.gitattributes`
so line-ending normalisation cannot alter them. This makes "no score was edited after the fact"
a check rather than a promise.

**A blank is never a zero** and is never back-filled. **Automated indicators populate no rubric
cell and may not select a checkpoint, weight, style or verdict** - they live in separate files
from human judgement.
