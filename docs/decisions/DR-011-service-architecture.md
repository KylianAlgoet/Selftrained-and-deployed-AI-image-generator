# DR-011 — Service architecture for the integrated MVP

**Status:** accepted (with one item deliberately left open) · **Date:** 2026-08-06 · **Milestone:** M7 (Prototype 5)
**Answers:** how the measured generation stack is exposed as a usable application on one 8 GB device.
**Related:** DR-002 (FastAPI), DR-003 (React/R3F), DR-007 (base model, deck format), DR-008 (IP-Adapter 0.55), DR-009 (LoRA), DR-010 (per-style adapters at 0.7)
**Evidence:** EXP-034, EXP-035, `docs/evidence/prototype-5/`

## Context

Every modelling question was settled before this milestone. What was not settled is how to
put the result behind an HTTP interface without breaking the one property the whole stack
depends on: **it fits in 8 GB with 202 MiB to spare, and that margin is not comfortable.**

Prototype 5 therefore decides operational questions, not modelling ones.

## Decisions

### 1. Synchronous `POST /api/generate` with a single-flight busy lock

**Kylian's choice at the planning gate.** A generation is 12–13 s once resident. The endpoint
blocks until it finishes and returns JSON with an image URL; a concurrent request is refused
immediately with **409**, not queued.

*Alternative considered:* job id plus polling. Rejected as roughly double the endpoint surface
and lifecycle to maintain, for progress reporting the UI does not need at this scale.

### 2. The pipeline is resident, loaded lazily on the first request

**Kylian's choice at the planning gate.** SD 1.5, IP-Adapter and its CLIP encoder load once and
stay; only the per-style LoRA is swapped. Measured cost of residency: the first request takes
30.54 s, every later one 12–13 s.

*Alternative considered:* build and tear down per request. Rejected because it pays the full
model load on every generation, and EXP-034 showed residency accumulates nothing.

### 3. Exactly one API process — a correctness requirement, not a deployment preference

The busy lock is a `threading.Lock` and is therefore **process-local**. Two workers would each
hold their own lock, their own resident pipeline and their own in-flight generation against one
device — and with 200 MiB spare, **a second pipeline does not fit at all**. The first symptom
would be an OOM in whichever request happened to be running.

So: `--workers 1`, no Gunicorn, no `WEB_CONCURRENCY > 1`, and **no `--reload`** during real
generation or evidence capture, because the reloader runs a second process holding the same GPU.
A startup guard **rejects** a detectable worker count above 1 rather than warning, and
`/api/health` reports the PID so a duplicate process is visible.

**Stated limitation:** nothing inside one process can detect a second API process someone
started by hand. Multiple separately launched servers are **unsupported**.

### 4. Prompt-only requests keep IP-Adapter resident at scale 0.0 with a constructed placeholder

This is **structural, not stylistic**. In diffusers 0.39.0, `added_cond_kwargs` is `None` when no
reference is passed (`pipeline_stable_diffusion.py:1014-1018`), and the UNet then **raises**,
because `encoder_hid_dim_type == "ip_image_proj"` requires `image_embeds`
(`unet_2d_condition.py:964-967`). A prompt-only request cannot simply omit the image while the
adapter is loaded.

*Alternative considered:* `unload_ip_adapter()` for prompt-only requests. Rejected because it
discards the 2.35 GiB CLIP encoder, so every toggle would pay to rebuild it.

**EXP-035 tested the claim this rests on** rather than assuming it: two generations differing
only in their reference — the constructed grey placeholder and real holdout artwork — produced
**byte-identical** output at scale 0.0, and the same bytes as EXP-034's prompt-only result.
The reference content demonstrably cannot influence the result at scale 0.0.

### 5. Checkpoints are verified by sha256 on every activation

Adapters live in git-ignored `outputs/`, where a stale copy or partial write is realistic. Every
style activation re-verifies size and hash against the gate-2 record and **refuses to serve** on
mismatch. It never regenerates: R14 means these files cannot be reproduced from their seed.

Proved in Phase B against a **corrupted copy** of the same length — damaging a real checkpoint to
test the guard would destroy the artifact the guard exists to protect.

### 6. A 504 means the work actually stopped

The deadline is enforced **inside** the denoising loop via `callback_on_step_end`, which sets the
pipeline's supported `_interrupt` flag; the loop exits at the next step boundary and the lock is
held through cleanup. The response reports how far it got — "stopped after 14 of 30 steps" —
so the early stop is verifiable from the response rather than inferred from timing.

**Stated limitations:** the abort lands on a **step boundary**, so the deadline can overshoot by
up to one step, and the VAE decode after the loop is **not interruptible**. A client disconnect
or frontend timeout does **not** release the lock — there is no background thread, so no path
exists where a response is sent while GPU work continues.

## Measured results

| fact | value | source |
|---|---|---|
| Peak allocated, resident service | **5143.73 MiB** — byte-identical to M5's EXP-019b | EXP-034 |
| Allocated after generation | **3316.64 MiB in all 13 runs**, growth **0.00 MiB** | EXP-034 |
| Worst spare device memory | **200.0 MiB** (reference-conditioned) | EXP-034, Phase A |
| Repeated identical requests | **6 of 6 byte-identical** across cycles | EXP-034 |
| Generation latency | 12–13 s resident; 30.54 s first request | Phase A |
| Deadline abort | 504 after 14 of 30 steps, 6.33 s warmed | Phase C |

## Consequences

- **200.0 MiB is the operative production ceiling**, tighter than the 202.0 MiB quoted from
  EXP-032. Anything added — a second adapter, higher rank, larger reference batch, ControlNet —
  must fit inside it and requires a new memory measurement.
- The service is **single-process by design**. Horizontal scaling is not a configuration change;
  it would need a second device or a rewrite of the concurrency model.
- `retro-poster` ships as a **partial pass** and returns its limitation as a warning on every
  request, so H4 reaches the user rather than only the documentation.

## Deliberately left open — now closed by DR-012

**The production texture-fit mode was NOT decided here.** The generated decal is 1:3 and the deck
UV domain is 1:3.902, and there is no fit that is simply correct: `full-surface` stretches the
artwork by **1.3008×**, `fit-without-stretch` leaves **23.12 %** of the deck length bare
(11.56 % per end). Both were implemented, both measured, and both screenshotted with the same
decal, with nothing in the code picking one.

**Kylian selected `full-surface` at the M7 review gate on 2026-08-07.** See **DR-012** and
`docs/evidence/prototype-5/GATE-approval.md`. That closes the item; every other decision in this
record is unaffected.
