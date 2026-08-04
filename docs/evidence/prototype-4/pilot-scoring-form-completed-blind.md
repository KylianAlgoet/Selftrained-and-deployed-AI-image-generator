# Prototype 4 — Gate 1 blind scoring

**Scored before opening the blinding map.**  
**Reviewer:** ChatGPT visual review with Kylian present  
**Date:** 2026-08-05

## Scores

| sheet | prompt_adherence | style_consistency | visual_quality | decal_suitability | composition | artefacts | originality | diversity_across_seeds | copy_or_overfitting_risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BASE-GEO | 3 | 2 | 3 | 2 | 3 | 4 | 4 | 4 | 5 |
| BASE-PST | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 5 |
| BASE-UKY | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 5 |
| GEO-1 | 3 | 3 | 3 | 2 | 3 | 4 | 4 | 3 | 5 |
| GEO-2 | 3 | 4 | 3 | 3 | 3 | 4 | 4 | 3 | 5 |
| GEO-3 | 4 | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 5 |
| GEO-4 | 4 | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 5 |
| GEO-5 | 3 | 4 | 4 | 3 | 4 | 4 | 4 | 3 | 5 |
| GEO-6 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 5 |
| GEO-7 | 5 | 5 | 5 | 5 | 5 | 4 | 5 | 5 | 5 |
| GEO-8 | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 4 | 5 |
| PST-1 | 5 | 5 | 4 | 5 | 5 | 2 | 4 | 4 | 5 |
| PST-2 | 4 | 5 | 4 | 5 | 4 | 2 | 4 | 5 | 5 |
| UKY-1 | 5 | 5 | 5 | 4 | 5 | 4 | 5 | 5 | 5 |
| UKY-2 | 5 | 5 | 5 | 4 | 5 | 4 | 5 | 4 | 5 |

## Failure-mode probe

| sheet | pseudo_text | unwanted_frame | background_transfer | repeated_motifs | vertical_stretching |
|---|---|---|---|---|---|
| GEO-1 | same | same | same | worse | same |
| GEO-2 | same | same | same | worse | same |
| GEO-3 | same | better | better | worse | same |
| GEO-4 | same | better | better | worse | same |
| GEO-5 | same | same | same | worse | same |
| GEO-6 | same | better | better | same | same |
| GEO-7 | same | better | better | worse | same |
| GEO-8 | same | better | better | worse | same |
| PST-1 | worse | worse | better | worse | same |
| PST-2 | worse | worse | better | worse | same |
| UKY-1 | same | better | better | worse | same |
| UKY-2 | same | better | better | worse | same |

## Blind observations

- Best minimal-geometric sheets: GEO-7, then GEO-8; GEO-3 and GEO-4 are the next strongest.
- GEO-1 and GEO-2 remain too close to room/wall-decoration mockups and are less decal-ready.
- Both retro-poster sheets are strongly recognisable and deck-suitable, but pseudo-text is a clear defect and border/poster framing remains visible.
- UKY-1 and UKY-2 are both strong; UKY-1 has slightly better diversity, while UKY-2 is marginally more uniform.
- No sheet visually suggests a near-copy, consistent with the automated dHash result.

## Blind ranking

1. GEO-7
2. GEO-8
3. GEO-4 / GEO-3
4. GEO-6
5. GEO-5
6. GEO-2
7. GEO-1

For the two-style pairs:
- PST-1 preferred over PST-2 by a small margin.
- UKY-1 preferred over UKY-2 by a small margin.
