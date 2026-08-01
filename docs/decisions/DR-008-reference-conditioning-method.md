# DR-008: Reference-conditioning method for Prototypes 3–5

**Date:** 2026-08-01 · **Status:** accepted (approved by Kylian after manual review of the Prototype 2 evidence)
**Answers:** RQ6 (how to combine text and reference conditioning), part of RQ7 (which parameters dominate perceived control)
**Builds on:** DR-007, which selected SD 1.5 and the `direct 1:3 @ 512×1536` deck format but left reference conditioning open.

## Decision

**Standard IP-Adapter (`h94/IP-Adapter`, `ip-adapter_sd15.safetensors`, pinned at
`018e402774aeeddd60609b4ecdb7e298259dc729`) is the primary reference-conditioning method for
Prototypes 3–5.**

| Parameter | Value |
|---|---|
| Default scale | **0.55** |
| Recommended initial user-adjustable range | **0.40 – 0.60** |
| Lower values | stronger prompt authority |
| Higher values | permitted **only with an explicit warning** that prompt authority falls and pseudo-text / source-like composition increase |

**img2img is retained as a documented low-VRAM fallback and optional transformation mode, not the
default reference-conditioning path.** IP-Adapter-Plus and ControlNet are not selected.

## Context

Everything in DeckForge AI up to M3 was text-only. `reference_influence` had been recorded as **N/A**
in every rubric to date because no reference mechanism existed, while the primary research question
and the Prototype 5 MVP flow both require a reference image alongside the prompt.

M4 built that mechanism and measured it on SD 1.5 at 512×512 and at the DR-007 deck format
512×1536, on the audited RTX 4060 Laptop GPU (**8187.5 MiB VRAM**).

**Every figure below was measured on this machine. None is estimated.** The human scores are
Kylian's own aggregate judgements, supplied at the review gate; none was inferred or filled in.

## Alternatives considered

| Candidate | Outcome |
|---|---|
| **Text-only baseline** | Measured (EXP-010) — the control, not a candidate |
| **img2img** (SD 1.5 native) | Measured (EXP-008, EXP-008b, EXP-011, EXP-013) — **not selected as primary** |
| **IP-Adapter** (base, SD 1.5) | Measured (EXP-007, EXP-009, EXP-009b, EXP-010, EXP-011, EXP-013) — **SELECTED** |
| **IP-Adapter-Plus** | Measured at medium only (EXP-012) — not selected |
| **ControlNet** (`control_v11p_sd15_canny`) | Compared on criteria, deliberately **not implemented** |
| **T2I-Adapter** | Screened out — thinner ecosystem and documentation for the same structural-control role |
| **"reference-only" attention hacks** | Screened out — no official Diffusers pipeline; community implementations only, the same provenance standard applied to the SD 2.1 mirror in M3 |

## Criteria

Reference influence must be **controllable**, not all-or-nothing. Four conditions, defined before any
measurement:

1. **Bounded below** — at minimum influence the output is equivalent to the text-only baseline.
2. **Bounded above** — at maximum influence reference influence is unmistakable to the reviewer.
3. **Monotone** — median overall reference-image similarity rises with influence, in ≥ 3 of the 4 style-matched conditions.
4. **Usable mid-range** — at least one intermediate level scores **both** `reference_influence ≥ 3` **and** `prompt_adherence ≥ 3`. This is the actual product requirement.

Plus cost: VRAM and latency, and feasibility at 512×1536.

---

## Part 1 — Objective measurements

**Reported separately from the human scores, and never blended with them.** 299 generation rows
across EXP-007 → EXP-013, **zero failures, zero timeouts, memory tier 0 throughout, no escalation
anywhere**, in 16 fresh OS processes.

### VRAM — peak allocated per run (fp16, tier 0)

| geometry | text-only | img2img | IP-Adapter | IP-Adapter-Plus |
|---|---|---|---|---|
| 512×512 | 2675.38 MiB | **2675.38 (+0.00)** | 3924.07 (+1248.69) | 3978.87 (+1303.49) |
| 512×1536 | 3892.01 MiB | **3892.01 (+0.00)** | 5140.69 (+1248.68) | not measured |

img2img costs **exactly zero extra VRAM** at both geometries — byte-identical to the baseline,
because `AutoPipelineForImage2Image.from_pipe` shares the already-loaded components. IP-Adapter's
overhead is the **same fixed ~1248.7 MiB at both geometries**, consistent with its scale acting on
attention rather than on output size.

### Latency — median seconds

| geometry | text-only | img2img | IP-Adapter | IP-Adapter-Plus |
|---|---|---|---|---|
| 512×512 | 3.248 | 3.021 (s=0.90) → 1.208 (s=0.30) | 3.35–3.47 | 3.436 |
| 512×1536 | 11.837 | 7.980 (s=0.65) | 12.022 | not measured |

**The img2img latency advantage is an artefact, not a speed-up.** Diffusers runs
`int(steps × strength)` denoising steps, so a stronger reference is also faster. Seconds per
effective step stays flat at 0.112–0.134 across the whole sweep: **fewer steps, not faster ones.**

### Controllability conditions 1–3, from data

- **Condition 1 (bounded below) — met exactly.** **12 of 12** IP-Adapter runs at `scale=0.0` are
  **byte-identical** to the text-only baseline at the same prompt and seed. At zero scale the
  cross-attention path contributes nothing, so the lower bound is the baseline *exactly*, not
  approximately. This was tested, not assumed; a hash mismatch alone would not have failed the
  condition, and the caveat remains recorded in `lower-bound-diagnostic.md`.
- **Condition 3 (monotone) — met by both measured methods.** Median overall reference-image
  similarity rises with influence level in **6 of 6 conditions for img2img and 6 of 6 for
  IP-Adapter**, clearing the ≥ 3-of-4 bar. IP-Adapter-Plus is *not applicable* — it ran at medium
  only by design, so monotonicity is untestable for it, which is not a failure.
- **Measurement validity.** The clean-process spot check passed at **+0.000 % on 6 of 6 pairs**
  against a 2 % tolerance pre-declared in code before any measurement, so sharing one process
  across influence levels did not distort the per-run VRAM figures.

### Cross-milestone repeatability

**12 of 12** M4 text-only baselines are byte-identical to Prototype 1's EXP-002 hashes. The M4
baseline provably *is* the M3 baseline, so the two milestones' figures are directly comparable.

### What the CLIP indicator is not

`overall_reference_similarity` entangles subject, composition, semantics, colour and style, so it is
**not a style score**, and it is computed with the same CLIP family IP-Adapter conditions on — making
it descriptive *within* a method rather than a neutral referee *between* methods. It ordered the
levels; it did not choose the method.

---

## Part 2 — Human rubric scores

**Reported separately from the measurements.** Aggregate scores at (method × influence level ×
resolution), Kylian's own judgement, recorded verbatim in
`docs/evidence/EXP-015-scoring/human-scores.csv`. **29 cells are recorded as NOT SCORED; blanks are
excluded from every mean and never treated as zeros.**

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

These means average across influence levels, including the deliberately weak and deliberately
extreme ones, so they describe each method's behaviour across its whole range rather than at its
best setting. **`diversity_across_seeds` carries n=1 per method** and is the weakest-supported row
in the table; it is not load-bearing for this decision.

**Condition 4 (usable mid-range) — met by both measured methods.** Nine settings score both
`reference_influence ≥ 3` and `prompt_adherence ≥ 3`, including img2img at 0.6/0.65 and IP-Adapter
at 0.4/0.55/0.6. Neither method is forced to choose between ignoring the reference and ignoring the
prompt.

### Scores at the deck format 512×1536

| method | prompt | style | reference | quality | decal | comp | artefacts | originality | diversity | copy risk |
|---|---|---|---|---|---|---|---|---|---|---|
| img2img medium (0.65) | 2 | 5 | 5 | 4 | 4 | 4 | 3 | **1** | – | **1** |
| ip-adapter medium (0.55) | 3 | 4 | 4 | 4 | 4 | 4 | 3 | **4** | – | **4** |
| text-only | – | – | – | – | – | – | – | – | – | – |

**text-only at 512×1536 was not visually rescored from the M4 contact sheets and remains NOT
SCORED.** No M3 value has been substituted for it, and none may be — the M3 review used different
sheets and answered a different question.

---

## ⚠️ Two risks that must not be softened

### 1. img2img produces near-copies at the production geometry

**All six copy-risk flags in the entire milestone (dHash ≤ 6) are img2img at 512×1536**, on exactly
the two references that are natively 512×1536 (R2, R4). **Three are at dHash 0–1 — perceptually
indistinguishable from the reference.** Median dHash for img2img at the medium level is **27 at
512×512 but 5 at 512×1536**. Kylian scored these outputs `originality 1` and
`copy_or_overfitting_risk 1`.

The mechanism is mechanical, not mysterious: **img2img forces the reference into the output
resolution.** When the reference already matches the output aspect, nothing is cropped away and
denoising at `strength=0.65` starts from an essentially intact copy. This is not an edge case — it
is **the deck geometry the product ships**, and it is the decisive reason img2img is not the primary
method.

### 2. IP-Adapter at 512×1536 is feasible but memory-critical

Peak physical usage was **7965.5 MiB of 8187.5 MiB — about 222 MiB spare.** All 9 runs succeeded and
no overflow flag fired, but **this must never be described as comfortable headroom.**

**Do not assume that IP-Adapter + LoRA will fit.** A combined **SD 1.5 + selected LoRA + IP-Adapter
at 512×1536** smoke test is an explicit acceptance requirement for the next relevant milestone
(risk **R12**, `docs/process/risk-register.md`). If it fails, the failure is recorded as its own
result row and the approved memory tiers are tested in separate runs. **Geometry is never silently
reduced to make it pass.**

---

## Justification

1. **Both measured methods demonstrated monotone, controllable influence** — conditions 1–4 met by
   img2img and IP-Adapter alike. This is a genuine positive answer to RQ6, and the choice between
   them is therefore not about whether control works but about what each costs.
2. **Standard IP-Adapter gives the best overall visual balance in the supplied evidence:** visible
   reference influence, better diversity, stronger originality (4.11 vs 3.12), and **no near-copy
   flags anywhere in the milestone.**
3. **img2img is not selected as primary** because at 512×1536 its medium setting produced six
   dHash ≤ 6 flags, including dHash 0–1 outputs perceptually indistinguishable from the reference,
   at the very geometry the product uses.
4. **img2img remains a documented low-VRAM fallback or optional transformation mode.** It costs
   literally zero extra VRAM, which keeps it valuable if the combined LoRA + IP-Adapter stack proves
   infeasible.
5. **IP-Adapter-Plus is not selected:** no decisive visual advantage over standard IP-Adapter
   (its single medium row is comparable) while using slightly more VRAM (3978.87 vs 3924.07 MiB).
6. **ControlNet remains criteria-only and screened out for M4** because it conditions on structural
   edges and layout rather than on an artwork reference's style and content, which is what RQ6 asks.
   It would also have added opencv as a new pinned dependency and ~700 MiB for a question this
   milestone was not posing. **This is a scope decision, not a quality judgement**, and it is flagged
   for Prototype 5 if user-supplied layout control becomes a requirement.
7. **IP-Adapter at 512×1536 is technically feasible but memory-critical** — see the risk above.
8. **The combined LoRA + IP-Adapter smoke test is mandatory** before the stack is relied on.

## Consequences

- Prototypes 3–5 build on **SD 1.5 + IP-Adapter** at default scale 0.55, exposing 0.40–0.60 to users.
- The backend must budget **~1249 MiB above bare SD 1.5**, and the UI must warn when scale exceeds
  the recommended range.
- A **512×1536 LoRA + IP-Adapter smoke test gates Prototype 3/4** (risk R12).
- **img2img stays implemented and documented** as the low-VRAM fallback; the runner already supports
  it, so retaining it costs nothing.
- The near-copy behaviour of img2img at the deck format is a **first-class RQ11 finding** and must be
  reported as such, not quietly dropped with the method.
- ControlNet is **deferred, not rejected**, for user-supplied layout control in Prototype 5.

## Limitations, stated rather than buried

- Scores are **aggregate**, at (method × level × resolution), not per image. They are one reviewer's
  judgement on one pass.
- The shared level names are an **assumption under test, not a calibrated equivalence**: img2img
  `strength=0.65` and IP-Adapter `scale=0.55` are both labelled *medium* with nothing establishing
  they exert comparable influence.
- `diversity_across_seeds` rests on **n=1 row per method** and is not load-bearing here.
- **IP-Adapter-Plus was measured at one level only**, so its comparison with the base variant is
  narrower than the img2img-versus-IP-Adapter comparison.
- **text-only at 512×1536 is unscored**, so the deck-format table has no scored baseline column.
- ControlNet was **never measured**, so no statement about its performance is made or implied.
- `overall_reference_similarity` uses the same CLIP family IP-Adapter conditions on, so it is not a
  neutral referee between methods.

## Evidence

`docs/evidence/EXP-007/` … `EXP-014/` · `docs/evidence/prototype-2/` (measurement summary,
process-isolation check, monotonicity check, lower-bound diagnostic, copy-risk report, eight contact
sheets with their grid legend, reference kit) · `docs/evidence/EXP-015-scoring/` (rubric,
`human-scores.csv`/`.md`, scoring form, failure-mode probe) · `experiments/registry.csv`
EXP-007…EXP-014 · `docs/prototypes/prototype-2.md`.
