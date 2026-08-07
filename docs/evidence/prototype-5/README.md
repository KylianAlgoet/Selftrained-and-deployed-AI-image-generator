# Prototype 5 — API validation evidence

**Date:** 2026-08-06 · **Milestone:** M7 · **Result:** all three phases passed.

Driven against a **real uvicorn process** started the way the demo starts it
(`--workers 1`, no reload) and exercised over HTTP — not a test client. Script:
`scripts/validate_p5_api.py`. Rows: `api-validation.jsonl`.

## Phase A — serving (6 generations)

| style | mode | wall | active adapters | scale | spare | warnings |
|---|---|---:|---|---:|---:|---:|
| minimal-geometric | prompt-only | 30.54 s | `['minimal-geometric']` | 0.0 | 218.0 | 0 |
| minimal-geometric | reference | 13.07 s | `['minimal-geometric']` | 0.55 | 200.0 | 0 |
| ukiyo-e | prompt-only | 12.89 s | `['ukiyo-e']` | 0.0 | 218.0 | 0 |
| ukiyo-e | reference | 12.96 s | `['ukiyo-e']` | 0.55 | 200.0 | 0 |
| retro-poster | prompt-only | 13.14 s | `['retro-poster']` | 0.0 | 218.0 | **1** |
| retro-poster | reference | 13.31 s | `['retro-poster']` | 0.55 | 202.0 | **1** |

The first request carries the one-off model load (30.54 s vs ~13 s once resident).
`/api/health` reported `pid 21604`, `cuda True`, `pipeline_loaded False` before the first
generation, and `single_worker_guard: enforced`.

**`retro-poster` returns a warning on every request** — its H4 limitation reaches the user
rather than staying in the documentation, which is what "ships with its limitation stated"
has to mean in practice.

## Phase B — the integrity gate, proved without damaging anything

The three real checkpoints were **copied** to a sandbox and the `retro-poster` copy replaced
with `\x00` bytes of **exactly the same length**, so the sha256 check is what rejects it rather
than the size check in front of it. The real artifacts were never written to — R14 makes them
unregenerable, so proving the gate by damaging one would destroy the thing being protected.

- corrupted `retro-poster` → **HTTP 503** `model_unavailable`; the response leaks no path and no
  filename, while the server log carries the full hash mismatch.
- the busy lock was **not** left held.
- `minimal-geometric` → **HTTP 200** immediately afterwards: the service recovers **without a
  restart**.

## Phase C — the deadline actually stops the work

A server with `GENERATION_TIMEOUT_SECONDS=5`, against generations that take ~13 s.

| request | result | wall |
|---|---|---:|
| cold (warm-up, includes model load) | 504 | 20.06 s |
| **warmed (the measurement)** | **504, stopped after 14 of 30 steps** | **6.33 s** |

Lock released afterwards: **yes**.

**A measurement error found and corrected here.** The first attempt asserted the abort by wall
clock alone and failed at 25.69 s — but that request was the *cold* one, and almost all of that
time was the model load, not denoising. The service was behaving correctly; the check was wrong.
It now proves the early stop two independent ways: the **step count reported in the response**
(14 of 30), which no amount of loading time can fake, and the wall clock of a **warmed** request
(6.33 s against ~13 s). The 5 s deadline plus one step boundary plus the uninterruptible VAE
decode accounts for the 6.33 s.

**Stated limitation:** the abort happens at a **step boundary**, so the deadline can overshoot by
up to one step, and the VAE decode that follows the loop is not interruptible. A 504 therefore
means "the denoising loop was stopped", not "the GPU went idle at exactly 5.000 s".

## Provenance note

Phases A and B were executed once and passed. Phase C was re-run after the measurement fix
described above; that fix changed only the `GenerationAborted` signature and the 504 detail
string, neither of which is on the Phase A or Phase B path. Their rows are preserved rather than
regenerated, because M7 declared a hard cap of **25 real generations** before any ran, and
re-running passed phases to correct another phase's assertion would have spent that budget on
nothing. `--phases` exists for exactly this.

## Browser evidence (`screenshots/`)

Captured from the running application — API on `--workers 1`, Vite dev server, Chrome.

| file | what it shows |
|---|---|
| `orientation-reference.jpg` | the deck with Prototype 0's orientation decal: "NOSE" upright and **unmirrored** at the nose, arrow pointing noseward |
| `fit-full-surface.jpg` | a **generated** ukiyo-e decal filling the deck — the 1.3008× stretch |
| `fit-without-stretch.jpg` | the **same** decal, **same camera**, aspect preserved — the 23.12 % bare ends |

The two fit screenshots differ only in the selected mode; the camera was not touched between
them, which is also the evidence that swapping a texture does not move the viewpoint. **They are
the review material the gate decision was made on** — Kylian selected `full-surface` on
2026-08-07 (DR-012, `GATE-approval.md`).

**How they were captured without spending GPU budget.** The cap of 25 generations was already
reached, so the decal was loaded from disk through a review-only "Load decal" control rather
than generated afresh. That control exists because it had to: Prototype 0's bundled decals are
**512×2000** — 1:3.906, essentially the deck's own aspect — so they cannot demonstrate a
mismatch that only appears with 1:3 generated artwork. It also lets a reviewer inspect any
earlier decal at the gate without spending GPU time.

**One observation worth recording rather than reporting as a bug.** A screenshot taken in the
same second the R3F scene finished initialising showed an empty viewer. Re-checking three
seconds later showed the deck rendering correctly, and the console held no errors across either
load. It was a capture-timing artifact.

## GPU budget

| purpose | count |
|---|---:|
| EXP-034 smoke | 1 |
| EXP-034 residency matrix | 12 |
| Phase A serving | 6 |
| Phase B recovery | 1 |
| Phase C aborts (cold + warmed) | 2 |
| EXP-035 neutralisation | 2 |
| **total** | **25 of 25** |

The cap was reached exactly. No further real generation may run in M7 without a new decision.
