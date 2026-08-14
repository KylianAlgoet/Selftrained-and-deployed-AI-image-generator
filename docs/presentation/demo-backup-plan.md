# Backup demo plan

**Milestone:** M8 · **Companion to:** [`demo-script.md`](demo-script.md)
**Rule: every fallback below is executable in under 30 seconds, and every asset already exists.**
Nothing here is fabricated or staged — the images are real outputs of real recorded runs.

## The one thing to internalise

**A failed generation does not end the demo.** The 3D preview, the styles list, the interface and
the entire research argument work without the model. If generation dies, you lose ~40 seconds of a
4-minute talk — and only if you let it show.

Say this, and mean it:

> "Live generation isn't cooperating — I'll switch to a validated recorded run. This is
> `P5__minimal-geometric__seed42`, generated on this machine on the date in the metadata."

Then move. Do not debug on stage.

**Name the recorded run when you switch to it.** Stating which run the audience is looking at is the
difference between a fallback and a substitution, and it costs three seconds. **Do not editorialise
about whose fault the failure is** — an earlier draft of this line said the failure was "a live-demo
problem, not a project problem", which is defensive and invites the question it is trying to close.

## The failure ladder

| # | what failed | fallback | time |
|---:|---|---|---:|
| 1 | Generation is slow / progress stalls | Keep talking — the progress panel is itself a demo point. Give it 30 s. | 0 s |
| 2 | 504 timeout, 503, or CUDA/OOM error | **`Upload your own decal`** with a pre-generated PNG. The **live app still works**; the 3D section runs unchanged. | ~15 s |
| 3 | API down, or the frontend will not load | Pre-captured screenshot set in a second window. | ~20 s |
| 4 | Machine dead, no network, projector lost | Slides carrying the same screenshots. | ~30 s |

**Rung 2 is the important one** and is the reason `Upload your own decal` is worth its place in the
demo script at 2:30: by the time you need it as a fallback, the audience has already seen it work,
so using it reads as continuity rather than as a retreat.

## Backup assets — all pre-existing and verified

Assembled into git-ignored `outputs/demo-backup/` by
[`scripts/build-demo-backup.ps1`](../../scripts/build-demo-backup.ps1). The **manifest is
committed; the binaries are not**, because every one of them is a copy of something already tracked
or already recorded.

| asset | source | what it covers |
|---|---|---|
| 6 generated decals, 512×1536 | `outputs/prototype-5/P5__*__seed42.png` — the real Phase A runs | rung 2 and 3 |
| Phase A results | `docs/evidence/prototype-5/api-validation.jsonl` | the durations quoted live |
| 11 UI screenshots | `docs/evidence/prototype-5/screenshots/ui/` | idle, loading, denoising, finalising, success, error, responsive, review, upload |
| 3 deck screenshots | `docs/evidence/prototype-5/screenshots/` | orientation, both texture-fit modes |
| 2 clean-clone screenshots | `docs/evidence/M8/clean-clone/screenshots/` | reproducibility claim |
| checkpoint hashes | `docs/deployment/weights-manifest.md` | the traceability claim |
| EXP-034 residency figures | `experiments/registry.csv` | the 200 MiB claim |

**No asset is fabricated.** If a claim has no evidence behind it, it is not in this plan.

### The one asset that does not exist yet

**A screen recording of the working flow.** It must be a recording of a real session or it does not
exist, and no such session has been recorded. Listed as an open item; if it is not made, rungs 3
and 4 rest on the screenshots, which is sufficient.

## Rung 2, step by step

1. Say the line above. **Do not** reload, retry, or open a terminal.
2. Click **Upload your own decal** → pick `outputs/demo-backup/decals/P5__ukiyo-e__promptonly__seed42.png`.
3. Continue the 3D section **exactly as scripted** — orbit, zoom, the 1.3× stretch disclosure.
4. Say once, plainly:

> "That's a real output from this model, generated on this machine — the run is in the evidence,
> with its seed and its adapter hash."

Then continue to the research findings, which is the strongest part of the talk and needs no GPU.

## Rung 3, step by step

1. Switch to the screenshot window (already open, minimised).
2. Walk `01-idle` → `03-denoising` → `05-success` → the deck screenshot.
3. Say:

> "This is the same flow captured from a real session. The generation timings — 30 seconds cold,
> 13 warm — are measured and recorded, not estimates."

## Pre-flight, the evening before and again on the day

```powershell
.\scripts\preflight.ps1                    # 10/10 PASS
.\scripts\start-demo.ps1
# one warm-up generation, if authorised
.\scripts\stop-demo.ps1
```

Also: laptop **on mains** and NVIDIA set to maximum performance · nothing else on the GPU (close
other browsers, video calls, editors) · `outputs/demo-backup/` populated · backup screenshots open
in a second window · a copy of the backup folder on a USB stick.

## Known live risks, and what each looks like

| risk | symptom on stage | rung |
|---|---|---|
| Cold model load | ~30 s with "Loading the local generation model…" and no percentage | 1 — this is correct behaviour, say so |
| VRAM pressure from another process | 503, or a very slow generation | 2 |
| 504 deadline | "stopped after N of 30 steps" | 2 |
| A second API process left running | 409 on every attempt | 2, then `stop-demo.ps1 -Force` after |
| Prompt adherence | The decal is beautiful but ignores half the prompt | **Not a failure — it is a documented finding.** Say so and use it. |

That last row matters: **do not apologise for it and do not re-roll.** A measured, documented
limitation presented as such is stronger evidence of research quality than a lucky image.

## What must not happen

- **Do not debug live.** Every rung exists so you never have to.
- **Do not run a second generation** hoping the first was unlucky. That is how 40 seconds becomes
  three minutes.
- **Do not open `?review=1`** looking for something to show.
- **Do not present a backup image as live output.** If it is pre-generated, say so — the assets are
  real and the honesty costs nothing.
