# Prototype 2 scoring form (SCORED by Kylian, 2026-08-01)

Frozen kit fingerprint: `c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228`

Rows are at **aggregate (method x influence level x resolution)** granularity, which
is the granularity the review was actually performed at. Scale: 1 = worst, 5 = best.

The authoritative record is [`human-scores.csv`](human-scores.csv); this table is
generated from it and joined onto the inventory of what was actually generated. No
score here is derived, averaged, or inferred.

**An empty cell means NOT SCORED and is never back-filled** (29 such cells).
It is not a zero, and it is never carried over from another row, another resolution,
or another milestone. In particular:

- `diversity_across_seeds` was scored only where the multi-seed sheet supported it.
- `reference_influence` and `copy_or_overfitting_risk` are blank for **text-only**,
  which uses no reference image at all.
- **text-only at 512x1536 is entirely unscored:** it was not visually rescored from
  the M4 contact sheets, and no M3 value has been substituted for it.

`reference_influence` is scored here for the first time in the project.

## 512x512

| method | level | param | value | conditions | seeds | n | prompt_adherence | style_consistency | reference_influence | visual_quality | decal_suitability | composition | artefacts | originality | diversity_across_seeds | copy_or_overfitting_risk | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| img2img | medium | strength | 0.6 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 3 |  | 3 | Balanced but reference begins to dominate C3/C4; some pseudo-text and reduced originality. |
| img2img | medium | strength | 0.65 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 3 | 3 | Usable mid-range at 512; controllable, but C5/C6 show prompt loss and frame/text transfer. |
| img2img | strong | strength | 0.3 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 1 |  | 1 | Strongest reference level; outputs frequently approach source reconstruction. |
| img2img | strong | strength | 0.4 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 | 2 | 4 | 5 | 4 | 4 | 4 | 3 | 2 |  | 2 | Strong reference influence with obvious prompt loss in conflict/difficult cases. |
| img2img | strong | strength | 0.45 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 2 | 4 | 5 | 4 | 4 | 4 | 3 | 2 |  | 2 | Strong reference influence; good coherence but low originality and higher copy risk. |
| img2img | weak | strength | 0.75 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 4 | 4 | 3 | 4 | 4 | 4 | 4 | 4 |  | 4 | Good prompt/reference balance; reference influence visible without major copying. |
| img2img | weak | strength | 0.85 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 5 |  | 5 | Prompt-led and original; reference influence is limited. |
| img2img | weak | strength | 0.9 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 5 |  | 5 | Weakest reference influence; close to prompt-led generation. |
| ip-adapter | medium | scale | 0.55 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 | 3 | 5 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 | Best overall balance in the supplied sheets; controllable influence, strong diversity, no near-copy flags. |
| ip-adapter | medium | scale | 0.6 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 3 | 5 | 4 | 4 | 4 | 4 | 3 | 4 |  | 4 | Strong mid-range reference control with good originality; some pseudo-text/content takeover. |
| ip-adapter | none | scale | 0.0 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 3 | 3 | 1 | 4 | 2 | 3 | 4 | 4 |  | 5 | Byte-identical to text-only baseline; reference influence intentionally absent. |
| ip-adapter | strong | scale | 0.8 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 3 | 5 | 5 | 4 | 4 | 4 | 3 | 4 |  | 4 | Strong reference control without direct copying, but prompt authority declines. |
| ip-adapter | strong | scale | 0.85 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 4 |  | 4 | Strong reference control; conflict case is reference-led and pseudo-text increases. |
| ip-adapter | strong | scale | 1.0 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 3 |  | 4 | Maximum reference influence; coherent but prompt loss and source-like composition are obvious. |
| ip-adapter | weak | scale | 0.2 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 5 |  | 5 | Prompt-led, diverse and original; reference influence is subtle. |
| ip-adapter | weak | scale | 0.25 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 5 |  | 5 | Weak level preserves prompt well; some physical/mockup behavior remains. |
| ip-adapter | weak | scale | 0.4 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 4 | 4 | 3 | 4 | 4 | 4 | 4 | 4 |  | 4 | Good early balance: visible reference influence with strong prompt adherence. |
| ip-adapter-plus | medium | scale | 0.55 | C1,C2,C3,C4 | 42,1337,2026 | 12 | 3 | 5 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 | Strong quality and diversity, but no decisive advantage over standard IP-Adapter and slightly higher VRAM. |
| text-only | none | - | - | C1,C2,C3,C4 | 42,1337,2026 | 12 | 3 | 3 |  | 4 | 2 | 3 | 4 | 4 | 4 |  | Baseline only; frequent physical-skateboard/mockup outputs reduce decal suitability. |

## 512x1536

| method | level | param | value | conditions | seeds | n | prompt_adherence | style_consistency | reference_influence | visual_quality | decal_suitability | composition | artefacts | originality | diversity_across_seeds | copy_or_overfitting_risk | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| img2img | medium | strength | 0.65 | C1,C2,C4 | 42,1337,2026 | 9 | 2 | 5 | 5 | 4 | 4 | 4 | 3 | 1 |  | 1 | Reject as primary production mode: C2/C4 are near-copies (dHash 0-5); some repetition/cropping in C1. |
| ip-adapter | medium | scale | 0.55 | C1,C2,C4 | 42,1337,2026 | 9 | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 4 |  | 4 | Visually usable and original at deck geometry, but repeated motifs/vertical elongation remain; only ~222 MiB physical GPU headroom. |
| text-only | none | - | - | C1,C2,C4 | 42,1337,2026 | 9 |  |  |  |  |  |  |  |  |  |  | Not visually scored from the supplied M4 contact sheets; retain as not scored or reuse separately approved M3 evidence. |

## Conditions referenced above

| condition | reference | prompt | purpose |
|---|---|---|---|
| C1 | R1 (retro-poster) | P1-poster | style-matched - reference and prompt are both retro-poster |
| C2 | R2 (minimal-geometric) | P2-geo | style-matched; already at the deck aspect |
| C3 | R3 (ukiyo-e) | P3-ukiyo | style-matched on style; subject differs (interior scene vs cresting wave) |
| C4 | R4 (simple shape/layout transfer) | P4-deck | layout transfer onto a different subject |
| C5 | R3 (ukiyo-e) | P2-geo | CONFLICT - reference is a figurative ukiyo-e interior scene, prompt asks for minimal-geometric flat shapes |
| C6 | R5 (deliberately difficult) | P1-poster | difficult - frames, typography, wrong orientation |

## Methods referenced above

| method | native parameter | direction |
|---|---|---|
| SD 1.5 text-only baseline | - | n/a - no reference |
| SD 1.5 img2img | strength | INVERTED: lower value = stronger reference |
| IP-Adapter (base, SD 1.5) | scale | higher value = stronger reference |
| IP-Adapter-Plus (SD 1.5) | scale | higher value = stronger reference |

## Where the images are

Full-resolution PNGs are git-ignored under `outputs/EXP-###/`. The committed contact
sheets and their grid legend are in `docs/evidence/prototype-2/`.
