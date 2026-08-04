# EXP-026 — memorisation and similarity indicators (Phase 2, offline CPU)

108 pilot generations, compared against each style's **training** images and
against the **holdout** images that were never trained on. CLIP encoder loaded on CPU in
0.429s, in its own process after all generation finished, so it enters no
GPU VRAM or latency figure.

## What these numbers are — and are not

`dhash <= 6` is a **coarse near-copy INDICATOR**, kept at the
M4 threshold for continuity. **It is not proof of memorisation** and not a general
memorisation measure: it is sensitive to layout, blind to recolouring, and two flat
geometric compositions can score close for reasons unrelated to training.

**These indicators decide nothing.** They populate no rubric cell, select no checkpoint,
and choose no hyperparameter. Any flagged output is preserved and surfaced for human
inspection, never deleted.

## Per-arm summary

| arm | style | n | median dHash to train | min dHash to train | flagged | median dHash to holdout | median CLIP cos to train |
|---|---|---|---|---|---|---|---|
| `BASE-minimal-geometric` | minimal-geometric | 4 | 23.0 | 22 | **0** | 27.5 | 0.3844 |
| `BASE-retro-poster` | retro-poster | 4 | 23.5 | 22 | **0** | 23.5 | 0.2599 |
| `BASE-ukiyo-e` | ukiyo-e | 4 | 19.0 | 16 | **0** | 25.0 | 0.3855 |
| `EXP-020` | minimal-geometric | 16 | 23.0 | 20 | **0** | 27.0 | 0.6244 |
| `EXP-021` | ukiyo-e | 16 | 20.5 | 17 | **0** | 26.5 | 0.7220 |
| `EXP-022` | retro-poster | 16 | 27.0 | 23 | **0** | 25.5 | 0.3695 |
| `EXP-023` | minimal-geometric | 16 | 22.5 | 18 | **0** | 27.5 | 0.5201 |
| `EXP-024n12` | minimal-geometric | 16 | 22.0 | 19 | **0** | 28.0 | 0.5234 |
| `EXP-024n24` | minimal-geometric | 16 | 22.5 | 19 | **0** | 27.0 | 0.4330 |

**0 of 108 generations carry a near-copy flag.**

The holdout column is the control: those images were never trained on, so a distance
there similar to the training distance suggests the similarity comes from the base model
or the prompt rather than from memorisation.
