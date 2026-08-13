- Full fine-tuning does not fit. Training from scratch needs **millions of images and a cluster** — neither exists here
- LoRA trains a **small pair of low-rank matrices** beside the frozen base model
- Measured: **rank {{ facts.lora_rank }}**, 3 133 MiB at 512², 300 steps in **91 seconds**. It fits with room to work
- Each adapter is **{{ facts.adapter_bytes }} bytes** — the styles ship as megabytes, not gigabytes
- **The claim is feasibility, not superiority.** Four alternatives were screened on criteria and never run

<p class="source">DR-009 · EXP-016 to EXP-019b · RQ1, recorded as bounded</p>

## Speaker notes

Why LoRA, and — just as important — what that does not claim.

From scratch was never realistic: a base diffusion model takes hundreds of millions of images and a
cluster. I have one laptop and a hundred and forty-eight pictures. Full fine-tuning updates every
weight, and the optimiser state alone does not fit in eight gigabytes.

LoRA freezes the base model and trains a small pair of low-rank matrices beside it. Measured here:
rank eight, about three gigabytes during training, three hundred steps in ninety-one seconds. It
fits with room to iterate.

The honest bound, before you ask: I did not prove LoRA beats the alternatives, only that it is
feasible here. Textual Inversion, DreamBooth and full fine-tuning were screened on criteria and
never run, so RQ1 is bounded, not answered.
