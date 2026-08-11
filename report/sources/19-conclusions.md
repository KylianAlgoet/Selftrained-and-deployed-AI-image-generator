# <span class="section-number">19</span> Conclusions

## 19.1 The primary question

> How can a locally fine-tuned diffusion model, conditioned on both a text prompt and a reference
> image, generate skateboard-decal artwork in multiple visually distinct styles with reproducible
> quality on consumer hardware with 8 GB of VRAM?

**It can, and this project establishes the specific configuration that fits.**

Stable Diffusion 1.5 [1], generating directly at
{{ facts.generation_width }}×{{ facts.generation_height }}, with one of three per-style LoRA
adapters [3] at weight {{ facts.lora_weight_default }} and IP-Adapter [4] at scale
{{ facts.ip_adapter_scale_default }}, served by a single resident pipeline. Peak allocated
{{ facts.peak_allocated_mib }} MiB; **worst spare {{ facts.worst_spare_mib }} MiB of
{{ facts.device_total_mib }} MiB under real serving conditions.**

The answer is bounded in three ways that matter more than the affirmative:

- **The margin is 2.4 %.** The configuration fits; it does not fit comfortably, and anything added to
  it has {{ facts.worst_spare_mib }} MiB to fit into.
- **"Reproducible" holds for inference and not for training.** A clean clone reproduced an output
  byte for byte three days later in a fresh environment. Training cannot be reproduced from its
  recorded seed, so the adapters are artifacts rather than recipes.
- **"Multiple visually distinct styles" is three, and one of them is a partial pass.**

## 19.2 Conclusions per research question

| RQ | conclusion | strength |
|---|---|---|
| RQ1 | LoRA is **demonstrated feasible** on 8 GB: rank {{ facts.lora_rank }}, 3 133 MiB at 512², 300 steps in 91 s | feasibility only — four alternatives screened, never run |
| RQ2 | SD 1.5 is feasible; **SDXL is not**, at the resolution where it is better | strong, on two candidates |
| RQ3 | A {{ facts.dataset_total }}-item dataset of public-domain, CC0 and self-created work is sufficient and legally documentable | strong |
| RQ4 | Style-only captions beat verbatim captions; **image count: no conclusion** | split — captions strong, count inconclusive |
| RQ5 | **Separate per-style adapters**, because each style needs a different checkpoint step | strong |
| RQ6 | **IP-Adapter over img2img**, decided by near-copy behaviour rather than by quality | strong |
| RQ7 | Reference strength and adapter weight dominate perceived control | partial — rank and LR not swept |
| RQ8 | **Generate the deck ratio directly.** The hypothesis that this would degrade was refuted | strong |
| RQ9 | UV layout alone controls orientation; textures swap at runtime | strong |
| RQ10 | A pre-declared rubric with fixed seeds and blinding at the first gate gives usable comparability | adequate — one scorer |
| RQ11 | Licensing and privacy are settled; **memorisation is not** | partial |
| RQ12 | A documented two-process local run, validated by a clean clone | strong |

**Ten of twelve are answered. RQ4's count half is inconclusive and RQ7 and RQ11 are partial**, and
§18.2 states exactly what limits each.

## 19.3 The findings worth carrying beyond this project

Four results generalise past the assignment.

**A successful run is not a run that fitted.** SDXL reported 30 of 30 successes at 1024×1024 while
allocating 10 738 MiB on an 8 187.5 MiB card, because the operating system spilled into host memory
instead of raising an error. Reading memory against the ceiling rather than against the exit code is
the single most useful habit this project adopted, and it was adopted because one experiment nearly
concluded the opposite.

**The cheapest method can be disqualified by what it does, not by what it costs.** img2img adds zero
VRAM — decisive on an 8 GB budget — and was rejected because at the deck format it returns its own
input. Every near-copy flag in that milestone came from it.

**Training longer made the model less obedient.** Prompt adherence fell from 4 to 3 at step 600 for
two of three styles while style consistency held at 5. Two of the three shipped checkpoints are
therefore step 300. This is visible only if you checkpoint several times and let a human compare.

**Determinism has halves.** Inference here is byte-reproducible across machines and days. Training is
not reproducible at all from its recorded seed, because the adapter initialisation draws from an
unseeded global generator — a defect that produces perfectly valid-looking runs and is invisible
unless you compare weights.

## 19.4 On the process

The assignment assesses the research process, and the honest conclusion about it is that **the
process was worth more than the result three separate times.**

The prototype ladder caught a geometry mismatch that four milestones of convenient test assets had
hidden. The clean-clone test caught an integrity control that had only ever passed on the machine
that wrote it. The two-gate review protocol caught a checkpoint selection that a single global step
count would have got wrong for two styles out of three.

None of those would have surfaced from building the system and documenting it afterwards. Each came
from a deliberately awkward step — build the next prototype rather than assume, clone into an empty
directory rather than trust, stop and let a human look rather than let an indicator decide.

## 19.5 What this project does not conclude

It does not conclude that LoRA is the best fine-tuning method, that SD 1.5 is the best base model,
that three styles is enough, that 40 images per style is a threshold, that the system is unbiased,
or that a green test suite means the generator works.

Each of those would have been an easy sentence to write and none of them is supported by what was
measured.
