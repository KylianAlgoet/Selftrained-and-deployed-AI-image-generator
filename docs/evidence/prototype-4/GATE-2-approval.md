# Prototype 4 — Gate 2 approval record

**Milestone:** M6 (Prototype 4 — style learning) · **Gate:** 2 of 2 · **M6 CLOSED**
**Final human approver:** Kylian Algoet · **Date:** 2026-08-05

## 1. Provenance

- **Kylian Algoet is the final human approver of Gate 2.** Every decision in section 3 is his.
- **ChatGPT assisted with visual analysis** of the 21 labelled Gate-2 contact sheets.
- **Kylian inspected the review material and approved the final conclusions and production
  decisions.**
- **No automated indicator selected any checkpoint, weight, style or verdict.** The indicators
  in `docs/evidence/EXP-026/` and `docs/evidence/EXP-033/` are descriptive and populate no
  rubric cell.

## 2. The fixed scoring artifact

| | |
|---|---|
| path | `docs/evidence/prototype-4/gate-2-scoring-form-completed.md` |
| sha256 | `835488f3821c4f6774546978b4e19f4d9a11b6b2e0fb88535b5796405aa16dbb` |
| size | 5872 bytes |
| completeness | 21 of 21 score rows, 15 of 15 failure-mode rows |

The hash was supplied before the file was read and verified against it. **The numeric scores
and written decisions are preserved unchanged**; a pytest asserts the hash, and `.gitattributes`
keeps Git from rewriting the file's line endings.

Unlike Gate 1, these sheets were **labelled**. Gate 1 blinded arms that each differed in one
hidden variable; Gate 2 asks which checkpoint ships, which cannot be answered without knowing
which checkpoint a sheet is. **Labelled sheets carry an expectation effect that blinded ones do
not** — stated here rather than left implicit.

## 3. Approved decisions

### 3.1 Final production checkpoints

**Verified against the recorded run rows and re-hashed on disk.** All three are rank 8 /
alpha 8 UNet-attention adapters, fp32, **256 tensors, 256 LoRA keys, zero base-model keys**,
6 414 480 bytes each.

| style | run | step | sha256 | outcome |
|---|---|---:|---|---|
| minimal-geometric | EXP-027 | **300** | `2d425838cce59adc5c12b894e29439b695b98b9e40ef5d7ae667bd5216cb96a8` | PASS |
| ukiyo-e | EXP-028 | **600** | `52381b6052ad71f165ed23425bfc4ea1ba794a3886948a741cea9cad3d81abfd` | PASS |
| retro-poster | EXP-029 | **300** | `70d2afbfb3c09aff6ba37e1f1cf82c02ad69b0269969ea7cdf43b0ead17ba8db` | PARTIAL PASS |

Paths, all under **git-ignored** `outputs/` — weights are never committed:

```
outputs/lora/EXP-027__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0/step00300/pytorch_lora_weights.safetensors
outputs/lora/EXP-028__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0/step00600/pytorch_lora_weights.safetensors
outputs/lora/EXP-029__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0/step00300/pytorch_lora_weights.safetensors
```

**These artifacts are immutable and must not be retrained or replaced.** Because of R14
(section 3.8) they cannot be regenerated from their seed, so the files themselves — not the
recipe — are the authoritative production artifacts.

Two of the three selected checkpoints are **step 300, not step 600**: more training did not
mean better for `minimal-geometric` or `retro-poster`, and Kylian's scores show why —
prompt adherence fell from 4 to 3 at step 600 in both, while style consistency stayed at 5.

### 3.2 Default application LoRA weight — **0.7**

- **0.4** often produces insufficient style influence.
- **0.7** gives the best general balance between style strength and prompt adherence.
- **1.0** frequently increases prompt override, repeated motifs or style leakage.
- The application **may** expose an adjustable range of **0.4–1.0**, but **must default to 0.7**.

### 3.3 RQ5 — separate per-style adapters selected; multi-style viable but not selected

**The balanced multi-style LoRA is technically feasible and visually competitive at 512×512, and
no severe cross-style token bleed was observed.** It scored well — `EXP-030` ukiyo-e matched the
best per-style ukiyo-e sheet on every dimension.

Separate per-style adapters are selected for production because each style has a **different**
approved checkpoint, separate adapters give cleaner independent style control, each selected
adapter was evaluated at **both** 512×512 and 512×1536, styles can be improved or replaced
independently, and the multi-style adapter's advantage does not outweigh the reduced flexibility.

**The multi-style experiment did not fail.** It is recorded as **viable but not selected for
production**.

### 3.4 H4 — **confirmed**

`retro-poster` learns a recognisable and useful vintage-poster aesthetic, **and** it transfers
pseudo-text, poster borders, framed composition and repeated poster-layout motifs. The
failure-mode probe marks `pseudo_text` and `unwanted_frame` **worse** than base on all four
`EXP-029` sheets and on the multi-style retro-poster sheet, and `artefacts` scores 2 throughout.

This confirms the M2 dataset finding and the pre-training caption audit, which measured a dark
border on **35 of 36** retro-poster training images (median delta −73.5).

### 3.5 H5 — **supported**

Style strength generally increases as LoRA weight rises, but at the highest tested weight prompt
authority can weaken, repeated motifs can increase, style-free prompts can show more leakage,
and the trained composition can dominate the requested content.

**Weight 0.7 is the selected compromise, not a universal optimum.**

### 3.6 Per-style outcomes

| style | outcome |
|---|---|
| minimal-geometric | **PASS** |
| ukiyo-e | **PASS** |
| retro-poster | **PARTIAL PASS** — pseudo-text and framing artefacts |

**`retro-poster` is not upgraded to a full pass**, per the standing rule that a partial pass is
never upgraded. It is also not dropped: it is recorded with its named defect.

### 3.7 Contingency — **not authorised**

**Both contingency slots remain unused. 10 of 12 authorised training runs were used.**

Unchanged: learning rate · rank and alpha · dataset · captions · resolution · optimizer · step
count. **No style is retrained.**

### 3.8 R14 — reproducibility finding preserved, runner fixed for future work only

**The completed M6 runs and the selected checkpoints are preserved exactly as evidence.**

**The completed training artifacts are not bit-reproducible from their seed**, because the LoRA
initialisation drew from the unseeded global torch RNG. That statement stands and is not
softened by the fix below.

The runner is fixed **for future training only**: Python `random`, the global PyTorch RNG and
CUDA are all seeded before adapter construction, the existing explicitly seeded `Generator`
usage is preserved, and two regression tests prove that the same seed gives identical initial
adapter weights while a different seed does not.

**EXP-027, EXP-028, EXP-029 and EXP-030 are not rerun or replaced after this fix.**

- **M6 evidence was generated before the fix.**
- **The selected checkpoint hashes above remain the authoritative production artifacts.**
- **The code fix improves future reproducibility and does not retroactively change the
  historical finding.**

### 3.9 DR-010 — finalised

`docs/decisions/DR-010-style-learning-configuration.md` moves from draft to **accepted**, with
every limitation stated rather than softened.

## 4. Milestone closure

**M6 is complete in repository documentation.** The GitHub issue and project-board status are
**not** updated — `gh` is unavailable and those browser actions remain Kylian's.

**Nothing is pushed.** M7 has not begun.
