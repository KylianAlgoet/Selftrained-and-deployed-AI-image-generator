# Prototype 1 evaluation rubric (1-5 per dimension)

Copied from `docs/05-experiment-methodology.md` so this form is self-contained.
Score each dimension 1-5 using the anchors below. Scores are the student's;
they are never estimated or filled in by the assistant.

| dimension | 1 | 5 | applies in Prototype 1? |
|---|---|---|---|
| prompt_adherence | ignores prompt | matches all stated elements | yes |
| style_consistency | style unrecognizable | unmistakably the target style | yes |
| reference_influence | no visible relation to reference | clear, controllable influence | no - no reference image until Prototype 2 |
| visual_quality | broken/blurry | clean, coherent | yes |
| decal_suitability | unusable on a deck | print-ready composition for a deck | yes |
| composition | chaotic/cropped badly | balanced for the deck format | yes |
| artefacts | dominant artefacts | none visible | yes |
| originality | near-copy of a source | clearly new artwork | yes |
| diversity_across_seeds | mode-collapsed | varied yet on-style | yes |

## How to score

1. Open the Track A cross-model sheet: all candidates at 512x512, same prompts, same seed.
   This is the controlled comparison - use it for like-for-like judgement.
2. Open the Track B cross-model sheet: each candidate at the resolution it was
   designed for. Use this for quality judgement, so SDXL is not penalised for a
   size it was never built for.
3. For each row in `scoring-form.md`, view the fixed-seed group listed in `images`
   and enter one score per dimension.
4. `diversity_across_seeds` is judged across the seed group as a whole, not per image.

Track A and Track B scores are reported separately in DR-007 and must not be averaged
together - the trade-off between them is the actual finding.
