# Prototype 4 — caption and source-image audit

**Date:** 2026-08-04 · **Milestone:** M6 · Gathered **before** any training run.

This audit is the recorded justification for the style-only caption strategy and the
baseline for **H4** (does `retro-poster` carry frames and pseudo-text into a trained
LoRA?). `dataset-v1.csv` was opened read-only; nothing here modifies it.

## 1. Caption classification (rule-based)

Deterministic rules over the dataset-v1 **content phrase** — the part after
`skateboard decal artwork,`. **Stated limit: these rules detect the SHAPE of a caption, not
whether its words are true of the image.** A phrase classified `visual` is not thereby
verified as accurate.

| class | rule |
|---|---|
| `truncated` | ends on a dangling function word (`…of`, `…and`, `…from`) |
| `attribution` | contains `by <name>` — an authorship credit, not a description |
| `venue-or-archive` | names a venue, city, or archive programme |
| `visual` | none of the above |

| style | items | distinct phrases | visual | attribution | truncated | venue/archive |
|---|---|---|---|---|---|---|
| `minimal-geometric` | 44 | **6** | 44 | **0** | **0** | 0 |
| `ukiyo-e` | 44 | **41** | 32 | **5** | **7** | 0 |
| `retro-poster` | 36 | **28** | 14 | **16** | **0** | 6 |

**What this shows.** `retro-poster` carries the most authorship credits — play titles and
writers rather than anything visible in the image. `ukiyo-e` carries truncated phrases cut
off mid-sentence. `minimal-geometric` captions are accurate and visual but nearly
duplicated: only a handful of distinct phrases across the whole set, because the generator
varies little but the shape count.

**Consequence.** Training a *style* LoRA on these teaches the trigger proper nouns and
sentence fragments. The frozen strategy is therefore **style-only** captions
(`xgeo minimal geometric abstract style skateboard decal artwork`).
**This remains a hypothesis under test, not a settled fact:** EXP-023 retrains the lead
style on the dataset-v1 captions verbatim, changing nothing else, and both arms are scored
blind against the rules in the plan.

## 2. Border-darkness indicator (objective measurement, NOT a verdict)

Mean luminance of the outer 6% ring versus the interior, on a 0–255
scale. **A delta at or below −25 is FLAGGED for inspection.** The
threshold was fixed before any image was measured.

**This is an indicator, not proof.** A dark border can mean a framed or matted scan, or
simply dark artwork at the edges. It flags candidates; it decides nothing, and it never
excludes an image.

| style | items measured | median delta | flagged (≤ −25) | flagged % |
|---|---|---|---|---|
| `minimal-geometric` | 44 | +17.5 | **11** | 25% |
| `ukiyo-e` | 44 | +29.7 | **2** | 5% |
| `retro-poster` | 36 | -73.5 | **35** | 97% |

## 3. Source geometry

| style | items | landscape | portrait | median h/w | items ≥ 2.5:1 tall |
|---|---|---|---|---|---|
| `minimal-geometric` | 44 | 0 | 44 | 3.00 | 44 |
| `ukiyo-e` | 44 | 15 | 29 | 1.33 | 0 |
| `retro-poster` | 36 | 8 | 28 | 1.48 | 0 |

The deck target is **3.00**. Only `minimal-geometric` is already there. This is why
training runs at **512×512 for all three styles**: cropping a 1.33:1 ukiyo-e print to 1:3
would teach a crop artefact rather than a style. Deck geometry comes from generation
(DR-007), which EXP-019 already proved works with a 512×512-trained LoRA.

## Files

- `caption-classification.csv` — every training item, its classification and both captions
- `border-darkness-indicator.csv` — per-image border/interior luminance and the flag
- `style-manifest-exclusions.csv` — every dataset-v1 item no training manifest uses
