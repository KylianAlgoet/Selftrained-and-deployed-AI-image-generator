<div class="figure-pair">
<figure>
<img src="docs/evidence/prototype-4/final-sheets/EXP-027__minimal-geometric__ck00300__512x512.jpg" alt="Minimal-geometric outputs from the step 300 checkpoint">
<figcaption><span class="label">Step 300 — shipped.</span> Style consistency 5, prompt adherence 4. <em>EXP-027.</em></figcaption>
</figure>
<figure>
<img src="docs/evidence/prototype-4/final-sheets/EXP-027__minimal-geometric__ck00600__512x512.jpg" alt="Minimal-geometric outputs from the step 600 checkpoint, more stylised but less faithful to the prompt">
<figcaption><span class="label">Step 600 — rejected.</span> Style still 5, prompt adherence <strong>3</strong>. <em>Same prompts, same seeds.</em></figcaption>
</figure>
</div>

**Longer training bought style and spent obedience.** Three per-style LoRA adapters, rank
{{ facts.lora_rank }}, applied at {{ facts.lora_weight_default }} — two ship at step 300, ukiyo-e at
600. **The claim is feasibility, not superiority.**

## Speaker notes

My favourite result, and I only have it because of a process decision.

Same style, same prompts, same seeds. Left is three hundred training steps, right is six hundred.
Six hundred is more stylised — and less obedient. Prompt adherence dropped from four to three while
style consistency held at five. The model got better at the style by getting worse at listening to
you. On a product where the customer types what they want, that is the wrong trade.

So two of three adapters ship from step three hundred, not the six hundred they trained to. I only
saw that because I checkpointed four times along each run and had them scored blind. One global
step count would have got two styles out of three wrong.

On LoRA itself: full fine-tuning does not fit, and from scratch needs a cluster. LoRA freezes the
base model and trains a small pair of matrices beside it.

The honest bound, before you ask: I did not prove LoRA beats the alternatives. Textual Inversion,
DreamBooth and full fine-tuning were screened on criteria and never run, so that question is
bounded, not answered.
