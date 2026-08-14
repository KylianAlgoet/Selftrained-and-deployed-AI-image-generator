# Claude asset manifest — visual evidence per slide

**Companion to** [`claude-presentation-handoff.md`](claude-presentation-handoff.md).
**Date:** 2026-08-14 · **Milestone:** M10 (OPEN)

Every path below is **tracked in this repository** and every dimension was measured on 2026-08-14.
**No binary is duplicated for this handoff** — these are references to existing evidence files.

## Rules that apply to every asset

- **Cropping and scaling are allowed.** Cropping to one pair, one row or one panel of a contact
  sheet is normal and expected — the sheets were built for review at desk distance, not for a
  projector.
- **Recolouring, retouching, compositing outputs that were never produced together, or "cleaning up"
  a generated image is NOT allowed.** These are experimental results.
- **A crop must not change what the image proves.** Cropping a near-copy pair down to one member of
  the pair, or cropping the garbled lettering out of a `retro-poster` sheet, would each destroy the
  finding the image exists to show.
- **Captions naming the experiment are required** where indicated. `EXP-###` identifiers are
  validated against `experiments/registry.csv`, so they are safe to print.

---

## Slide 1 — Title

**No image.** Typography only. A full-bleed dark background is preferred over any decorative
graphic.

---

## Slide 2 — The assignment + research question

**No image required.** If one is wanted, use a single generated deck at large scale:

| | |
|---|---|
| path | `docs/evidence/prototype-5/screenshots/fit-full-surface.jpg` |
| type | application screenshot (3D deck with a generated decal applied, shipped fit mode) |
| depicts | the finished artefact — a generated decal mapped onto the 3D board |
| why evidence | it is the real product output, not a mock-up |
| crop | allowed; crop to the board itself |
| caption | not required on this slide |

Sibling `fit-without-stretch.jpg` is the **rejected** fit mode — do not use it here, and do not
present the two as if the choice were open. It was decided in DR-012.

---

## Slide 3 — 8 GB changed every decision

**Diagram, not a photograph.** Claude should draw the P0 → P5 prototype ladder and the memory bar
from the numbers in the handoff. There is no image asset to reuse: the existing ladder is inline SVG
inside `slides/sources/03-method.md`, and it should be **redrawn**, not extracted.

Optional supporting asset:

| | |
|---|---|
| path | `docs/evidence/prototype-1/measurement-summary.md` |
| type | markdown table (source of the memory figures) |
| use | reference only — do not screenshot a markdown file onto a slide |

---

## Slide 4 — Dataset + provenance

| | |
|---|---|
| path | `docs/evidence/dataset-v1/contact-sheet-ukiyo-e.jpg` |
| type | contact sheet, **1024 × 896** |
| depicts | the ukiyo-e training split — woodblock prints from the Metropolitan Museum (CC0) |
| why evidence | it is the actual training data, not an illustration of it |
| crop | **allowed and recommended** — 6–9 tiles read far better than the full grid |
| caption | *"Ukiyo-e split — Metropolitan Museum of Art, CC0."* |

**Better — and recommended — show all three styles.** All three sheets exist and are tracked:

| style | path | items |
|---|---|---:|
| ukiyo-e | `docs/evidence/dataset-v1/contact-sheet-ukiyo-e.jpg` | 55 |
| minimal-geometric | `docs/evidence/dataset-v1/contact-sheet-minimal-geometric.jpg` | 52 |
| retro-poster | `docs/evidence/dataset-v1/contact-sheet-retro-poster.jpg` | 41 |

Build a **three-column strip, one column per style**, each cropped to 4–6 tiles. That communicates
"three visually distinct styles" in one glance, which a single sheet cannot, and it makes the
distinctness claim on slide 13 something the jury has already seen rather than been told.

**Do not** present the dataset as a spreadsheet or a file listing.

---

## Slide 5 — SDXL was better, and rejected

| | |
|---|---|
| path | `docs/evidence/prototype-1/cross-model-track-B-seed42.jpg` |
| type | benchmark grid, **1280 × 512** |
| depicts | SDXL outputs at its designed 1024 × 1024, seed 42 |
| why evidence | **these are the images the 10 738 MiB measurement came from** — the quality that was rejected |
| crop | allowed; 2–3 panels at large scale beat all of them small |
| caption | **required** — *"Track B — SDXL at 1024 × 1024, its designed resolution. EXP-006."* |

Optional companion (only if the comparison needs both halves):

| | |
|---|---|
| path | `docs/evidence/prototype-1/cross-model-track-A-seed42.jpg` |
| type | benchmark grid, **1280 × 512** |
| depicts | all candidates at a common 512 × 512 |
| caption | *"Track A — all candidates at 512 × 512."* |

**The memory contrast should be typographic, not photographic**: `10 738 MiB needed` against
`8 187.5 MiB available` set large is the point of the slide, and no image can make it.

---

## Slide 6 — The free method lost (img2img near-copy)

**This is the slide the human review flagged as too small to read. It needs a large crop.**

| | |
|---|---|
| path | `docs/evidence/prototype-2/copy-risk-pairs.jpg` |
| type | comparison sheet, **512 × 2048**, portrait |
| depicts | flagged near-copy pairs: **left column = the reference the user supplied, right column = what img2img returned** |
| why evidence | 6 outputs were flagged at dHash ≤ 6; **two scored dHash 0 — perceptually identical to their reference** |
| crop | **required** — the full sheet is unusable on a projector |

### Layout of that file, measured

Two blocks, described in fractions of the 512 × 2048 canvas:

| block | region | content |
|---|---|---|
| **A (top, ~y 0.00–0.72)** | two tall strips: left `x ≈ 0.15–0.40`, right `x ≈ 0.64–0.90` | the **deck-format (512 × 1536) minimal-geometric pair** — reference vs img2img output, near-identical |
| **B (bottom-left, ~y 0.73–1.00, `x ≈ 0.08–0.42`)** | two stacked framed posters | a **retro-poster reference and its img2img output** — visually indistinguishable |
| B′ (bottom-right) | two stacked posters | a pair that differs more; **weaker evidence, do not lead with it** |

### Recommended treatment

**Primary — crop block A, upper half only** (`y ≈ 0.00–0.40`, both columns). This is the research
result at the production geometry: two tall deck graphics side by side that are obviously the same
image. Label the columns **REFERENCE** and **IMG2IMG OUTPUT** in large type.

**Alternative — crop block B.** The two framed theatre posters read as identical instantly, even
from the back of a room, and are the stronger *pure* near-copy demonstration if legibility beats
geometry.

Using **one** of these very large is better than using both.

**Caption required:** *"img2img at the deck format, strength 0.65. Two of six flagged outputs scored
dHash 0 — perceptually identical to the reference. EXP-013."*

**Do not** crop away either column, and do not present a single image as though it were the pair.

### The quantitative contrast worth setting in type

| geometry | runs | median dHash to reference | minimum |
|---|---:|---:|---:|
| 512 × 512 | 31 | 27 | 12 |
| **512 × 1536 (production)** | 9 | **5** | **0** |

Lower means more similar. The mechanism is mechanical and can be stated in one line: img2img forces
the reference into the output resolution, and references natively at 512 × 1536 keep 100 % of their
area, so denoising starts from an essentially intact copy.

**Do not** use `method-comparison-medium-seed42.jpg` for this slide. It is a 4 × 4 grid at
512 × 512 — the geometry where near-copies do **not** occur — so it shows diversity and would
undercut the point.

---

## Slide 7 — Training longer made it less obedient

**A matched pair. Both images, side by side, large.**

| | |
|---|---|
| path A | `docs/evidence/prototype-4/final-sheets/EXP-027__minimal-geometric__ck00300__512x512.jpg` |
| path B | `docs/evidence/prototype-4/final-sheets/EXP-027__minimal-geometric__ck00600__512x512.jpg` |
| type | rubric sheets, **512 × 896** each |
| depicts | the same style, same prompts, **same seeds**, at 300 and 600 training steps |
| why evidence | style consistency held at **5**; prompt adherence fell **4 → 3**. This is why two adapters ship at step 300 |
| crop | **allowed and recommended** — crop both to the **same rows** so the comparison stays honest |
| caption | **required** — *"EXP-027, minimal-geometric. Same prompts, same seeds."* plus a **STEP 300 — shipped** / **STEP 600 — rejected** label |

**The crop must be identical on both.** Cropping different regions of the two sheets would fabricate
a comparison.

`retro-poster` shows the same effect (`EXP-029__retro-poster__ck00300|ck00600__512x512.jpg`, both
512 × 896) and is an acceptable substitute, but **minimal-geometric is preferred** — it is the
cleaner demonstration and `retro-poster` carries its own partial-pass complication onto slide 8.

**Ukiyo-e is the counterexample and ships at step 600.** If it is shown, it must be labelled as the
exception, not as a third example of the same effect.

---

## Slide 8 — What did not work

| | |
|---|---|
| path | `docs/evidence/prototype-4/final-sheets/EXP-029__retro-poster__ck00300__512x512.jpg` |
| type | rubric sheet, **512 × 896** |
| depicts | `retro-poster` outputs carrying **poster frames, borders and pseudo-text lettering** inherited from the training material |
| why evidence | this *is* the PARTIAL PASS. The failure mode is directly visible: garbled display type reading `KTIRER`, `XETAXE`, `MAUNTIT REST`, and mountains sitting inside poster frames |
| crop | **allowed and recommended** — the middle rows (`y ≈ 0.35–0.75`) hold the clearest framed-poster-with-lettering examples |
| caption | **required** — *"EXP-029, retro-poster at step 300. The frames and lettering are inherited from the source material, not requested by the prompt."* |

**Do not crop the lettering out.** The garbled type is the evidence.

**Currently the deck references the `512x1536` variant of this sheet, which is only 512 × 128 — far
too small to read.** Use the `512x512` variant above.

---

## Slide 9 — The integrated system

**Build a new diagram. Do not reuse or trace the existing one.**

The current inline SVG in `slides/sources/09-system.md` is the diagram that **rendered as literal
source code** in an earlier PDF (root cause in the handoff). It has since been fixed in-repo, but
its layout was built for a 26-slide deck and is not the right visual answer here.

Draw from the verified facts in the handoff. **No image asset.**

---

## Slide 10 — Testing

**No image.** Typography and one number.

If a visual is wanted, the clean-clone result is the only honest candidate:

| | |
|---|---|
| path | `docs/evidence/M8/clean-clone/real-output/screenshots/02-result-and-deck.jpg` |
| type | application screenshot, **1440 × 900** |
| depicts | a fresh clone, fresh environment, producing a generation and rendering it on the deck |
| why evidence | this run reproduced an earlier output **byte for byte**, three days later |
| crop | allowed |
| caption | *"Clean clone, fresh environment — byte-identical to the original run."* |

**It is the same image as slide 11's.** Use it on one slide, not both — slide 11 has the stronger
claim on it.

---

## Slide 11 — Reproducibility has two halves

| | |
|---|---|
| path | `docs/evidence/M8/clean-clone/real-output/screenshots/02-result-and-deck.jpg` |
| type | application screenshot, **1440 × 900** |
| depicts | the clean-clone environment generating and rendering a decal |
| why evidence | **SHA-256 `46bbf160e427…`, 1 089 939 bytes, identical to the original run three days earlier in a freshly built environment** |
| crop | allowed |
| caption | **required** — *"Clean clone, fresh environment. SHA-256 identical to the original run."* |

**The right-hand (training) half has no image and must not be given one.** There is no photograph of
a reproducibility failure; it is a statement about weights. Set it in type.

---

## Slide 12 — Local, deliberately

**No image.** A compact four-option comparison, set typographically, with the selected option marked.

---

## Slide 13 — Conclusion

**No image.** Large type.

---

## Slide 14 — Live demo

**No image, or one.** The slide stays on screen during the browser transition, so it must be
readable and calm.

| | |
|---|---|
| path | `docs/evidence/prototype-5/screenshots/ui/03-denoising.jpg` |
| type | application screenshot, **1960 × 938** |
| depicts | the interface mid-generation, showing the real denoising step count |
| why evidence | the progress display reports **actual diffusion steps**, not a synthetic animation |
| crop | allowed |
| caption | optional |

---

## Slide 15 — What I would change

**No image.** Typography only.

---

## Assets deliberately NOT recommended

| path | why not |
|---|---|
| `docs/evidence/prototype-2/method-comparison-medium-seed42.jpg` | 4 × 4 grid at 512 × 512 — the geometry where near-copies do **not** occur. Shows diversity, undercuts slide 6 |
| `docs/evidence/prototype-4/final-sheets/*__512x1536.jpg` | all are 512 × **128** — thin strips, unreadable when projected |
| `docs/evidence/prototype-2/reference-kit-sheet.jpg` | 1280 × 256; useful context, no argument attached |
| `docs/evidence/prototype-4/final-sheets/EXP-030__*` | the multi-style adapter — **viable but not selected**. Showing it invites a question the deck has no time to answer |
