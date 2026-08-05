# Prototype 4 — Gate 2 completed scoring and decisions

**Date:** 2026-08-05  
**Final human approver:** Kylian Algoet  
**Visual-analysis assistance:** ChatGPT  
**Basis:** the 21 labelled Gate-2 contact sheets in the review package

## Scores

| sheet | prompt_adherence | style_consistency | visual_quality | decal_suitability | composition | artefacts | originality | diversity_across_seeds | copy_or_overfitting_risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `BASE__minimal-geometric__512x1536` | 3 | 2 | 3 | 3 | 3 | 4 | 4 | 3 | 5 |
| `BASE__minimal-geometric__512x512` | 3 | 2 | 3 | 2 | 3 | 4 | 4 | 4 | 5 |
| `BASE__retro-poster__512x1536` | 3 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | 5 |
| `BASE__retro-poster__512x512` | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 5 |
| `BASE__ukiyo-e__512x1536` | 4 | 4 | 3 | 4 | 4 | 3 | 4 | 3 | 5 |
| `BASE__ukiyo-e__512x512` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 5 |
| `EXP-027__minimal-geometric__ck00300__512x1536` | 4 | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 5 |
| `EXP-027__minimal-geometric__ck00300__512x512` | 4 | 5 | 4 | 4 | 4 | 4 | 5 | 4 | 5 |
| `EXP-027__minimal-geometric__ck00600__512x1536` | 3 | 5 | 3 | 4 | 3 | 3 | 5 | 3 | 5 |
| `EXP-027__minimal-geometric__ck00600__512x512` | 3 | 5 | 4 | 4 | 4 | 4 | 5 | 4 | 5 |
| `EXP-028__ukiyo-e__ck00300__512x1536` | 4 | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 5 |
| `EXP-028__ukiyo-e__ck00300__512x512` | 4 | 5 | 5 | 4 | 5 | 4 | 5 | 4 | 5 |
| `EXP-028__ukiyo-e__ck00600__512x1536` | 5 | 5 | 5 | 5 | 5 | 4 | 5 | 4 | 5 |
| `EXP-028__ukiyo-e__ck00600__512x512` | 5 | 5 | 5 | 4 | 5 | 4 | 5 | 4 | 5 |
| `EXP-029__retro-poster__ck00300__512x1536` | 4 | 5 | 4 | 5 | 4 | 2 | 4 | 4 | 5 |
| `EXP-029__retro-poster__ck00300__512x512` | 4 | 5 | 4 | 5 | 4 | 2 | 4 | 4 | 5 |
| `EXP-029__retro-poster__ck00600__512x1536` | 3 | 5 | 4 | 4 | 4 | 2 | 4 | 3 | 5 |
| `EXP-029__retro-poster__ck00600__512x512` | 3 | 5 | 4 | 4 | 4 | 2 | 4 | 4 | 5 |
| `EXP-030__minimal-geometric__ck01800__512x512` | 4 | 4 | 4 | 4 | 4 | 4 | 5 | 4 | 5 |
| `EXP-030__retro-poster__ck01800__512x512` | 4 | 5 | 4 | 4 | 4 | 2 | 4 | 4 | 5 |
| `EXP-030__ukiyo-e__ck01800__512x512` | 5 | 5 | 5 | 4 | 5 | 4 | 5 | 4 | 5 |

## Failure-mode probe

| sheet | pseudo_text | unwanted_frame | background_transfer | repeated_motifs | vertical_stretching |
|---|---|---|---|---|---|
| `EXP-027__minimal-geometric__ck00300__512x1536` | same | better | better | worse | same |
| `EXP-027__minimal-geometric__ck00300__512x512` | same | better | better | worse | same |
| `EXP-027__minimal-geometric__ck00600__512x1536` | same | better | better | worse | same |
| `EXP-027__minimal-geometric__ck00600__512x512` | same | better | better | worse | same |
| `EXP-028__ukiyo-e__ck00300__512x1536` | same | better | better | worse | same |
| `EXP-028__ukiyo-e__ck00300__512x512` | same | better | better | worse | same |
| `EXP-028__ukiyo-e__ck00600__512x1536` | same | better | better | worse | same |
| `EXP-028__ukiyo-e__ck00600__512x512` | same | better | better | worse | same |
| `EXP-029__retro-poster__ck00300__512x1536` | worse | worse | better | worse | same |
| `EXP-029__retro-poster__ck00300__512x512` | worse | worse | better | worse | same |
| `EXP-029__retro-poster__ck00600__512x1536` | worse | worse | better | worse | same |
| `EXP-029__retro-poster__ck00600__512x512` | worse | worse | better | worse | same |
| `EXP-030__minimal-geometric__ck01800__512x512` | same | better | better | worse | same |
| `EXP-030__retro-poster__ck01800__512x512` | worse | worse | better | worse | same |
| `EXP-030__ukiyo-e__ck01800__512x512` | same | better | better | worse | same |

## Gate-2 decisions

1. **Final production checkpoints**
   - minimal-geometric: `EXP-027`, checkpoint **300**
   - ukiyo-e: `EXP-028`, checkpoint **600**
   - retro-poster: `EXP-029`, checkpoint **300**

2. **Default application LoRA weight:** **0.7**
   - Weight 0.4 is often too weak.
   - Weight 1.0 strengthens style but more often overrides prompt content, repeats motifs, or increases leakage.
   - Weight 0.7 is the best general balance; expose 0.4–1.0 as an advanced control if the application supports it.

3. **RQ5:** the balanced multi-style LoRA is technically viable and visually competitive at 512×512, with no obvious severe cross-style token bleed. **Separate per-style adapters remain the production choice** because they provide cleaner independent control, allow different selected checkpoints, and have been evaluated at both 512×512 and 512×1536.

4. **H4:** confirmed. Retro-poster learns useful poster aesthetics but also bakes in pseudo-text and framed/poster-like composition. This is a named limitation.

5. **H5:** supported. Higher LoRA weights strengthen the target style, but prompt adherence and style-free isolation tend to weaken at the highest weight. The trade-off is visible, especially around weight 1.0.

6. **Per-style outcomes**
   - minimal-geometric: **PASS**
   - ukiyo-e: **PASS**
   - retro-poster: **PARTIAL PASS** because of pseudo-text and framing artefacts

7. **Contingency:** **not authorised.** Preserve both unused slots. Record R14 (unseeded LoRA initialisation) as a reproducibility limitation and fix the runner for future training without invalidating or replacing the completed comparison runs.

8. **DR-010:** may be finalised with these conclusions, provided the reproducibility limitation, matrix-duplicate correction, R12 memory ceiling, and retro-poster limitation remain explicit.

## Additional production notes

- Keep the selected checkpoint files immutable and record their full SHA-256 values.
- The 512×1536 combined path remains near the physical VRAM ceiling: about 202 MiB spare.
- Do not add another adapter, raise rank, add ControlNet, or increase reference batch size on the current 8 GB path without a new memory test.
- The final application should default to separate per-style LoRAs and weight 0.7.
