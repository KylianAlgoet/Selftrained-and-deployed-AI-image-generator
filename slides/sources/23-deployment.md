- Four options were compared. **Selected: native local run + pre-generated backup demo assets** (Option D of four)
- **{{ facts.worst_spare_mib }} MiB spare prevents a second resident pipeline on the validated GPU**, so multi-worker inference is unsupported
- Docker with GPU passthrough was **never verified on this machine**; its VRAM overhead is unmeasured
- **Public cloud deployment was deliberately not selected for this bachelor version** — it is a cost and a network dependency on demo day, for no research gain
- Reproducibility is carried by the **runbook and the clean-clone proof**, not by a public URL

<p class="source">DR-014 · alternatives A–D compared on nine criteria · EXP-034</p>

## Speaker notes

"Is it actually deployed" is a fair question and the answer needs no spin.

There is no public URL. It runs locally, and that was a choice between four compared options rather
than something I ran out of time for.

Not cloud, because renting a GPU costs money for the length of the project, adds a network
dependency on the one day everything must work, and — the deciding part — answers nothing. The
question is what fits in eight gigabytes of consumer hardware. A rented A100 replaces that question
rather than answering it.

Not Docker, because GPU passthrough was never verified here and its overhead is unmeasured. On a
two hundred megabyte margin, unmeasured overhead is disqualifying.

What I do claim is reproducibility, and it rests on the runbook and the clean-clone test — a
stronger claim than a URL, which only proves it runs where I put it.
