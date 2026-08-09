# Timed demo script — DeckForge AI

**Target: 4 minutes live.** · **Milestone:** M8 · **Presentation:** 2026-09-02
**Backup plan:** [`demo-backup-plan.md`](demo-backup-plan.md) — read it before presenting.

## The one mechanic that makes this work

**Press Generate at 0:45 and talk over it.** A warm generation is ~13 s; a cold one is ~30 s. Both
are dead air if you stop talking, and both are ample time to explain the interesting part if you
do not. The script is built around that, so **nothing is padded and no timing is faked**.

## Before the audience is in the room

```powershell
.\scripts\preflight.ps1      # must be 10/10 PASS
.\scripts\start-demo.ps1
```

Then **warm the model with one generation**, so the live one is 13 s rather than 30 s. This costs a
generation and is Kylian's decision — see the open item at the end. If it is not authorised, the
live generation is cold at ~30 s and the 0:45–1:30 block simply runs longer; the script still works.

Checklist: browser at the printed URL, **not** `?review=1` · one browser tab, no console open ·
notifications off · `docs/evidence/M8/backup-demo/` open in a second window, minimised.

## The script

### 0:00–0:30 · What and why

> "DeckForge AI generates skateboard decal artwork from a text prompt, in a chosen visual style,
> and previews it on a 3D deck. The model runs **locally, on this laptop's GPU** — nothing is sent
> to an API. The three styles are not prompt tricks: they are **LoRA adapters I trained myself** on
> a 148-image dataset I collected and licensed."

No clicking yet. Let them read the interface.

### 0:30–0:45 · The controls

Point, don't click: prompt · style · optional reference image · advanced settings.

> "Three styles. Note this one" — point at **Retro silkscreen poster (partial)** — "ships marked
> *partial pass*, because it learned poster conventions along with the style. I'll come back to
> that."

### 0:45 · **Press Generate**

Type the prompt beforehand so the click is instant. Suggested: **`a mountain and a rising sun`**,
style **Ukiyo-e woodblock** — the unambiguous PASS, and its results read well at a distance.

### 0:45–1:30 · Talk over the generation

Point at the progress panel as you speak.

> "That progress bar is showing **real diffusion steps** — step 14 of 30 — reported by the pipeline
> as they happen. It is not a timer pretending to be progress.
>
> When the model is loading, it says so and shows **no percentage at all**, because loading exposes
> no measurable progress. I could have shown a bar creeping to 90 %. It would look better and it
> would be a lie about where the time went, so the interface refuses to make one up."

If it is still running, add:

> "Behind this: Stable Diffusion 1.5, one of my trained adapters at weight 0.7, and optional
> IP-Adapter reference conditioning. The whole stack fits in 8 GB with about **200 MiB to spare** —
> 2.4 % of the card. That margin is the constraint the entire project is built around."

### 1:30–1:50 · The result

> "There it is. About thirteen seconds."

Open **Reproducibility metadata**.

> "Every generation carries the seed, the pinned model revision, the **SHA-256 of the adapter that
> produced it**, and the measured VRAM. This image is traceable back to a specific experiment — it
> isn't just a picture."

### 1:50–2:30 · The 3D deck

Orbit and zoom.

> "The artwork is applied to the deck as a texture. The geometry is my own — procedurally generated,
> not a downloaded model.
>
> One honest detail: generated decals are 1:3 and the deck's surface is 1:3.9, so the artwork is
> **stretched 1.3×**. I built both options — stretch to fill, or preserve aspect and leave 23 % of
> the board bare — and chose to fill. **The interface says so, right there**, rather than hiding it."

### 2:30–2:50 · Upload your own decal

> "Not everything needs the model. If you already have artwork, upload it and it goes straight onto
> the board — no GPU, no server round trip."

Upload a prepared file. **This is also the live fallback**, so the audience seeing it work is not a
detour.

### 2:50–3:30 · What the research actually found

The strongest section. Do not skip it for more clicking.

> "Two results worth stating. First: **two of my three production checkpoints are from step 300, not
> the 600 they trained to.** Training longer made the style stronger and the model **less obedient
> to the prompt** — adherence dropped from 4 to 3 while style consistency held at 5. I only found
> that because I checkpointed along the way and had a human score them blind.
>
> Second, the limitation: **style conditioning can dominate detailed prompts.** Ask for a city
> skyline with a skateboarder and you get a beautiful, correctly-styled deck in which neither is
> clearly there. That's measured, it's documented, and it's not fixed."

### 3:30–4:00 · Reproducibility, and close

> "All of it is reproducible: 469 backend tests, 169 frontend, 37 browser end-to-end, a clean-clone
> test that installs from scratch and reaches a working system in ten minutes, and every checkpoint
> verified by hash on every request.
>
> The deliverable is the process — thirty-five experiments, fourteen decision records, and the
> failures kept in the write-up rather than deleted."

## What NOT to show

- **`?review=1`** — review tools are not production, and explaining them costs 30 s for nothing.
- A **second live generation.** One is the demo; two is a queue.
- The terminal, beyond the start command.
- Raw evidence files, the experiment registry, or the process log — **reference** them, don't scroll
  them.
- `retro-poster` as the live generation. It is a **partial pass**; showcase it in words, generate
  with a full pass.

## If a question comes

| question | one-line answer |
|---|---|
| "Why not SDXL?" | Measured: 1024×1024 needed 10.7 GB against 8 GB physical — it degraded silently rather than failing. DR-007. |
| "Why so slow?" | 30 denoising steps at 512×1536 on a laptop GPU. 13 s warm is the measured cost, not an unoptimised path. |
| "Can several people use it?" | No, and not by accident: one GPU, one resident pipeline, 200 MiB spare. A second request gets a 409 rather than an OOM. |
| "Is this just Stable Diffusion?" | The base is. The **styles are mine** — trained adapters, from my own dataset, selected at a blind human gate. |
| "Could you train more styles?" | Yes; ~3 minutes of training each. The limit was evaluation, not compute. |

## Open item for Kylian

**Whether to pre-warm the model with one generation before presenting.** It costs one generation
(total → 28) and turns the live cold start of ~30 s into ~13 s. The script works either way; only
the length of the 0:45–1:30 talk-over changes.
