# Prototype 4 — style learning and visual comparison

**Milestone:** M6 · **Status:** Phase A and Phase B complete, **stopped at Gate 2**
**Answers:** RQ4 (how many images, what caption standards) and RQ5 (per-style vs multi-style)
**Builds on:** DR-007 (SD 1.5), DR-008 (IP-Adapter @ 0.55), DR-009 (LoRA rank 8, tier 0)

## Research questions

- **RQ4** — how many images per style, and what caption standards, does style learning need?
- **RQ5** — one multi-style LoRA, or separate per-style LoRAs?

### Hypotheses, as stated before any run

| | hypothesis | status |
|---|---|---|
| H1 | Style learning varies with training-set size across nested 12 ⊂ 24 ⊂ 44 subsets at equal compute | **O5 inconclusive** (Gate 1, Kylian) |
| H2 | *(replaced)* the original wording was unfalsifiable — "at least as strong" cannot be refuted by equality. Replaced by four explicit verdict rules | **style-only preferred** (Gate 1, Kylian) |
| H3 | Separate per-style LoRAs give cleaner style separation than one balanced multi-style LoRA | **open — Gate 2** |
| H4 | `retro-poster` transfers frames and pseudo-text into generations | **open — Gate 2** |
| H5 | Style strength and prompt adherence trade off as LoRA weight rises | **open — Gate 2** |

## Scope

Three styles in a fixed order set by risk: `minimal-geometric` → `ukiyo-e` → `retro-poster`.
512×512 training for all three. `dataset-v1.csv` opened **read-only** for the whole milestone
and asserted byte-identical at the end.

## What was decided before any GPU work

**Trigger tokens `xgeo` / `xkyo` / `xpst`.** The first candidate family was rejected on
measured tokenizer evidence: `dfukiyo` split into four BPE pieces and lost the shared prefix,
`dfposter` contained `poster</w>` which sits in its own style phrase, and a replacement `xuki`
collided with the literal words "uki e" in the ukiyo-e captions. **No tokenizer vocabulary
entry is added** — the text encoder is frozen, so an added embedding would never be trained.

**Style-only captions as the primary strategy, under test.** Justified by a caption audit
gathered *before* any run, not rationalised afterwards: 20 of 41 `retro-poster` captions are
play-title attributions, 9 of 55 `ukiyo-e` captions are truncated mid-phrase, and
`minimal-geometric` has only ~6 distinct phrases across 52 items. EXP-023 retrains the lead
style on the verbatim captions, changing nothing else, and both arms were scored blind.

## Phase A — pilots (6 runs, 6 passes, tier 0)

| arm | style | captions | images | pres./item | s/step | first → last loss |
|---|---|---|---:|---:|---:|---|
| EXP-020 | minimal-geometric | style-only | 44 | 6.818 | 0.284 | 0.0780 → 0.0044 |
| EXP-021 | ukiyo-e | style-only | 44 | 6.818 | 0.408 | 0.6583 → 0.0302 |
| EXP-022 | retro-poster | style-only | 36 | 8.333 | 0.294 | 0.4973 → 0.0351 |
| EXP-023 | minimal-geometric | **verbatim** | 44 | 6.818 | 0.294 | 0.0781 → 0.0045 |
| EXP-024n12 | minimal-geometric | style-only | **12** | 25.000 | 0.296 | 0.0648 → 0.0042 |
| EXP-024n24 | minimal-geometric | style-only | **24** | 12.500 | 0.331 | 0.0849 → 0.0052 |

EXP-025 generated the capped pilot matrix (108 of 108). EXP-026 found **0 of 108** near-copy
flags. The sheets were **blinded within style** and scored before the mapping was opened.

**Declared confound, recorded in code before results existed:** at fixed 300 steps the 12-image
arm presents each item 25.0×, the 24-image arm 12.5× and the 44-image arm 6.818×. This measures
**set size at equal compute, not at equal epochs**, for `minimal-geometric` only.

## Gate 1 — Kylian's decisions (2026-08-05)

Scores fixed and hashed **before** the blinding map was opened; no score changed afterwards.
Full record in `docs/evidence/prototype-4/GATE-1-approval.md`.

Checkpoints selected for traceability (GEO-7, UKY-1, PST-1) · **600 steps** for every full run ·
**style-only captions preferred** · **dataset size O5 inconclusive** · **no contingency
authorised** · **multi-style approved**, conditional on all three per-style runs passing.

## Phase B — approved runs (4 runs, 4 passes, tier 0)

| run | style | steps | s/step | wall | first → last loss | L2 |
|---|---|---:|---:|---:|---|---:|
| EXP-027 | minimal-geometric | 600 | 0.283 | 175.9 s | 0.0780 → 0.0025 | 4.752 |
| EXP-028 | ukiyo-e | 600 | 0.398 | 244.1 s | 0.6583 → 0.2297 | 4.080 |
| EXP-029 | retro-poster | 600 | 0.308 | 189.5 s | 0.4973 → 0.1425 | 4.972 |
| EXP-030 | multi-style | 1800 | 0.350 | 633.8 s | 0.6290 → 0.1960 | 8.307 |

**Peak allocated 3133.4 MiB in all ten runs of the milestone.** Training memory is set by
geometry alone.

**RQ5 fairness rule, frozen before the run:** each style's exposure is matched to its own
per-style run — exactly 600 presentations each, 1800 total — rather than dividing a shared
total three ways, which would have given each style a third of the exposure it got alone. The
runner asserts the achieved exposure and fails rather than producing an unbalanced adapter.

EXP-031 generated 252 of a capped 432. EXP-032 measured the combined stack. EXP-033 found
**0 of 252** near-copy flags, with the holdout control at a comparable distance.

## Real problems diagnosed in this prototype

**1. The approved plan's trigger tokens were wrong.** Found by checking them against the live
tokenizer rather than assuming, before any training run was spent on them.

**2. Training runs are not bit-reproducible from their recorded seed.** The adapter is built
with `init_lora_weights="gaussian"`, drawing from the global torch RNG, which the runner never
seeds. Diagnosed from the *shape* of the discrepancy: same-step adapters differ by an L2 of
~158 against a norm of ~112, a ratio of √2 — the signature of two independent draws, not of
floating-point drift. The data pipeline was verified deterministic in the same pass. Recorded
as a limitation; **not fixed mid-milestone**, because seeding the initialisation would alter
every run the Gate-1 arms were compared against.

**3. My own matrix orchestration generated 24 duplicate images.** Blocks A and B overlap at
weight 0.7. The duplicates were byte-identical — which incidentally confirms generation
determinism — but they wasted capped budget and put a **self-pair into 12 of 102 diversity
cells**, biasing them toward zero and manufacturing apparent mode collapse out of a bug. Found
by noticing a `seeds=5` count where the design allowed at most 3. Fixed in the plan, in the
diversity computation, and guarded by a regression test; the matrix was not regenerated because
its evidence is a valid superset of the fixed plan.

**4. Line-ending normalisation would have broken a hash lock.** `core.autocrlf` is true and no
`.gitattributes` existed, so committing the Gate-1 scoring artifact would have rewritten it to
CRLF on checkout and silently invalidated the sha256 that proves no score was edited after
unblinding.

## Acceptance criteria

- **Pass** — all technical gates hold; recognisably on-style at some weight in 0.4–1.0 without
  collapsing prompt adherence; no unresolved memorisation flag.
- **Partial pass** — gates hold and style is visible, but with a named defect. **Never upgraded.**
- **Failure** — a first-class recorded result.
- **Fallback** — ship what passed and report the failure. **A failed style is never quietly
  dropped from the record.**

**Technical acceptance is met: 10 of 10 runs pass every gate.** The style-quality half of the
criteria is unjudged and stays that way until Gate 2.

## Evidence

`experiments/registry.csv` (EXP-020…EXP-033) · `docs/evidence/EXP-020…EXP-033/` ·
`docs/evidence/prototype-4/` (caption audit, pilot sheets, Gate-1 approval, full-run
validation, final sheets, Gate-2 handover) · `docs/decisions/DR-010-style-learning-configuration.md`
(**draft, no conclusion**).

Model weights, adapters and full-resolution outputs live in git-ignored `outputs/` and are
never committed; re-run the recorded commands to regenerate them.

## Impact on the next iteration

Prototype 5 inherits a **202.0 MiB** production memory ceiling at the deck format, measured
identically for all four candidates, and the standing rule that this is never described as
comfortable headroom. Which checkpoint it ships, at which weight, and whether it ships one
adapter or three, are Gate-2 decisions and are not made here.
