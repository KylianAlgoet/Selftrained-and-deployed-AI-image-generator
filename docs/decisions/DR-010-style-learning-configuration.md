# DR-010 — Style-learning configuration for Prototype 5

**Status:** **DRAFT — NO CONCLUSION.** This record may not be finalised until Kylian
completes Gate 2. · **Date opened:** 2026-08-04 · **Milestone:** M6 (Prototype 4)
**Answers:** RQ4 — *how many images, and what caption standards, does style learning need?*
and RQ5 — *one multi-style LoRA, or separate per-style LoRAs?*
**Related:** DR-006 (dataset styles), DR-007 (base model), DR-008 (reference conditioning),
DR-009 (fine-tuning method)

> **Why this record has no decision section yet.** Every remaining question in it is a
> visual-quality judgement, and no visual-quality claim is made anywhere in Prototype 4.
> The automated indicators in `docs/evidence/EXP-026/` and `docs/evidence/EXP-033/` are
> descriptive; they populate no rubric cell and may not select a checkpoint, style or
> hyperparameter. The M4 and M5 precedent applies: the conclusion is written **after** the
> human gate, from the human's scores, or not at all.

## Context

DR-009 established that a rank-8 UNet-attention LoRA trains, saves, reloads and measurably
changes generation on 8 GB of VRAM at memory tier 0. It answered a **technical** question and
deliberately made no style-quality claim. Prototype 4 is where the style questions are asked.

Three styles are in scope, in a fixed order set by risk (`ml/training/style_kit.py`):
`minimal-geometric` → `ukiyo-e` → `retro-poster`.

## What was decided before any GPU work, and why

### Trigger tokens — one unique token per style

A shared project token cannot separate styles inside a multi-style LoRA, which would make
RQ5 unanswerable. One token per style makes the token the selector.

The first candidate family was **rejected on measured tokenizer evidence, not on taste**:
`dfukiyo` split into four BPE pieces and lost the shared prefix; `dfposter` contained
`poster</w>`, which already sits inside its own style phrase; a replacement `xuki` collided
because several ukiyo-e captions contain the literal words "uki e". The frozen family
**`xgeo` / `xkyo` / `xpst`** is two pieces each, shares a leading piece, and has zero overlap
with the caption corpus, the style phrases or the frozen prompt kit.

**No tokenizer vocabulary entry is ever added.** The text encoder is frozen for the whole of
M6, so an added embedding would never receive a gradient and would behave as untrained noise.
A test asserts the vocabulary size is unchanged.

### Training resolution — 512×512 for all three styles

Measured in M5: 0.285 s/step at 512×512 against 1.12 s/step at native 512×1536, a 3.9×
difference. Only `minimal-geometric` is deck-shaped (44/44 at exactly 1:3); `ukiyo-e` has a
median 1.33 h/w with 15 landscape items and `retro-poster` a median 1.48 with 8 landscape.
Identical conditions keep the styles cross-comparable, and deck geometry comes from
*generation* (DR-007), already proven with a 512×512-trained LoRA in EXP-019.

**Explicitly not assumed:** that native-resolution training would produce better skateboard
art. M5 measured native *feasibility and cost only*. The final matrix therefore generates at
both 512×512 and 512×1536, so a deck-format regression is caught rather than hidden by the
training choice.

## Measured results, Phase A (gate-1 pilots)

Six runs, six passes, tier 0, no escalation. Full rows in `experiments/registry.csv`.

| arm | style | captions | images | pres./item | s/step | first → last loss |
|---|---|---|---|---:|---:|---|
| EXP-020 | minimal-geometric | style-only | 44 | 6.818 | 0.284 | 0.0780 → 0.0044 |
| EXP-021 | ukiyo-e | style-only | 44 | 6.818 | 0.408 | 0.6583 → 0.0302 |
| EXP-022 | retro-poster | style-only | 36 | 8.333 | 0.294 | 0.4973 → 0.0351 |
| EXP-023 | minimal-geometric | **verbatim** | 44 | 6.818 | 0.294 | 0.0781 → 0.0045 |
| EXP-024n12 | minimal-geometric | style-only | 12 | 25.000 | 0.296 | 0.0648 → 0.0042 |
| EXP-024n24 | minimal-geometric | style-only | 24 | 12.500 | 0.331 | 0.0849 → 0.0052 |

**Loss is not evidence of style quality** and is recorded only to show the runs are comparable.

## Gate-1 human decisions (Kylian Algoet, 2026-08-05)

Recorded in full in `docs/evidence/prototype-4/GATE-1-approval.md`. Scores were fixed and
hashed **before** the blinding map was opened (`cf6bf2605b715912…`), and no score was changed
at or after unblinding.

- **Caption strategy: style-only, approved and preferred.** Tied across all nine dimensions at
  step 150; at step 300 style-only matched verbatim on prompt adherence and style consistency
  and scored higher on visual quality and diversity across seeds.
- **Dataset size: O5 — inconclusive.** 44 scored highest, 12 second, 24 lowest, and the
  ordering was non-monotonic at both checkpoints. The experiment establishes **no monotonic
  relationship** and **no universal minimum image count**; it establishes only that the
  44-image `minimal-geometric` arm performed best **under this exact equal-compute
  experiment**. It must not be relabelled O1–O4.
- **Full-run step count: 600** for every style, the lower bound of the pre-declared band.
- **Contingency: none authorised.** Both slots preserved.

**The RQ4 confound is recorded, not buried.** At a fixed 300 steps the 12-image arm presents
each item 25.0×, the 24-image arm 12.5× and the 44-image arm 6.818×. This measures **set size
at equal compute, not at equal epochs**, for `minimal-geometric` only.

## Measured results, Phase B (approved runs)

Four runs, four passes, tier 0, no escalation.

| run | style | steps | pres./item | s/step | wall | first → last loss | L2 |
|---|---|---:|---:|---:|---:|---|---:|
| EXP-027 | minimal-geometric | 600 | 13.636 | 0.283 | 175.9 s | 0.0780 → 0.0025 | 4.752 |
| EXP-028 | ukiyo-e | 600 | 13.636 | 0.398 | 244.1 s | 0.6583 → 0.2297 | 4.080 |
| EXP-029 | retro-poster | 600 | 16.667 | 0.308 | 189.5 s | 0.4973 → 0.1425 | 4.972 |
| EXP-030 | **multi-style** | 1800 | 14.516 | 0.350 | 633.8 s | 0.6290 → 0.1960 | 8.307 |

**Peak allocated is 3133.4 MiB in all four, and in all six pilots.** Training memory is set by
geometry alone: neither the number of styles, nor the number of images, nor the step count
moves it. That is consistent with EXP-016/017, where activations scaled with geometry
(3114 → 5183 MiB) while optimizer state did not (2109 → 2119).

### RQ5 — how the multi-style run was made fair

"Matched steps" is ambiguous when the combined set is roughly three times larger, so the rule
was frozen before the run: **each style's exposure is matched to its own per-style run** —
exactly 600 optimizer-step presentations each, 1800 total. The style slots are an exact
multiset that is then seeded-shuffled, so balance holds by construction rather than in
expectation, and the order is deliberately not a round-robin, which would tie style to step
parity. The runner **asserts** the achieved exposure and fails rather than producing a
plausible but unbalanced adapter; the recorded value is
`minimal-geometric:600;retro-poster:600;ukiyo-e:600`.

Item counts differ by design (44 / 44 / 36), so per-*item* presentation differs while
per-*style* exposure is identical — which is exactly what makes the comparison fair.

### An honest limitation found during validation

**Training runs are not bit-reproducible from their recorded seed.** The adapter is created
with `init_lora_weights="gaussian"`, which draws from the global torch RNG; the runner seeds a
`torch.Generator` for the VAE sample, the noise and the timesteps but never seeds the global
RNG. Measured consequence: the same-step full-run and pilot adapters differ by an L2 of ~158
against a weight norm of ~112 — a ratio of √2, the signature of two independent draws — while
training itself moves the weights by ~5.

The **data** pipeline is deterministic and was verified, not assumed: the 600-step sample
order's first 300 draws are byte-identical to the 300-step pilot's recorded
`sample_order_sha256`. This is recorded as a limitation and as future work; it was **not**
fixed mid-milestone, because seeding the initialisation would change every run that the
gate-1 arms were compared against.

## Alternatives considered for the open questions

| question | alternatives | how it is being decided |
|---|---|---|
| step count | 600 / 900 / 1200 / 1500 within the pre-declared band | **decided at gate 1: 600**, by Kylian |
| caption strategy | style-only vs dataset-v1 verbatim | **decided at gate 1: style-only**, by Kylian, from blinded scores |
| dataset size | 12 / 24 / 44 at equal compute | **decided at gate 1: O5 inconclusive**, by Kylian |
| production checkpoint per style | step 300 vs 600 per style, or none | **open — gate 2** |
| default LoRA weight | 0.0 / 0.4 / 0.7 / 1.0 | **open — gate 2** |
| per-style vs multi-style (RQ5) | 3 adapters vs 1 balanced adapter | **open — gate 2** |
| H4 (retro-poster frames / pseudo-text) | confirmed / refuted | **open — gate 2** |
| H5 (style vs adherence trade-off) | confirmed / refuted | **open — gate 2** |

## Criteria the gate-2 decision will be judged against

Fixed before the evidence existed, in the approved plan:

- **Pass** — all technical gates hold; recognisably on-style at some weight in 0.4–1.0 without
  collapsing prompt adherence; no unresolved memorisation flag.
- **Partial pass** — gates hold and style is visible, but with a named defect. Reported as
  partial; **never upgraded**.
- **Failure** — gates fail, or no weight yields visible style, or memorisation is confirmed.
  A first-class recorded result.
- **Fallback** — ship the styles that passed and report the failure honestly. **A failed style
  is never quietly dropped from the record.**

## Consequences (to be completed after gate 2)

Not written. Filling this in before Kylian's Gate-2 scores would be inventing the result the
gate exists to produce.

## Decision

**None recorded. This record is a draft.**
