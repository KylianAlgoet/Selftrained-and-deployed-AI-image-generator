# DR-007: Base model and deck-format strategy for Prototypes 2–5

**Date:** 2026-07-30 · **Status:** accepted (approved by Kylian after manual review of the Prototype 1 evidence)
**Answers:** RQ2 (base-model feasibility on 8 GB VRAM), RQ8 (deck aspect ratio)
**Supersedes:** the open question deliberately left in `docs/03-architecture.md` section D-D, which decided the
Diffusers toolchain (DR-004) but explicitly did **not** decide the base model.

## Context

The project needs a pretrained diffusion base model that can run **locally** on the audited hardware
(RTX 4060 Laptop GPU, **8187.5 MiB VRAM**, 16 GB system RAM) for interactive skateboard-decal
generation, and that must still leave room for reference-image conditioning (Prototype 2) and LoRA
fine-tuning (Prototypes 3–4). Phase 0 recorded "SD 1.5-class at 512 px runs and trains; SDXL
inference works but training is marginal" as a **hypothesis only**, to be settled with measurements.

Prototype 1 produced those measurements. Every figure below was measured on this machine; none is
estimated.

## Alternatives considered

| Candidate | Outcome |
|---|---|
| **SD 1.5** (`stable-diffusion-v1-5/stable-diffusion-v1-5` @ `451f4fe1`) | Benchmarked — EXP-002 |
| **SDXL base 1.0** (`stabilityai/stable-diffusion-xl-base-1.0` @ `46216598`) | Benchmarked — EXP-004 |
| **SD 2.1 base** (`stabilityai/stable-diffusion-2-1-base`) | **BLOCKED** — HTTP 401, repository gated (EXP-003) |
| FLUX.1-dev | Screened out before download: non-commercial licence; ~24 GB weight class, far beyond 8 GB |
| FLUX.1-schnell | Screened out: Apache-2.0 but same size class; would need quantised third-party builds → deadline risk |
| SD 3.5 Medium | Screened out: gated, and immature adapter ecosystem for Prototypes 2–4 |
| Closed APIs (DALL·E, Midjourney, Firefly) | Screened out: violate the local-inference requirement of the assignment |

### The blocked candidate is a limitation, not a footnote

`stabilityai/stable-diffusion-2-1-base` returns **HTTP 401**, as do `stable-diffusion-2-1` and
`stable-diffusion-2-base`, while SDXL from the same organisation returns 200 — so this is repository
gating, not an outage or a local network fault. Per the approved plan, Kylian was asked rather than
authenticating or silently substituting a model, and chose to proceed with two candidates.

Three alternatives were offered and declined, each for a stated reason: creating a Hugging Face
account (would add an auth dependency to the reproducibility story), using the ungated community
mirror `sd2-community/stable-diffusion-2-1` (a third-party re-upload whose fidelity **cannot be
verified while the original is gated** — weaker provenance than this project applies to its own
dataset), and substituting `segmind/SSD-1B` (a new candidate outside the approved registry).

**Consequence, stated plainly: this decision rests on two measured candidates, not three.** The
mid-point of the intended comparison is missing, and anyone re-running the benchmark today cannot
obtain candidate B without authenticating. → `docs/evidence/EXP-003/blocked-gated-repository.md`

## Criteria and measured evidence

All runs at **memory tier 0** (fp16, SDPA attention, no offload). No memory-tier escalation was needed
anywhere. Track A and Track B are reported **separately and never averaged** — the gap between them is
the finding.

### Track A — controlled feasibility (both candidates at 512×512)

| Criterion | SD 1.5 | SDXL base |
|---|---|---|
| Median generation time | **4.07 s** | 16.51 s (**4.1× slower**) |
| Peak VRAM allocated | **2675 MiB** | 7859 MiB (**2.9×**) |
| Peak VRAM reserved | 3246 MiB | 9030 MiB |
| Peak device used | 4360 MiB | **8188 MiB — the entire GPU** |
| Runs succeeded | 15/15 | 15/15 |
| Human aggregate scores | 3/3/4/3/3/4/3 | 3/3/4/3/3/4/3 — **identical** |

Under the controlled condition SDXL bought **no qualitative advantage whatsoever** at 4.1× the time
and 2.9× the memory.

### Track B — each candidate at its designed resolution

| Criterion | SD 1.5 @ 512×512 (native) | SDXL @ 1024×1024 (native) |
|---|---|---|
| Median generation time | **4.07 s** | **118.73 s (29× slower)** |
| Peak VRAM allocated | **2675 MiB** | **10738 MiB** |
| Peak VRAM reserved | 3246 MiB | **14510 MiB** |
| Peak process RSS | 2667 MiB | 6807 MiB |
| Runs succeeded | 15/15 | 15/15 |
| prompt_adherence | 3 | **4** |
| style_consistency | 3 | **5** |
| visual_quality | 4 | **5** |
| decal_suitability | 3 | **4** |
| composition | 3 | **4** |
| artefacts | 4 | 4 |
| originality | 3 | 3 |

`diversity_across_seeds` was **not scored** (the review sheets showed the fixed seed-42 comparison
only) and `reference_influence` is **N/A** until Prototype 2. Neither has been invented.
→ `docs/evidence/EXP-006-scoring/human-scores.md`

### The decisive technical finding: SDXL does not fit, it spills

SDXL reported **30/30 successful runs**, which read alone suggests it runs fine on this hardware.
**It must not be described that way.** At 1024×1024, peak allocated (**10738 MiB**) and peak reserved
(**14510 MiB**) both **exceed the 8187.5 MiB of physical VRAM**. Windows WDDM silently spilled the
overflow into **shared host memory** — process RSS rose to 6807 MiB — instead of raising a CUDA
out-of-memory error.

Because no exception was ever raised, the benchmark's memory-tier escalation logic never triggered:
there was nothing to catch. **SDXL degraded quietly rather than failing loudly**, and the 118.73 s
median is the cost of that spill across the PCIe bus. Even at 512×512 it saturates the whole device
(8188 MiB device-used).

This was only detectable because three VRAM figures were recorded instead of one. A single
"peak VRAM" number would have looked unremarkable and the report would have carried a false claim.

## Decision

**Selected base model for Prototypes 2–5: Stable Diffusion 1.5** (`stable-diffusion-v1-5/stable-diffusion-v1-5`, pinned at revision `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`).

**SDXL base 1.0 is retained as the visual-quality benchmark, not as the default local production model.**

Stated honestly, without collapsing the trade-off:

| Question | Answer |
|---|---|
| Visual-quality winner | **SDXL at native 1024×1024** (style_consistency 5 vs 3, visual_quality 5 vs 4) |
| Practical feasibility winner, and selected project base | **SD 1.5** |
| Selected deck-format strategy | **Direct 1:3 generation at 512×1536** |
| Rejected main deck strategy | **square-crop** (~170×512 usable — far below deck-print resolution) |
| Blocked third candidate | **SD 2.1 base** — HTTP 401 access restriction (EXP-003) |

### Justification

Combining the measured evidence with Kylian's scores:

1. SD 1.5 generated 512×512 images in a measured median of **4.07 s**.
2. SDXL required **16.51 s** at 512×512.
3. SDXL required **118.73 s** at native 1024×1024.
4. SD 1.5 used ~**2675 MiB** peak allocated VRAM at 512×512.
5. SDXL used ~**7859 MiB** at 512×512 and **saturated the physical GPU**.
6. SDXL at 1024×1024 allocated ~**10738 MiB against 8188 MiB physical VRAM**.
7. SDXL native inference **only completed because Windows WDDM silently spilled into shared host RAM**.
8. **"30/30 successful" must not be described as SDXL fitting comfortably on this hardware.**
9. SD 1.5 generated direct **512×1536** deck-format images using ~**3892 MiB** peak allocated.
10. SD 1.5 leaves substantially more headroom for IP-Adapter / reference conditioning and later LoRA training.
11. SD 1.5 carries lower implementation, latency, memory, and bachelor-deadline risk.
12. SDXL produced the strongest native-resolution visual quality, but that advantage **does not
    outweigh** its hardware and latency costs for an interactive local application.

The Track A result is what makes this clear-cut rather than a close call: at the *same* resolution the
student scored the two models **identically**, so SDXL's quality advantage exists only at a resolution
this GPU cannot actually hold.

## Deck-format decision (RQ8)

Measured on SD 1.5, one geometry per fresh OS process, 24/24 runs succeeded at tier 0:

| Strategy | Resolution | Median | Peak allocated | visual_quality | decal_suitability | composition |
|---|---|---|---|---|---|---|
| `direct-1x1` | 512×512 | 4.11 s | 2675 MiB | 4 | **2** | 3 |
| `direct-1x2` | 512×1024 | 8.96 s | 3284 MiB | 4 | 4 | 4 |
| **`direct-1x3`** | **512×1536** | 15.24 s | **3892 MiB** | 4 | **5** | 4 |
| `square-crop` | 512×512 → ~170×512 | 4.28 s | 2675 MiB | 3 | **2** | 3 |

**Selected: direct 1:3 generation at 512×1536.** It produces a tall decal directly, completed reliably
on SD 1.5, and used ~3892 MiB peak allocated — under half the VRAM budget.

**The starting hypothesis was refuted.** Phase 0 expected direct tall generation to degrade composition
and generate-then-crop to be more reliable. The opposite held: direct 1:3 was reliable and cheap, while
square-crop's real cost is resolution — a 1:3 strip from a 512×512 image leaves only ~**170×512 usable
pixels**, rejected as the main strategy on those grounds.

Two honest caveats: **1:3 is an approximation** of the true ~1:3.6 deck ratio, because latent
dimensions must be multiples of 64; and **some repetition or vertical stretching remains possible** at
512×1536 and must be addressed in later prompt, reference-conditioning, and LoRA experiments.

## Measurement-methodology note attached to this decision

EXP-005's first run measured all four geometries in a **single process** and produced two contaminated
figures: `peak_vram_reserved_mb` and `peak_device_used_mb` became process-lifetime high-water marks
(the caching allocator retains its pool across `reset_peak_memory_stats()`), and `square-crop`'s
wall-clock inflated to 7.96 s for work provably identical to `direct-1x1`.

The obvious explanation — thermal throttling — was **tested and refuted**: on a hotter, more throttled
card (2250 → 1965 MHz, 75 °C) the same work ran *faster*, at 4.10 s. The cause was in-process
allocator state. Re-running one strategy per process cut timing spread ~20× and made `square-crop`
report 2675 MiB and 4.28 s, matching `direct-1x1` exactly, as identical work should.

The contaminated first run is retained as a **documented failed measurement design**, not deleted.
→ `docs/evidence/EXP-005/measurement-methodology-correction.md`

**Rule adopted for Prototypes 3–5:** one configuration per OS process whenever VRAM or timing is
measured. `peak_vram_reserved_mb` and `peak_device_used_mb` must be read as process-lifetime
high-water marks, never compared across configurations sharing a process.

## Consequences

- **Prototype 2** (reference conditioning) targets SD 1.5 IP-Adapter / ControlNet, the richest adapter
  ecosystem of the candidates, with ~5.5 GB of VRAM headroom at 512×512.
- **Prototypes 3–4** (LoRA) assume the SD 1.5-class envelope. The SDXL figures are direct evidence that
  LoRA training at 1024 is **not viable** on this hardware — see risk **R1**.
- **Prototype 5** (MVP) benefits from the 4.07 s latency; an interactive local app cannot reasonably
  ship 118 s generations. The safety-checker decision, disabled during benchmarking for a like-for-like
  core-pipeline comparison, **must be revisited** when the surface becomes user-facing.
- The **frozen evaluation kit** (fingerprint `c40749bc…`) carries forward unchanged so later
  comparisons stay valid against these baselines.
- **Reproducibility is claimed only within the recorded environment** — same pinned revision, hardware,
  and library versions. No claim is made that identical images reproduce across other GPUs, CUDA
  versions, PyTorch versions, or Diffusers versions.
- **Revisit trigger:** if a future milestone obtains a GPU with ≥ 16 GB VRAM, or if a distilled
  SDXL-class model with an SD 1.5-scale memory footprint becomes available and ungated, this decision
  should be re-examined — SDXL's native-resolution quality advantage is real and measured.
