# EXP-034 — resident-service memory and state behaviour

**Date:** 2026-08-06 · **Milestone:** M7 (Prototype 5) · **Status:** PASS on every declared
criterion · **Runs:** 1 smoke + 12 matrix requests, one process each.

## Question

Every VRAM figure this project owns was measured under the rule adopted after the EXP-005
contamination incident: **one configuration per OS process**. The API is the opposite — one
process, resident, swapping between three LoRA adapters and between reference-conditioned and
prompt-only requests. EXP-019b and EXP-032 measured the production stack at 7985.5 MiB of
8187.5 MiB, leaving **202.0 MiB**. Nothing had measured what repeated switching does to it.

**This run deliberately breaks the one-config-per-process rule.** That is its purpose, and it is
why these are **service-residency figures that are not comparable** with the per-process
benchmarks in EXP-016…EXP-032. They answer a different question.

## Method

Frozen before execution in `scripts/measure_service_residency.py`: six cases, run twice, with
identical inputs in both cycles. Subject `"a mountain and a rising sun"` (FP2-shared, chosen in
M6 because an identical subject across styles attributes differences to the adapter rather than
the prompt), seed 42, LoRA weight 0.7 (DR-010), IP-Adapter scale 0.55 (DR-008), 512×1536.
Reference `R2` — project-original, natively 1:3 so it needs no crop, and from the **holdout**
split, so no LoRA in this project has ever seen it.

| # | style | reference |
|---:|---|---|
| 1 | minimal-geometric | prompt-only |
| 2 | ukiyo-e | reference |
| 3 | retro-poster | prompt-only |
| 4 | minimal-geometric | reference |
| 5 | ukiyo-e | prompt-only |
| 6 | retro-poster | reference |

Every adjacent pair changes style, and the reference flag alternates, so both transition
directions and a return to every style are covered.

## Results — 12 of 12 complete, no OOM, no escalation

| cycle | case | style | reference | alloc after | peak alloc | device | spare | s |
|---:|---:|---|---|---:|---:|---:|---:|---:|
| 1 | 1 | minimal-geometric | prompt-only | 3316.64 | 5143.73 | 7969.5 | 218.0 | 13.277 |
| 1 | 2 | ukiyo-e | reference | 3316.64 | 5143.73 | 7987.5 | **200.0** | 12.211 |
| 1 | 3 | retro-poster | prompt-only | 3316.64 | 5143.73 | 7969.5 | 218.0 | 12.163 |
| 1 | 4 | minimal-geometric | reference | 3316.64 | 5143.73 | 7987.5 | **200.0** | 12.237 |
| 1 | 5 | ukiyo-e | prompt-only | 3316.64 | 5143.73 | 7969.5 | 218.0 | 12.174 |
| 1 | 6 | retro-poster | reference | 3316.64 | 5143.73 | 7985.5 | 202.0 | 12.301 |
| 2 | 1 | minimal-geometric | prompt-only | 3316.64 | 5143.73 | 7969.5 | 218.0 | 12.193 |
| 2 | 2 | ukiyo-e | reference | 3316.64 | 5143.73 | 7987.5 | **200.0** | 12.440 |
| 2 | 3 | retro-poster | prompt-only | 3316.64 | 5143.73 | 7969.5 | 218.0 | 12.376 |
| 2 | 4 | minimal-geometric | reference | 3316.64 | 5143.73 | 7987.5 | **200.0** | 12.536 |
| 2 | 5 | ukiyo-e | prompt-only | 3316.64 | 5143.73 | 7969.5 | 218.0 | 12.638 |
| 2 | 6 | retro-poster | reference | 3316.64 | 5143.73 | 7987.5 | **200.0** | 12.500 |

All figures MiB. Live UNet LoRA modules: **128 in every request**. Peak process RSS 2978.59 MiB.

### Declared criteria, all met

| criterion | result |
|---|---|
| 12/12 complete, no OOM | PASS |
| exactly one style LoRA active per request | PASS |
| no previous style adapter remains active | PASS |
| prompt-only requests apply IP-Adapter scale 0.0 | PASS |
| cycle-2 output byte-identical to cycle-1, per case | PASS — 6 of 6 |
| same-case allocated growth ≤ 64 MiB between cycles | PASS — growth is **0.00 MiB** |
| physical device use never exceeds 8187.5 MiB | PASS |
| no monotonic growth across the sequence | PASS |

## What the numbers actually say

**There is no accumulation at all.** `allocated_after` is **3316.64 MiB in all 13 runs** — not
"within tolerance", identical. The 64 MiB allowance declared in advance was never approached.
Six unload/load cycles across three adapters left the allocator exactly where it started.

**Peak allocated is 5143.73 MiB in every run — byte-identical to M5's EXP-019b.** A one-shot
process measured in a different milestone and a resident service swapping adapters reach the
*same* peak allocation. That is the fourth milestone in which this cross-milestone continuity
has held, and it means residency costs nothing in allocated terms.

**The margin is tighter than the headline 202 MiB, not looser.** The worst observed spare is
**200.0 MiB**, on every reference-conditioned request. EXP-032's 202.0 MiB is reproduced exactly
in one row. Prompt-only requests sit at 218.0 MiB because the neutral placeholder is smaller
than the 512×1536 reference. **200 MiB is 2.4 % of the device and must never be described as
comfortable headroom.** A second adapter, a higher rank, a larger reference or ControlNet all
have to fit inside it.

**Byte-identical repeats are evidence of no residue, not proof of none.** All six cases
reproduced exactly, which is what a clean unload/load and a properly reset conditioning state
should produce. Had any differed, that would have been recorded as a **failure requiring
investigation** rather than as proof of adapter residue — nondeterminism or any other state
defect produces the same symptom, and separating them is the investigation.

**An unplanned cross-process result.** The smoke run executed in a *separate process* before the
matrix, with the same inputs, and produced sha256 `46bbf160e427…` — the same image the matrix
produced for case 1. Cross-process determinism therefore still holds for inference, consistent
with M4's 12/12 byte-identical baselines. This is an observation from two samples, not a
systematic determinism study.

## Evidence

- `service-residency.jsonl` — **13 rows: 1 smoke + 12 matrix.** The smoke row is the first
  `cycle 1 / case 1` entry and is kept rather than deleted; it is a single-case run in its own
  process and is excluded from the criteria evaluation, which used only the 12 matrix rows.
- `service-residency-verdict.json` — machine-readable verdict with per-case detail.
- `outputs/EXP-034/` — 12 PNGs, git-ignored like every other generated image.

## Reproduce

```
.venv/Scripts/python.exe scripts/measure_service_residency.py --smoke
.venv/Scripts/python.exe scripts/measure_service_residency.py
```

One process, nothing else on the GPU. Note R14: the adapters themselves cannot be regenerated
from their seed, so this reproduces the *measurement*, given the preserved checkpoint files.
