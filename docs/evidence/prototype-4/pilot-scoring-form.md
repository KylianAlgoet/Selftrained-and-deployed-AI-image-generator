# Prototype 4 — pilot scoring form (BLANK, BLINDED)

**Gate 1.** Score the sheets in `pilot-sheets/`, then open the mapping at
`docs/evidence/EXP-025/BLINDING-MAP-do-not-open-before-scoring.csv`. **Not before** — the mapping is what the
blinding protects.

## What is blinded

Style is visible and cannot be hidden. Everything the comparison is actually about is
hidden: which `GEO-*` sheet uses style-only versus dataset-v1 verbatim captions, which is
the 12-, 24- or 44-image arm, and whether a sheet is the 150- or 300-step checkpoint.
Labels were assigned by a seeded shuffle within each style (seed 20260804), so the
blinding is reproducible from the repository alone.

**One disclosed weakness.** The shuffle happened to place a few same-arm pairs at adjacent
labels, so adjacent numbers *may* be one arm at its two checkpoints. **The seed was fixed
before the draw and has not been re-rolled** — re-drawing until the arrangement looked
better would be exactly the kind of tampering the blinding exists to prevent. This does not
weaken what matters: adjacency reveals nothing about *which* arm a sheet is, so style-only
versus verbatim and 12 versus 24 versus 44 remain fully masked. Treat adjacent labels as
unrelated.

`BASE-*` sheets are the untrained SD 1.5 control on the identical prompt text, and are
deliberately **not** blinded.

## Sheet layout

Every trained sheet holds 8 images in 4 columns, ordered deterministically by
**(prompt, seed, LoRA weight)**:

| cell | prompt | seed | weight |
|---|---|---|---|
| 1 | VP1-style | 42 | 0.7 |
| 2 | VP1-style | 42 | 1.0 |
| 3 | VP1-style | 1337 | 0.7 |
| 4 | VP1-style | 1337 | 1.0 |
| 5 | VP2-shared | 42 | 0.7 |
| 6 | VP2-shared | 42 | 1.0 |
| 7 | VP2-shared | 1337 | 0.7 |
| 8 | VP2-shared | 1337 | 1.0 |

Prompt roles — `VP1-style` is style-matching; `VP2-shared` is the identical subject across
all three styles, so style differences are attributable to the LoRA rather than the prompt.

## Sheets to score

| sheet | style | images |
|---|---|---|
| `BASE-GEO` | minimal-geometric | 4 |
| `BASE-PST` | retro-poster | 4 |
| `BASE-UKY` | ukiyo-e | 4 |
| `GEO-1` | minimal-geometric | 8 |
| `GEO-2` | minimal-geometric | 8 |
| `GEO-3` | minimal-geometric | 8 |
| `GEO-4` | minimal-geometric | 8 |
| `GEO-5` | minimal-geometric | 8 |
| `GEO-6` | minimal-geometric | 8 |
| `GEO-7` | minimal-geometric | 8 |
| `GEO-8` | minimal-geometric | 8 |
| `PST-1` | retro-poster | 8 |
| `PST-2` | retro-poster | 8 |
| `UKY-1` | ukiyo-e | 8 |
| `UKY-2` | ukiyo-e | 8 |

## Rubric (1–5, per `docs/05-experiment-methodology.md`)

| dimension | 1 | 5 |
|---|---|---|
| `prompt_adherence` | ignores prompt | matches all stated elements |
| `style_consistency` | style unrecognizable | unmistakably the target style |
| `visual_quality` | broken/blurry | clean, coherent |
| `decal_suitability` | unusable on a deck | print-ready for a deck |
| `composition` | chaotic/cropped badly | balanced for the deck format |
| `artefacts` | dominant artefacts | none visible |
| `originality` | near-copy of a source | clearly new artwork |
| `diversity_across_seeds` | mode-collapsed | varied yet on-style |
| `copy_or_overfitting_risk` | reproduces training data | clearly independent |

**Leave a cell blank if you did not judge it.** A blank is never a zero and will never be
back-filled — the M3/M4 rule. `reference_influence` is deliberately absent: no reference
image is used anywhere in the pilot matrix.

## Scores

| sheet | `prompt_adherence` | `style_consistency` | `visual_quality` | `decal_suitability` | `composition` | `artefacts` | `originality` | `diversity_across_seeds` | `copy_or_overfitting_risk` |
|---|---|---|---|---|---|---|---|---|---|
| `BASE-GEO` |  |  |  |  |  |  |  |  |  |
| `BASE-PST` |  |  |  |  |  |  |  |  |  |
| `BASE-UKY` |  |  |  |  |  |  |  |  |  |
| `GEO-1` |  |  |  |  |  |  |  |  |  |
| `GEO-2` |  |  |  |  |  |  |  |  |  |
| `GEO-3` |  |  |  |  |  |  |  |  |  |
| `GEO-4` |  |  |  |  |  |  |  |  |  |
| `GEO-5` |  |  |  |  |  |  |  |  |  |
| `GEO-6` |  |  |  |  |  |  |  |  |  |
| `GEO-7` |  |  |  |  |  |  |  |  |  |
| `GEO-8` |  |  |  |  |  |  |  |  |  |
| `PST-1` |  |  |  |  |  |  |  |  |  |
| `PST-2` |  |  |  |  |  |  |  |  |  |
| `UKY-1` |  |  |  |  |  |  |  |  |  |
| `UKY-2` |  |  |  |  |  |  |  |  |  |

## Failure-mode probe

Mark `worse`, `same`, `better` or leave blank, against the `BASE-*` control for that style.

| sheet | `pseudo_text` | `unwanted_frame` | `background_transfer` | `repeated_motifs` | `vertical_stretching` |
|---|---|---|---|---|---|
| `GEO-1` |  |  |  |  |  |
| `GEO-2` |  |  |  |  |  |
| `GEO-3` |  |  |  |  |  |
| `GEO-4` |  |  |  |  |  |
| `GEO-5` |  |  |  |  |  |
| `GEO-6` |  |  |  |  |  |
| `GEO-7` |  |  |  |  |  |
| `GEO-8` |  |  |  |  |  |
| `PST-1` |  |  |  |  |  |
| `PST-2` |  |  |  |  |  |
| `UKY-1` |  |  |  |  |  |
| `UKY-2` |  |  |  |  |  |

## Decisions this gate needs from you

These are the decisions Phase B cannot start without. None of them has been made for you.

1. **Checkpoint per style** — 150 or 300 steps, for each of the three styles.
2. **Full-run step count per style** — within the pre-declared band 600–1500.
3. **Caption strategy verdict** — style-only preferred / verbatim preferred / trade-off /
   tie-inconclusive, per the rules in the approved plan.
4. **Dataset-size verdict** — which of O1 monotone, O2 plateau, O3 no effect,
   O4 trade-off, O5 inconclusive the 12/24/44 arms support.
5. **Contingency** — whether any contingency run is authorised, and if so which SINGLE
   variable it may change (LR, rank/alpha, steps, or caption dropout).
6. **Multi-style** — whether the balanced multi-style run proceeds.

## Not decided, and not decidable from this package

- No style has been selected, and no arm is described as better than another.
- No visual-quality claim is made anywhere in Phase A.
- The automated indicators in `docs/evidence/EXP-026/` are descriptive only. They populate
  no cell above, and they may not select a checkpoint or a hyperparameter.
