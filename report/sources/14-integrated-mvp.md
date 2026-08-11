# <span class="section-number">14</span> The integrated MVP

## 14.1 What it does

A customer enters a prompt, optionally uploads a reference image, picks one of three styles, adjusts
reference strength and LoRA weight within bounded ranges, and generates. The result appears as a 2D
decal and on an interactive 3D deck that can be rotated, zoomed and reset, and both the artwork and
the deck view can be downloaded.

```
React + Three.js  ──HTTP──>  FastAPI (one process, one worker)
                                   │
                                   ├── single-flight lock (process-local)
                                   └── resident pipeline
                                          SD 1.5 @ 451f4fe1
                                          + one of three style LoRAs @ weight 0.7
                                          + IP-Adapter @ 018e4027, scale 0.55
                                          -> 512x1536, 30 steps, guidance 7.5
```

Generation is direct to the deck format. The pipeline loads on the **first** request, so that one
takes about 30 s and every later one 12–13 s.

## 14.2 One process, one worker — a measurement, not a preference

The service holds one pipeline resident and serves one generation at a time behind a process-local
lock. A startup guard rejects a worker count above 1.

This follows from §9.3 arithmetic: the production stack leaves
**{{ facts.worst_spare_mib }} MiB spare**, and a second resident pipeline needs about 5 GB. The lock
being process-local means a second API process would not see it, so **multiple separately launched
processes are unsupported and undetectable from inside one**.

<div class="callout">
<span class="callout__label">Stated as a limitation, not a virtue</span>
Scaling this system is <strong>not a configuration change</strong>. It requires a second GPU or a
smaller resident footprint. The single-process design is what the memory measurement permits.
</div>

The lock's discipline is tested rather than assumed: it is released only after the generation call
returns, a second request is refused while work is active, a later request succeeds after a
controlled abort, and a client disconnect does not free it.

## 14.3 Progress reporting that refuses to invent a number

The interface reports real progress, and the design was constrained by one instruction from the
student: *this must not be a fake progress bar.*

**Only denoising has a real denominator.** So the implementation publishes a step count during
denoising and, for model loading, decoding and saving, a **stage name with a null estimate**. There is
no weighted overall percentage, because no honest one exists.

- A test enumerates every non-denoising stage to assert **no percentage is produced** for it.
- **100 % waits for the PNG to decode in the browser**, not for the last diffusion step to land.
- The "finalising" stage is genuinely about a second and **is deliberately not padded** to make the
  label linger. Padding a finished result is exactly the dishonesty the feature exists to avoid.

This replaced a static "around 15 seconds" line that was wrong for a cold start by a factor of two.

## 14.4 The geometry decision

Generated decals are 1:3. The deck's UV domain is 1:3.902. Something has to give, and Prototype 0's
512×2000 test assets had hidden the discrepancy for four milestones (§11.5).

| option | cost | status |
|---|---|---|
| **full-surface** | **1.3008× longitudinal stretch** | **production default** (DR-012) |
| fit-without-stretch | **23.12 % of the deck bare** | retained and selectable |
| regenerate at 512×1998 | invalidates every VRAM figure | screened, not measured |
| reshape the deck to 1:3 | invalidates Prototype 0's evidence | screened, not measured |

**Both shipped options were built, neither was argued for, and a test asserted that no default was
exported** so the choice had to be made by a human looking at two screenshots differing in one
variable. The student selected full-surface, and his rationale is quoted **verbatim** in the decision
record — a justification the assistant invented would have been worse evidence than none.

<figure>
<img src="docs/evidence/prototype-5/screenshots/fit-full-surface.jpg" alt="The deck with the decal mapped across the full surface">
<figcaption><span class="caption__label">Figure 5.</span> The selected mode: the decal covers the
whole deck surface at the cost of a 1.3008× longitudinal stretch. The rejected alternative is kept
selectable because it is the evidence behind the decision.
<span class="caption__source">docs/evidence/prototype-5/screenshots/fit-full-surface.jpg</span>
</figcaption>
</figure>

The evidence behind DR-012 is **one reviewer, one decal, one camera**, and the record scopes the
judgement to the three production styles at the deck format rather than claiming that a 1.3× stretch
is imperceptible in general.

## 14.5 A feature added at the review gate

**Upload your own decal** was scoped by the student after using the application: customers who
already own artwork should not have to spend a generation to see it on a board.

It is **wholly local** — decoded in the browser, never sent to the server, never touching the model —
and that claim is proved from **server-side request counts** rather than asserted. It is kept visually
distinct from the AI reference upload so the two cannot be confused, uploaded artwork receives **no
reproducibility metadata** because none exists for it, and a failed decode preserves the previous
texture.

It also turned out to be the load-bearing element of the demonstration fallback plan, because it needs
no GPU, no model and no server round trip (§16.4).

## 14.6 Reproducibility surfaced to the user

Each result carries the model revision, adapter, weights, scale, seed, steps, guidance and geometry,
and the interface shows them. The `retro-poster` limitation is surfaced **to the user on every
request** rather than confined to documentation.

Metadata never contains a filesystem path, and generation identifiers resolve through a registry
lookup rather than a path join — so a traversal string has nothing to traverse (§17.3).

## 14.7 What the MVP does not do

It does not batch, queue, or serve concurrent users. It has no accounts, payments or persistence
beyond the generation registry. There is no CPU fallback: without a GPU and the three adapter files,
the service returns 503 for every style, by design and verified in both directions (§16.3).
