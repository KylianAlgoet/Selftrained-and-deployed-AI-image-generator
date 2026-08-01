# 🛑 Prototype 2 (M4) — human-review gate

**Status: stopped here, awaiting Kylian's visual review and rubric scores.**

Everything below is **measurement only**. No quality judgement has been made, no
conditioning method has been selected, DR-008 has no conclusion, issue #5 is open, M4 is
not Done, and nothing has been pushed. That is deliberate: the qualitative decision is the
assessed research judgement (D1/D4/D6) and it is yours to make.

---

## 1. What to open, in this order

All paths are relative to the repository root.

| # | File | What it answers |
|---|---|---|
| 0 | `docs/evidence/prototype-2/contact-sheets.md` | **Read this first.** The sheets carry no burnt-in labels; this is how a cell is identified. |
| 1 | `docs/evidence/prototype-2/method-comparison-medium-seed42.jpg` | The like-for-like comparison: baseline │ img2img │ IP-Adapter │ IP-Adapter-Plus across C1–C4 |
| 2 | `docs/evidence/prototype-2/sweep-img2img-seed42.jpg` | Is img2img influence controllable? 4 conditions × 5 strengths |
| 3 | `docs/evidence/prototype-2/sweep-ipadapter-seed42.jpg` | Is IP-Adapter influence controllable? 4 conditions × 5 scales |
| 4 | `docs/evidence/prototype-2/multiseed-diversity.jpg` | **The first sheet that can answer `diversity_across_seeds`** — 4 methods × C1–C4 × all 3 frozen seeds |
| 5 | `docs/evidence/prototype-2/conflict-text-vs-reference.jpg` | C5: when reference and prompt disagree, which wins as influence rises? |
| 6 | `docs/evidence/prototype-2/difficult-reference-artefacts.jpg` | C6: frames, pseudo-lettering, landscape orientation |
| 7 | `docs/evidence/prototype-2/copy-risk-pairs.jpg` | Reference beside its perceptually closest output |
| 8 | `docs/evidence/prototype-2/deck-format-512x1536.jpg` | Does control survive the production geometry? |
| 9 | `docs/evidence/prototype-2/reference-kit-sheet.jpg` | The five frozen references themselves |

**Full-resolution PNGs** (297 of them, git-ignored) are under `outputs/EXP-008/` …
`outputs/EXP-013/`. Every filename encodes experiment, method, condition, reference, level,
strength, geometry, seed and tier, so any image traces back to its exact run.

**Two reading rules that apply to every sheet:**

- **img2img `strength` is inverted.** A *lower* number means a *stronger* reference. Sweep
  columns are ordered by ascending reference influence, so the img2img strength numbers
  **descend** left to right.
- **The shared level names are an assumption under test, not a calibrated equivalence.**
  `medium` means `strength=0.65` for img2img and `scale=0.55` for IP-Adapter. Nothing
  establishes that these exert comparable influence. Score what you see.

---

## 2. Unscored technical summary

Full tables: `measurement-summary.md`, `process-isolation-check.md`,
`lower-bound-diagnostic.md`, `monotonicity-check.md`, `all-generation-results.csv`.

### Scale of the evidence

**299 generation rows across EXP-007 → EXP-013. Zero failures, zero timeouts, memory tier 0
throughout, no tier escalation anywhere.** 16 fresh OS processes.

### VRAM — peak allocated per run (fp16, tier 0)

| geometry | text-only | img2img | IP-Adapter | IP-Adapter-Plus |
|---|---|---|---|---|
| 512×512 | 2675.38 MiB | **2675.38 MiB (+0.00)** | 3924.07 MiB (+1248.69) | 3978.87 MiB (+1303.49) |
| 512×1536 | 3892.01 MiB | **3892.01 MiB (+0.00)** | 5140.69 MiB (+1248.68) | not measured |

- **img2img costs exactly zero extra VRAM**, byte-identical to the baseline at both
  geometries — the consequence of deriving it from the already-loaded components.
- **IP-Adapter's overhead is the same fixed 1248.7 MiB at both geometries**, consistent
  with its scale acting on attention rather than on output size.
- **Headroom warning.** IP-Adapter at 512×1536 reached **7965.5 MiB peak device used against
  8187.5 MiB physical — about 222 MiB spare.** All 9 runs succeeded and no overflow flag
  was raised, but this is not headroom to call comfortable, and a LoRA stacked on top in
  Prototypes 3–4 cannot be assumed to fit.

### Latency — median seconds

| geometry | text-only | img2img | IP-Adapter | IP-Adapter-Plus |
|---|---|---|---|---|
| 512×512 | 3.248 | 3.021 (s=0.90) → 1.208 (s=0.30) | 3.35–3.47 | 3.436 |
| 512×1536 | 11.837 | 7.980 (s=0.65) | 12.022 | not measured |

**The img2img latency trap, confirmed rather than assumed.** Wall-clock *falls* as reference
influence *rises*, purely because diffusers runs `int(steps × strength)` denoising steps.
Seconds per effective step stays flat at 0.112–0.134, so the apparent speed advantage is
**fewer steps, not faster ones**. Do not read img2img as intrinsically faster.

### Process isolation — ACCEPTED in full

All **6 of 6** clean-process spot-check pairs agree with their shared-process counterparts at
**+0.000 %**, against a **2 % tolerance pre-declared in code before any measurement**. Sharing
one process across influence levels did not distort `peak_vram_allocated_mb`, so no method
needed re-running one level per process.

Recorded as a confirmation precisely because it could have gone the other way, as EXP-005's
allocator contamination did one milestone earlier.

### EXP-010 lower-bound diagnostic — both comparisons maximally positive

- **12 of 12** IP-Adapter runs at `scale=0.0` are **byte-identical** to the text-only baseline
  at the same prompt and seed. At zero scale the cross-attention path contributes nothing, so
  the method's lower bound is the baseline **exactly**, not approximately.
- **12 of 12** M4 baseline outputs are **byte-identical to Prototype 1's EXP-002 hashes** —
  cross-milestone repeatability, and proof that the M4 baseline *is* the M3 baseline, so the
  two milestones' figures are directly comparable.

Both were tested, not promised. The written caveat that hash inequality alone would **not**
have failed the lower-bound condition remains in the document, because it governs how the
result would have been read had it come out differently.

### Measurement validity

`image_encoder_revision_sha` is **empty on every text-only and img2img row** — positive
evidence from the data itself that no CLIP encoder was resident in those measured processes.
A pytest parses the Phase-1 runner with `ast` and fails if it ever imports the similarity
module. Phase-2 indicators live in a **separate file** and were computed in a **separate
process after all generation finished**.

### What the measurements do not establish

Nothing here says whether reference influence is *visually* controllable, whether either
method's mid-range is usable, or which method suits DeckForge. Those are questions 2 and 4 of
the controllability definition and they are settled by your rubric, not by these numbers.

---

## 3. The rubric

`docs/evidence/EXP-015-scoring/rubric.md` — 10 dimensions, 1–5, with anchors.

The 9 from `docs/05-experiment-methodology.md` plus one M4 addition:

- **`reference_influence` is scoreable for the first time in the project.** Every rubric to
  date recorded it as N/A because no reference mechanism existed.
- **`copy_or_overfitting_risk` is new**, because RQ11 and the near-copy flag both need it
  recorded rather than inferred from a hash distance.

**The four axes are kept separate and never collapsed into one score.** The automatic
indicators support the human judgement and never replace it:

| axis | decided by | supported, never replaced, by |
|---|---|---|
| content preservation | `reference_influence` | `dhash_distance_to_reference` — a coarse near-copy flag only |
| style influence | `style_consistency` | nothing; no automatic proxy is claimed |
| prompt adherence | `prompt_adherence`; C5 forces the trade-off open | — |
| copy risk | `originality` + `copy_or_overfitting_risk` | `dhash ≤ 6` flags candidates |

`overall_reference_similarity` (CLIP cosine) is a **descriptive indicator across all four and
attributable to none of them individually.** It entangles subject, composition, semantics,
colour and style, so it is **not a style score**, and it is computed with the same CLIP family
IP-Adapter conditions on — which makes it descriptive *within* a method rather than a neutral
referee *between* methods. **Your rubric is the decision authority.**

---

## 4. Blank scoring form and failure-mode checklist

| File | Contents |
|---|---|
| `docs/evidence/EXP-015-scoring/scoring-form.md` | **22 aggregate rows** at (method × level × resolution), every cell blank |
| `docs/evidence/EXP-015-scoring/scoring-form.csv` | the same rows, for tallying |
| `docs/evidence/EXP-015-scoring/failure-mode-probe.md` | the carried-over M3/M2 checklist |

Granularity is aggregate because that is how you actually reviewed in M3. Leave a cell blank
rather than guessing — a blank is recorded as "not scored" and is never back-filled.

The failure probe asks, per method and level, whether reference conditioning **reduces, leaves
unchanged, or worsens**: `repeated_elements`, `vertical_stretching`, `physical_deck_mockup`,
`unwanted_frame`, `pseudo_text`, `background_transfer`.

Worth checking deliberately: **R1 is also a framed, text-dominated poster scan**, not just R5.
R5 is the harder case because it adds landscape orientation, so frame and typography transfer
should be looked for in **C1 as well as C6**.

---

## 5. Deviations and corrections, stated rather than buried

1. **A factual error in the approved plan was corrected.** The plan describes C5's reference as
   *"cresting wave"*. That is the wording of prompt **P3-ukiyo**, not the content of **R3**
   (`DS-0103`), which is a landscape ukiyo-e print of a seated figure at a low desk in an
   interior. The conflict C5 tests is real and unchanged — a figurative ukiyo-e scene against a
   minimal-geometric prompt — but it is now described accurately, C3 is relabelled
   *style-matched on style, subject-mismatched*, and a pytest guards the old label from
   returning.
2. **EXP-008 and EXP-009 ran more than the planned 60 runs each (96).** The named levels run
   alongside the sweep in the same shared process. Two measurement reasons: the sweep values and
   the named levels are *different numbers*, so the clean-process spot check would otherwise
   have had no counterpart to be compared against; and the comparison and multi-seed sheets need
   `medium` across the whole condition grid.
3. **A usage-limit cutoff killed the first orchestrator run mid-EXP-009.** Stages 1–4 had
   completed. EXP-009's 77 partial rows were **discarded and the experiment re-run from
   scratch** — nothing was reconstructed by hand. `--start-at` was added for clean resumption.
4. **No linter is installed** in this environment (`ruff` absent), so pytest is the validation
   gate. No lint step is claimed to have run.
5. **`multiseed-diversity.jpg` uses 160 px thumbnails** rather than the 192 px used elsewhere,
   to stay within the 300 KB evidence limit at 48 cells.
6. **ControlNet was compared on criteria only and deliberately not implemented**, per the
   approved scope decision. The screen-out reason belongs in DR-008.
7. **`experiments/registry.csv` has not been updated yet.** Its `evaluation` and `conclusion`
   fields require your scores; filling them now would mean inventing them. Registry
   finalisation is a post-approval step in the plan.

---

## 6. What happens after you supply scores

Only then, and in this order: record the scores at the granularity you actually used → write
DR-008 with its conclusion and the ControlNet screen-out → `docs/prototypes/prototype-2.md` →
finalise `experiments/registry.csv` → update planning, risks, testing strategy, traceability,
AI-usage and the dataset-methodology wording → close issue #5 → board to Done → push → M4
milestone report. **Then stop before M5.**

If the outcome is negative — if neither method gives visible, monotone, usable control — that
is a legitimate RQ6 answer and it will be recorded as one, not worked around.
