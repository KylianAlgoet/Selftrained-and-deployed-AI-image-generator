# EXP-007 — IP-Adapter environment gate (hard gate)

**Date:** 2026-08-01 · **Status:** **PASSED** · **Prototype 2 / M4, execution step 2**

The rule that produced this experiment is the one that caught the sampler bug in M3
before ~90 minutes of GPU time were spent: *nothing downstream runs until the smallest
possible end-to-end test passes.* EXP-008…EXP-014 were not started until this gate was
green.

## Question

Does `h94/IP-Adapter` load onto the pinned SD 1.5 at a pinned revision, actually attach
its attention processors to the UNet, generate one 512×512 image, and what does it cost
in VRAM against bare SD 1.5 on this 8 GB GPU?

## Method

Two runs, each in its **own fresh OS process** (the §D.5 boundary), same frozen prompt
kit, same seed, same geometry, same memory tier:

| | run A | run B |
|---|---|---|
| method | SD 1.5 text-only | SD 1.5 + IP-Adapter |
| condition | C1 (R1 retro-poster × `P1-poster`) | C1 |
| level | none | medium (`scale=0.55`) |
| seed / geometry / tier | 42 / 512×512 / 0 | 42 / 512×512 / 0 |
| `process_config_key` | `text-only@512x512@tier0` | `ip-adapter@512x512@tier0` |

One discarded warm-up per process. Frozen-kit fingerprint recorded in both gate records:
`c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228` — unchanged.

Commands actually run:

```
.venv\Scripts\python.exe -m ml.inference.reference_conditioning --exp EXP-007 \
    --method text-only --conditions C1 --levels none --seeds 42 \
    --width 512 --height 512 --gate --suffix gate

.venv\Scripts\python.exe -m ml.inference.reference_conditioning --exp EXP-007 \
    --method ip-adapter --conditions C1 --levels medium --seeds 42 \
    --width 512 --height 512 --gate
```

## Pinning — both components, deliberately

Diffusers 0.39.0 pops `revision` and forwards it to the adapter weights but **not** to
`CLIPVisionModelWithProjection.from_pretrained` (`loaders/ip_adapter.py`), so the image
encoder would have come from a moving `main`. Since that encoder is 2.35 GiB of the
download and shapes every embedding, the reproducibility claim would have been quietly
false. The runner therefore loads and registers the encoder itself at the pinned
revision before calling `load_ip_adapter`, which then skips its own encoder load.

Both SHAs are recorded per run and both came back pinned:

| component | repo | revision |
|---|---|---|
| base model | `stable-diffusion-v1-5/stable-diffusion-v1-5` | `451f4fe16113bff5a5d2269ed5ad43b0592e9a14` |
| adapter weights | `h94/IP-Adapter` · `models/ip-adapter_sd15.safetensors` | `018e402774aeeddd60609b4ecdb7e298259dc729` |
| image encoder | `h94/IP-Adapter` · `models/image_encoder` | `018e402774aeeddd60609b4ecdb7e298259dc729` |

`.safetensors` only; the `.bin` twins in the same repository were never loaded.

## Result 1 — the adapter is genuinely attached

Read back from the **live UNet**, not inferred from a call returning without error
(`load_ip_adapter` replacing nothing would also return cleanly):

| | text-only | IP-Adapter |
|---|---|---|
| IP-Adapter attention processors | `[]` | `['IPAdapterAttnProcessor2_0']` |
| IP-Adapter processor count | 0 | **16** |
| total UNet attention processors | 32 | 32 |

16 of 32 is the expected signature rather than a coincidence: SD 1.5's UNet has one
self-attention (`attn1`) and one cross-attention (`attn2`) processor per block, and
IP-Adapter replaces the cross-attention half only. The self-attention path is untouched,
which is consistent with the mechanism claimed in the RQ6 hypothesis — that the scale
acts on a separate cross-attention path and leaves the prompt path intact.

## Result 2 — measured VRAM cost of the method

All figures from `torch.cuda`, tier 0, fp16, 512×512, safety checker present but
disabled in both processes (identical policy, so the comparison is like-for-like).

| figure (MiB) | text-only | IP-Adapter | delta |
|---|---|---|---|
| post-load allocated | 2056.60 | 3305.29 | **+1248.69** |
| post-load reserved | 2108.00 | 3436.00 | +1328.00 |
| peak allocated (per run) | 2675.38 | 3924.07 | **+1248.69** |
| peak reserved (process) | 3246.00 | 4582.00 | +1336.00 |
| peak device used (process) | 4359.50 | 5695.50 | +1336.00 |

The post-load and peak allocated deltas are **identical to the hundredth of a MiB**
(+1248.69), which is what a fixed resident cost looks like: the encoder and adapter are
loaded once and do not grow with the denoising loop.

**This 1248.69 MiB is a genuine, unavoidable cost of the IP-Adapter *generation* method
and belongs in its VRAM figure.** The same CLIP encoder used later in Phase 2 to compute
similarity indicators is a *different workload* and enters no generation figure — see
`docs/evidence/EXP-014/`. Reporting IP-Adapter without its encoder would understate the
method exactly as removing a safety checker from one Prototype 1 candidate and not the
other would have distorted that benchmark.

**Headroom.** Peak device used 5695.50 MiB against 8187.5 MiB of physical VRAM leaves
~2492 MiB. No run exceeded physical VRAM, so no `vram_overflow_suspected` flag was
raised and no memory tier escalation was needed. Tier 0 throughout.

## Result 3 — latency

| | text-only | IP-Adapter |
|---|---|---|
| generate seconds (30 steps) | 3.282 | 3.446 |
| effective steps | 30 | 30 |
| s / effective step | 0.1094 | 0.1149 |
| load seconds | 20.539 | 104.145 |

The +0.164 s per image (+5.0 %) is the image-encoder forward plus the extra
cross-attention work per step. **It is a single measurement at one seed and one
condition, not a benchmark** — the sweeps in EXP-008/EXP-009 carry the multi-run
figures.

**The 104.145 s load is not a warm-cache load time.** It includes the first-time
download of the adapter and image encoder, because the download happens inside
`from_pretrained`. Measured cache footprint afterwards:

| file | size |
|---|---|
| `models/image_encoder/model.safetensors` | 2411.2 MiB |
| `models/ip-adapter_sd15.safetensors` | 42.6 MiB |
| **total** | **2453.8 MiB** |

A warm-cache load figure is **not measured here**; the EXP-009 runs record one, since
their cache is already populated. The cache lives at
`C:\Users\kylia\.cache\huggingface`, outside the repository, and nothing from it is
tracked in Git.

## Gate decision

| gate condition | result |
|---|---|
| adapter loads at the pinned revision | **pass** |
| image encoder loads at the *same* pinned revision | **pass** |
| IP-Adapter attention processors present in the UNet | **pass** (16 of 32) |
| one 512×512 image generated | **pass** |
| VRAM delta against bare SD 1.5 measured | **pass** (+1248.69 MiB) |
| runs within physical VRAM at tier 0 | **pass** |
| frozen-kit fingerprint unchanged | **pass** |

**EXP-007 passed, so EXP-008…EXP-014 were authorised to proceed.** The pre-declared
fallback (img2img alone) was not needed.

## What this experiment does not establish

No quality judgement whatsoever. That the adapter is attached and affordable says
nothing about whether reference influence is *controllable*, monotone, or visually
useful — those are RQ6's actual questions, answered by the sweeps and by the human
rubric at the review gate. In particular a single image at one scale cannot show
monotonicity, and nothing here compares IP-Adapter against img2img.

## Evidence files

- `gate-text-only-512x512-gate.json` — run A record
- `gate-ip-adapter-512x512.json` — run B record, including the live-UNet processor counts
- `results-text-only-512x512-gate.jsonl` / `.csv`, `summary-text-only-512x512-gate.md`
- `results-ip-adapter-512x512.jsonl` / `.csv`, `summary-ip-adapter-512x512.md`
- `cuda-gate-recheck.json` — EXP-001 CUDA smoke test re-run on today's driver
- `pip-freeze.txt` — the exact installed stack
- Images: `outputs/EXP-007/` (not committed, per the outputs policy)
