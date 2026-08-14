- Four options compared on nine criteria. **Selected: native local run + pre-generated backup assets**
- **{{ facts.worst_spare_mib }} MiB spare prevents a second resident pipeline**, so multi-worker inference is unsupported
- Docker GPU passthrough was **never verified on this machine**; unmeasured overhead is disqualifying on this margin
- **Public cloud was deliberately not selected** — cost, a demo-day network dependency, and no research gain
- Reproducibility rests on the **runbook and the clean-clone proof**, not on a public URL

<p class="source">DR-014 · alternatives A–D · EXP-034</p>

## Speaker notes

Is it actually deployed is a fair question, and the answer needs no spin. There is no public URL.
It runs locally, and that was a choice between four compared options rather than something I ran
out of time for.

Not cloud, because it adds a network dependency on the one day everything must work and — the
deciding part — answers nothing. The question is what fits in eight gigabytes of consumer hardware.
A rented data-centre card replaces that question rather than answering it.

Not Docker, because GPU passthrough was never verified here and its overhead is unmeasured. On this
margin, that is disqualifying.

What I do claim is reproducibility, and it rests on the runbook and the clean-clone test — a
stronger claim than a URL, which only proves it runs where I put it.
