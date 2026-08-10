# Prototype 3 — Local LoRA smoke test (M5)

**Status:** **COMPLETE**, 2026-08-04. Fine-tuning method selected in DR-009.
**Date:** 2026-08-04 · **Research questions:** RQ1 (which fine-tuning method is feasible on 8 GB),
RQ8 (does the deck geometry survive training), plus the mandatory R12 combined-stack acceptance item

> **Written retrospectively in M9 (2026-08-10) from the M5 evidence**, because Prototypes 0, 1, 2, 4
> and 5 each had a document and Prototype 3 did not, while `docs/06-prototype-overview.md` promises
> one per prototype. **No result, score or measurement in this file is new.** Every figure is copied
> from `experiments/registry.csv` (EXP-016a…EXP-019b), `docs/evidence/prototype-3/`, DR-009 and the
> M5 sections of `docs/process/process-log.md` and `docs/process/session-handoff.md`. Nothing was
> re-run to produce it, and no GPU work was performed.

## Outcome

| | |
|---|---|
| **Selected method (Prototypes 4–5)** | **LoRA** — PEFT 0.20.0, applied to UNet attention only |
| **Rank / alpha** | **8 / 8** |
| **Target modules** | `to_q`, `to_k`, `to_v`, `to_out.0` |
| **Frozen** | text encoder and VAE |
| **Training memory tier** | **0** — no escalation in any of the 13 runs |
| **Human review gate** | **none, by Kylian's decision** — acceptance here is automated and measurable, following the EXP-007 precedent |
| **Visual-quality claim** | **none made anywhere.** Style quality is Prototype 4's question |

## Research questions and hypotheses

**RQ1** — *Which fine-tuning method (from scratch, full fine-tune, DreamBooth, Textual Inversion,
LoRA) is feasible and most effective on 8 GB VRAM?*
Hypothesis: LoRA is the only method that fits the VRAM and the 19-day budget while capturing style.

**RQ8 (continued from Prototype 1)** — does training, not just inference, fit at the DR-007 deck
format of 512×1536?

**R12 (mandatory acceptance item, raised in M4)** — does the combined SD 1.5 + LoRA + IP-Adapter
stack fit 8 GB at 512×1536? IP-Adapter **alone** had already peaked at 7 965.5 of 8 187.5 MiB in
EXP-013, so this was genuinely open.

## Scope

In scope: a minimal LoRA training loop, train → save → reload → generate, measured VRAM and
duration at both geometries, and the combined-stack smoke test.

**Deliberately out of scope:** any long native 512×1536 training run. EXP-017a/b are **feasibility
probes only**, at 1 and 10 steps. Expanding them was recorded as a separate Prototype 4 decision
needing Kylian, not something M5 could take on its own.

Also out of scope by design: any style-quality judgement, any trigger-token design (M5 used
dataset-v1 captions **verbatim, with no trigger token**, deliberately, so the smoke test carried
one variable), and any comparison against DreamBooth or Textual Inversion — see
"What this prototype does not establish".

## Method — micro-gating before anything long ran

The milestone's rule was that **no longer run starts from an unmeasured projection**. Each
experiment gated the next:

```
EXP-016a  1 step  @512x512    -> does one optimizer step complete at all?
EXP-016b  10 steps @512x512   -> is the loop stable, and what does a step really cost?
EXP-016   300 steps @512x512  -> authorised only by a MEASURED projection (130.2 s)
EXP-017a  1 step  @512x1536   -> does the deck format fit in training?
EXP-017b  10 steps @512x1536  -> stable, and at what per-step cost?
EXP-018   inference           -> does the saved adapter reload and change output?
EXP-019a  512x512             -> do LoRA and IP-Adapter coexist at all?
EXP-019b  512x1536            -> R12: does the combined stack fit the deck format?
```

One configuration per fresh OS process throughout — the measurement rule Prototype 1 adopted after
the EXP-005 allocator contamination. EXP-019b ran **only** after EXP-019a passed, in that fixed
order.

## Measured results — 13 runs across 8 experiments, tier 0, zero escalations

| run | geometry | steps | peak allocated | peak device | spare | s/step |
|---|---|---:|---:|---:|---:|---:|
| EXP-016a | 512×512 | 1 | 3 114.09 | 4 267.5 | 3 920.0 | 1.9344 |
| EXP-016b | 512×512 | 10 | 3 133.40 | 4 285.5 | 3 902.0 | 0.4340 |
| EXP-016 | 512×512 | 300 | 3 133.40 | 4 285.5 | 3 902.0 | 0.2854 |
| EXP-017a | 512×1536 | 1 | 5 160.96 | 6 429.5 | 1 758.0 | 2.5533 |
| EXP-017b | 512×1536 | 10 | 5 182.58 | 6 449.5 | 1 738.0 | 1.1223 |
| EXP-018 | 512×512 (inference) | — | 2 678.42 | 4 361.5 | — | — |
| **EXP-019a** | 512×512 (LoRA + IP-Adapter) | — | 3 927.11 | 5 697.5 | 2 490.0 | — |
| **EXP-019b** | **512×1536 (LoRA + IP-Adapter)** | — | **5 143.73** | **7 985.5** | **202.0** | — |

All figures in MiB against a **8 187.5 MiB** device.

### The mechanism, measured rather than assumed

Post-load allocation is **byte-identical at both geometries** (2 066.56 MiB), and the optimizer-step
peak barely moves (2 108.93 → 2 118.76), while the forward/backward peak rises 3 114.09 → 5 160.96.

**Activations scale with geometry; optimizer state does not.** That is why **gradient checkpointing
(tier 1) is the correct first escalation** and a lower-memory optimizer would have been the wrong
first move. The phase-separated peaks are what made this readable — a single process-level peak
would have shown only that memory went up.

### A rank-8 LoRA costs +3.04 MiB, and it does not scale with geometry

Measured independently three times: EXP-018 against its own baseline, EXP-019a against EXP-009's
IP-Adapter-alone figure, and EXP-019b against EXP-013's. The same +3.04 MiB at 512×512 and at
512×1536.

### Training is cheap

**300 steps in 91.2 s.** The comparison grid Prototype 4 needed was affordable many times over, and
this materially reduced risk R2 (training time exceeding the schedule).

## Technical gates — read back, never inferred

Nine gates per run, each read from the live object rather than concluded from a call that returned
without raising:

- 256 LoRA tensors / 1 594 368 trainable parameters, matching the attached adapter's own count;
- **no non-LoRA parameter trainable**;
- base UNet parameters unchanged, compared by **float64 byte-hash before and after**;
- gradients present, **finite and non-zero**;
- losses finite;
- LoRA parameters actually moved (L2 delta 0.0877 at 1 step → 3.8573 at 300).

`loss_decreased` is **False for EXP-016a and correctly not a pass condition** — a single step has
the same first and last loss by construction. Recording it as a non-condition rather than quietly
dropping it is the point.

**Cross-process determinism was verified rather than assumed:** EXP-016b's step-1 loss (0.064612) is
identical to EXP-016a's in a **separate OS process**, and EXP-017b's (0.050128) matches EXP-017a's.
The frozen sample order and seed reproduce exactly across process boundaries.

## EXP-018 — the adapter reloads, and the evidence was pre-declared

Three arms, one per fresh process: baseline (no adapter), weight 0.0, weight 1.0.

**Reload proven from the live UNet:** 0 LoRA modules before load, **128 after**, 128 with populated
layers.

| bound | result | status |
|---|---|---|
| weight 0.0 | **4/4 byte-identical** to the no-adapter baseline (mean abs pixel diff 0.0, dHash 0, CLIP cosine 1.0) | **a DIAGNOSTIC, not a pass condition** |
| weight 1.0 | **4/4 beyond a noise floor declared before any result was read** — mean abs diff 51.89–66.33, dHash 20–28, CLIP cosine 0.4796–0.7247 | PASS |

The weight-0.0 result is recorded as a diagnostic **on purpose**: loading an inactive adapter can
legitimately alter the execution graph, so byte-identity was a welcome outcome that could not have
been allowed to fail the experiment. And **a differing PNG SHA alone was never treated as
sufficient** for the weight-1.0 arm — the threshold was `mean abs diff ≥ 0.5` **and** `≥ 1 % of
subpixels differing`, written down first.

**Cross-milestone continuity, third milestone running:** the EXP-018 baseline peak of
**2 675.38 MiB is byte-identical** to Prototype 1's EXP-002 and Prototype 2's text-only baseline.

## EXP-019 — R12, the mandatory acceptance item

Both adapters confirmed live **simultaneously** by reading the UNet back: **128 LoRA modules and 16
IP-Adapter attention processors** — the expected signature, since SD 1.5 has one self-attention and
one cross-attention processor per block and IP-Adapter replaces the cross-attention half only.

**At the deck format the combined stack fits by 202.0 MiB of 8 187.5 — 2.5 % of the device.**

That is **less margin than IP-Adapter alone had** in EXP-013 (222 MiB), because the LoRA takes about
20 MiB of device-level memory on top. **No overflow flag fired and no tier escalated** — which is
precisely the pattern that made SDXL look viable in EXP-004 until its figures were read against the
ceiling. So the number is quoted against the ceiling here, every time. **Geometry was never reduced
to make this pass.**

**This is not comfortable headroom, and it must never be described as such.**

## One honest failure, preserved

The first **EXP-019a** attempt is kept in `combined-stack.jsonl` with `status: failed`. The cause
was a defect in that experiment's **own runner** — `preprocess_for_adapter` returns `(image, note)`
and the caller unpacked one value — **not a finding about the stack**. It is retained rather than
deleted, and it still records that the full stack loaded at 3 308.33 MiB before failing in
preprocessing.

## Real problems diagnosed in this prototype

1. **Gradient accumulation is not a memory tier.** The draft plan treated it as one. **Kylian caught
   this in plan review**, the measurements confirmed him, and a guard now enforces it: at micro-batch
   1 it changes effective batch size, not micro-step peak memory.
2. **The training tier ladder is not the inference tier ladder.** A test asserts they stay distinct,
   so "tier 2" cannot quietly mean two different things in two files.
3. **Import boundaries are AST-parsed, not text-scanned.** The schema imports no torch, and neither
   training runner may import the CLIP evaluator — loading a 2.35 GiB metric encoder inside a
   generation process would inflate exactly the VRAM figures the comparison rests on.
4. **A new dependency was admitted only on parsed evidence.** `peft==0.20.0` was installed
   `--no-deps` after a parsed `--dry-run --report` proved it moved none of torch, diffusers,
   transformers, accelerate or safetensors. `bitsandbytes` and `xformers` were confirmed absent and
   **left uninstalled**, so no 8-bit-optimizer capability is claimed anywhere.

## Acceptance criteria

| criterion | result |
|---|---|
| Training completes without OOM | **MET** — 13/13 runs, tier 0, zero escalations |
| LoRA visibly affects output | **MET** — EXP-018, 4/4 beyond a pre-declared noise floor |
| Peak VRAM and duration measured | **MET** — per-run, phase-separated |
| Reproducible via config and seed | **PARTIALLY MET** — see below |
| R12 combined stack at 512×1536 | **MET** — fits by 202.0 MiB |

**"Reproducible via config and seed" is recorded as partially met, and it was not softened.** The
data pipeline is deterministic and was verified so across process boundaries. But the LoRA
*initialisation* draws from the unseeded global torch RNG, which is what **risk R14** records — it
was diagnosed in M6, one milestone after this one, from the √2 shape of the discrepancy. M5's runs
predate the fix, and the fix is deliberately **forward-only**.

## Limitations

1. **DR-009 makes no superiority claim.** From-scratch training, full fine-tuning, DreamBooth and
   Textual Inversion were **screened on criteria and never measured**. The defensible statement is
   that LoRA is the mandated method **demonstrated feasible on this hardware** — not that it is the
   best of the five.
2. **No long native 512×1536 training run happened.** EXP-017a/b establish native **feasibility and
   cost only**, at 1 and 10 steps. They say nothing about native style quality.
3. **No style-quality claim of any kind is made here**, and none may be added retroactively. The
   smoke adapter trained on 12 images for 300 steps; that is a mechanism test, not a style result.
4. **The 202.0 MiB margin is 2.5 % of the device.** R12 is **re-scoped, not closed**: the open
   question is no longer "does this stack fit" but "does anything added to it still fit".
5. **Per-step cost at the deck format is 2.6× the 512×512 figure** (1.1223 s vs 0.4340 s), roughly
   tracking the 3× pixel count.

## Impact on the next iteration

Prototype 4 inherited: LoRA at rank 8 / alpha 8 and tier 0 as the working configuration; a measured
0.2854 s/step at 512×512, making a large comparison grid affordable; the smoke adapter
(`EXP-016__smoke__…`, sha256 `e76f822bd3b6314a…`) as a validated artifact; **202.0 MiB as the
binding memory ceiling of the production path**; and three open decisions M5 deliberately did not
take — the trigger-token design, whether to run a long native 512×1536 training run, and whether
DreamBooth or Textual Inversion get measured comparisons at all.

## Evidence and commits

| what | where |
|---|---|
| registry rows | `experiments/registry.csv` — EXP-016a, EXP-016b, EXP-016, EXP-017a, EXP-017b, EXP-018, EXP-019a, EXP-019b |
| training summary | `docs/evidence/prototype-3/training-summary.md` |
| LoRA effect | `docs/evidence/prototype-3/lora-effect-baseline-vs-weight1.jpg`, `docs/evidence/EXP-018/` |
| combined stack | `docs/evidence/prototype-3/combined-stack-lora-ipadapter.jpg`, `docs/evidence/EXP-019/combined-stack.md` |
| micro-gates | `docs/evidence/EXP-016/`, `docs/evidence/EXP-017/` |
| decision | `docs/decisions/DR-009-fine-tuning-method.md` |
| risks | `docs/process/risk-register.md` — R1, R12, R14 |
| commits | `d78bf10` (EXP-016/017), `bd07d11` (EXP-018), `769bf85` (EXP-019) |

Adapters and generated images live in **git-ignored `outputs/`**; re-run the experiments to
regenerate them. Model weights are never committed.
