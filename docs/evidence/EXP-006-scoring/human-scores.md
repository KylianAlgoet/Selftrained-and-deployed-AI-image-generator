# Prototype 1 — human evaluation scores (Kylian Algoet, 2026-07-30)

**Authoritative record of the qualitative evaluation.** These are the student's own scores,
supplied verbatim after manual inspection of the contact sheets. Nothing here was estimated,
interpolated, or filled in by the assistant.

## Scope and honesty statement

Scores were given at **aggregate model/track level**, based on reading complete contact-sheet rows —
**not** by scoring each of the 28 individual prompt/seed units separately. That is recorded plainly
here rather than disguised:

- The per-unit cells in `scoring-form.md` / `scoring-form.csv` are marked **"not individually scored"**.
- The aggregate scores below are **not** copied down into every per-unit row, because presenting one
  aggregate judgement as 28 independent judgements would misrepresent how the review was done.

Material reviewed:

- `docs/evidence/prototype-1/cross-model-track-A-seed42.jpg`
- `docs/evidence/prototype-1/cross-model-track-B-seed42.jpg`
- `docs/evidence/EXP-005/aspect-ratio-comparison-seed42.jpg`

Verdict on the evidence itself: **visually usable; approved for completing M3.**

## Dimensions not scored, and why

| Dimension | Status | Reason |
|---|---|---|
| `reference_influence` | **N/A** | There is no reference image in Prototype 1. Reference conditioning arrives in Prototype 2 (RQ6). |
| `diversity_across_seeds` | **Not manually scored** | The contact sheets supplied for review showed the **fixed seed-42 comparison**, not a complete multi-seed comparison. Judging seed diversity from a single-seed sheet is not possible, so no score was given and **none has been invented**. A multi-seed sheet is required before this dimension can be scored. |

## Model comparison — Track A (controlled: both candidates at 512×512)

Scale 1–5, 1 = worst, 5 = best.

| Dimension | SD 1.5 @ 512×512 | SDXL @ 512×512 |
|---|---|---|
| prompt_adherence | 3 | 3 |
| style_consistency | 3 | 3 |
| reference_influence | N/A | N/A |
| visual_quality | 4 | 4 |
| decal_suitability | 3 | 3 |
| composition | 3 | 3 |
| artefacts | 4 | 4 |
| originality | 3 | 3 |
| diversity_across_seeds | not scored | not scored |

**Track A observation:** the two candidates scored identically on every dimension the student scored.
Under the controlled 512×512 condition, SDXL shows no qualitative advantage — while costing 4× the
time and 2.9× the peak allocated VRAM (see EXP-002 / EXP-004).

## Model comparison — Track B (each candidate at its designed resolution)

| Dimension | SD 1.5 @ 512×512 (native) | SDXL @ 1024×1024 (native) |
|---|---|---|
| prompt_adherence | 3 | **4** |
| style_consistency | 3 | **5** |
| reference_influence | N/A | N/A |
| visual_quality | 4 | **5** |
| decal_suitability | 3 | **4** |
| composition | 3 | **4** |
| artefacts | 4 | 4 |
| originality | 3 | 3 |
| diversity_across_seeds | not scored | not scored |

**Track B observation:** SDXL at its native resolution scores higher on five of the seven scored
dimensions, notably style consistency (5 vs 3) and visual quality (5 vs 4). This is the qualitative
counterpart to the resolution-dependent behaviour recorded in `prototype-1.md`: SDXL produces flat
artwork at 1024 and deck-shaped mockups at 512.

**Track A and Track B are reported separately and must never be averaged together.** The gap between
them is the actual finding, and it is the reason the two-track design exists.

## Aspect-ratio strategies (EXP-005, SD 1.5)

| Strategy | Resolution | visual_quality | decal_suitability | composition |
|---|---|---|---|---|
| `direct-1x1` | 512×512 | 4 | **2** | 3 |
| `direct-1x2` | 512×1024 | 4 | 4 | 4 |
| **`direct-1x3`** | **512×1536** | 4 | **5** | 4 |
| `square-crop` | 512×512 → ~170×512 | 3 | **2** | 3 |

### Student findings, verbatim in substance

- **`direct-1x1` (512×512):** too square for the deck, and sometimes resembles a mockup or a physical
  skateboard presentation rather than a decal.
- **`direct-1x2` (512×1024):** visually balanced and clean, but does not fully use the target deck ratio.
- **`direct-1x3` (512×1536) — SELECTED:** directly produces a tall decal, completed reliably on
  SD 1.5, and used approximately **3892 MiB peak allocated VRAM**. Some repetition or vertical
  stretching remains possible and must be addressed in later prompt, reference-conditioning, and
  LoRA experiments.
- **`square-crop` — REJECTED as the main strategy:** the resulting ~**170×512** usable image is far
  below an appropriate deck-print resolution.

## Decision recorded from this review

- **Visual-quality winner:** SDXL at native 1024×1024.
- **Practical feasibility winner and selected project base model:** **Stable Diffusion 1.5**, for
  Prototypes 2–5.
- **Selected deck-format strategy:** direct 1:3 generation at 512×1536.
- **Rejected main strategy:** square-crop.
- **Blocked third candidate:** SD 2.1 base, HTTP 401 access restriction (EXP-003).

Full justification, combining these scores with the measured technical evidence, is in
`docs/decisions/DR-007-base-model-selection.md`.
