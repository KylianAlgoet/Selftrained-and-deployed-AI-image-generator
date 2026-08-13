<div class="col-text">

- Two ways to use a reference image: **img2img** or **IP-Adapter**
- img2img costs **zero extra VRAM** — decisive on this budget, and it lost anyway
- At the deck format it **returned its own input.** Every near-copy flag in that milestone came from img2img
- **IP-Adapter selected**, scale {{ facts.ip_adapter_scale_default }}. *A method that reproduces its input is not a generator.*

</div>
<div class="col-figure">
<figure>
<img src="docs/evidence/prototype-2/copy-risk-pairs.jpg" alt="Reference images beside their img2img outputs, several pairs near-identical">
<figcaption><span class="label">Reference, then img2img output.</span> Some pairs are perceptually indistinguishable. This is why the free method was not selected.
</figcaption>
</figure>
</div>

## Speaker notes

The decision where the criteria mattered most.

Two realistic ways to condition on a reference. img2img starts the diffusion from the reference
itself. IP-Adapter encodes it and injects it through cross-attention, which costs extra VRAM.

On a card with two hundred megabytes spare, "costs extra VRAM" should have ended the argument.
img2img is free.

Look at the pairs. Left is the reference the user supplied, right is what img2img returned at the
deck format. Several are perceptually the same image. Every near-copy flag in that milestone came
from img2img; none came from IP-Adapter.

So I rejected the cheaper method on what it does, not what it costs. A system that hands back the
customer's own upload with a filter on it is not a generator.
