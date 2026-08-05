# EXP-033 — final-matrix indicators (Phase 2, offline CPU)

252 generations from the EXP-031 final validation matrix, compared against
each style's **training** images and against the **holdout** images that were never
trained on. CLIP encoder loaded on CPU in 0.187s, in its own process
after all generation finished, so it enters no GPU VRAM or latency figure.

## What these numbers are — and are not

`dhash <= 6` is a **coarse near-copy INDICATOR**, kept at the
M4 threshold for continuity. **It is not proof of memorisation** and not a general
memorisation measure: it is sensitive to layout, blind to recolouring, and two flat
geometric compositions can score close for reasons unrelated to training.

**These indicators decide nothing.** They populate no rubric cell, select no checkpoint,
style or hyperparameter, and are not a quality ranking. Any flagged output is preserved
and surfaced for human inspection, never deleted.

## Per-arm summary

| arm@step/geometry | style | n | median dHash to train | min | flagged | median dHash to holdout | median CLIP cos |
|---|---|---:|---:|---:|---:|---:|---:|
| `BASE@0/512x1536` | minimal-geometric,retro-poster,ukiyo-e | 6 | 20.5 | 13 | **0** | 26.5 | 0.4066 |
| `BASE@0/512x512` | minimal-geometric,retro-poster,ukiyo-e | 24 | 22.5 | 16 | **0** | 24.5 | 0.2961 |
| `EXP-027@300/512x1536` | minimal-geometric | 4 | 21.5 | 21 | **0** | 25.5 | 0.5979 |
| `EXP-027@300/512x512` | minimal-geometric | 28 | 23.0 | 18 | **0** | 28.0 | 0.5265 |
| `EXP-027@600/512x1536` | minimal-geometric | 4 | 21.0 | 18 | **0** | 26.5 | 0.6471 |
| `EXP-027@600/512x512` | minimal-geometric | 28 | 23.0 | 17 | **0** | 27.0 | 0.6175 |
| `EXP-028@300/512x1536` | ukiyo-e | 4 | 19.5 | 17 | **0** | 23.0 | 0.6139 |
| `EXP-028@300/512x512` | ukiyo-e | 28 | 20.5 | 15 | **0** | 26.0 | 0.6385 |
| `EXP-028@600/512x1536` | ukiyo-e | 4 | 19.5 | 16 | **0** | 26.0 | 0.7026 |
| `EXP-028@600/512x512` | ukiyo-e | 28 | 20.0 | 16 | **0** | 26.0 | 0.7003 |
| `EXP-029@300/512x1536` | retro-poster | 4 | 27.5 | 23 | **0** | 23.5 | 0.4121 |
| `EXP-029@300/512x512` | retro-poster | 28 | 25.0 | 18 | **0** | 26.0 | 0.3222 |
| `EXP-029@600/512x1536` | retro-poster | 4 | 21.0 | 18 | **0** | 26.5 | 0.3676 |
| `EXP-029@600/512x512` | retro-poster | 28 | 25.0 | 13 | **0** | 26.0 | 0.3356 |
| `EXP-030@1800/512x512` | minimal-geometric,retro-poster,ukiyo-e | 30 | 24.0 | 19 | **0** | 26.5 | 0.5068 |

**0 of 252 generations carry a near-copy flag.**

The holdout column is the control: those images were never trained on, so a distance
there similar to the training distance suggests the similarity comes from the base model
or the prompt rather than from memorisation.

## Diversity across seeds

Mean pairwise CLIP distance between generations that differ **only** in seed. A low
number means the cell produces near-identical images regardless of seed. It is
descriptive: what counts as too low is a human judgement at Gate 2.

| arm@step | style | prompt | weight | geometry | seeds | mean pairwise distance | min |
|---|---|---|---:|---|---:|---:|---:|
| `BASE@0` | minimal-geometric | FP1-style | None | 512x1536 | 2 | 0.3835 | 0.3835 |
| `BASE@0` | minimal-geometric | FP1-style | None | 512x512 | 2 | 0.4890 | 0.4890 |
| `BASE@0` | minimal-geometric | FP2-shared | None | 512x512 | 2 | 0.4835 | 0.4835 |
| `BASE@0` | minimal-geometric | FP3-out-of-style | None | 512x512 | 2 | 0.4560 | 0.4560 |
| `BASE@0` | minimal-geometric | FP4-style-free | None | 512x512 | 2 | 0.3611 | 0.3611 |
| `BASE@0` | retro-poster | FP1-style | None | 512x1536 | 2 | 0.4145 | 0.4145 |
| `BASE@0` | retro-poster | FP1-style | None | 512x512 | 2 | 0.3947 | 0.3947 |
| `BASE@0` | retro-poster | FP2-shared | None | 512x512 | 2 | 0.5308 | 0.5308 |
| `BASE@0` | retro-poster | FP3-out-of-style | None | 512x512 | 2 | 0.4655 | 0.4655 |
| `BASE@0` | retro-poster | FP4-style-free | None | 512x512 | 2 | 0.3611 | 0.3611 |
| `BASE@0` | ukiyo-e | FP1-style | None | 512x1536 | 2 | 0.3780 | 0.3780 |
| `BASE@0` | ukiyo-e | FP1-style | None | 512x512 | 2 | 0.4988 | 0.4988 |
| `BASE@0` | ukiyo-e | FP2-shared | None | 512x512 | 2 | 0.4612 | 0.4612 |
| `BASE@0` | ukiyo-e | FP3-out-of-style | None | 512x512 | 2 | 0.3397 | 0.3397 |
| `BASE@0` | ukiyo-e | FP4-style-free | None | 512x512 | 2 | 0.3611 | 0.3611 |
| `EXP-027@300` | minimal-geometric | FP1-style | 0.0 | 512x512 | 2 | 0.4890 | 0.4890 |
| `EXP-027@300` | minimal-geometric | FP1-style | 0.4 | 512x512 | 2 | 0.6152 | 0.6152 |
| `EXP-027@300` | minimal-geometric | FP1-style | 0.7 | 512x1536 | 2 | 0.3250 | 0.3250 |
| `EXP-027@300` | minimal-geometric | FP1-style | 0.7 | 512x512 | 3 | 0.4067 | 0.3874 |
| `EXP-027@300` | minimal-geometric | FP1-style | 1.0 | 512x1536 | 2 | 0.3377 | 0.3377 |
| `EXP-027@300` | minimal-geometric | FP1-style | 1.0 | 512x512 | 2 | 0.3591 | 0.3591 |
| `EXP-027@300` | minimal-geometric | FP2-shared | 0.0 | 512x512 | 2 | 0.4835 | 0.4835 |
| `EXP-027@300` | minimal-geometric | FP2-shared | 0.4 | 512x512 | 2 | 0.4170 | 0.4170 |
| `EXP-027@300` | minimal-geometric | FP2-shared | 0.7 | 512x512 | 3 | 0.4715 | 0.3010 |
| `EXP-027@300` | minimal-geometric | FP2-shared | 1.0 | 512x512 | 2 | 0.2278 | 0.2278 |
| `EXP-027@300` | minimal-geometric | FP3-out-of-style | 0.7 | 512x512 | 3 | 0.4722 | 0.3877 |
| `EXP-027@300` | minimal-geometric | FP4-style-free | 0.7 | 512x512 | 3 | 0.5055 | 0.4404 |
| `EXP-027@600` | minimal-geometric | FP1-style | 0.0 | 512x512 | 2 | 0.4890 | 0.4890 |
| `EXP-027@600` | minimal-geometric | FP1-style | 0.4 | 512x512 | 2 | 0.4066 | 0.4066 |
| `EXP-027@600` | minimal-geometric | FP1-style | 0.7 | 512x1536 | 2 | 0.2820 | 0.2820 |
| `EXP-027@600` | minimal-geometric | FP1-style | 0.7 | 512x512 | 3 | 0.3967 | 0.3650 |
| `EXP-027@600` | minimal-geometric | FP1-style | 1.0 | 512x1536 | 2 | 0.3258 | 0.3258 |
| `EXP-027@600` | minimal-geometric | FP1-style | 1.0 | 512x512 | 2 | 0.4175 | 0.4175 |
| `EXP-027@600` | minimal-geometric | FP2-shared | 0.0 | 512x512 | 2 | 0.4835 | 0.4835 |
| `EXP-027@600` | minimal-geometric | FP2-shared | 0.4 | 512x512 | 2 | 0.4396 | 0.4396 |
| `EXP-027@600` | minimal-geometric | FP2-shared | 0.7 | 512x512 | 3 | 0.4427 | 0.3875 |
| `EXP-027@600` | minimal-geometric | FP2-shared | 1.0 | 512x512 | 2 | 0.3739 | 0.3739 |
| `EXP-027@600` | minimal-geometric | FP3-out-of-style | 0.7 | 512x512 | 3 | 0.3314 | 0.3106 |
| `EXP-027@600` | minimal-geometric | FP4-style-free | 0.7 | 512x512 | 3 | 0.4130 | 0.3278 |
| `EXP-028@300` | ukiyo-e | FP1-style | 0.0 | 512x512 | 2 | 0.4988 | 0.4988 |
| `EXP-028@300` | ukiyo-e | FP1-style | 0.4 | 512x512 | 2 | 0.1916 | 0.1916 |
| `EXP-028@300` | ukiyo-e | FP1-style | 0.7 | 512x1536 | 2 | 0.1049 | 0.1049 |
| `EXP-028@300` | ukiyo-e | FP1-style | 0.7 | 512x512 | 3 | 0.3038 | 0.1249 |
| `EXP-028@300` | ukiyo-e | FP1-style | 1.0 | 512x1536 | 2 | 0.1281 | 0.1281 |
| `EXP-028@300` | ukiyo-e | FP1-style | 1.0 | 512x512 | 2 | 0.2246 | 0.2246 |
| `EXP-028@300` | ukiyo-e | FP2-shared | 0.0 | 512x512 | 2 | 0.4612 | 0.4612 |
| `EXP-028@300` | ukiyo-e | FP2-shared | 0.4 | 512x512 | 2 | 0.4649 | 0.4649 |
| `EXP-028@300` | ukiyo-e | FP2-shared | 0.7 | 512x512 | 3 | 0.3432 | 0.2159 |
| `EXP-028@300` | ukiyo-e | FP2-shared | 1.0 | 512x512 | 2 | 0.1756 | 0.1756 |
| `EXP-028@300` | ukiyo-e | FP3-out-of-style | 0.7 | 512x512 | 3 | 0.3994 | 0.3223 |
| `EXP-028@300` | ukiyo-e | FP4-style-free | 0.7 | 512x512 | 3 | 0.4681 | 0.4536 |
| `EXP-028@600` | ukiyo-e | FP1-style | 0.0 | 512x512 | 2 | 0.4988 | 0.4988 |
| `EXP-028@600` | ukiyo-e | FP1-style | 0.4 | 512x512 | 2 | 0.2520 | 0.2520 |
| `EXP-028@600` | ukiyo-e | FP1-style | 0.7 | 512x1536 | 2 | 0.2175 | 0.2175 |
| `EXP-028@600` | ukiyo-e | FP1-style | 0.7 | 512x512 | 3 | 0.4379 | 0.1738 |
| `EXP-028@600` | ukiyo-e | FP1-style | 1.0 | 512x1536 | 2 | 0.1261 | 0.1261 |
| `EXP-028@600` | ukiyo-e | FP1-style | 1.0 | 512x512 | 2 | 0.1799 | 0.1799 |
| `EXP-028@600` | ukiyo-e | FP2-shared | 0.0 | 512x512 | 2 | 0.4612 | 0.4612 |
| `EXP-028@600` | ukiyo-e | FP2-shared | 0.4 | 512x512 | 2 | 0.4116 | 0.4116 |
| `EXP-028@600` | ukiyo-e | FP2-shared | 0.7 | 512x512 | 3 | 0.3170 | 0.1747 |
| `EXP-028@600` | ukiyo-e | FP2-shared | 1.0 | 512x512 | 2 | 0.2582 | 0.2582 |
| `EXP-028@600` | ukiyo-e | FP3-out-of-style | 0.7 | 512x512 | 3 | 0.3209 | 0.2656 |
| `EXP-028@600` | ukiyo-e | FP4-style-free | 0.7 | 512x512 | 3 | 0.5001 | 0.4885 |
| `EXP-029@300` | retro-poster | FP1-style | 0.0 | 512x512 | 2 | 0.3947 | 0.3947 |
| `EXP-029@300` | retro-poster | FP1-style | 0.4 | 512x512 | 2 | 0.3595 | 0.3595 |
| `EXP-029@300` | retro-poster | FP1-style | 0.7 | 512x1536 | 2 | 0.2565 | 0.2565 |
| `EXP-029@300` | retro-poster | FP1-style | 0.7 | 512x512 | 3 | 0.5416 | 0.4718 |
| `EXP-029@300` | retro-poster | FP1-style | 1.0 | 512x1536 | 2 | 0.3819 | 0.3819 |
| `EXP-029@300` | retro-poster | FP1-style | 1.0 | 512x512 | 2 | 0.3797 | 0.3797 |
| `EXP-029@300` | retro-poster | FP2-shared | 0.0 | 512x512 | 2 | 0.5308 | 0.5308 |
| `EXP-029@300` | retro-poster | FP2-shared | 0.4 | 512x512 | 2 | 0.6313 | 0.6313 |
| `EXP-029@300` | retro-poster | FP2-shared | 0.7 | 512x512 | 3 | 0.5611 | 0.4315 |
| `EXP-029@300` | retro-poster | FP2-shared | 1.0 | 512x512 | 2 | 0.6460 | 0.6460 |
| `EXP-029@300` | retro-poster | FP3-out-of-style | 0.7 | 512x512 | 3 | 0.4577 | 0.3078 |
| `EXP-029@300` | retro-poster | FP4-style-free | 0.7 | 512x512 | 3 | 0.5417 | 0.4853 |
| `EXP-029@600` | retro-poster | FP1-style | 0.0 | 512x512 | 2 | 0.3947 | 0.3947 |
| `EXP-029@600` | retro-poster | FP1-style | 0.4 | 512x512 | 2 | 0.4635 | 0.4635 |
| `EXP-029@600` | retro-poster | FP1-style | 0.7 | 512x1536 | 2 | 0.2859 | 0.2859 |
| `EXP-029@600` | retro-poster | FP1-style | 0.7 | 512x512 | 3 | 0.4626 | 0.4151 |
| `EXP-029@600` | retro-poster | FP1-style | 1.0 | 512x1536 | 2 | 0.2854 | 0.2854 |
| `EXP-029@600` | retro-poster | FP1-style | 1.0 | 512x512 | 2 | 0.5209 | 0.5209 |
| `EXP-029@600` | retro-poster | FP2-shared | 0.0 | 512x512 | 2 | 0.5308 | 0.5308 |
| `EXP-029@600` | retro-poster | FP2-shared | 0.4 | 512x512 | 2 | 0.6885 | 0.6885 |
| `EXP-029@600` | retro-poster | FP2-shared | 0.7 | 512x512 | 3 | 0.5709 | 0.5311 |
| `EXP-029@600` | retro-poster | FP2-shared | 1.0 | 512x512 | 2 | 0.4956 | 0.4956 |
| `EXP-029@600` | retro-poster | FP3-out-of-style | 0.7 | 512x512 | 3 | 0.3766 | 0.3518 |
| `EXP-029@600` | retro-poster | FP4-style-free | 0.7 | 512x512 | 3 | 0.4773 | 0.4592 |
| `EXP-030@1800` | minimal-geometric | FP1-style | 0.0 | 512x512 | 2 | 0.4890 | 0.4890 |
| `EXP-030@1800` | minimal-geometric | FP1-style | 0.4 | 512x512 | 2 | 0.6295 | 0.6295 |
| `EXP-030@1800` | minimal-geometric | FP1-style | 0.7 | 512x512 | 2 | 0.3861 | 0.3861 |
| `EXP-030@1800` | minimal-geometric | FP1-style | 1.0 | 512x512 | 2 | 0.2769 | 0.2769 |
| `EXP-030@1800` | minimal-geometric | FP2-shared | 1.0 | 512x512 | 2 | 0.3024 | 0.3024 |
| `EXP-030@1800` | retro-poster | FP1-style | 0.0 | 512x512 | 2 | 0.3947 | 0.3947 |
| `EXP-030@1800` | retro-poster | FP1-style | 0.4 | 512x512 | 2 | 0.4603 | 0.4603 |
| `EXP-030@1800` | retro-poster | FP1-style | 0.7 | 512x512 | 2 | 0.4407 | 0.4407 |
| `EXP-030@1800` | retro-poster | FP1-style | 1.0 | 512x512 | 2 | 0.5583 | 0.5583 |
| `EXP-030@1800` | retro-poster | FP2-shared | 1.0 | 512x512 | 2 | 0.4830 | 0.4830 |
| `EXP-030@1800` | ukiyo-e | FP1-style | 0.0 | 512x512 | 2 | 0.4988 | 0.4988 |
| `EXP-030@1800` | ukiyo-e | FP1-style | 0.4 | 512x512 | 2 | 0.2062 | 0.2062 |
| `EXP-030@1800` | ukiyo-e | FP1-style | 0.7 | 512x512 | 2 | 0.2007 | 0.2007 |
| `EXP-030@1800` | ukiyo-e | FP1-style | 1.0 | 512x512 | 2 | 0.2046 | 0.2046 |
| `EXP-030@1800` | ukiyo-e | FP2-shared | 1.0 | 512x512 | 2 | 0.2356 | 0.2356 |
