# <span class="section-number">9</span> Model and fine-tuning comparison

Two decisions are recorded here: which pretrained base model the system generates from, and which
fine-tuning method teaches it a style. Both were taken on measured data, and both carry limitations
that are stated rather than smoothed over.

## 9.1 Base model

Three candidates were planned. One could never be measured.

| candidate | outcome |
|---|---|
| Stable Diffusion 1.5 | **measured** — selected (DR-007) |
| SDXL base 1.0 | **measured** — rejected on memory, not on quality |
| SD 2.1 base | **blocked** — the repository returns HTTP 401 |

SD 2.1 was gated behind authentication. Two sibling repositories from the same organisation returned
401 while SDXL returned 200, so this was repository gating rather than an outage. Per the approved
plan the student was asked rather than the assistant authenticating or silently substituting a
mirror; three alternatives were declined and recorded, including an ungated community mirror rejected
because its fidelity to the original cannot be verified while the original is gated.

**The base-model decision therefore rests on two measured candidates, not three.** That is a
limitation of the evidence, and it is carried into section 18 rather than left implicit.

### The measurement design that changed the answer

Scoring every model at 512×512 would have been unfair to SDXL, which was never designed for it. The
benchmark was therefore split into two tracks, reported separately and never averaged:

- **Track A** — every candidate at 512×512, so speed, memory and reliability are comparable.
- **Track B** — every candidate at its designed resolution, SDXL at 1024×1024.

| model | geometry | peak allocated | peak device | median latency | quality (student) |
|---|---|---:|---:|---:|:---:|
| SD 1.5 | 512×512 | 2 675.38 | 4 359.5 | 4.069 s | 4 |
| SD 1.5 | 512×768 | 2 979.33 | 4 977.5 | 6.811 s | — |
| SDXL | 512×512 | 7 859.26 | 8 187.5 | 16.512 s | 4 |
| **SDXL** | **1024×1024** | **10 738.08** | **8 187.5** | **118.733 s** | **5** |

All memory figures in MiB, against a physical {{ facts.device_total_mib }} MiB.
Evidence: `experiments/registry.csv` EXP-002, EXP-004; `docs/evidence/prototype-1/`.

<figure>
<img src="docs/evidence/prototype-1/cross-model-track-B-seed42.jpg" alt="Contact sheet comparing SD 1.5 and SDXL at their native resolutions, fixed seed 42">
<figcaption><span class="caption__label">Figure 1.</span> Track B — each candidate at its designed
resolution, identical prompts and seed 42. SDXL at 1024×1024 produces flat artwork with no mockup
framing; SD 1.5 at 512 px tends toward photographic product mockups. The literal-deck reading is
resolution-dependent, not a property of all models.
<span class="caption__source">docs/evidence/prototype-1/cross-model-track-B-seed42.jpg</span>
</figcaption>
</figure>

### The result that set the project's method

SDXL reported **30 of 30 successful runs at 1024×1024**. It also allocated **10 738 MiB and reserved
14 510 MiB on a card holding {{ facts.device_total_mib }} MiB.**

<div class="callout">
<span class="callout__label">The failure that did not look like one</span>
Windows WDDM spilled the overflow into shared host memory instead of raising a CUDA
out-of-memory error. Resident host memory rose to 6 806 MiB, no exception was thrown, and the
pipeline's memory-tier escalation never triggered. A run that reports success is not evidence that it
fitted.
</div>

Every memory figure in this report is consequently quoted **against the device ceiling**, and that
convention comes directly from this experiment. It is also why the {{ facts.worst_spare_mib }} MiB
production margin in section 14 is never called comfortable headroom.

SDXL is retained as the visual-quality benchmark. Its advantage is real and exists only at a
resolution this GPU cannot hold.

## 9.2 Fine-tuning method

The assignment mandates comparing five methods. They were **not** all measured, and this section says
so plainly.

| method | treatment | why |
|---|---|---|
| Training from scratch | screened out | infeasible on 8 GB and a 19-day budget by orders of magnitude |
| Full fine-tuning | screened out | the full UNet in optimizer state does not fit |
| DreamBooth | screened, never run | subject-driven; the task is style, and budget allowed one method to be measured properly |
| Textual Inversion | screened, never run | learns an embedding, not style weights; same budget constraint |
| **LoRA** | **measured** | selected (DR-009) |

<div class="callout">
<span class="callout__label">What DR-009 does not claim</span>
LoRA is <strong>not</strong> shown to be the best of the five. Four of them were screened on criteria
and never executed. The defensible statement, and the one the decision record makes, is that LoRA is
the mandated method <strong>demonstrated feasible on this hardware</strong>.
</div>

### What was measured

A rank-{{ facts.lora_rank }} LoRA on the UNet attention projections, with the text encoder and VAE
frozen. Thirteen runs across eight experiments, every one at the lowest memory tier, with no
escalation anywhere.

| run | geometry | steps | peak allocated | spare | s/step |
|---|---|---:|---:|---:|---:|
| EXP-016a | 512×512 | 1 | 3 114.09 | 3 920.0 | 1.9344 |
| EXP-016b | 512×512 | 10 | 3 133.40 | 3 902.0 | 0.4340 |
| EXP-016 | 512×512 | 300 | 3 133.40 | 3 902.0 | 0.2854 |
| EXP-017a | 512×1536 | 1 | 5 160.96 | 1 758.0 | 2.5533 |
| EXP-017b | 512×1536 | 10 | 5 182.58 | 1 738.0 | 1.1223 |

Three findings came out of separating the memory peaks by phase rather than recording one
process-level maximum:

1. **Activations scale with geometry; optimizer state does not.** Post-load allocation is identical
   at both geometries (2 066.56 MiB) and the optimizer-step peak barely moves (2 108.93 → 2 118.76),
   while the forward/backward peak rises from 3 114 to 5 183. Gradient checkpointing is therefore the
   correct first escalation, and a lower-memory optimizer would have been the wrong move.
2. **A rank-{{ facts.lora_rank }} adapter costs +3.04 MiB, and that cost does not scale with output
   size.** Measured independently three times.
3. **Training is cheap.** Three hundred steps in 91 seconds, which made the style-comparison grid in
   the next prototype affordable many times over.

### Proving the adapter does something

An adapter that loads without error has not been shown to work. Thresholds were written down before
any result was read:

```
weight 0.0  ->  4/4 byte-identical to the no-adapter baseline
                recorded as a DIAGNOSTIC, never a pass condition
weight 1.0  ->  4/4 beyond a pre-declared noise floor
                mean |pixel diff| >= 0.5 AND >= 1% of subpixels differing
                measured: 51.89-66.33 mean diff, dHash 20-28
```

The weight-0.0 arm is recorded as a diagnostic deliberately: loading an inactive adapter can
legitimately alter the execution graph, so byte-identity was a welcome result that was never allowed
to become a pass criterion. Equally, **a differing image hash alone was never treated as sufficient**
evidence that the adapter had changed anything.

## 9.3 The combined stack, and the ceiling it set

The two decisions above have to hold *simultaneously*, and that was genuinely uncertain:
IP-Adapter alone had already peaked at 7 965.5 MiB of {{ facts.device_total_mib }} at the deck
format.

Both adapters were confirmed live at once by reading the UNet back — 128 LoRA modules and 16
IP-Adapter attention processors — rather than inferred from a call that returned without raising.

**The combined stack fits at {{ facts.generation_width }}×{{ facts.generation_height }} by
{{ facts.oneshot_spare_mib }} MiB**, later measured at **{{ facts.worst_spare_mib }} MiB** under real
serving. That is *less* margin than IP-Adapter alone had, because the adapter takes roughly 20 MiB of
device memory on top. No overflow flag fired and no tier escalated — which is precisely the pattern
that made SDXL look viable until its figures were read against the ceiling.

Geometry was never reduced to make this pass. The result re-scoped the risk rather than closing it:
the open question stopped being *does this stack fit* and became *does anything added to it still
fit*.
