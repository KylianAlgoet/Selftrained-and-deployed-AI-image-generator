# DR-013 — How the interface reports generation progress

**Status:** accepted · **Date:** 2026-08-07 · **Milestone:** M7 (Prototype 5)
**Answers:** how a browser waiting on a synchronous 12–13 s generation is told what is happening,
without changing what the generation does.
**Related:** DR-011 (synchronous endpoint, single-flight lock, one process — all preserved here)
**Evidence:** `apps/api/progress.py`, `apps/api/tests/test_progress.py`,
`apps/web/src/generate/progressModel.ts`, `docs/evidence/prototype-5/screenshots/ui/`

## Context

A generation takes 12–13 s resident and **30.54 s on the first request of a process**. The M7
interface showed one static line for all of it: *"Generating at 512×1536 — this takes around 15
seconds."* That sentence is wrong for a cold start by a factor of two, and it says nothing at all
while the model loads.

The constraint that shapes every option: **DR-011's `POST /api/generate` is synchronous, holds a
process-local lock for the whole generation, and must not change.** Anything added here observes;
it may not participate.

## Alternatives

| # | option | why it was or was not chosen |
|---|---|---|
| **A** | **Read-only `GET /api/generation-progress`, polled by the client** | **Selected.** One extra endpoint, no new dependency, no second process, no protocol. The POST contract is untouched and the endpoint cannot influence a generation. |
| B | Server-Sent Events | Rejected. A streaming response occupies a connection for the request's lifetime and adds a second lifecycle to reason about on a single-worker server whose one certainty is that it does one thing at a time. |
| C | WebSocket | Rejected for the same reason as B, with more machinery and a handshake, for strictly one-way data. |
| D | Job id plus a status endpoint (async generation) | Rejected. Already rejected once as DR-011 §1: it roughly doubles the endpoint surface and lifecycle, and it would make the generation asynchronous — the change this decision exists to avoid. |
| E | Report nothing; keep the static estimate | Rejected. It is the current behaviour and it is measurably wrong on a cold start. |

B, C and D were **screened, not measured** — none was implemented, and no performance claim is
made about them.

## Decision

**Option A.** `GET /api/generation-progress` publishes process-local telemetry for the single
in-flight generation, polled by the frontend every 750 ms.

Four properties make it safe to read while the GPU is working, and each has a test:

1. **It never touches the generation lock**, in either direction. A gated test polls ten times
   mid-generation and asserts a concurrent POST still receives 409.
2. **The deadline callback is composed, not replaced.** Diffusers accepts one
   `callback_on_step_end`, and the deadline that makes a 504 truthful lives in it. Passing a
   progress callback instead would have silently removed the abort. `compose_step_callbacks`
   threads both and returns the loop kwargs unchanged.
3. **Writes are bound to an operation id**, so a stale reporter from an abandoned generation
   cannot overwrite the current one's numbers, and a 409 never reaches `progress.begin`.
4. **The state holds only numbers and short enumerated strings** — no paths, filenames, prompts,
   tensors or model objects. What cannot be stored cannot be leaked.

## The honesty rule this decision turns on

**Only denoising has a real denominator.** Diffusers reports "step 18 of 30", so a percentage
there is a measurement. Model loading, LoRA loading, reference preparation, VAE decoding and PNG
encoding expose **no progress signal at all**.

The tempting design is a weighted overall percentage — "loading is 40 % of the request" — which
would look better and would be invented. It is refused. Those stages get a **stage name and no
number**, and `estimated_remaining_seconds` is `null` for all of them. A test enumerates every
non-denoising stage and asserts no percentage is produced for any of it.

Consequences of that rule, all visible in the interface:

- a cold start says **"Loading the local generation model…"** with no bar and no estimate;
- the estimate is withheld until **at least three real steps have been timed** (one sample would
  be the warm-up step), and until then the panel says **"Measuring generation speed…"**;
- when the last denoising step lands the percentage is **withdrawn**, because what remains is the
  VAE decode: **"Finalising the decal…"**;
- an estimate that runs out is **retracted** — "Finishing the artwork…" — never counted past zero;
- **100 % is claimed only when the response has arrived AND the PNG has decoded in the browser.**
  The diffusion track filling is labelled as diffusion progress, not as request completion.

## Estimate method

Exponential moving average (α = 0.3) over completed step durations on a **monotonic** clock,
multiplied by the steps remaining. Published only during denoising, only after 3 samples, only
while steps remain. Clamped at zero, rounded to whole seconds for display, hedged as "About", and
smoothed so a change below one second does not redraw — a change of a second or more is shown
immediately, so a genuine slowdown is never hidden.

## Consequences

- **The first request of a process cannot have a reliable end-to-end estimate.** ~30 s of model
  loading has no measurable progress and is deliberately not modelled. This is stated in the
  interface rather than papered over.
- The estimate covers **measured denoising only**. It does not include decoding, saving, transfer
  or texture application, and it is labelled approximate.
- **Losing telemetry never fails a generation.** A failed poll degrades the display to elapsed
  time; the POST remains authoritative.
- Polling adds one cheap GET per 750 ms against a server that is single-flight by design. It takes
  only the tracker's own lock and cannot materially delay a diffusion step.
- **`applying-texture` is frontend-owned and the backend never reports it** — by the time it is
  true the GPU has finished, so calling it generation progress would misattribute the time.
