# Prototype 2 scoring form (BLANK - to be filled in by Kylian)

Frozen kit fingerprint: `c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228`

Rows are at **aggregate (method x influence level x resolution)** granularity, which
is how the M3 review was actually performed. Scale: 1 = worst, 5 = best.

Every score cell is intentionally empty. See [`rubric.md`](rubric.md) for the 1-5
anchors and the recommended order of review, and
[`failure-mode-probe.md`](failure-mode-probe.md) for the checklist that goes with it.

`reference_influence` is scoreable here for the first time in the project.

## 512x512

| method | level | param | value | conditions | seeds | n | prompt_adherence | style_consistency | reference_influence | visual_quality | decal_suitability | composition | artefacts | originality | diversity_across_seeds | copy_or_overfitting_risk | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| img2img | medium | strength | 0.6 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| img2img | medium | strength | 0.65 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 |  |  |  |  |  |  |  |  |  |  |  |
| img2img | strong | strength | 0.3 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| img2img | strong | strength | 0.4 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 |  |  |  |  |  |  |  |  |  |  |  |
| img2img | strong | strength | 0.45 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| img2img | weak | strength | 0.75 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| img2img | weak | strength | 0.85 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 |  |  |  |  |  |  |  |  |  |  |  |
| img2img | weak | strength | 0.9 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | medium | scale | 0.55 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | medium | scale | 0.6 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | none | scale | 0.0 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | strong | scale | 0.8 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | strong | scale | 0.85 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | strong | scale | 1.0 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | weak | scale | 0.2 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | weak | scale | 0.25 | C1,C2,C3,C4,C5,C6 | 42,1337,2026 | 19 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | weak | scale | 0.4 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter-plus | medium | scale | 0.55 | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |
| text-only | none | - | - | C1,C2,C3,C4 | 42,1337,2026 | 12 |  |  |  |  |  |  |  |  |  |  |  |

## 512x1536

| method | level | param | value | conditions | seeds | n | prompt_adherence | style_consistency | reference_influence | visual_quality | decal_suitability | composition | artefacts | originality | diversity_across_seeds | copy_or_overfitting_risk | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| img2img | medium | strength | 0.65 | C1,C2,C4 | 42,1337,2026 | 9 |  |  |  |  |  |  |  |  |  |  |  |
| ip-adapter | medium | scale | 0.55 | C1,C2,C4 | 42,1337,2026 | 9 |  |  |  |  |  |  |  |  |  |  |  |
| text-only | none | - | - | C1,C2,C4 | 42,1337,2026 | 9 |  |  |  |  |  |  |  |  |  |  |  |

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
