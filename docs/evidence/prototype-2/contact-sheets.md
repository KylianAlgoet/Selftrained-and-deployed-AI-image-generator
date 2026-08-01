# Prototype 2 contact sheets - grid legend

Every sheet below is a plain grid with no burnt-in labels, so this file is how a
cell is identified. Rows fill left to right, top to bottom.

**Two reading rules that apply throughout:**

- **img2img `strength` is inverted** - a LOWER number means a STRONGER reference.
  Sweep columns are ordered by ascending reference influence, so the img2img
  strength numbers descend from left to right.
- **The shared level names are an assumption under test, not a calibrated
  equivalence.** img2img `strength=0.65` and IP-Adapter `scale=0.55` are both
  labelled *medium*; nothing establishes that they exert comparable influence.

No sheet carries a quality judgement. Scoring is the reviewer's, on the blank form.

## `method-comparison-medium-seed42.jpg`

**Method comparison at the medium influence level, seed 42, 512x512**

4 columns · 16 cells · 219 KB

The 'medium' label is an assumption under test: nothing establishes that img2img 0.65 and IP-Adapter 0.55 exert comparable influence.

**Rows**

- row 1 = C1 (style-matched - reference and prompt are both retro-poster)
- row 2 = C2 (style-matched; already at the deck aspect)
- row 3 = C3 (style-matched on style; subject differs (interior scene vs cresting wave))
- row 4 = C4 (layout transfer onto a different subject)

**Columns**

- column 1 = text-only baseline (no reference)
- column 2 = img2img, strength 0.65
- column 3 = IP-Adapter, scale 0.55
- column 4 = IP-Adapter-Plus, scale 0.55

## `sweep-img2img-seed42.jpg`

**img2img reference-strength sweep, seed 42, 512x512**

5 columns · 20 cells · 177 KB

Columns run left to right from WEAKEST to STRONGEST reference influence. For img2img that means the strength number DECREASES left to right, because strength is inverted.

**Rows**

- row 1 = C1
- row 2 = C2
- row 3 = C3
- row 4 = C4

**Columns**

- column 1 = strength 0.9
- column 2 = strength 0.75
- column 3 = strength 0.6
- column 4 = strength 0.45
- column 5 = strength 0.3

## `sweep-ipadapter-seed42.jpg`

**ip-adapter reference-strength sweep, seed 42, 512x512**

5 columns · 20 cells · 195 KB

Columns run left to right from weakest to strongest reference influence.

**Rows**

- row 1 = C1
- row 2 = C2
- row 3 = C3
- row 4 = C4

**Columns**

- column 1 = scale 0.2
- column 2 = scale 0.4
- column 3 = scale 0.6
- column 4 = scale 0.8
- column 5 = scale 1.0

## `multiseed-diversity.jpg`

**Multi-seed diversity at the medium level, 512x512**

3 columns · 48 cells · 283 KB

This is what makes `diversity_across_seeds` scoreable for the first time. Its limitation is stated rather than glossed: it shows the three FROZEN seeds (42, 1337, 2026), not a random sample of the seed space.

**Rows**

- row 1 = text-only / C1
- row 2 = text-only / C2
- row 3 = text-only / C3
- row 4 = text-only / C4
- row 5 = img2img / C1
- row 6 = img2img / C2
- row 7 = img2img / C3
- row 8 = img2img / C4
- row 9 = ip-adapter / C1
- row 10 = ip-adapter / C2
- row 11 = ip-adapter / C3
- row 12 = ip-adapter / C4
- row 13 = ip-adapter-plus / C1
- row 14 = ip-adapter-plus / C2
- row 15 = ip-adapter-plus / C3
- row 16 = ip-adapter-plus / C4

**Columns**

- column 1 = seed 42
- column 2 = seed 1337
- column 3 = seed 2026

## `conflict-text-vs-reference.jpg`

**C5 conflict: a figurative ukiyo-e reference against a minimal-geometric prompt**

3 columns · 6 cells · 100 KB

CONFLICT - reference is a figurative ukiyo-e interior scene, prompt asks for minimal-geometric flat shapes. Reference R3: ukiyo-e. Prompt loss as influence rises is the measurement here, not a defect.

**Rows**

- row 1 = img2img
- row 2 = ip-adapter

**Columns**

- column 1 = weak
- column 2 = medium
- column 3 = strong

## `difficult-reference-artefacts.jpg`

**C6 difficult reference: frame, typography and landscape orientation**

3 columns · 6 cells · 99 KB

difficult - frames, typography, wrong orientation. Reference R5: deliberately difficult. Prompt loss as influence rises is the measurement here, not a defect.

**Rows**

- row 1 = img2img
- row 2 = ip-adapter

**Columns**

- column 1 = weak
- column 2 = medium
- column 3 = strong

## `deck-format-512x1536.jpg`

**EXP-013 deck format 512x1536 at the medium level, seed 42**

3 columns · 6 cells · 30 KB

img2img must crop each reference to 1:3 and lose the discarded area (R1 keeps ~49 %, R2 100 %, R4 100 %); IP-Adapter passes the reference through a 224 px CLIP crop regardless of output geometry. Look here for repeated elements and vertical stretching, the open M3 observation.

**Rows**

- row 1 = img2img
- row 2 = ip-adapter

**Columns**

- column 1 = C1
- column 2 = C2
- column 3 = C4

## `copy-risk-pairs.jpg`

**The 8 outputs perceptually closest to their reference**

2 columns · 16 cells · 95 KB

Ordered by ascending dHash distance, closest first. dHash is a COARSE NEAR-COPY FLAG ONLY - not a measure of style, quality, or influence strength, and a low distance is a candidate for human judgement rather than a verdict. Near-copies are flagged and kept, never deleted: reproducing the reference is a first-class RQ11 finding. Score these under `originality` and `copy_or_overfitting_risk`.

**Rows**

- row 1 = R4 vs img2img C4 medium (0.65) seed 1337 - **dHash distance 0** - AT OR BELOW THE COPY-RISK THRESHOLD OF 6
- row 2 = R4 vs img2img C4 medium (0.65) seed 2026 - **dHash distance 0** - AT OR BELOW THE COPY-RISK THRESHOLD OF 6
- row 3 = R4 vs img2img C4 medium (0.65) seed 42 - **dHash distance 1** - AT OR BELOW THE COPY-RISK THRESHOLD OF 6
- row 4 = R2 vs img2img C2 medium (0.65) seed 42 - **dHash distance 3** - AT OR BELOW THE COPY-RISK THRESHOLD OF 6
- row 5 = R2 vs img2img C2 medium (0.65) seed 1337 - **dHash distance 5** - AT OR BELOW THE COPY-RISK THRESHOLD OF 6
- row 6 = R2 vs img2img C2 medium (0.65) seed 2026 - **dHash distance 5** - AT OR BELOW THE COPY-RISK THRESHOLD OF 6
- row 7 = R1 vs img2img C1 strong (0.4) seed 42 - **dHash distance 10**
- row 8 = R1 vs img2img C1 strong (0.4) seed 1337 - **dHash distance 10**

**Columns**

- column 1 = the reference image
- column 2 = the generated output
