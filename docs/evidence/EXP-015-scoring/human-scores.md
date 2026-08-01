# Prototype 2 human rubric scores (approved by Kylian, 2026-08-01)

Authoritative record: [`human-scores.csv`](human-scores.csv). These are **aggregate**
scores at (method x influence level x resolution), which is the granularity the review
was actually performed at. They are **not** per-image scores and must never be presented
as such.

## How blanks are handled

**A blank cell means NOT SCORED. It is never a zero and is never back-filled.** Blanks
are excluded from every mean below, and the surviving `n` is printed beside each figure
so a dimension averaged over three rows cannot be mistaken for one averaged over nine.

Specifically:

- `reference_influence` and `copy_or_overfitting_risk` are blank for **text-only**, which
  uses no reference image at all.
- `diversity_across_seeds` was scored only where the multi-seed sheet supported it, so it
  carries a much smaller `n` than the other dimensions.
- **text-only at 512x1536 is entirely unscored.** It was not visually rescored from the M4
  contact sheets. **No M3 value has been substituted for it**, and none may be: the M3
  review used different sheets and a different question. It stays not scored.

## Objective measurements are reported separately

Nothing on this page is a measurement. VRAM, latency, effective steps, the process-isolation
spot check, the lower-bound diagnostic and the similarity indicators live in
`docs/evidence/prototype-2/` and in `docs/evidence/EXP-014/`. Measured figures and human
judgements are never averaged together or traded off inside a single number.

## Per-method means at 512x512 (blanks excluded)

| dimension | text-only | img2img | ip-adapter | ip-adapter-plus |
|---|---|---|---|---|
| prompt_adherence | 3.00 (n=1) | 3.00 (n=8) | 3.11 (n=9) | 3.00 (n=1) |
| style_consistency | 3.00 (n=1) | 4.12 (n=8) | 4.44 (n=9) | 5.00 (n=1) |
| reference_influence | not scored | 3.75 (n=8) | 3.44 (n=9) | 4.00 (n=1) |
| visual_quality | 4.00 (n=1) | 4.00 (n=8) | 4.00 (n=9) | 4.00 (n=1) |
| decal_suitability | 2.00 (n=1) | 3.75 (n=8) | 3.56 (n=9) | 4.00 (n=1) |
| composition | 3.00 (n=1) | 4.00 (n=8) | 3.89 (n=9) | 4.00 (n=1) |
| artefacts | 4.00 (n=1) | 3.38 (n=8) | 3.44 (n=9) | 3.00 (n=1) |
| originality | 4.00 (n=1) | 3.12 (n=8) | 4.11 (n=9) | 4.00 (n=1) |
| diversity_across_seeds | 4.00 (n=1) | 3.00 (n=1) | 4.00 (n=1) | 4.00 (n=1) |
| copy_or_overfitting_risk | not scored | 3.12 (n=8) | 4.33 (n=9) | 4.00 (n=1) |

Row counts at 512x512: text-only 1, img2img 8, ip-adapter 9, ip-adapter-plus 1.

**These means average across influence levels**, including the deliberately weak and
deliberately extreme ones, so they describe a method's behaviour across its whole range
rather than at its best setting. The selected operating point is judged from the rows
themselves, not from these column averages.

## Scores at the deck format 512x1536

| method | prompt_adherence | style_consistency | reference_influence | visual_quality | decal_suitability | composition | artefacts | originality | diversity_across_see | copy_or_overfitting_ |
|---|---|---|---|---|---|---|---|---|---|---|
| img2img medium | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 1 | - | 1 |
| ip-adapter medium | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 4 | - | 4 |
| text-only none | - | - | - | - | - | - | - | - | - | - |

`-` means not scored. The text-only row is blank throughout for the reason given above.

## Controllability condition 4 - a usable mid-range

The product requirement: at least one intermediate level must score **both**
`reference_influence >= 3` **and** `prompt_adherence >= 3`. A method that can only choose
between ignoring the reference and ignoring the prompt is not controllable.

| method | level | value | resolution | reference_influence | prompt_adherence |
|---|---|---|---|---|---|
| img2img | medium | 0.6 | 512x512 | 4 | 3 |
| img2img | medium | 0.65 | 512x512 | 4 | 3 |
| img2img | weak | 0.75 | 512x512 | 3 | 4 |
| ip-adapter | medium | 0.55 | 512x512 | 4 | 3 |
| ip-adapter | medium | 0.55 | 512x1536 | 4 | 3 |
| ip-adapter | medium | 0.6 | 512x512 | 4 | 3 |
| ip-adapter | strong | 0.8 | 512x512 | 5 | 3 |
| ip-adapter | weak | 0.4 | 512x512 | 3 | 4 |
| ip-adapter-plus | medium | 0.55 | 512x512 | 4 | 3 |

Settings meeting the condition, by method: **img2img** 3, **ip-adapter** 5, **ip-adapter-plus** 1.

## Per-row scores

| method | level | value | resolution | prompt_adherence | style_consistency | reference_influence | visual_quality | decal_suitability | composition | artefacts | originality | diversity_across_seeds | copy_or_overfitting_risk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| img2img | medium | 0.6 | 512x512 | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 3 |  | 3 |
| img2img | medium | 0.65 | 512x512 | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 3 | 3 |
| img2img | medium | 0.65 | 512x1536 | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 1 |  | 1 |
| img2img | strong | 0.3 | 512x512 | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 1 |  | 1 |
| img2img | strong | 0.4 | 512x512 | 2 | 4 | 5 | 4 | 4 | 4 | 3 | 2 |  | 2 |
| img2img | strong | 0.45 | 512x512 | 2 | 4 | 5 | 4 | 4 | 4 | 3 | 2 |  | 2 |
| img2img | weak | 0.75 | 512x512 | 4 | 4 | 3 | 4 | 4 | 4 | 4 | 4 |  | 4 |
| img2img | weak | 0.85 | 512x512 | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 5 |  | 5 |
| img2img | weak | 0.9 | 512x512 | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 5 |  | 5 |
| ip-adapter | medium | 0.55 | 512x512 | 3 | 5 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 |
| ip-adapter | medium | 0.55 | 512x1536 | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 4 |  | 4 |
| ip-adapter | medium | 0.6 | 512x512 | 3 | 5 | 4 | 4 | 4 | 4 | 3 | 4 |  | 4 |
| ip-adapter | none | 0.0 | 512x512 | 3 | 3 | 1 | 4 | 2 | 3 | 4 | 4 |  | 5 |
| ip-adapter | strong | 0.8 | 512x512 | 3 | 5 | 5 | 4 | 4 | 4 | 3 | 4 |  | 4 |
| ip-adapter | strong | 0.85 | 512x512 | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 4 |  | 4 |
| ip-adapter | strong | 1.0 | 512x512 | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 3 |  | 4 |
| ip-adapter | weak | 0.2 | 512x512 | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 5 |  | 5 |
| ip-adapter | weak | 0.25 | 512x512 | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 5 |  | 5 |
| ip-adapter | weak | 0.4 | 512x512 | 4 | 4 | 3 | 4 | 4 | 4 | 4 | 4 |  | 4 |
| ip-adapter-plus | medium | 0.55 | 512x512 | 3 | 5 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 |
| text-only | none | - | 512x512 | 3 | 3 |  | 4 | 2 | 3 | 4 | 4 | 4 |  |
| text-only | none | - | 512x1536 |  |  |  |  |  |  |  |  |  |  |

## Reviewer notes, verbatim

- **img2img medium 0.6 @ 512x512** — Balanced but reference begins to dominate C3/C4; some pseudo-text and reduced originality.
- **img2img medium 0.65 @ 512x512** — Usable mid-range at 512; controllable, but C5/C6 show prompt loss and frame/text transfer.
- **img2img medium 0.65 @ 512x1536** — Reject as primary production mode: C2/C4 are near-copies (dHash 0-5); some repetition/cropping in C1.
- **img2img strong 0.3 @ 512x512** — Strongest reference level; outputs frequently approach source reconstruction.
- **img2img strong 0.4 @ 512x512** — Strong reference influence with obvious prompt loss in conflict/difficult cases.
- **img2img strong 0.45 @ 512x512** — Strong reference influence; good coherence but low originality and higher copy risk.
- **img2img weak 0.75 @ 512x512** — Good prompt/reference balance; reference influence visible without major copying.
- **img2img weak 0.85 @ 512x512** — Prompt-led and original; reference influence is limited.
- **img2img weak 0.9 @ 512x512** — Weakest reference influence; close to prompt-led generation.
- **ip-adapter medium 0.55 @ 512x512** — Best overall balance in the supplied sheets; controllable influence, strong diversity, no near-copy flags.
- **ip-adapter medium 0.55 @ 512x1536** — Visually usable and original at deck geometry, but repeated motifs/vertical elongation remain; only ~222 MiB physical GPU headroom.
- **ip-adapter medium 0.6 @ 512x512** — Strong mid-range reference control with good originality; some pseudo-text/content takeover.
- **ip-adapter none 0.0 @ 512x512** — Byte-identical to text-only baseline; reference influence intentionally absent.
- **ip-adapter strong 0.8 @ 512x512** — Strong reference control without direct copying, but prompt authority declines.
- **ip-adapter strong 0.85 @ 512x512** — Strong reference control; conflict case is reference-led and pseudo-text increases.
- **ip-adapter strong 1.0 @ 512x512** — Maximum reference influence; coherent but prompt loss and source-like composition are obvious.
- **ip-adapter weak 0.2 @ 512x512** — Prompt-led, diverse and original; reference influence is subtle.
- **ip-adapter weak 0.25 @ 512x512** — Weak level preserves prompt well; some physical/mockup behavior remains.
- **ip-adapter weak 0.4 @ 512x512** — Good early balance: visible reference influence with strong prompt adherence.
- **ip-adapter-plus medium 0.55 @ 512x512** — Strong quality and diversity, but no decisive advantage over standard IP-Adapter and slightly higher VRAM.
- **text-only none n/a @ 512x512** — Baseline only; frequent physical-skateboard/mockup outputs reduce decal suitability.
- **text-only none n/a @ 512x1536** — Not visually scored from the supplied M4 contact sheets; retain as not scored or reuse separately approved M3 evidence.
