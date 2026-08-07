# Prototype 5 — the integrated MVP

**Milestone:** M7 · **Dates:** 2026-08-06 to 2026-08-07 (planned Aug 10–13; started early on M6's buffer)
**Status: COMPLETE.** Final human visual gate **APPROVED by Kylian Algoet on 2026-08-07**
(`docs/evidence/prototype-5/FINAL-GATE-approval.md`, 12 of 12 checklist items PASS).
Closed **locally only** — nothing pushed, the remote issue and project board untouched.
**Decision records:** DR-011, DR-012, DR-013 · **Experiments:** EXP-034, EXP-035
**Evidence:** `docs/evidence/prototype-5/`

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

## What the live progress run actually established (2026-08-07)

Kylian ran **one real generation** through the reviewed interface — the **26th**, past the declared
cap of 25, and his decision. Recorded as a planning change rather than absorbed silently.

**Confirmed from the retained telemetry** (operation `cHWlV0J6Qgh2BKze`):

```
status completed · stage completed · current_step 30 · total_steps 30
denoising_fraction 1.0 · elapsed_seconds 40.83 · pipeline_loaded true
```

**Confirmed from the API access log:** **1** `POST /api/generate` → 200, and **48**
`GET /api/generation-progress` polls across the request. At 750 ms that is continuous polling for
the whole ~41 s, so the browser was receiving snapshots throughout — including the denoising
window, whose snapshots carried `stage: denoising` and `total_steps: 30`.

**What the server cannot establish:** which strings the browser painted. The access log records
requests, not rendered text. Rendering those snapshots as `Diffusion step N of 30` and an
approximate remaining time is covered by tests, and no defect was found in the path — but "the
data was produced and delivered" is not the same claim as "he saw it", and the two are not merged
here.

**Two reasons a stage could be present and still be missed**, both measured rather than guessed:

- The request was a **cold start**: 40.83 s total against a ~13 s warm generation, so roughly
  **28 s of it was model loading**, and denoising occupied only about the last twelve seconds.
- **`Finalising the decal…` is genuinely brief.** It is shown from the last denoising callback
  until the response arrives — the VAE decode, the PNG encode and the file write, on the order of
  a second. It is not padded, and it will not be: delaying a finished result to make a label
  linger is the kind of dishonesty this whole feature exists to avoid.

**No fix was made, because no defect was found.** A warm generation is the decisive check: at
~13 s with no model load, the step counter is the dominant display for most of the wait.

## Upload your own decal (2026-08-07)

A **production** feature, added at Kylian's request: someone who already owns artwork can preview
it on the deck without spending a generation.

It is **wholly local**. The file is decoded in the browser and drawn onto a canvas — it never
reaches the server, never calls `POST /api/generate`, and never loads or touches the model. That
is checked from the server rather than asserted: across the upload tests the access log's POST
count stayed at 1 and `allocated_mb` stayed at 3316.64.

It is deliberately **not** the reference-image upload, and they sit in different parts of the
interface: the reference is *conditioning*, sent to the server to influence what the model
produces; this is the *finished decal*.

Honesty rules it inherits from the rest of the project:

- uploaded artwork is labelled **`User-uploaded artwork`** with its filename;
- it gets **no reproducibility metadata**, because there is none to give — and the AI PNG and
  metadata downloads continue to refer only to the generated result;
- when an upload is on the deck, the result panel says so rather than claiming the generation is
  applied;
- a failed decode **preserves the previous decal** and says what happened.

It uses the `full-surface` mapping (DR-012) and the existing orientation, colour-space,
texture-disposal and camera-state behaviour, unchanged. The review-only "Load decal" control it
supersedes was removed; texture-fit and inverted-UV remain review-only.

## Conclusion

**Prototype 5 answers its research question: yes.** The measured stack — SD 1.5 + one per-style
LoRA at 0.7 + IP-Adapter at 0.55 at 512×1536 — runs as a usable application on one 8 GB device,
with residency costing nothing measurable (0.00 MiB growth across six adapter cycles) and peak
allocation byte-identical to M5's EXP-019b. The application generates, previews on an interactive
deck, downloads, and reports its own provenance.

Three decisions were taken here and all three are human: **DR-011** (service architecture),
**DR-012** (`full-surface`), **DR-013** (progress telemetry). Two were left deliberately open
until Kylian could see them, and a test enforced that the code had not pre-empted him.

**Approved at the final visual gate on 2026-08-07, 12 of 12 checklist items PASS.**

## Accepted limitations, carried into M8 and the report

These were **approved as limitations**, not deferred as defects:

1. **Cold model loading has no honest percentage** — ~30 s with no progress signal; the stage is
   named instead.
2. **The ETA is approximate and mainly covers denoising** — not loading, decoding, saving,
   transfer or texture application.
3. **Finalising may be visible only briefly** (~1 s). **It must not be artificially delayed.**
4. **Prompt adherence can be weaker than style adherence.**
5. **The physical GPU margin is approximately 200 MiB** — not comfortable headroom.
6. **One API process and one worker only.**

## Generation budget — final

**26 total.** The research budget closed at **25 / 25**; generation **26** was a manual
human-review run performed by Kylian during the final interface review, **outside the frozen
research matrix**. It is deliberately **not** in EXP-034 and **not** in `experiments/registry.csv`
— it produced no research result and was not run under the pre-declared measurement conditions.

## Next

**M8 — testing, deployment and demo.** It has **not** begun. It inherits a single-process service
by design, the ~200 MiB ceiling, `full-surface`, `retro-poster` as a named partial pass, and the
prompt-adherence limitation above.

Still Kylian's, and still outstanding: the **push**, the **GitHub issue** and the **project
board**. `gh` is unavailable in this environment.
