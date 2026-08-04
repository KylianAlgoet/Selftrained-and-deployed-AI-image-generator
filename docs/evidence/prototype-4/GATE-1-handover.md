# Prototype 4 — Gate 1 handover package

**Date:** 2026-08-04 · **Milestone:** M6 Phase A complete · **Status:** STOPPED, awaiting review

Phase A is finished. **Phase B does not start until you return scores and the six decisions
at the bottom of this page.**

## What was NOT done, deliberately

No checkpoint has been selected. No full-run step count has been chosen. No style has been
called recognisable or unrecognisable. No undertraining or overtraining has been diagnosed.
No hyperparameter has been changed. No full, contingency or multi-style run has been started.
The final validation matrix has not been generated. DR-010 has not been written. Nothing has
been pushed.

**No visual-quality claim appears anywhere in Phase A.**

## 1. Pilot checkpoints — paths and hashes

All 6414480 bytes, 256 tensors, 256 LoRA keys, zero base-model keys. All in **git-ignored**
`outputs/`; re-run the training commands to regenerate.

| arm | style | captions | images | step | sha256 |
|---|---|---|---|---|---|
| EXP-020 | minimal-geometric | style-only | 44 | 150 | `cc186bc91bca171bd6c7f550…` |
| EXP-020 | minimal-geometric | style-only | 44 | 300 | `514f17c3ca2c3938a111c3be…` |
| EXP-021 | ukiyo-e | style-only | 44 | 150 | `2137e544e273ee4a1d9f3a1d…` |
| EXP-021 | ukiyo-e | style-only | 44 | 300 | `85106fbdbbcb2b23afac37c9…` |
| EXP-022 | retro-poster | style-only | 36 | 150 | `8e7f16158db46946ba3a1a15…` |
| EXP-022 | retro-poster | style-only | 36 | 300 | `d78a2e01139b3997113b3424…` |
| EXP-023 | minimal-geometric | **verbatim** | 44 | 150 | `1748aabad204c6af53c3e7f2…` |
| EXP-023 | minimal-geometric | **verbatim** | 44 | 300 | `d04701191dfab99d89825c67…` |
| EXP-024n12 | minimal-geometric | style-only | **12** | 150 | `20e31c451c0abe0f3af9a99b…` |
| EXP-024n12 | minimal-geometric | style-only | **12** | 300 | `ed5f41c3af3a6990b90bae17…` |
| EXP-024n24 | minimal-geometric | style-only | **24** | 150 | `2ad0ae36102812116e5b9981…` |
| EXP-024n24 | minimal-geometric | style-only | **24** | 300 | `7ff597f3cf35ba6827b5d30f…` |

Full paths and untruncated hashes: `experiments/registry.csv` and each
`docs/evidence/EXP-0xx/training-runs.jsonl`.

## 2. Technical gate results

**6 of 6 runs pass all nine gates.** Expected trainable parameter count matched, no non-LoRA
parameter trainable, base UNet unchanged (float64 byte-hash before and after), gradients
present / finite / non-zero, losses finite, LoRA parameters demonstrably moved.

| arm | images | pres./item | s/step | wall | first → last loss | L2 delta |
|---|---|---|---|---|---|---|
| EXP-020 | 44 | 6.818 | 0.284 | 90.4 s | 0.0780 → 0.0044 | 3.449 |
| EXP-021 | 44 | 6.818 | **0.408** | 127.6 s | 0.6583 → 0.0302 | 2.737 |
| EXP-022 | 36 | 8.333 | 0.294 | 93.3 s | 0.4973 → 0.0351 | 3.534 |
| EXP-023 | 44 | 6.818 | 0.294 | 93.1 s | 0.0781 → 0.0045 | 3.559 |
| EXP-024n12 | **12** | **25.000** | 0.296 | 93.4 s | 0.0648 → 0.0042 | 3.831 |
| EXP-024n24 | **24** | **12.500** | 0.331 | 104.6 s | 0.0849 → 0.0052 | 3.406 |

Peak allocated is **3133.4 MiB in all six** — neither style nor set size moves training
memory; only geometry does, as EXP-016/017 measured. Tier 0 throughout, no escalation.

`ukiyo-e` is the slowest per step because its sources run to 4000 px, so decode and crop
dominate. That is a **data-loading** cost, not a model-side one.

**Loss is not evidence of style quality** and is reported here only to show the runs are
comparable.

## 3. The blinded scoring package

- **Sheets:** `docs/evidence/prototype-4/pilot-sheets/` — 12 blinded + 3 base controls.
- **Form (blank):** `docs/evidence/prototype-4/pilot-scoring-form.md`.
- **Mapping:** `docs/evidence/EXP-025/BLINDING-MAP-do-not-open-before-scoring.csv` —
  **open only after scoring.**

Style is visible and cannot be hidden. What *is* hidden is everything the comparison is
about: which `GEO-*` sheet is style-only versus verbatim, which is the 12/24/44 arm, and
whether a sheet is the 150- or 300-step checkpoint. Seed `20260804`, fixed before the draw and
**not re-rolled**. One disclosed weakness: the draw placed some same-arm pairs at adjacent
labels — that reveals nothing about *which* arm a sheet is, and it is documented rather than
quietly re-drawn.

## 4. Unscored automated indicators

`docs/evidence/EXP-026/memorisation-indicators.md` — **descriptive only.** These populate no
rubric cell, select no checkpoint and choose no hyperparameter.

**0 of 108 generations carry a near-copy flag** at the M4 threshold `dHash ≤ 6`. Median
nearest-training dHash is 20.5–27.0 per arm, far above the flag, and the **holdout control**
sits at a comparable 25.0–28.0 — which is what the control is for: a similar distance to
images never trained on says the residual similarity comes from the base model or the prompt,
not from memorisation.

**`dHash ≤ 6` is a coarse near-copy indicator, not proof of memorisation** and not a general
memorisation measure — it is sensitive to layout and blind to recolouring.

Descriptive, not a quality claim: median CLIP cosine to the training set rises from
**0.26–0.39** (base model) to **0.37–0.72** (trained arms).

## 5. Pre-training evidence for H4

From `docs/evidence/prototype-4/caption-audit.md`, gathered **before** any run:

| style | captions: visual / attribution / truncated | distinct phrases | border delta (median) | flagged |
|---|---|---|---|---|
| minimal-geometric | 44 / 0 / 0 | **6** | +17.5 | 11/44 |
| ukiyo-e | 32 / 5 / 7 | 41 | +29.7 | 2/44 |
| retro-poster | **14** / 16 / 0 (+6 venue) | 28 | **−73.5** | **35/36 (97%)** |

The border-darkness figure is an **indicator, not proof** — a dark border can be a framed scan
or simply dark artwork. **H4 is not answered by it.** H4 is answered by your failure-mode
probe on the `PST-*` sheets against `BASE-PST`.

## 6. Decisions this gate needs from you

1. **Checkpoint per style** — 150 or 300, for each of the three styles.
2. **Full-run step count per style** — within the pre-declared band **600–1500**.
3. **Caption verdict** — style-only preferred / verbatim preferred / trade-off /
   tie-inconclusive.
4. **Dataset-size verdict** — which of O1 monotone, O2 plateau, O3 no effect, O4 trade-off,
   O5 inconclusive the 12/24/44 arms support.
5. **Contingency** — whether any contingency run is authorised, and if so which **single**
   variable it may change.
6. **Multi-style** — whether the balanced multi-style run proceeds.

## 7. Budget position

**6 of 12** training runs used. Remaining: ≤3 full + ≤1 multi-style + ≤2 contingency.
Pilot matrix used **108 of 108** allowed generations; the final matrix cap is **432** and
applies only to checkpoints you approve.

Phase A took roughly **4 hours**. **Hard stop remains 2026-08-09 end of day**, and the
scope-reduction order is unchanged: keep minimal-geometric, then ukiyo-e, then reduce or drop
retro-poster before M7 integration is at risk.

`dataset-v1.csv` is **byte-identical** to its recorded hash `cd18cbb0…`, asserted by pytest.
