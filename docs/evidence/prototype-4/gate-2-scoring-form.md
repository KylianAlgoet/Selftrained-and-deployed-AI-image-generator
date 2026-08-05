# Prototype 4 — Gate 2 scoring form (BLANK)

**Gate 2.** Score the sheets in `final-sheets/`, then return the decisions in the last
section. Nothing in Phase B selected a production checkpoint, declared a winner, or made
any visual-quality claim — those are yours.

## Why these sheets are labelled

Gate 1 was blinded because it compared arms differing in one hidden variable each —
style-only versus verbatim, 12 versus 24 versus 44, 150 versus 300. Gate 2 asks which
checkpoint goes to production, and that question cannot be answered without knowing which
checkpoint each sheet is. **The trade-off is stated rather than hidden:** labelled sheets
carry an expectation effect that blinded ones do not.

`BASE__*` sheets are the untrained SD 1.5 control on identical prompt text.

## Prompt roles

| id | role | what it probes |
|---|---|---|
| `FP1-style` | style-matching | does the trigger produce the trained style on a subject the style can carry |
| `FP2-shared` | shared-cross-style | identical subject across all three styles, isolating the LoRA from the prompt |
| `FP3-out-of-style` | out-of-style | a subject the style does not naturally carry; probes prompt authority under the LoRA |
| `FP4-style-free` | style-free | NO trigger and NO style phrase - does the adapter leak into prompts that never asked for it, which a style LoRA should not do |

`FP4-style-free` carries **no trigger and no style phrase**. A style LoRA should leave it
close to the base model; drift there is leakage, not style learning.

## Sheets to score

| sheet | style | images | cells |
|---|---|---:|---|
| `BASE__minimal-geometric__512x1536` | minimal-geometric | 2 | prompts FP1-style; weights base |
| `BASE__minimal-geometric__512x512` | minimal-geometric | 8 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights base |
| `BASE__retro-poster__512x1536` | retro-poster | 2 | prompts FP1-style; weights base |
| `BASE__retro-poster__512x512` | retro-poster | 8 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights base |
| `BASE__ukiyo-e__512x1536` | ukiyo-e | 2 | prompts FP1-style; weights base |
| `BASE__ukiyo-e__512x512` | ukiyo-e | 8 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights base |
| `EXP-027__minimal-geometric__ck00300__512x1536` | minimal-geometric | 4 | prompts FP1-style; weights 0.7, 1 |
| `EXP-027__minimal-geometric__ck00300__512x512` | minimal-geometric | 28 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights 0, 0.4, 0.7, 1 |
| `EXP-027__minimal-geometric__ck00600__512x1536` | minimal-geometric | 4 | prompts FP1-style; weights 0.7, 1 |
| `EXP-027__minimal-geometric__ck00600__512x512` | minimal-geometric | 28 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights 0, 0.4, 0.7, 1 |
| `EXP-028__ukiyo-e__ck00300__512x1536` | ukiyo-e | 4 | prompts FP1-style; weights 0.7, 1 |
| `EXP-028__ukiyo-e__ck00300__512x512` | ukiyo-e | 28 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights 0, 0.4, 0.7, 1 |
| `EXP-028__ukiyo-e__ck00600__512x1536` | ukiyo-e | 4 | prompts FP1-style; weights 0.7, 1 |
| `EXP-028__ukiyo-e__ck00600__512x512` | ukiyo-e | 28 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights 0, 0.4, 0.7, 1 |
| `EXP-029__retro-poster__ck00300__512x1536` | retro-poster | 4 | prompts FP1-style; weights 0.7, 1 |
| `EXP-029__retro-poster__ck00300__512x512` | retro-poster | 28 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights 0, 0.4, 0.7, 1 |
| `EXP-029__retro-poster__ck00600__512x1536` | retro-poster | 4 | prompts FP1-style; weights 0.7, 1 |
| `EXP-029__retro-poster__ck00600__512x512` | retro-poster | 28 | prompts FP1-style, FP2-shared, FP3-out-of-style, FP4-style-free; weights 0, 0.4, 0.7, 1 |
| `EXP-030__minimal-geometric__ck01800__512x512` | minimal-geometric | 10 | prompts FP1-style, FP2-shared; weights 0, 0.4, 0.7, 1 |
| `EXP-030__retro-poster__ck01800__512x512` | retro-poster | 10 | prompts FP1-style, FP2-shared; weights 0, 0.4, 0.7, 1 |
| `EXP-030__ukiyo-e__ck01800__512x512` | ukiyo-e | 10 | prompts FP1-style, FP2-shared; weights 0, 0.4, 0.7, 1 |

Every sheet is ordered deterministically by **(prompt, seed, LoRA weight)**, 4 columns.

## Rubric (1–5, per `docs/05-experiment-methodology.md`)

| dimension | 1 | 5 |
|---|---|---|
| `prompt_adherence` | ignores prompt | matches all stated elements |
| `style_consistency` | style unrecognizable | unmistakably the target style |
| `visual_quality` | broken/blurry | clean, coherent |
| `decal_suitability` | unusable on a deck | print-ready for a deck |
| `composition` | chaotic/cropped badly | balanced for the deck format |
| `artefacts` | dominant artefacts | none visible |
| `originality` | near-copy of a source | clearly new artwork |
| `diversity_across_seeds` | mode-collapsed | varied yet on-style |
| `copy_or_overfitting_risk` | reproduces training data | clearly independent |

**Leave a cell blank if you did not judge it.** A blank is never a zero and will never be
back-filled — the M3/M4/M5 rule. `reference_influence` is absent from the LoRA-alone
sheets because they use no reference image.

## Scores

| sheet | `prompt_adherence` | `style_consistency` | `visual_quality` | `decal_suitability` | `composition` | `artefacts` | `originality` | `diversity_across_seeds` | `copy_or_overfitting_risk` |
|---|---|---|---|---|---|---|---|---|---|
| `BASE__minimal-geometric__512x1536` |  |  |  |  |  |  |  |  |  |
| `BASE__minimal-geometric__512x512` |  |  |  |  |  |  |  |  |  |
| `BASE__retro-poster__512x1536` |  |  |  |  |  |  |  |  |  |
| `BASE__retro-poster__512x512` |  |  |  |  |  |  |  |  |  |
| `BASE__ukiyo-e__512x1536` |  |  |  |  |  |  |  |  |  |
| `BASE__ukiyo-e__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-027__minimal-geometric__ck00300__512x1536` |  |  |  |  |  |  |  |  |  |
| `EXP-027__minimal-geometric__ck00300__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-027__minimal-geometric__ck00600__512x1536` |  |  |  |  |  |  |  |  |  |
| `EXP-027__minimal-geometric__ck00600__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-028__ukiyo-e__ck00300__512x1536` |  |  |  |  |  |  |  |  |  |
| `EXP-028__ukiyo-e__ck00300__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-028__ukiyo-e__ck00600__512x1536` |  |  |  |  |  |  |  |  |  |
| `EXP-028__ukiyo-e__ck00600__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-029__retro-poster__ck00300__512x1536` |  |  |  |  |  |  |  |  |  |
| `EXP-029__retro-poster__ck00300__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-029__retro-poster__ck00600__512x1536` |  |  |  |  |  |  |  |  |  |
| `EXP-029__retro-poster__ck00600__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-030__minimal-geometric__ck01800__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-030__retro-poster__ck01800__512x512` |  |  |  |  |  |  |  |  |  |
| `EXP-030__ukiyo-e__ck01800__512x512` |  |  |  |  |  |  |  |  |  |

## Failure-mode probe

Mark `worse`, `same`, `better` or leave blank, against the `BASE__*` sheet for that style
and geometry.

| sheet | `pseudo_text` | `unwanted_frame` | `background_transfer` | `repeated_motifs` | `vertical_stretching` |
|---|---|---|---|---|---|
| `EXP-027__minimal-geometric__ck00300__512x1536` |  |  |  |  |  |
| `EXP-027__minimal-geometric__ck00300__512x512` |  |  |  |  |  |
| `EXP-027__minimal-geometric__ck00600__512x1536` |  |  |  |  |  |
| `EXP-027__minimal-geometric__ck00600__512x512` |  |  |  |  |  |
| `EXP-028__ukiyo-e__ck00300__512x1536` |  |  |  |  |  |
| `EXP-028__ukiyo-e__ck00300__512x512` |  |  |  |  |  |
| `EXP-028__ukiyo-e__ck00600__512x1536` |  |  |  |  |  |
| `EXP-028__ukiyo-e__ck00600__512x512` |  |  |  |  |  |
| `EXP-029__retro-poster__ck00300__512x1536` |  |  |  |  |  |
| `EXP-029__retro-poster__ck00300__512x512` |  |  |  |  |  |
| `EXP-029__retro-poster__ck00600__512x1536` |  |  |  |  |  |
| `EXP-029__retro-poster__ck00600__512x512` |  |  |  |  |  |
| `EXP-030__minimal-geometric__ck01800__512x512` |  |  |  |  |  |
| `EXP-030__retro-poster__ck01800__512x512` |  |  |  |  |  |
| `EXP-030__ukiyo-e__ck01800__512x512` |  |  |  |  |  |

## Decisions Gate 2 needs from you

None of these has been made for you, and none may be inferred from an automated indicator.

1. **Final production checkpoint per style** — which arm and step for minimal-geometric,
   ukiyo-e and retro-poster, or *none* for a style that did not reach a usable state.
2. **Default LoRA weight** for the application, from the 0.0 / 0.4 / 0.7 / 1.0 sweep.
3. **RQ5 verdict** — does the balanced multi-style LoRA match the per-style LoRAs, or do
   separate per-style adapters stay? Include whether you see cross-style token bleed.
4. **H4 verdict** — does `retro-poster` bake in frames or pseudo-text? This was left
   unanswered at Gate 1 on purpose.
5. **H5 verdict** — do style strength and prompt adherence trade off as weight rises?
6. **Per-style outcome** — pass / partial pass / failure for each style, per the criteria
   in the approved plan. A partial pass is never upgraded, and a failed style is recorded
   as failed rather than dropped.
7. **Contingency** — whether any contingency run is now authorised and which SINGLE
   variable it may change. Both slots are still unused.
8. **DR-010** — whether the draft may be finalised with your conclusion.

## Not decided, and not decidable from this package

- No production checkpoint has been selected and no style is described as better.
- **No visual-quality claim is made anywhere in Phase B.**
- The indicators in `docs/evidence/EXP-033/` are descriptive only. They populate no cell
  above and may not select a checkpoint, style or hyperparameter.
- `DR-010` is a **draft with no conclusion** until you complete this gate.
