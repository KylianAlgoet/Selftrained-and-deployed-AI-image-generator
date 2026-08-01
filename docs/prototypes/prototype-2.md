# Prototype 2 — Text + reference-image conditioning (M4)

**Status:** **COMPLETE.** Reviewed and scored by Kylian 2026-08-01; conditioning method selected in DR-008.
**Date:** 2026-08-01 · **Research questions:** RQ6 (combining text and reference conditioning), RQ7 (which parameters dominate perceived control), RQ11 (copy / overfitting risk)

## Outcome

| | |
|---|---|
| **Selected method (Prototypes 3–5)** | **Standard IP-Adapter** — `h94/IP-Adapter`, `ip-adapter_sd15.safetensors` @ `018e402774` |
| **Default scale** | **0.55** |
| **User-adjustable range** | **0.40 – 0.60**; higher values only with an explicit warning |
| **Documented fallback** | **img2img** — zero extra VRAM, retained as a low-VRAM / transformation mode, **not** the default |
| **Not selected** | IP-Adapter-Plus (no decisive advantage, slightly more VRAM) |
| **Criteria-only, not implemented** | ControlNet — answers structural edge/layout control, not the artwork reference question |

Decision record: `docs/decisions/DR-008-reference-conditioning-method.md`.
Kylian's scores: `docs/evidence/EXP-015-scoring/human-scores.md`.

The measurements below were produced **before** any conclusion was drawn. The assistant stopped at a
human-review gate and assigned no quality score of its own.

## Research questions and hypotheses

| RQ | Hypothesis at the start | Status after measurement |
|---|---|---|
| **RQ6** | Reference influence can be made *controllable* rather than all-or-nothing | **Confirmed for both measured methods.** All four controllability conditions met by img2img and IP-Adapter alike |
| **RQ6 (mechanism)** | IP-Adapter's scale is independent of output geometry; img2img couples influence to `strength` and forces the reference into the output resolution, so img2img will degrade specifically at 512×1536 | **Confirmed, and more sharply than expected** — see the near-copy finding below |
| **RQ7** | The reference-strength parameter dominates perceived control more than CFG | **Partially tested only.** Strength was swept; CFG was held at the frozen 7.5, so no CFG comparison was made and none is claimed |
| **RQ11** | — | **New evidence:** near-copies are produced by img2img at the deck format, not by IP-Adapter at any setting |

## Scope

**Inference research only. No LoRA training. Dataset v1 was read, never written.** The frozen prompt
kit was reused verbatim (fingerprint `c40749bc…`, unchanged and hash-locked by pytest) and extended
with reference images in a **new** module rather than edited.

---

## Part 1 — Objective measurements

**299 generation rows across EXP-007 → EXP-013. Zero failures, zero timeouts, memory tier 0
throughout, no escalation anywhere.** 16 fresh OS processes.

### VRAM — peak allocated per run (fp16, tier 0)

| geometry | text-only | img2img | IP-Adapter | IP-Adapter-Plus |
|---|---|---|---|---|
| 512×512 | 2675.38 MiB | **2675.38 (+0.00)** | 3924.07 (+1248.69) | 3978.87 (+1303.49) |
| 512×1536 | 3892.01 MiB | **3892.01 (+0.00)** | 5140.69 (+1248.68) | not measured |

img2img costs **exactly zero extra VRAM** — byte-identical to the baseline, because
`AutoPipelineForImage2Image.from_pipe` shares the already-loaded components. IP-Adapter's overhead
is the **same fixed ~1248.7 MiB at both geometries**, consistent with its scale acting on attention
rather than on output size.

### Latency — median seconds

| geometry | text-only | img2img | IP-Adapter | IP-Adapter-Plus |
|---|---|---|---|---|
| 512×512 | 3.248 | 3.021 (s=0.90) → 1.208 (s=0.30) | 3.35–3.47 | 3.436 |
| 512×1536 | 11.837 | 7.980 (s=0.65) | 12.022 | not measured |

**The img2img latency advantage is an artefact, not a speed-up.** Diffusers runs
`int(steps × strength)` steps, so a stronger reference is also faster. Seconds per effective step
stays flat at 0.112–0.134 across the whole sweep: fewer steps, not faster ones.

### Controllability, established from data

| Condition | Result |
|---|---|
| **1. Bounded below** | **Met exactly.** 12/12 IP-Adapter runs at `scale=0.0` are **byte-identical** to the text-only baseline |
| **2. Bounded above** | Met — confirmed by Kylian at the review gate (`reference_influence` 5 at the strongest levels of both methods) |
| **3. Monotone** | **Met by both.** Median overall reference-image similarity rises with level in **6/6 conditions for img2img and 6/6 for IP-Adapter** |
| **4. Usable mid-range** | **Met by both.** Nine settings score both `reference_influence ≥ 3` and `prompt_adherence ≥ 3` |

### Measurement validity

- **Process isolation accepted in full:** 6/6 clean-process spot-check pairs at **+0.000 %** against
  a 2 % tolerance **pre-declared in code before any measurement**.
- **Generation measurement was separated from similarity evaluation.**
  `image_encoder_revision_sha` is **empty on every text-only and img2img row** — positive evidence
  from the data that no CLIP encoder was resident in those measured processes. A pytest parses the
  Phase-1 runner with `ast` and fails if it ever imports the similarity module.
- **Cross-milestone repeatability:** 12/12 M4 baselines are byte-identical to Prototype 1's EXP-002
  hashes, so the M3 and M4 figures are directly comparable.

---

## Part 2 — Human rubric scores

**Reported separately from the measurements and never blended with them.** Aggregate scores at
(method × influence level × resolution) — Kylian's own judgement, recorded verbatim in
`docs/evidence/EXP-015-scoring/human-scores.csv`.

### Per-method means at 512×512, blanks excluded, `n` stated

| dimension | text-only | img2img | ip-adapter | ip-adapter-plus |
|---|---|---|---|---|
| prompt_adherence | 3.00 (n=1) | 3.00 (n=8) | 3.11 (n=9) | 3.00 (n=1) |
| style_consistency | 3.00 (n=1) | 4.12 (n=8) | 4.44 (n=9) | 5.00 (n=1) |
| reference_influence | not scored | 3.75 (n=8) | 3.44 (n=9) | 4.00 (n=1) |
| visual_quality | 4.00 (n=1) | 4.00 (n=8) | 4.00 (n=9) | 4.00 (n=1) |
| decal_suitability | 2.00 (n=1) | 3.75 (n=8) | 3.56 (n=9) | 4.00 (n=1) |
| composition | 3.00 (n=1) | 4.00 (n=8) | 3.89 (n=9) | 4.00 (n=1) |
| artefacts | 4.00 (n=1) | 3.38 (n=8) | 3.44 (n=9) | 3.00 (n=1) |
| originality | 4.00 (n=1) | **3.12 (n=8)** | **4.11 (n=9)** | 4.00 (n=1) |
| diversity_across_seeds | 4.00 (n=1) | 3.00 (n=1) | 4.00 (n=1) | 4.00 (n=1) |
| copy_or_overfitting_risk | not scored | **3.12 (n=8)** | **4.33 (n=9)** | 4.00 (n=1) |

**A blank is NOT SCORED, never a zero.** 29 cells are blank; they are excluded from every mean and
the surviving `n` is printed beside each figure. `reference_influence` and
`copy_or_overfitting_risk` are blank for text-only, which uses no reference at all.
`diversity_across_seeds` carries n=1 per method and is **not load-bearing**.

**`reference_influence` was scoreable for the first time in the project** — every rubric before this
recorded it as N/A.

### Deck format 512×1536

| method | prompt | style | reference | quality | decal | comp | artefacts | originality | diversity | copy risk |
|---|---|---|---|---|---|---|---|---|---|---|
| img2img medium (0.65) | 2 | 5 | 5 | 4 | 4 | 4 | 3 | **1** | – | **1** |
| ip-adapter medium (0.55) | 3 | 4 | 4 | 4 | 4 | 4 | 3 | **4** | – | **4** |
| text-only | – | – | – | – | – | – | – | – | – | – |

**text-only at 512×1536 was not visually rescored from the M4 contact sheets and remains NOT
SCORED.** No M3 value has been substituted, and none may be.

---

## ⚠️ Two risks carried forward

### 1. img2img produces near-copies at the production geometry

**All six copy-risk flags in the milestone (dHash ≤ 6) are img2img at 512×1536**, on exactly the two
references natively 512×1536 (R2, R4). **Three are at dHash 0–1 — perceptually indistinguishable
from the reference.** Median dHash for img2img at medium is **27 at 512×512 but 5 at 512×1536**.
Kylian scored these `originality 1`, `copy_or_overfitting_risk 1`.

Mechanism: **img2img forces the reference into the output resolution.** When the reference already
matches the output aspect nothing is cropped, and denoising at `strength=0.65` starts from an
essentially intact copy. This is **the deck geometry the product ships**, which is why img2img is
not the primary method. Flagged outputs were **kept and surfaced, never deleted** — a first-class
RQ11 finding.

### 2. IP-Adapter at 512×1536 is memory-critical

Peak physical usage **7965.5 MiB of 8187.5 MiB — about 222 MiB spare.** All 9 runs succeeded and no
overflow flag fired, but **this is never to be described as comfortable headroom.**

**Do not assume IP-Adapter + LoRA will fit.** A combined **SD 1.5 + selected LoRA + IP-Adapter at
512×1536** smoke test is a mandatory acceptance item for the next relevant milestone (risk **R12**).
If it fails, the failure is recorded as its own result row and approved memory tiers are tested in
separate runs. **Geometry is never silently reduced to make it pass.**

---

## Failure-mode observations (Kylian, verbatim)

**C6, the difficult reference** — both methods **worsen** `unwanted_frame`, `pseudo_text` and
`background_transfer` at medium and strong. img2img at weak shows none of the six; IP-Adapter at
weak worsens `repeated_elements` and `pseudo_text`.

**EXP-013, deck format** — img2img worsens `background_transfer` at C2 and C4 (recorded as
*near-copy / wholesale layout preservation*), while IP-Adapter **reduces** it at both. IP-Adapter
worsens `repeated_elements` at C1 and `vertical_stretching` at C4.

`physical_deck_mockup` was **not observed** under any conditioned setting, against
`decal_suitability 2` for the text-only baseline — the M3 mockup failure appears to be a text-only
behaviour.

**This is evidence, not the dataset mitigation decision.** The crop-pass-versus-negative-prompting
decision for framed, text-heavy source material stays in **Prototype 4 (M6)**, where training
evidence will exist.

---

## Corrections and deviations, stated rather than buried

1. **A factual error in the approved plan was corrected.** The plan described C5's reference as a
   *"cresting wave"*; that is the wording of prompt **P3-ukiyo**, not the content of **R3**
   (`DS-0103`), which is a landscape ukiyo-e print of a seated figure at a low desk in an interior.
   The conflict C5 tests is real and unchanged, but is now described accurately. A pytest guards the
   old label from returning. Recorded also: **R1 is likewise a framed, text-dominated poster scan** —
   R5 is harder because it adds landscape orientation, not because it is the only framed reference.
2. **EXP-008/EXP-009 ran 96 rows each rather than the planned 60.** The named levels run alongside
   the sweep in the same shared process: the sweep values and named levels are *different numbers*,
   so the clean-process spot check would otherwise have had no counterpart to compare against.
3. **A usage-limit cutoff killed the first orchestrator run mid-EXP-009.** The 77 partial rows were
   **discarded and the experiment re-run from scratch**; nothing was reconstructed by hand.
4. **No linter is installed** (`ruff` absent), so pytest is the validation gate. No lint step is
   claimed to have run.
5. **ControlNet was never measured**, so no statement about its performance is made or implied.

## Limitations

- Scores are **aggregate**, not per image; one reviewer, one pass.
- The shared level names are an **assumption under test, not a calibrated equivalence**.
- `diversity_across_seeds` rests on **n=1 row per method**.
- **IP-Adapter-Plus was measured at one level only**; monotonicity is *not applicable* for it rather
  than failed.
- **text-only at 512×1536 is unscored**, so the deck-format table has no scored baseline column.
- `overall_reference_similarity` uses the same CLIP family IP-Adapter conditions on, so it is
  descriptive *within* a method, not a neutral referee *between* methods.

## Impact on the next iteration

- Prototype 3 (LoRA smoke test) and Prototype 4 build on **SD 1.5 + IP-Adapter at scale 0.55**.
- The **combined LoRA + IP-Adapter 512×1536 smoke test (R12) gates that work.**
- Prototype 5 must expose scale 0.40–0.60 with a warning beyond it, and budget **~1249 MiB** above
  bare SD 1.5.
- ControlNet is **deferred, not rejected**, should user-supplied layout control become a requirement.

## Evidence and commits

`docs/evidence/EXP-007/` … `EXP-014/` · `docs/evidence/prototype-2/` · `docs/evidence/EXP-015-scoring/` ·
`experiments/registry.csv` EXP-007…EXP-014 · `docs/decisions/DR-008-reference-conditioning-method.md`.

Commits `ce681b7`, `9f0d664`, `9053c71`, `331c6aa`, `d15dc17`, `aaa0e06`, `1985d8d`, `dd80659`,
`d4552c3`, `6ace111`, `9c6cbbd` and the closing documentation commits.
