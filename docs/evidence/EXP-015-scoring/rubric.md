# Prototype 2 evaluation rubric (1-5 per dimension)

Nine dimensions from `docs/05-experiment-methodology.md` plus one M4 addition.
Scores are the student's own research judgement; nothing here is estimated,
suggested, or filled in by the assistant.

| dimension | 1 | 5 | note |
|---|---|---|---|
| prompt_adherence | ignores prompt | matches all stated elements | unchanged from Prototype 1 |
| style_consistency | style unrecognizable | unmistakably the target style | unchanged from Prototype 1 |
| reference_influence | no visible relation to reference | clear, controllable influence | **scoreable for the first time** - every rubric to date recorded N/A |
| visual_quality | broken/blurry | clean, coherent | unchanged from Prototype 1 |
| decal_suitability | unusable on a deck | print-ready composition for a deck | unchanged from Prototype 1 |
| composition | chaotic/cropped badly | balanced for the deck format | unchanged from Prototype 1 |
| artefacts | dominant artefacts | none visible | unchanged from Prototype 1 |
| originality | near-copy of a source | clearly new artwork | unchanged from Prototype 1 |
| diversity_across_seeds | mode-collapsed | varied yet on-style | unchanged from Prototype 1 |
| copy_or_overfitting_risk | reproduces the reference | no trace of copying | **new in M4** - RQ11 and the near-copy flag both need it recorded |

## The four axes, kept separate

These are deliberately never collapsed into one score, and the automatic
indicators never replace the human judgement:

| axis | decided by | supported, never replaced, by |
|---|---|---|
| content preservation | `reference_influence` | `dhash_distance_to_reference`, a coarse near-copy flag only |
| style influence | `style_consistency` | nothing - no automatic proxy is claimed |
| prompt adherence | `prompt_adherence`; C5 forces the trade-off open | - |
| copy risk | `originality` + `copy_or_overfitting_risk` | `dhash <= 6` flags candidates for the copy-risk sheet |

`overall_reference_similarity` (CLIP cosine) is a **descriptive indicator across all
four and attributable to none of them individually.** It entangles subject,
composition, semantics, colour and style, so it is not a style score. It is also
computed with the same CLIP family IP-Adapter conditions on, which makes it
descriptive *within* a method rather than a neutral referee *between* methods.
**The human rubric is the decision authority.**

## How to score

1. Read `docs/evidence/prototype-2/contact-sheets.md` first - the sheets carry no
   burnt-in labels, so that file is how a cell is identified.
2. `method-comparison-medium-seed42.jpg` - the like-for-like comparison at one level.
3. `sweep-img2img-seed42.jpg` and `sweep-ipadapter-seed42.jpg` - is influence
   *controllable*? Columns run weakest to strongest reference influence. **For
   img2img the strength number DECREASES left to right, because strength is inverted.**
4. `multiseed-diversity.jpg` - the only sheet that can answer `diversity_across_seeds`.
5. `conflict-text-vs-reference.jpg` (C5) - when reference and prompt disagree, which
   wins as influence rises? Prompt loss here is the measurement, not a defect.
6. `difficult-reference-artefacts.jpg` (C6) and `copy-risk-pairs.jpg`.
7. `deck-format-512x1536.jpg` - does control survive the production geometry?
8. Fill in `scoring-form.md` at aggregate level and the failure probe checklist.

**A note on the shared level names.** `medium` means `strength=0.65` for img2img and
`scale=0.55` for IP-Adapter. That mapping is an assumption under test, not a
calibrated equivalence - nothing establishes the two exert comparable influence.
Score what you see rather than assuming the labels are matched.

Leave a cell blank rather than guessing. A blank cell is recorded as
"not scored"; it is never back-filled.
