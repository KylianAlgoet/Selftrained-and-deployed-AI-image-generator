# <span class="section-number">11</span> Prototypes

Six prototypes were built in sequence. Each answered a question the next one depended on, and none
was skipped. This section reports what each established; §12 reports what failed along the way, and
§13 the measured results.

## 11.0 Prototype 0 — the 3D viewer

**Question (RQ9):** how is decal artwork correctly mapped onto a 3D deck — UV layout, nose-to-tail
orientation, and runtime texture updates?

A procedurally generated deck mesh in React Three Fiber, with **asymmetric kicks** (nose 0.17, tail
0.12) so that orientation is physically meaningful rather than decorative, and a documented UV
convention in which `v = 1` is the nose. Orbit, zoom and reset; runtime texture swap without reload;
thirteen passing tests covering UV invariants, the nose mapping, winding, determinism and the kick
asymmetry.

**The hypothesis was confirmed on the first render, and the report says so rather than manufacturing
a struggle.** The decal landed correctly the first time. There is consequently **no fix commit for an
orientation defect, because there was no orientation defect.**

<figure>
<img src="docs/evidence/prototype-0/p0-02-inverted-uv-demonstration.png" alt="Deck rendered with deliberately inverted UV mapping, showing TAIL text upside down at the nose">
<figcaption><span class="caption__label">Figure 3.</span> A <strong>controlled demonstration</strong>,
not a record of a failure: a labelled developer toggle inverts the V axis so the consequence of a
wrong UV layout is visible. The evidence files are named accordingly.
<span class="caption__source">docs/evidence/prototype-0/p0-02-inverted-uv-demonstration.png</span>
</figcaption>
</figure>

**No experiment row exists for this prototype**, because it contains no generative-model experiment.
The registry begins at Prototype 1.

**What it handed forward, including a trap.** The test decals were 512×2000, approximately 1:3.9 —
close enough to the deck's UV domain that no mismatch was visible. That is why the geometry problem in
§11.5 stayed hidden for four milestones.

## 11.1 Prototype 1 — base-model benchmark

**Questions (RQ2, RQ8):** which base model is feasible on 8 GB, and how should the deck's aspect ratio
be produced?

Covered in detail in §9.1. Three results carried forward: **SD 1.5 selected**, **SDXL rejected on
memory despite winning on quality**, and **direct 1:3 generation at
{{ facts.generation_width }}×{{ facts.generation_height }} selected** — the latter refuting the
hypothesis that tall generation would degrade and that generate-then-crop would be more reliable.
Cropping a 1:3 strip from a square generation leaves roughly 170×512 usable pixels, far below print
needs.

## 11.2 Prototype 2 — text and reference conditioning

**Question (RQ6):** how should text prompting and a reference image be combined?

Four arms were compared on measured data: img2img, standard IP-Adapter, IP-Adapter-Plus, and a
text-only baseline. ControlNet was compared on criteria and **deliberately not implemented**, with the
screen-out reason recorded.

| method | extra VRAM at 512² | control | near-copy flags |
|---|---:|---|---:|
| text-only baseline | 0 | n/a | 0 |
| img2img | **0** | monotone in strength | **6 — all of them** |
| **standard IP-Adapter** | **+1 248.69 MiB** | monotone in scale | **0** |
| IP-Adapter-Plus | +1 303.49 MiB | one level only, by design | 0 |

**Standard IP-Adapter was selected** at a default scale of
**{{ facts.ip_adapter_scale_default }}**, user-adjustable 0.40–0.60 (DR-008).

### The result that decided it

img2img costs **exactly zero extra VRAM**, which on an 8 GB budget is a serious argument. It was
rejected anyway.

Every one of the six near-copy flags in the milestone was **img2img at the deck format**, three of
them at a perceptual-hash distance of 0–1 — visually indistinguishable from the reference image. The
median distance for img2img at medium strength is 27 at 512×512 but **5 at
{{ facts.generation_width }}×{{ facts.generation_height }}**.

The mechanism was identified rather than guessed: img2img forces the reference into the output
resolution, so when the aspect ratio already matches, nothing is cropped and denoising begins from an
essentially intact copy. **A method that returns its own input is not a generator**, and the student
scored those outputs 1 for originality.

img2img is retained as a documented zero-extra-VRAM fallback, never as the default path.

<figure>
<img src="docs/evidence/prototype-2/copy-risk-pairs.jpg" alt="Side-by-side pairs of reference images and img2img outputs at the deck format, showing near-identical results">
<figcaption><span class="caption__label">Figure 4.</span> Reference images beside their img2img
outputs at {{ facts.generation_width }}×{{ facts.generation_height }}. These pairs are why the
zero-VRAM method was not selected.
<span class="caption__source">docs/evidence/prototype-2/copy-risk-pairs.jpg</span>
</figcaption>
</figure>

### Two measurement decisions worth recording

**The lower bound was tested, not promised.** IP-Adapter at scale 0.0 produced output
**byte-identical** to the text-only baseline in 12 of 12 runs, and that baseline was itself
byte-identical to Prototype 1's — cross-milestone repeatability, measured.

**The evaluation encoder was kept out of every process whose memory it would have inflated.** CLIP
similarity runs on CPU in a separate phase, and a test asserts the generation runner never imports
it. Loading 2.35 GiB of metric encoder inside a generation process would have corrupted exactly the
VRAM figures the comparison rests on.

## 11.3 Prototype 3 — LoRA smoke test

**Question (RQ1):** is local fine-tuning viable end to end on this machine?

Covered in §9.2. Thirteen runs, zero memory-tier escalations, LoRA selected (DR-009) at rank
{{ facts.lora_rank }}. The combined stack was proven to fit the deck format, which re-scoped the
project's binding risk from *does this fit* to *does anything added to it still fit*.

Full record: `docs/prototypes/prototype-3.md`.

## 11.4 Prototype 4 — style learning

**Questions (RQ4, RQ5):** how much data and which caption strategy, and one multi-style adapter or
several?

Ten training runs of a permitted twelve; both contingency slots went unused. Two human gates (§6.3).

### What shipped

| style | run | step | outcome |
|---|---|---:|---|
| minimal-geometric | EXP-027 | **300** | PASS |
| ukiyo-e | EXP-028 | **600** | PASS |
| retro-poster | EXP-029 | **300** | **PARTIAL PASS** |

**Three separate per-style adapters** at a default weight of
**{{ facts.lora_weight_default }}** (DR-010), each {{ facts.adapter_bytes }} bytes.

### The finding worth remembering

**Two of the three ship at step 300, not the 600 they were trained to.** Prompt adherence fell from
4 to 3 at step 600 for both `minimal-geometric` and `retro-poster` while style consistency held at 5.
Training longer made the model more stylish and less obedient. Only `ukiyo-e` improved.

That result exists only because checkpoints were saved at 150, 300, 450 and 600 and a human compared
them per style, instead of assuming one global step count. It is also the origin of an accepted
product limitation: **prompt adherence can be weaker than style adherence** (§18.1).

### RQ5: multi-style is viable, and was not selected

The multi-style adapter was trained with **exposure asserted rather than hoped for** — an unbalanced
run raises an error rather than producing a plausible adapter. It was competitive at 512×512 with no
severe cross-style bleed.

**It is not a failed experiment and this report does not present it as one.** Per-style adapters won
on flexibility, because each style turned out to need a *different* checkpoint step — which the
multi-style approach cannot express.

### RQ4: the caption A/B answered, the image count did not

Captions were compared as a **blinded A/B changing exactly one variable**, and style-only captions
were selected at the first gate.

The image-count arm is **inconclusive** (§5.2): non-monotonic, no minimum established, equal compute
rather than equal epochs, lead style only. The repetition confound was **declared in code before any
result existed** — 25.0, 12.5 and 6.8 presentations per item — so the limitation is part of the
experiment's design rather than an excuse added afterwards.

## 11.5 Prototype 5 — the integrated MVP

**Question:** the primary research question, end to end.

Covered in §14. Two results belong here because they are about the prototype ladder rather than the
product.

**A four-milestone-old assumption failed.** Generated decals are 1:3; the deck's UV domain is
1:3.902. Prototype 0's 512×2000 test decals had concealed this since the first milestone. Both
remedies were **built** rather than argued about — full-surface mapping with a 1.3008× longitudinal
stretch, and fit-without-stretch leaving 23.12 % of the deck bare — each disclosing its cost
numerically, with **a test asserting that no default was exported** so the choice had to be made by a
human. The student selected full-surface (DR-012) and his rationale is quoted verbatim in the record
rather than paraphrased.

**The gate found what tests could not.** Twelve manual acceptance items, all passing, plus three
defects no automated suite had caught: a 70-pixel viewport overflow, a page-wide horizontal scrollbar
from a CSS specificity conflict, and a polling loop restarting on every render.

## 11.6 What the ladder produced

Each prototype's output became the next one's input, and three times a prototype invalidated an
assumption the previous one had left in place: Prototype 1 refuted the aspect-ratio hypothesis,
Prototype 2 disqualified the cheapest conditioning method, and Prototype 5 exposed a geometry
mismatch that four milestones of test assets had hidden. **A ladder that never contradicts itself is
not being climbed carefully.**
