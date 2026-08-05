# DR-010 — Style-learning configuration for Prototype 5

**Status:** **accepted** · **Date opened:** 2026-08-04 · **Finalised:** 2026-08-05 at Gate 2
by Kylian Algoet · **Milestone:** M6 (Prototype 4)
**Answers:** RQ4 — *how many images, and what caption standards, does style learning need?*
and RQ5 — *one multi-style LoRA, or separate per-style LoRAs?*
**Related:** DR-006 (dataset styles), DR-007 (base model), DR-008 (reference conditioning),
DR-009 (fine-tuning method)

> **How this record reached a conclusion.** It stayed a draft with an empty decision section
> until Kylian completed Gate 2, because every question left in it was a visual-quality
> judgement. The conclusion below is written **from his scores**, recorded in
> `docs/evidence/prototype-4/gate-2-scoring-form-completed.md` (sha256 `835488f3…`) and
> `GATE-2-approval.md`. The automated indicators in `docs/evidence/EXP-026/` and
> `docs/evidence/EXP-033/` remain descriptive: they populate no rubric cell and selected no
> checkpoint, weight, style or verdict.

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

**Every M6 training run is not bit-reproducible from its recorded seed.** The adapter was
created with `init_lora_weights="gaussian"`, which draws from the global torch RNG, and at the
time of these runs the runner seeded a `torch.Generator` for the VAE sample, the noise and the
timesteps but never the global RNG. Measured consequence: the same-step full-run and pilot
adapters differ by an L2 of ~158 against a weight norm of ~112 — a ratio of √2, the signature of
two independent draws — while training itself moves the weights by ~5.

The **data** pipeline is deterministic and was verified, not assumed: the 600-step sample
order's first 300 draws are byte-identical to the 300-step pilot's recorded
`sample_order_sha256`.

It was **not** fixed mid-milestone, because seeding the initialisation would have changed every
run the gate-1 arms were compared against. At Gate 2 Kylian authorised the fix **for future
training only**: `seed_everything()` now seeds Python `random`, the global torch RNG and CUDA
before the adapter is constructed, with regression tests proving the same seed gives identical
initial weights and a different seed does not. **The M6 runs above predate that call, were not
rerun, and this finding stands unchanged for them** — their checkpoints are authoritative as
files, by sha256, not as a recipe.

## Alternatives considered for the open questions

| question | alternatives | how it is being decided |
|---|---|---|
| step count | 600 / 900 / 1200 / 1500 within the pre-declared band | **decided at gate 1: 600**, by Kylian |
| caption strategy | style-only vs dataset-v1 verbatim | **decided at gate 1: style-only**, by Kylian, from blinded scores |
| dataset size | 12 / 24 / 44 at equal compute | **decided at gate 1: O5 inconclusive**, by Kylian |
| production checkpoint per style | step 300 vs 600 per style, or none | **decided at gate 2**: 300 / 600 / 300 |
| default LoRA weight | 0.0 / 0.4 / 0.7 / 1.0 | **decided at gate 2: 0.7** |
| per-style vs multi-style (RQ5) | 3 adapters vs 1 balanced adapter | **decided at gate 2**: 3 adapters; multi-style viable, not selected |
| H4 (retro-poster frames / pseudo-text) | confirmed / refuted | **CONFIRMED at gate 2** |
| H5 (style vs adherence trade-off) | confirmed / refuted | **SUPPORTED at gate 2** |

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

## Decision

### D1. Separate per-style LoRA adapters, one selected checkpoint each

| style | run | step | sha256 | outcome |
|---|---|---:|---|---|
| minimal-geometric | EXP-027 | **300** | `2d425838cce59adc…` | **PASS** |
| ukiyo-e | EXP-028 | **600** | `52381b6052ad71f1…` | **PASS** |
| retro-poster | EXP-029 | **300** | `70d2afbfb3c09aff…` | **PARTIAL PASS** |

Full paths and untruncated hashes in `docs/evidence/prototype-4/GATE-2-approval.md`. All three
are rank 8 / alpha 8 UNet-attention adapters, 256 tensors, 256 LoRA keys, **zero base-model
keys**, 6 414 480 bytes, re-hashed on disk against their recorded values.

**Two of the three selected checkpoints are step 300, not step 600.** More training was not
better for `minimal-geometric` or `retro-poster`: prompt adherence fell from 4 to 3 at step 600
in both while style consistency stayed at 5. Only `ukiyo-e` improved to step 600. This is the
concrete reason a single global step count was never assumed.

### D2. Default application LoRA weight — 0.7

0.4 often gives insufficient style influence; 1.0 frequently increases prompt override, repeated
motifs or style leakage. The application may expose **0.4–1.0** as an advanced control but must
**default to 0.7**. **0.7 is the selected compromise, not a universal optimum.**

### D3. RQ5 — per-style adapters selected; the multi-style adapter is viable but not selected

The balanced multi-style LoRA is **technically feasible and visually competitive at 512×512**,
with **no severe cross-style token bleed observed** — its ukiyo-e arm matched the best per-style
ukiyo-e sheet on every dimension. **The multi-style experiment did not fail.**

Per-style adapters are selected because each style has a *different* approved checkpoint, they
give cleaner independent control, each was evaluated at both geometries, and styles can be
improved or replaced independently. The multi-style adapter's advantage does not outweigh the
reduced flexibility.

### D4. H4 — confirmed

`retro-poster` learns a recognisable, useful vintage-poster aesthetic **and** transfers
pseudo-text, poster borders, framed composition and repeated poster-layout motifs. The
failure-mode probe marks `pseudo_text` and `unwanted_frame` **worse than base on every**
`EXP-029` sheet, and `artefacts` scores 2 throughout. This confirms the M2 dataset finding and
the pre-training audit, which measured a dark border on **35 of 36** training images.

### D5. H5 — supported

Style strength rises with LoRA weight, but at the highest tested weight prompt authority can
weaken, repeated motifs can increase, style-free prompts can leak more, and the trained
composition can dominate the requested content.

### D6. RQ4 — image count remains inconclusive (O5), captions style-only

The **O5** verdict from Gate 1 stands: 44 scored highest, 12 second, 24 lowest, non-monotonic at
both checkpoints. **No monotonic relationship and no universal minimum image count is
established.** Style-only captions are selected, and were used for every Phase-B run.

## Consequences

**For Prototype 5 (the integrated application):**

- Ship **three separate per-style adapters**, defaulting to **weight 0.7**, with 0.4–1.0
  optionally adjustable.
- **`retro-poster` ships with a named limitation**, not as an equal. It is a partial pass and
  **is never upgraded**; if it is exposed to users, its pseudo-text and framing behaviour should
  be expected rather than treated as a defect to be surprised by.
- **The 202 MiB memory ceiling is binding.** SD 1.5 + one LoRA + IP-Adapter at 512×1536 peaks at
  7985.5 MiB device of 8187.5 — measured identically for all four candidates. **This is 2.5 % of
  the device and is not comfortable headroom.** A second adapter, a higher rank, a larger
  reference batch or ControlNet all have to fit inside it, and none may be added without a new
  memory test.
- **The selected checkpoints are authoritative as FILES, by sha256, not as a recipe** — see the
  limitation below. They must be preserved, not regenerated.

**Limitations carried forward, none softened:**

1. **R14 — the M6 artifacts are not bit-reproducible from their seed.** The LoRA initialisation
   drew from the unseeded global torch RNG. Measured: two runs of one configuration differ by an
   L2 of ~158 against a weight norm of ~112, the √2 ratio of independent draws, while training
   moves the weights by ~5. The **data** pipeline was verified deterministic. The runner is now
   seeded **for future training only**, with two regression tests; **EXP-027…EXP-030 were not
   rerun or replaced**, and the fix does not retroactively change the historical finding.
2. **An orchestration defect in the final matrix.** Two blocks overlapped at weight 0.7, so 24 of
   252 generations were exact repeats. They were byte-identical — which incidentally confirms
   generation determinism — but each put a self-pair into a diversity cell and pulled it toward
   zero; one cell moved from 0.3302 to **0.4067** once excluded. Fixed in the plan, in the
   diversity computation, and guarded by a test. The matrix was **not** regenerated, because its
   evidence is a valid superset of the fixed plan.
3. **Zero near-copy flags is not proof of no memorisation.** 0 of 108 and 0 of 252 generations
   flagged at `dHash ≤ 6`, with the holdout control at a comparable distance. **That threshold
   is a coarse near-copy indicator** — sensitive to layout, blind to recolouring — and not a
   general memorisation measure.
4. **RQ4 answers less than it appears to.** The size comparison holds *compute* fixed, not
   epochs, so it is deliberately confounded with repetition and applies to `minimal-geometric`
   only. It establishes no minimum image count.
5. **DreamBooth, Textual Inversion and full fine-tuning were never measured** (DR-009). Nothing
   here claims LoRA is superior to them.
6. **Gate 2 was scored on labelled sheets**, unlike Gate 1's blinded ones, because the question
   was which checkpoint ships. Labelled sheets carry an expectation effect that blinded ones do
   not.
