<div class="col-text">

- **Inference is deterministic.** A clean clone reproduced an earlier output **byte for byte**, three days later, in a fresh environment
- **Training is not.** Adapter initialisation draws from an **unseeded global generator** — a run cannot be repeated from its recorded seed
- So the checkpoints are **artifacts, verified by hash on every request** — not recipes
- A defect that produces perfectly valid-looking runs, and is **invisible unless you compare weights**

</div>
<div class="col-figure">
<figure>
<img src="docs/evidence/M8/clean-clone/real-output/screenshots/02-result-and-deck.jpg" alt="The clean-clone environment producing a generation and rendering it on the deck">
<figcaption><span class="label">Clean clone, fresh environment.</span> SHA-256 <code>{{ facts.output_sha256 }}</code>, identical to the original run.
</figcaption>
</figure>
</div>

## Speaker notes

The primary question asks for reproducible quality, and this is where my answer splits in half.

Inference is deterministic — and not just on my machine on the same day. A clean clone in a fresh
environment, three days later, reproduced an earlier output byte for byte. Same hash.

Training is not reproducible at all from its recorded seed. Two runs with identical configuration
and an identical seed produced different weights, because the adapter initialisation draws from an
unseeded global generator. The seed I was diligently recording never governed the part that
mattered.

So the checkpoints are artifacts, not recipes. Their hashes are verified on every request, and the
deployment docs say plainly that three required files cannot be regenerated.

The part worth pushing on is that this defect produces runs that look completely fine. It is
invisible unless you compare weights.
