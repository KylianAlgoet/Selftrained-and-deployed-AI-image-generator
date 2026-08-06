# Prototype 5 — the integrated MVP

**Milestone:** M7 · **Dates:** 2026-08-06 (planned Aug 10–13; started early on M6's buffer)
**Status:** built and validated; **awaiting Kylian's review gate.**
**Decision record:** DR-011 · **Experiments:** EXP-034, EXP-035 · **Evidence:** `docs/evidence/prototype-5/`

## Research question

Everything about *what* to generate was settled by M3–M6. Prototype 5 asks the operational
question that none of those answered:

> Can the measured generation stack — SD 1.5 + one per-style LoRA at 0.7 + IP-Adapter at 0.55,
> at 512×1536 — be exposed as a usable application on a single 8 GB device **without breaking
> the 202 MiB margin it depends on**, and what does putting a decal on a 3D deck actually
> require?

Two sub-questions were genuinely open and are answered by measurement, not assertion:

1. **Residency.** Every VRAM figure this project owns was taken one configuration per OS
   process. A service is the opposite. Does swapping between three adapters in one long-lived
   process accumulate memory or leak state? → **EXP-034**
2. **Geometry.** The generator produces 1:3. The deck's UV domain is 1:3.902. → **both fit
   modes built, neither chosen**

## Scope

**Built:** FastAPI service with upload security, checkpoint integrity gate, single-flight lock
and an in-loop deadline · React generate flow with loading/error/busy states · reproducibility
metadata and PNG + JSON download · both texture-fit modes on the deck · 82 API tests and 66 web
tests.

**Deliberately out:** Docker and the deployment decision (M8, RQ12) · accounts, persistence,
multi-user, job queue · any training · Playwright E2E (M8) · any further visual-quality sweep.

## Acceptance criteria and outcomes

| criterion | outcome |
|---|---|
| Full flow works locally: prompt → generation → 3D preview → download | **met** — Phase A, plus browser capture |
| Errors and loading handled | **met** — 422/409/503/504/500 each have a distinct state; busy is not shown as failure |
| Seeds reproduce | **met** — 6 of 6 repeated cases byte-identical (EXP-034) |
| Reference conditioning works and is optional | **met** — and the optional path is measured, not assumed (EXP-035) |
| Uploads treated as untrusted | **met** — limits frozen before implementation; a negative test per rule |
| The 202 MiB ceiling is respected | **met, and tightened** — worst observed spare is **200.0 MiB** |
| Correct nose–tail orientation | **met** — orientation reference screenshot, unmirrored |

## What the milestone actually found

### Residency costs nothing, and the margin is tighter than advertised

EXP-034 ran a frozen 12-request matrix — six cases twice — through one process. Allocated memory
after generation was **3316.64 MiB in all 13 runs**: not "within the 64 MiB tolerance declared in
advance", *identical*. Six unload/load cycles across three adapters left the allocator exactly
where it started. Peak allocated was **5143.73 MiB**, byte-identical to M5's one-shot EXP-019b.

But the worst spare device memory observed is **200.0 MiB**, not the 202.0 MiB quoted from
EXP-032 — every reference-conditioned request sits there. The margin got *tighter* under real
serving conditions, and it is recorded that way.

### Prototype 0's decals hid the geometry problem for four milestones

The bundled test decals are **512×2000** — 1:3.906, effectively the deck's own aspect. The
generator produces **512×1536**, which is 1:3. The mismatch could not appear until real generated
artwork reached the deck, which is this milestone. Neither fit is correct:

| mode | stretch | deck length covered | uncovered |
|---|---:|---:|---:|
| `full-surface` | **1.3008×** lengthwise | 100 % | 0 % |
| `fit-without-stretch` | none | 76.88 % | **23.12 %** (11.56 % per end) |

Both are built, both disclose their trade-off numerically in the UI, and **the choice is
Kylian's at the gate.** A test asserts the code exports no default.

A caveat belonging to neither mode: the Prototype-0 UV convention already compresses the texture
horizontally toward the tapered tips. That is pre-existing and applies to both.

### The optional-reference path was a real design problem, not a formality

With IP-Adapter resident, diffusers **raises** if no reference is passed — so "prompt-only" is not
simply "omit the image". The service keeps the adapter at scale 0.0 with a constructed grey
placeholder, and **EXP-035 tested the claim that rests on**: a grey placeholder and real holdout
artwork produced byte-identical output. The reference content cannot influence the result at
scale 0.0.

## Defects found in my own work

1. **A wrong measurement, not a wrong service.** The first deadline check asserted an early stop
   by wall clock and failed at 25.69 s — but that was a *cold* request, and nearly all of it was
   the model load. The service was correct. The 504 now reports how far the loop got (14 of 30
   steps), so the early stop is provable from the response, and the warmed request returns in
   6.33 s against ~13 s unaborted.
2. **A blank-deck screenshot that was not a bug.** A capture taken in the same second the scene
   finished initialising showed an empty viewer. Re-checking after three seconds showed the deck
   rendering correctly. Recorded because "screenshot looks wrong" is exactly the kind of thing
   that gets reported as a defect without verification.
3. **`<output>` inside a `<label>` made a control ambiguous** to assistive technology and to the
   tests. Replaced with a `<span>`.

## Limitations to carry forward

- **Single process, by design.** Scaling is not a config change (DR-011).
- **The deadline lands on a step boundary** and the VAE decode is not interruptible, so a 504
  means "the denoising loop stopped", not "the GPU idled at exactly 5.000 s".
- **Byte-identical repeats are strong evidence of no state residue, not proof of none.**
- **EXP-035 does not re-establish text-only equivalence** — that stack has no LoRA and a
  different prompt, and the claim still rests on M4's separate 12/12 result.
- **`retro-poster` remains a partial pass** and says so on every request.

## Next

**Kylian's review gate** — see `docs/evidence/prototype-5/GATE-handover.md`. Nothing about the
texture-fit default, milestone completion, the issue, or M8 proceeds before it.
