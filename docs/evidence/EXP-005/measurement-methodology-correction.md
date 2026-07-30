# EXP-005 measurement-methodology correction (2026-07-30)

A correction to how EXP-005 was measured, found while checking an anomaly in its own
results. Recorded rather than silently re-run, because the artefact and the way it was
diagnosed are themselves a result: they change how every timing and VRAM figure in
Prototype 1 must be read.

## The anomaly

The first EXP-005 run executed all four aspect-ratio strategies in **one process**.
`square-crop` generates at 512×512 and then crops — byte-for-byte the same diffusion
work as `direct-1x1`. Yet it measured **7.96 s median against direct-1x1's 4.98 s**, a
60 % difference for provably identical computation.

Two of the reported figures were therefore wrong, and one was not:

| Field | Trustworthy? | Why |
|---|---|---|
| `peak_vram_allocated_mb` | **Yes** | Reset per run and reflects live tensors only. Reported 2675.38 MiB for *both* `direct-1x1` and `square-crop` — identical, which is what exposed the artefact. |
| `peak_vram_reserved_mb` | **No** | `torch.cuda.reset_peak_memory_stats()` resets the peak counter but does **not** return the caching allocator's pool. After 512×1536 grew the pool to 5762 MiB, the later 512×512 strategy immediately re-reported 5762 MiB. |
| `peak_device_used_mb` | **No** | Same cause, one level out: the retained pool is still resident on the device, so `mem_get_info` counts it. `square-crop` inherited 6875.5 MiB — exactly the 1536 geometry's figure. |

## Hypothesis tested and REFUTED: thermal throttling

The obvious explanation was clock throttling, since the RTX 4060 Laptop is power-capped
and the later strategies ran on a hot card (`nvidia-smi` showed 2250 MHz against a
3105 MHz maximum at 69 °C). This was tested rather than assumed.

Re-running the identical 512×512 workload in a **fresh process on an even hotter, more
throttled card** (2250 → 1965 MHz, 66 → 75 °C):

```
512x512 seed=42:   5.11s
512x512 seed=1337: 4.097s
512x512 seed=2026: 4.104s
warm-card median:  4.10s
```

**4.10 s — faster than the 4.98 s "cold" figure, and far faster than 7.96 s.** Thermal
throttling is ruled out as the cause. Had this not been tested, the report would have
carried a confidently stated but false mechanism.

## Actual cause

In-process caching-allocator state. Sequentially generating at a larger geometry and
then a smaller one leaves a large, fragmented pool that inflates the reserved/device
figures outright and perturbs allocation timing. Nothing about the `square-crop`
strategy is slow; the measurement was contaminated by what ran before it.

## Fix

One strategy per fresh OS process (`scripts/run_aspect_ratio.py`), mirroring what the
model benchmark already did per candidate. The effect on variance is decisive:

| Strategy | Single process (contaminated) | Fresh process (clean) |
|---|---|---|
| `direct-1x2` | 9.16 – 11.05 s (spread 1.89 s) | 8.91 – 9.00 s (spread **0.09 s**) |
| `direct-1x3` | 15.64 – 17.93 s (spread 2.29 s) | 15.14 – 15.34 s (spread **0.20 s**) |

Roughly a 20× reduction in spread. The wide variance in the first run was not GPU noise;
it was allocator interference, and it would have made every timing claim soft.

The contaminated first-run data is retained outside the repository (it contains no
information the clean run lacks) and is superseded by `results-sd15.jsonl`.

## Consequences for the rest of Prototype 1

1. **EXP-002 and EXP-004 are unaffected.** Each candidate already ran in its own
   process, and within each process Track A preceded the larger Track B, so no smaller
   geometry inherited a larger one's pool.
2. **`peak_vram_reserved_mb` and `peak_device_used_mb` must be read as
   process-lifetime high-water marks, not per-configuration requirements.** They are
   still the right figures for answering "does this model fit in 8 GB", which is why
   they are kept — SDXL's 14510 MiB reserved at 1024×1024 is a genuine finding — but
   they cannot be compared across configurations measured in the same process.
3. **General rule adopted for Prototypes 3-5:** one configuration per process whenever
   VRAM or timing is being measured. Convenience of a single long-lived process costs
   measurement validity.

## Lesson learned

The anomaly was only visible because three VRAM figures were recorded instead of one. A
single number would have looked plausible and gone unchallenged. Recording overlapping,
partially redundant measurements is what made the contradiction detectable — and
checking a suspicious result against a cheap controlled experiment is what stopped a
false mechanism from reaching the report.
