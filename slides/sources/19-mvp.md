<div class="col-text">

- Generation is **direct to the deck format**, {{ facts.generation_width }}×{{ facts.generation_height }} — not square-then-crop
- The progress bar reports **real diffusion steps**, from the pipeline
- While the model loads it shows **no percentage at all**, because loading exposes none. *A bar creeping to 90 % would look better and be a lie*
- Every result carries its **seed, pinned model revision, adapter hash and measured VRAM**

</div>
<div class="col-figure">
<figure>
<img src="docs/evidence/prototype-5/screenshots/ui/03-denoising.jpg" alt="The interface during generation, showing the real denoising step count">
<figcaption><span class="label">Denoising, step-accurate.</span> The hypothesis that generating the deck ratio directly would degrade quality was tested, and refuted.
</figcaption>
</figure>
</div>

## Speaker notes

Two details I would defend.

First, generation goes straight to the deck's tall aspect ratio rather than generating a square and
cropping. I expected that to hurt — diffusion models are trained mostly on square images and drift
at extreme ratios. I wrote it down as a hypothesis, tested it, and it was refuted. That is RQ8, and
it saved me a workaround I did not need.

Second, the progress bar shows real denoising steps from the pipeline — step fourteen of thirty is
actually fourteen of thirty. And while the model loads it shows no percentage at all, because
loading exposes none. I could have drawn a bar creeping to ninety per cent. It would look better
and it would be a lie about where the time went.

Every image carries its seed, the pinned model revision, the adapter's hash and the measured VRAM.
It is traceable to a specific experiment, not just a picture.
