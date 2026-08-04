# Prototype 4 — Gate 1 approval record

**Milestone:** M6 (Prototype 4 — style learning) · **Gate:** 1 of 2
**Approved by:** Kylian Algoet · **Date:** 2026-08-05

## 1. Attestation

Kylian Algoet attests that:

- he **personally inspected the complete set of pilot sheets** — all 12 blinded sheets
  (`GEO-1`…`GEO-8`, `PST-1`, `PST-2`, `UKY-1`, `UKY-2`) and all 3 unblinded base
  SD 1.5 controls (`BASE-GEO`, `BASE-UKY`, `BASE-PST`) in
  `docs/evidence/prototype-4/pilot-sheets/`;
- he **accepted the fixed scoring package as the visual evidence used for Gate 1**;
- he **personally made and approved all six Gate-1 decisions** recorded in section 4,
  after the blinding map was opened;
- the **numeric scores were established before the blinding map was opened**;
- the **numeric scores must not be modified after unblinding**.

**The six Gate-1 decisions below are Kylian Algoet's own.** They were not made jointly, and
no automated indicator selected a checkpoint, a step count, a style, or any hyperparameter.

## 2. The fixed scoring artifact

| | |
|---|---|
| path | `docs/evidence/prototype-4/pilot-scoring-form-completed-blind.md` |
| sha256 | `cf6bf2605b7159128dc4d841ccd04cc8867211c53992d19fd0fb6856625b71ec` |
| size | 2613 bytes |
| completeness | 15 of 15 score rows, 12 of 12 failure-mode rows, **zero blanks** |

The hash was supplied by Kylian **before** the blinding map was read, verified against the
file at that point, and re-verified after unblinding — unchanged both times. The file is
preserved byte-for-byte; nothing in it was edited, reformatted or re-scored.

**Provenance note, recorded for accuracy rather than to qualify the approval.** The scoring
file's own header records its reviewer line as "ChatGPT visual review with Kylian present".
Kylian's attestation in section 1 — that he personally inspected every sheet and personally
made every decision below — is what governs Gate 1. Both facts are recorded here so the
record is complete; see `docs/ai-usage.md`.

**Order of operations, which is what the blinding protects:**

1. Sheets scored blind; scores fixed and hashed.
2. Hash verified against the fixed value.
3. Completeness verified — no blank cells.
4. **Only then** `docs/evidence/EXP-025/BLINDING-MAP-do-not-open-before-scoring.csv` opened.
5. Scores joined to arms. **No score changed at or after this point.**

## 3. Unblinded mapping

| label | arm | style | captions | images | step | mean |
|---|---|---|---|---|---:|---:|
| GEO-1 | EXP-024n24 | minimal-geometric | style-only | 24 | 150 | 3.333 |
| GEO-2 | EXP-024n24 | minimal-geometric | style-only | 24 | 300 | 3.556 |
| GEO-3 | EXP-020 | minimal-geometric | style-only | 44 | 150 | 4.444 |
| GEO-4 | EXP-023 | minimal-geometric | **verbatim** | 44 | 150 | 4.444 |
| GEO-5 | EXP-024n12 | minimal-geometric | style-only | 12 | 150 | 3.778 |
| GEO-6 | EXP-024n12 | minimal-geometric | style-only | 12 | 300 | 4.111 |
| GEO-7 | EXP-020 | minimal-geometric | style-only | 44 | 300 | 4.889 |
| GEO-8 | EXP-023 | minimal-geometric | **verbatim** | 44 | 300 | 4.667 |
| PST-1 | EXP-022 | retro-poster | style-only | 36 | 150 | 4.333 |
| PST-2 | EXP-022 | retro-poster | style-only | 36 | 300 | 4.222 |
| UKY-1 | EXP-021 | ukiyo-e | style-only | 44 | 300 | 4.778 |
| UKY-2 | EXP-021 | ukiyo-e | style-only | 44 | 150 | 4.667 |

Base controls: **BASE-GEO 3.333 · BASE-UKY 4.111 · BASE-PST 4.000.**

Means are unweighted arithmetic means over the nine rubric dimensions, computed from the
fixed scores. **Each cell is a single sheet (n = 1); these are single human judgements, not
distributions, and carry no significance test.**

## 4. The six approved Gate-1 decisions

### 4.1 Pilot checkpoint selections

| style | steps | arm | sheet |
|---|---:|---|---|
| minimal-geometric | 300 | EXP-020 | GEO-7 |
| ukiyo-e | 300 | EXP-021 | UKY-1 |
| retro-poster | **150** | EXP-022 | PST-1 |

These are the approved pilot checkpoints **for comparison and decision traceability**. They
are **not automatically the final production checkpoints**.

### 4.2 Full-run step counts

**600 total optimizer steps for every per-style full run** — minimal-geometric, ukiyo-e and
retro-poster alike. 600 is the lower bound of the pre-declared band 600–1500.

Each run must: start from the frozen SD 1.5 base model **in a fresh OS process**; use the
frozen style manifest; use style-only captions; rank 8 / alpha 8; LR 1e-4; batch size 1 and
gradient accumulation 1; preserve the pinned dependency stack; preserve deterministic sample
ordering and record its hash.

**Runs do not resume from the pilot LoRA checkpoint**, because equivalent optimizer-state
continuation was not preserved. Every full run trains from the base model.

Checkpoints are saved and recorded at **150, 300, 450 and 600**.

Where configuration and determinism permit, the new 150- and 300-step artifacts are compared
with the pilot artifacts. **Independently trained checkpoints are not assumed to be
byte-identical**; similarities and differences are recorded honestly either way.

**The final production checkpoint for every style remains undecided until Gate 2.**

### 4.3 Caption-strategy verdict — **style-only approved and preferred**

Evidence cited by Kylian:

- style-only and verbatim were **tied across all nine dimensions at step 150**;
- at step 300, style-only **matched** verbatim on prompt adherence and style consistency;
- at step 300, style-only scored **higher on visual quality and diversity across seeds**;
- the dataset-v1 verbatim captions contain documented archive metadata, attributions and
  truncated descriptions (`docs/evidence/prototype-4/caption-audit.md`).

Style-only captions are used for **all** Phase-B per-style and multi-style training.

### 4.4 Dataset-size verdict — **O5, inconclusive**

Recorded factual findings:

- the **44**-image arm scored highest under equal 300-step compute;
- the **12**-image arm scored second;
- the **24**-image arm scored lowest;
- this **non-monotonic ordering occurred at both checkpoint steps**;
- the experiment **does not establish a monotonic relationship** between dataset size and
  quality;
- it **does not establish a universal minimum image count**;
- it establishes only that the **44-image minimal-geometric arm performed best under this
  exact equal-compute experiment**.

**This result must not be relabelled O1, O2, O3 or O4.**

### 4.5 Contingency decision — **none authorised at Gate 1**

No contingency training run is authorised. **Both contingency slots are preserved.**

Unchanged for the whole of Phase B: learning rate · rank and alpha · caption dropout ·
training resolution · dataset composition · caption strategy · optimizer.

A contingency run may occur **only** after Gate 2 identifies a specific defect **and** Kylian
provides new explicit approval for one changed variable.

### 4.6 Multi-style decision — **proceed, but only after all three per-style runs pass**

One balanced multi-style run, conditional on all three per-style full runs passing their
technical gates. Configuration: balanced deterministic sampling across the three styles;
**exactly 600 effective optimizer-step presentations per style**; **1800 total optimizer
steps**; style-only captions; rank 8 / alpha 8; LR 1e-4; the same optimizer and 512×512
training resolution as the per-style runs; the frozen `xgeo`, `xkyo` and `xpst` trigger-token
sequences.

Recorded per run: total compute · per-style exposure · sample-order hash · item-presentation
counts · checkpoint hashes and sizes · loss history · VRAM and system-RAM measurements ·
runtime · every failure or interruption.

## 5. Standing constraints carried into Phase B

- **DR-010 stays a draft with no final conclusion until Gate 2 is complete.**
- **Automated indicators remain descriptive only** — they may not select a checkpoint, style
  or hyperparameter.
- **No final style or model winner is declared**, and no final production checkpoint is
  selected, before Gate-2 approval.
- **~202 MiB of spare VRAM is never described as comfortable**, and **geometry is never
  silently reduced**.
- **No weights, checkpoints, cached latents or full-resolution outputs are committed.**
- **No push. M6 is not closed or moved to Done. M7 does not begin.**
- **Run budget:** 6 of 12 used at Gate 1; Phase B adds 3 per-style + 1 multi-style = 10 of 12.
- **Hard stop 2026-08-09 end of day.**
