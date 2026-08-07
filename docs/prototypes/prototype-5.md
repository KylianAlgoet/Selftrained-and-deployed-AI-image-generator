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

Both are built and both disclose their trade-off numerically in the UI. **Kylian chose
`full-surface` at the gate on 2026-08-07** — the bare ends read as an unfinished deck and a
centred sticker, and the 1.3008× stretch was acceptable on the selected styles. It is now
`DEFAULT_TEXTURE_FIT_MODE`; the other mode stays selectable. Recorded in **DR-012** and
`docs/evidence/prototype-5/GATE-approval.md`.

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

## The human walkthrough (2026-08-07) — one qualitative finding

Kylian walked the complete application workflow and it **passed**: prompt-only generation,
deterministic repeat at identical settings, reference-conditioned generation, style switching,
the 2D result panel, the decal applied to the interactive deck, camera/orbit/zoom, PNG and
metadata download, correct metadata, visible `retro-poster` warnings, invalid-upload handling,
UV orientation, and the selection of `full-surface` as the production fit.

**The finding worth recording is not a defect.** One tested prompt was:

> `A futuristic city skyline with a skateboarder jumping over neon buildings`

The result was **clearly `minimal-geometric` and usable as a deck graphic**, but **the skyline and
the skateboarder were not clearly represented.** Strong style conditioning dominated detailed
prompt content.

This is a **known prompt-adherence limitation of the trained style**, not a frontend or
integration failure — the request, the metadata and the applied texture were all correct. It is
consistent with M6's measured result, where prompt adherence fell from 4 to 3 at step 600 for two
of three styles while style consistency held at 5, and it is why two of the three production
checkpoints are step 300 rather than 600.

**Nothing was changed in response to it.** No retraining, no change to the LoRA weight default, no
change to prompt assembly, and no automatic prompt rewriting — an interface that silently rewrote
the user's prompt would hide exactly this finding. The application does not claim perfect prompt
adherence anywhere.

## Limitations to carry forward

- **Single process, by design.** Scaling is not a config change (DR-011).
- **The deadline lands on a step boundary** and the VAE decode is not interruptible, so a 504
  means "the denoising loop stopped", not "the GPU idled at exactly 5.000 s".
- **Byte-identical repeats are strong evidence of no state residue, not proof of none.**
- **EXP-035 does not re-establish text-only equivalence** — that stack has no LoRA and a
  different prompt, and the claim still rests on M4's separate 12/12 result.
- **`retro-poster` remains a partial pass** and says so on every request.
- **Prompt adherence can be weaker than style adherence.** Detailed content in a prompt may not
  survive strong style conditioning; see the walkthrough finding above.
- **The first request of a process has no honest progress estimate.** Model loading is ~30 s with
  no measurable progress, so the interface names the stage and offers no number (DR-013).
- **The remaining-time estimate covers measured denoising only** — not decoding, saving, transfer
  or texture application — and is labelled approximate.

## The interface pass (2026-08-07)

After the walkthrough passed, one focused UI/UX pass rebuilt the interface as a deck studio and
replaced the static "this takes around 15 seconds" line with real progress from the pipeline
(DR-013). **No model, prompt assembly, generation setting or output behaviour changed**, and the
`POST /api/generate` request and response contracts are byte-for-byte the same shape.

Three defects were found and fixed during it, two of which no test could have caught:

1. The desktop shell **overflowed the viewport by 70 px**, pushing the deck below the fold.
2. A **horizontal scrollbar** on every page, from a `width: 100%` rule beating `.visually-hidden`
   and stretching a hidden file input to 1992 px.
3. The poll loop **restarted on every render** when the hook was given inline options, firing a
   request per render instead of one per interval. Found while writing the estimate-expiry test.

The status-readability defect was fixed at its cause: the stylesheet inherited Vite's
`color-scheme: light dark`, so a pale banner background met near-white inherited text whenever the
OS was in dark mode. Contrast is now a property of the tokens.

Interface states are evidenced in `docs/evidence/prototype-5/screenshots/ui/`, **captured with
mocked telemetry and labelled as such** — no 26th generation was run, and the API reported
`pipeline_loaded: false` afterwards as the independent check.

## Next

**The gate is partly answered.** The texture-fit default was returned on 2026-08-07 and is
implemented (DR-012, `GATE-approval.md`), and the functional walkthrough passed. **M7 is still
open:** the interface pass above stops at a **final visual human-review gate**. Milestone
completion, the issue, the board and M8 all still wait on Kylian.
