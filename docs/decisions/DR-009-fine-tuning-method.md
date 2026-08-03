# DR-009 — Fine-tuning method for Prototypes 4–5

**Status:** accepted · **Date:** 2026-08-04 · **Milestone:** M5 (Prototype 3)
**Answers:** RQ1 — *which fine-tuning method is feasible and most effective on 8 GB VRAM?*
**Supersedes:** the "HYPOTHESIS ONLY" ML-method screening in `docs/03-architecture.md`
**Related:** DR-004 (toolchain), DR-007 (base model), DR-008 (reference conditioning)

## Context

The assignment mandates comparing several fine-tuning approaches: training from scratch,
full fine-tuning, DreamBooth, Textual Inversion, and LoRA. `docs/03-architecture.md`
screened them against the audited constraint (8 GB VRAM, ~19 days) and named LoRA the
primary hypothesis — but that table decided nothing and said so.

Prototype 3 (M5) was the empirical gate. It asks a **technical** question only: does a LoRA
actually train, save, reload and measurably change generation on this hardware, and what
does it cost? Style quality is Prototype 4's question and is deliberately not answered here.

## Alternatives and how each was treated

| Method | Treatment in M5 | Basis |
|---|---|---|
| Training from scratch | **Screened out, not measured** | Multi-GPU-week compute class; infeasible within 8 GB and ~19 days by inspection of the requirement, not by experiment |
| Full fine-tuning | **Screened out, not measured** | Optimizer states for an SD-class UNet exceed 8 GB. AdamW holds two fp32 moments per trained parameter; for SD 1.5's ~860 M UNet parameters that is ~6.9 GB of optimizer state alone, before weights, gradients or activations |
| DreamBooth | **Deferred to Prototype 4, not measured** | Subject-driven rather than style-driven; a candidate comparison if time allows |
| Textual Inversion | **Deferred to Prototype 4, not measured** | Tiny trainable footprint, limited style capacity; a candidate comparison |
| **LoRA** | **MEASURED — 8 experiments, 13 runs** | EXP-016a/b, EXP-016, EXP-017a/b, EXP-018, EXP-019a/b |

## Criteria

1. Fits 8 GB VRAM at tier 0, at both 512×512 and the DR-007 deck format 512×1536.
2. Trains verifiably — not merely "returns without raising".
3. Produces a checkpoint that reloads into a fresh process and measurably changes output.
4. Coexists with the DR-008 reference-conditioning stack at the deck format (risk R12).
5. Fits the remaining schedule.

## Measured results

All at training tier 0. **No tier escalation was needed anywhere**, so tiers 1–5 were not
executed — the ladder forbids collecting deeper-tier results for their own sake.

| run | geometry | peak allocated | peak device used | spare | s/step |
|---|---|---|---|---|---|
| EXP-016a (1 step) | 512×512 | 3114.09 MiB | 4267.5 MiB | 3920.0 | 1.9344 |
| EXP-016b (10 steps) | 512×512 | 3133.40 MiB | 4285.5 MiB | 3902.0 | 0.4340 |
| EXP-016 (300 steps) | 512×512 | 3133.40 MiB | 4285.5 MiB | 3902.0 | 0.2854 |
| EXP-017a (1 step) | 512×1536 | 5160.96 MiB | 6429.5 MiB | 1758.0 | 2.5533 |
| EXP-017b (10 steps) | 512×1536 | 5182.58 MiB | 6449.5 MiB | 1738.0 | 1.1223 |

**Criterion 1 — met.** LoRA training fits at both geometries. Native deck-format training,
which the M5 plan treated as genuinely uncertain, fits at tier 0 with 1738 MiB spare.

**Criterion 2 — met.** All nine technical gates hold in every training run: 1 594 368
trainable parameters across 256 LoRA tensors, exactly matching the attached adapter's own
count, with no non-LoRA parameter trainable; base UNet weights unchanged (float64 byte-hash
compared before and after); gradients present, finite and non-zero; losses finite; and LoRA
parameters demonstrably moved (L2 delta 0.0877 after one step, 3.857 after 300).

**Criterion 3 — met (EXP-018).** The checkpoint reloads into a fresh process: 0 LoRA modules
before load, **128 after**, read back from the live UNet. At weight 0.0, **4/4 outputs are
byte-identical** to the no-adapter baseline. At weight 1.0, **4/4 change beyond a noise floor
declared before any result was read** (mean absolute pixel difference 51.89–66.33 on the
0–255 scale, dHash 20–28, CLIP cosine 0.4796–0.7247).

**Criterion 4 — met, but tightly (EXP-019).** SD 1.5 + LoRA + IP-Adapter at scale 0.55 runs
at the deck format with both adapters live simultaneously — **5143.73 MiB allocated,
7985.5 MiB device used of 8187.5, leaving 202.0 MiB spare.** See the consequences below;
this is not headroom to build on.

**Criterion 5 — met.** 300 training steps cost 91 seconds. Prototype 4's per-style and
multi-style comparisons are affordable many times over.

## Decision

**LoRA is selected as the fine-tuning method for Prototypes 4 and 5**, at rank 8 / alpha 8 on
the UNet attention projections, with the text encoder and VAE frozen, at training memory
tier 0.

### What this decision does NOT claim

**LoRA has not been shown to be objectively superior to DreamBooth, Textual Inversion, or
full fine-tuning.** Those methods were **screened on stated criteria, not measured**. No
image produced by them exists in this project, and no rubric score has been assigned to
them. The honest statement is narrower and is the one that carries:

> Of the mandated alternatives, LoRA is the one demonstrated to be **technically feasible**
> on this hardware, and it is selected on that basis plus schedule fit.

This is the same class of limitation DR-007 carries, where SD 2.1 was blocked by HTTP 401
and the base-model comparison rested on two measured candidates rather than three. It must
be stated in the final report, not smoothed over.

**No style-quality claim is made anywhere in M5.** Whether the LoRA learns the target style
well is Prototype 4's question, judged by a human against the rubric. M5 deliberately ran no
human scoring gate: the milestone's acceptance is measurable and automated, following the
EXP-007 precedent.

## Consequences

- **Prototype 4 (M6)** compares per-style versus multi-style LoRAs (RQ5) and dataset-size,
  rank and learning-rate variations (RQ4) on this foundation. Textual Inversion and
  DreamBooth remain available as candidate comparisons if time allows; if they are not run,
  the report says so plainly.
- **Trigger-token design remains open.** M5 used dataset-v1 captions verbatim with no trigger
  token, deliberately, so the smoke test carried one variable and stayed comparable with the
  frozen evaluation prompts. Prototype 4 decides the trigger-token question.
- **Native deck-format training is feasible but was only probed.** EXP-017 established
  feasibility and cost (1.1223 s/step, 1738 MiB spare), not style quality. A long native
  training run is a separate Prototype 4 decision and was explicitly out of M5's scope.
- **Risk R12 is re-scoped, not closed.** The tested stack fits by 202 MiB — 2.5 % of the
  device, and *less* margin than IP-Adapter alone had in EXP-013 (222 MiB), because the LoRA
  costs 20 MiB of device memory on top. Prototype 5 must treat 512×1536 + LoRA + IP-Adapter
  as the **memory ceiling of the production path**, not a base to extend. Anything added —
  a second adapter, a higher rank, ControlNet for layout control — has 202 MiB to fit in.
- **The LoRA's marginal cost is +3.04 MiB allocated and does not scale with geometry**,
  measured identically at 512×512 and 512×1536 and independently in EXP-018. Rank increases
  in Prototype 4 scale this figure, but from a very small base.
- **Activations, not optimizer state, dominate training memory.** Post-load allocation is
  identical at both geometries (2066.56 MiB) and the optimizer-step peak barely moves
  (2108.93 → 2118.76), while the forward/backward peak rises 3114.09 → 5182.58. If a future
  configuration does not fit, **gradient checkpointing (tier 1) is the correct first
  escalation** and a lower-memory optimizer would be the wrong move. This is a measured
  ordering, not a guess.
- **DR-004's kohya-ss fallback is not needed.** Diffusers + PEFT LoRA training fits 8 GB
  comfortably at 512×512 and adequately at 512×1536.
