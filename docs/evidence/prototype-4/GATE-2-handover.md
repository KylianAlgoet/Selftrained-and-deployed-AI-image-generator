# Prototype 4 — Gate 2 handover package

**Date:** 2026-08-05 · **Milestone:** M6 Phase B complete · **Status:** STOPPED, awaiting review

Phase B is finished. **M6 does not close, DR-010 stays a draft, and nothing is pushed until
you return the Gate-2 scores and decisions at the bottom of this page.**

## What was NOT done, deliberately

No production checkpoint has been selected. No style has been declared a winner. No default
LoRA weight has been chosen. RQ5, H4 and H5 have no verdict. DR-010 has no conclusion and no
consequences section. No contingency run was started — **both slots are still unused.** The
M6 issue is open, M6 is not on Done, and nothing has been pushed.

**No visual-quality claim appears anywhere in Phase B.**

## 1. What ran, at your approved settings

Four training runs, four passes, **tier 0 throughout, no escalation**.

| run | style | steps | pres./item | s/step | wall | first → last loss | L2 |
|---|---|---:|---:|---:|---:|---|---:|
| EXP-027 | minimal-geometric | 600 | 13.636 | 0.283 | 175.9 s | 0.0780 → 0.0025 | 4.752 |
| EXP-028 | ukiyo-e | 600 | 13.636 | 0.398 | 244.1 s | 0.6583 → 0.2297 | 4.080 |
| EXP-029 | retro-poster | 600 | 16.667 | 0.308 | 189.5 s | 0.4973 → 0.1425 | 4.972 |
| EXP-030 | **multi-style** | 1800 | 14.516 | 0.350 | 633.8 s | 0.6290 → 0.1960 | 8.307 |

Every run: fresh OS process, from the **base model** (not resumed from a pilot), frozen
manifest, style-only captions, rank 8 / alpha 8, LR 1e-4, batch 1, accumulation 1, 512×512,
seed 42, pinned dependency stack untouched. Checkpoints at 150 / 300 / 450 / 600, and at
450 / 900 / 1350 / 1800 for the multi-style run.

**Peak allocated is 3133.4 MiB in all four — and in all six Phase-A pilots.** Training memory
is set by geometry alone; neither style count, image count nor step count moves it.

**Loss is not evidence of style quality.** It is reported only to show the runs are comparable.

### The multi-style run is balanced by construction, not by hope

Recorded exposure: `minimal-geometric:600; retro-poster:600; ukiyo-e:600`. The runner
**asserts** this and fails rather than producing a plausible but unbalanced adapter. Item
counts differ by design (44 / 44 / 36), so per-*item* presentation differs while per-*style*
exposure is identical — which is what makes the RQ5 comparison fair rather than a comparison
against whichever style happened to have the most images.

## 2. Technical gates and checkpoint artifacts

`docs/evidence/prototype-4/full-run-validation.md` — **all gates pass, and every checkpoint
re-verifies on disk**: re-hashed, tensor inventory read back, 256 tensors and 256 LoRA keys
with **zero base-model keys** in each.

### An honest limitation the validation surfaced

**Training runs are not bit-reproducible from their recorded seed.** The adapter is created
with `init_lora_weights="gaussian"`, which draws from the global torch RNG; the runner seeds a
`torch.Generator` for the VAE sample, the noise and the timesteps but never the global RNG.

Measured, not guessed: the same-step full-run and pilot adapters differ by an L2 of ~158
against a weight norm of ~112 — a ratio of **√2**, the signature of two independent draws from
one distribution — while training itself moves the weights by ~5.

The **data** pipeline *is* deterministic, and that was verified rather than assumed: the
600-step sample order's first 300 draws are byte-identical to the pilot's recorded
`sample_order_sha256`. Recorded as a limitation and as future work. **Not fixed mid-milestone**,
because seeding the initialisation would alter every run the Gate-1 arms were compared against.

## 3. The final validation matrix

`docs/evidence/EXP-031/final-matrix.jsonl` — **252 generations, all ok**, against the
pre-declared cap of **432**, asserted before the first image. 21 arms, one fresh OS process
each. Only Gate-1 approved candidates: EXP-027/028/029 at steps 300 and 600, EXP-030 at 1800,
plus the untrained SD 1.5 control. **No rejected pilot checkpoint was generated for.**

Four prompt roles, including `FP4-style-free`, which carries **neither trigger nor style
phrase** — a style LoRA should leave it close to the base model, so drift there is leakage
rather than style learning.

The **+3.04 MiB** LoRA cost reproduced at both geometries for a third time (2675.38 → 2678.42
at 512×512; 3892.01 → 3895.05 at 512×1536), matching M5's EXP-018/019.

### A defect found in my own orchestration, recorded not smoothed over

Blocks A and B of the matrix plan overlap at the nominal weight 0.7, so **24 of the 252
generations were exact repeats**. All 24 duplicate pairs came back **byte-identical**, which
incidentally confirms generation determinism at a fixed seed within a process — but they wasted
capped budget and, worse, put a **self-pair into 12 of the 102 diversity cells**, dragging
their mean pairwise distance toward zero and manufacturing apparent mode collapse out of an
orchestration bug. Recomputed without the repeats, EXP-027@300 moved from 0.3302 to **0.4067**.

Fixed: the plan now deduplicates (228 distinct cells), a regression test forbids a repeat, and
the diversity pass excludes repeated configurations regardless of the plan. **The matrix was
not regenerated** — the evidence is valid and is a superset of the fixed plan. The executed
rows carry the pre-fix fingerprint `da7e4c36aa5a98cf`; the fixed plan's is `c58364681c087866`.

## 4. Combined stack — R12 remains re-scoped, not closed

`docs/evidence/EXP-032/combined-stack.jsonl` — 8 runs, **all ok**, 512×512 first and 512×1536
only after it succeeded, for each of the four candidates. Geometry was never reduced.

| geometry | allocated | reserved | device used | spare of 8187.5 |
|---|---:|---:|---:|---:|
| 512×512 | 3927.11 | 4584.0 | 5697.5 | 2490.0 |
| **512×1536** | 5143.73 | 6872.0 | **7985.5** | **202.0** |

Identical for all four candidates, and identical to M5's EXP-019b — rank, target modules and
IP-Adapter scale are unchanged, so the footprint is unchanged.

**202.0 MiB is 2.5 % of the device and is not comfortable headroom.** It is the memory ceiling
of the production path: a second adapter, a higher rank, a larger reference batch or ControlNet
all have to fit inside it.

**WDDM spill checked explicitly.** The EXP-004 signature is device-used near the ceiling
*together with* an RSS jump. Device used is 7985.5 of 8187.5, but peak RSS at the deck format
(5256–5424 MiB) is **lower** than at 512×512 (4908–5998 MiB). The signature is **absent**; no
silent host spill is indicated.

## 5. Unscored automated indicators

`docs/evidence/EXP-033/final-indicators.md` — **descriptive only.** These populate no rubric
cell, select no checkpoint, style or hyperparameter, and are not a quality ranking.

**0 of 252 generations carry a near-copy flag** at the M4 threshold `dHash ≤ 6`. Median
nearest-training dHash is 19.5–27.5 per arm with a minimum of 13, far above the flag, and the
**holdout control** sits at a comparable 23.0–28.0 — which is the point of the control: a
similar distance to images never trained on indicates the residual similarity comes from the
base model or the prompt, not from memorisation.

**`dHash ≤ 6` is a coarse near-copy indicator, not proof of memorisation**, and not a general
memorisation measure — it is sensitive to layout and blind to recolouring.

Descriptive, and explicitly not a quality claim — median CLIP cosine to the training set on the
**style-free** prompt, which carries no trigger and no style phrase:

| arm | style | median cosine |
|---|---|---:|
| BASE | minimal-geometric | 0.2436 |
| EXP-027@600 | minimal-geometric | 0.4876 |
| BASE | ukiyo-e | 0.1934 |
| EXP-028@600 | ukiyo-e | 0.2481 |
| BASE | retro-poster | 0.1987 |
| EXP-029@600 | retro-poster | 0.2135 |

What that means for leakage is **your** judgement on the `FP4-style-free` cells, not a number's.

## 6. The review package

- **Sheets:** `docs/evidence/prototype-4/final-sheets/` — 21 labelled sheets, all ≤300 KB.
- **Blank form:** `docs/evidence/prototype-4/gate-2-scoring-form.md`.
- **Review ZIP:** `outputs/m6-gate-2-review-package.zip` — no weights, checkpoints, latents or
  full-resolution outputs.

**These sheets are labelled, unlike Gate 1's.** Gate 1 blinded arms that differed in one hidden
variable each; Gate 2 asks which checkpoint goes to production, which cannot be answered
without knowing which checkpoint each sheet is. **The trade-off is stated rather than hidden:**
labelled sheets carry an expectation effect that blinded ones do not.

## 7. Decisions this gate needs from you

1. **Final production checkpoint per style** — arm and step, or *none* for a style that did
   not reach a usable state.
2. **Default LoRA weight** for the application, from the 0.0 / 0.4 / 0.7 / 1.0 sweep.
3. **RQ5 verdict** — balanced multi-style adapter, or separate per-style adapters? Include
   whether you see cross-style token bleed.
4. **H4 verdict** — does `retro-poster` bake in frames or pseudo-text? Left unanswered at
   Gate 1 on purpose.
5. **H5 verdict** — do style strength and prompt adherence trade off as weight rises?
6. **Per-style outcome** — pass / partial pass / failure for each style. A partial pass is
   never upgraded, and a failed style is recorded as failed rather than dropped.
7. **Contingency** — authorised or not, and if so which **single** variable.
8. **DR-010** — may the draft be finalised with your conclusion?

## 8. Budget and deadline position

**10 of 12** training runs used: 6 Phase-A pilots + 3 per-style full runs + 1 multi-style.
**Both contingency slots remain.** The final matrix used 252 of 432 allowed generations.

**Hard stop remains 2026-08-09 end of day.** M7 integration must begin 2026-08-10 to 08-12.
The scope-reduction order is unchanged: keep `minimal-geometric`, then `ukiyo-e`, then reduce
or drop `retro-poster` before M7 is at risk — and a dropped style is **stated as dropped**,
with the reason and date.

`dataset-v1.csv` is **byte-identical** to its recorded hash `cd18cbb0…`, asserted by pytest,
and was opened read-only for the whole of M6. The style kit fingerprint is still
`fc11d828…`, unchanged by Phase B.
