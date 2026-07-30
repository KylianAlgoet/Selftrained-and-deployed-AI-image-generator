# Prototype 1 — Local base-model benchmark (M3)

**Status:** measurements complete; **awaiting Kylian's rubric scores and visual approval before DR-007.**
**Date:** 2026-07-30 · **Research questions:** RQ2 (base-model feasibility on 8 GB), RQ8 (deck aspect ratio), RQ10 (applied)

This document records what was measured. It deliberately **does not name a winning base model** —
that conclusion requires the student's qualitative scores, which are collected at the human-review
gate (`docs/evidence/EXP-006-scoring/`).

## Research questions and hypotheses

| RQ | Hypothesis at the start | Status after measurement |
|---|---|---|
| RQ2 | SD 1.5-class at 512 px runs comfortably; SDXL inference works but is marginal on 8 GB | **Confirmed, and sharper than expected** — SDXL does not fit at native resolution at all (see below) |
| RQ8 | Direct tall generation degrades composition; generate-then-crop is more reliable | **Refuted on the memory/reliability axes**; composition judgement pending scoring |
| RQ10 | A fixed prompt/seed kit + 1–5 rubric yields comparable scores | Kit frozen and hash-locked; rubric applied at the gate |

## Scope

Inference only. **No training, fine-tuning, or LoRA** — that is Prototype 3. No reference-image
conditioning (Prototype 2). No backend or frontend work.

## What was built

| Component | Purpose |
|---|---|
| `ml/inference/gpu_smoke_test.py` | EXP-001 hard gate: CUDA availability, device identity, VRAM, fp32/fp16/bf16 correctness |
| `ml/evaluation/prompt_kit.py` | The frozen kit, hash-locked by pytest against fingerprint `c40749bc…` |
| `ml/inference/bench_schema.py` | Pure data model: candidate registry, memory tiers, result schema, aggregation |
| `ml/inference/benchmark.py` | The measurement harness (synchronised timing, three VRAM figures, RSS, per-run failure rows) |
| `ml/inference/aspect_ratio.py` | EXP-005 geometry comparison |
| `scripts/run_benchmarks.py` | One candidate per fresh OS process, then aggregation and cross-model sheets |
| `scripts/run_aspect_ratio.py` | One geometry per fresh OS process |
| `scripts/build_scoring_form.py` | Blank rubric + scoring form for the gate |

**66 pytest tests pass**, all CPU-only. The schema, filename, tier-escalation and aggregation logic are
testable without a GPU because `bench_schema` imports neither torch nor diffusers.

## Environment (EXP-001, verified not assumed)

torch **2.13.0+cu126**, bundled CUDA runtime **12.6**, diffusers 0.39.0, transformers 5.14.1,
Python 3.11.0, RTX 4060 Laptop GPU (sm_89), **8187.5 MiB VRAM**, driver **610.88**.

Two corrections to the Phase 0 audit came out of this:

1. The driver is **610.88**, not the 610.74 recorded on 2026-07-27 — it was updated in between.
2. `nvidia-smi`'s CUDA version (13.3) is the **driver's maximum supported API**, not a toolkit
   PyTorch must match. A CUDA 12.6 wheel runs correctly on it. Both numbers are recorded side by
   side in the evidence so they can never be conflated again.

A real blocker is also recorded: the venv shipped **pip 22.3**, which cannot resolve modern torch
wheels at all (it rejects metadata whose name is normalised with underscores). Upgrading to pip 26.2
was required before any install succeeded.

## Measured results

All runs at **memory tier 0** (fp16, SDPA, no offload). No tier escalation was needed anywhere.

### Model comparison — Track A (controlled: every candidate at 512×512)

| Model | Median | Peak allocated | Peak reserved | Peak device | Peak RSS | Runs |
|---|---|---|---|---|---|---|
| SD 1.5 | **4.07 s** | 2675 MiB | 3246 MiB | 4360 MiB | 2667 MiB | 15/15 |
| SDXL base | 16.51 s | 7859 MiB | 9030 MiB | 8188 MiB | 2310 MiB | 15/15 |

### Model comparison — Track B (each candidate at its designed resolution)

| Model | Resolution | Median | Peak allocated | Peak reserved | Peak RSS | Runs |
|---|---|---|---|---|---|---|
| SD 1.5 | 512×512 (native) | 4.07 s | 2675 MiB | 3246 MiB | 2667 MiB | 15/15 |
| SDXL base | 1024×1024 (native) | **118.73 s** | **10738 MiB** | **14510 MiB** | 6807 MiB | 15/15 |

SD 1.5's native resolution *is* the Track A resolution, so it has no separate Track B run. That is a
property of the candidate, not a gap in the method.

### The most important finding: "30/30 ok" is misleading for SDXL

SDXL reported **zero failures at every resolution**, which read alone would suggest it runs fine on
this hardware. It does not. At 1024×1024, peak allocated (**10738 MiB**) and peak reserved
(**14510 MiB**) both **exceed the 8187.5 MiB of physical VRAM**. Windows WDDM silently spilled into
shared host memory — process RSS rose to 6807 MiB — instead of raising a CUDA out-of-memory error.

Because no exception was ever thrown, the memory-tier escalation logic never triggered. The model
degraded quietly rather than failing loudly. Cost: about **29× SD 1.5 per 512 px image**, and about
**118 s per native image**. Even at 512 px SDXL saturates the entire device (8188 MiB).

This is exactly the class of result that the three-way VRAM instrumentation existed to catch: a
single "peak VRAM" number would have looked unremarkable.

### Aspect ratio (EXP-005, RQ8) — SD 1.5, one geometry per fresh process

| Strategy | Resolution | Median | Spread | Peak allocated |
|---|---|---|---|---|
| `direct-1x1` | 512×512 | 4.11 s | 0.08 s | 2675 MiB |
| `direct-1x2` | 512×1024 | 8.96 s | 0.09 s | 3284 MiB |
| `direct-1x3` | 512×1536 | 15.24 s | 0.20 s | 3892 MiB |
| `square-crop` | 512×512 → **170×512 usable** | 4.28 s | 0.53 s | 2675 MiB |

**The RQ8 hypothesis is refuted on the memory and reliability axes.** Direct 1:3 generation reached
512×1536 in 3892 MiB — under half the VRAM budget — with 24/24 runs succeeding. `square-crop`'s real
cost is resolution: a 1:3 strip out of a 512×512 image leaves only **170×512 usable pixels**, far
below what a deck print needs (recorded in `square-crop-resolution-cost.json`).

1:3 is a **stated approximation** of the true ~1:3.6 deck ratio, because latent dimensions must be
multiples of 64. Composition quality itself is Kylian's to judge at the gate.

### Factual observation for review (not a quality judgement) — and it is resolution-dependent

The prompt phrase "skateboard decal artwork" is often interpreted **literally**, producing an image
*of a physical deck* rather than the flat artwork that would be printed on one. But this is **not
uniform across candidates**, and an earlier draft of this document overstated it as universal before
the Track B sheet was inspected. What the images actually show:

| Condition | Observed output |
|---|---|
| SD 1.5 @ 512×512 (native) | Predominantly photographic product mockups — decks on concrete, on wooden floors, mounted on doors, a sticker on a wall beside a potted plant |
| SDXL @ 512×512 (out of native) | Deck-shaped panels and vertical strips — literal, but graphic rather than photographic |
| **SDXL @ 1024×1024 (native)** | **Flat artwork with no mockup framing** — a wolf-head medallion, a flat geometric composition, a Great Wave print, tiled skull patterns |

So the literal-mockup reading is strongest at 512 px and largely disappears when SDXL runs at the
resolution it was trained for. **This is exactly the distinction the two-track design existed to
expose:** judging both candidates only at 512×512 would have produced a materially wrong description
of SDXL's behaviour.

It matters beyond this milestone because the same phrasing comes from the dataset caption template, so
these are also the pre-training baselines that Prototypes 3–4 will measure LoRA effect against.
Whether any of it is a problem is for the student to decide; that it happens is measured.

## Failures and corrections (first-class results)

1. **EXP-003 blocked, not missing.** `stabilityai/stable-diffusion-2-1-base` returns **HTTP 401**, as
   do `-2-1` and `-2-base`, while SDXL from the same organisation returns 200 — repository gating,
   not an outage. Per the approved plan, Kylian was asked rather than authenticating or substituting
   a model, and chose two candidates. Three declined alternatives are recorded, including an ungated
   community mirror rejected because its fidelity cannot be verified while the original is gated.
   → `docs/evidence/EXP-003/blocked-gated-repository.md`

2. **A bug in the instrumentation, caught by the mandated smoke test.** The resource sampler stored
   its stop flag as `self._stop`, shadowing `threading.Thread._stop()` — an internal method `join()`
   calls — so every `stop()` raised `'Event' object is not callable` and destroyed the result row of a
   run that had *already succeeded*. Found on the very first one-image run, before ~90 minutes of GPU
   time was committed. Fixed, hardened so instrumentation teardown can never fail a run, and covered
   by four regression tests.

3. **A measurement-methodology correction, with a refuted hypothesis.** EXP-005's first run put all
   four geometries in one process, which contaminated the reserved and device VRAM figures (the
   caching allocator retains its pool across `reset_peak_memory_stats()`) and inflated `square-crop`
   to 7.96 s for provably identical work. The obvious explanation, thermal throttling, was **tested
   and ruled out**: on a hotter, more throttled card the same work ran *faster* (4.10 s). The cause
   was in-process allocator state. Re-running one strategy per process cut timing spread ~20×.
   → `docs/evidence/EXP-005/measurement-methodology-correction.md`

## Evidence

- `docs/evidence/EXP-001/` — `cuda-smoke-test.json`, `pip-freeze.txt`, `nvidia-smi.txt`
- `docs/evidence/EXP-002/`, `EXP-004/`, `EXP-005/` — per-run JSONL, CSV, summaries, pinned revision SHAs
- `docs/evidence/EXP-003/blocked-gated-repository.md`
- `docs/evidence/prototype-1/` — Track A and Track B cross-model contact sheets, combined CSV, unscored summary
- `docs/evidence/EXP-006-scoring/` — blank rubric and scoring form
- `experiments/registry.csv` — EXP-001…EXP-005
- Full-resolution PNGs in git-ignored `outputs/EXP-00{2,4,5}/` (84 images)

## Reproducibility

Every run records a **pinned Hugging Face commit SHA** (`451f4fe1…` for SD 1.5, `46216598…` for
SDXL), the frozen kit fingerprint, torch/diffusers versions, and an output SHA-256. Repeatability is
claimed **only within the same recorded environment** — same model revision, hardware, and library
versions. No claim is made that identical images reproduce across other GPUs, CUDA versions, PyTorch
versions, or Diffusers versions.

Reproducibility caveat: candidate B cannot be obtained today without authenticating to Hugging Face.

## Conclusion (measurements only)

RQ2 is answered on feasibility: **SD 1.5 runs with large headroom on 8 GB; SDXL does not fit at its
native resolution and only appears to work via silent host-memory spill.** RQ8's hypothesis is
refuted on memory and reliability grounds; direct tall generation is cheap and reliable, while
generate-then-crop pays a severe resolution penalty.

**The base-model selection (DR-007) is deliberately not made here.** It requires the rubric scores,
which are the student's own research judgement. See the gate materials.

## Impact on the next iteration

- Prototypes 3–4 (LoRA) should assume the **SD 1.5-class VRAM envelope**; the SDXL figures indicate
  LoRA training at 1024 is not viable on this hardware, which is direct evidence for risk R1.
- **One configuration per process** is adopted for all VRAM/timing measurement from here on.
- The literal "skateboard decal" interpretation is a prompt-design question to revisit in
  Prototypes 2 and 5.
- The frozen kit and its fingerprint carry forward unchanged.

## Related commits

`e5684f1` style relabel · `37650b6` pinned dependencies · `1d51ccc` CUDA smoke test ·
`f646ee9` frozen prompt kit · `eae6e41` benchmark runner · `e25f1e0` orchestrator + scoring form ·
`8829664` benchmark measurements
