# Architecture research and decisions

**Created:** 2026-07-27 · Decisions here follow the 13-step research loop. Phase 0 decides only what must be decided before Prototype 0; ML method choices remain open hypotheses until Prototypes 1–4 deliver benchmarks.

Scoring: each criterion weighted 1–5; each alternative scored 1–5; weighted totals justify (not replace) the reasoned decision. Scores are the student/agent's documented judgement given the environment audit (`docs/technical/environment-audit.md`) and the 19-day timeline — hardware-dependent ML scores will be **revised with measured data** after Prototypes 1 and 3.

**Update 2026-07-30:** section D-E below is the first matrix populated with **measured** hardware data rather than reasoned judgement (Prototype 1 / DR-007). Sections D-A…D-D remain reasoned judgements; D-D's ML-method screening is still awaiting Prototype 3.

---

## D-A: Repository structure — DECIDED (DR-001)

**Problem:** the project spans ML training, a backend, a frontend, datasets, experiments, and heavy documentation that must stay traceable for a jury.

| Criterion (weight) | Monorepo | Multi-repo | Flat single folder |
|---|---|---|---|
| Jury traceability: one history tells the whole story (5) | 5 | 2 | 3 |
| Tooling/setup simplicity on one machine (4) | 4 | 2 | 5 |
| Deadline risk (4) | 5 | 2 | 4 |
| Reproducibility / clean-clone test (4) | 5 | 3 | 3 |
| Separation of concerns (3) | 4 | 5 | 1 |
| **Weighted total (max 100)** | **93** | **51** | **69** |

**Decision:** monorepo with the structure mandated in the master prompt (`apps/`, `ml/`, `data/`, `experiments/`, `docs/`, …). A single Git history is itself D3/D7 evidence. → `docs/decisions/DR-001-repository-structure.md`

---

## D-B: Backend framework — DECIDED (DR-002)

Requirements: serve generation requests from a Python ML stack, validate untrusted uploads, typed request/response models, testable, async-friendly for long generation calls.

| Criterion (weight) | FastAPI | Flask | Node/Express |
|---|---|---|---|
| Native fit with Python ML stack (5) | 5 | 5 | 1 |
| Built-in validation (Pydantic) for untrusted input (5) | 5 | 2 | 3 |
| Async + long-running request handling (4) | 5 | 2 | 4 |
| Auto OpenAPI docs as jury evidence (3) | 5 | 2 | 3 |
| Testability with Pytest (4) | 5 | 4 | 2 |
| Student time-to-productivity in 19 days (4) | 4 | 4 | 3 |
| **Weighted total (max 125)** | **121** | **81** | **65** |

**Decision:** FastAPI + Pydantic. Express would force a second process boundary between ML and API for no benefit; Flask lacks first-class validation and async. → `docs/decisions/DR-002-backend-framework.md`

---

## D-C: Frontend and 3D stack — DECIDED (DR-003)

Requirements: interactive 3D deck (rotate/zoom/reset), dynamic texture swap, form-heavy generation UI, testable (Vitest/Playwright).

| Criterion (weight) | React+Vite+TS + React Three Fiber | Plain Three.js + vanilla TS | SvelteKit + Threlte |
|---|---|---|---|
| 3D scene + UI state integration (5) | 5 | 2 | 4 |
| Ecosystem/docs for skateboard-style product viewers (4) | 5 | 4 | 2 |
| Type safety for API contract (4) | 5 | 4 | 4 |
| Testing story (Vitest/Playwright) (4) | 5 | 3 | 4 |
| Time-to-first-prototype (4) | 4 | 3 | 3 |
| **Weighted total (max 105)** | **101** | **66** | **72** |

**Decision:** React + Vite + TypeScript with React Three Fiber (drei helpers for OrbitControls/loading). Prototype 0 validates this choice immediately — if R3F texture swapping or the deck model proves problematic, fallback is plain Three.js (documented as the revision path). → `docs/decisions/DR-003-frontend-3d-stack.md`

---

## D-D: ML tooling — DECIDED as toolchain, method stays open (DR-004)

Requirements: local LoRA training on 8 GB VRAM, scriptable/reproducible (no GUI-only flows), inference integration into FastAPI, config-as-code for the experiment registry.

| Criterion (weight) | HF Diffusers+PEFT+Accelerate | kohya-ss sd-scripts | ComfyUI pipeline |
|---|---|---|---|
| Scriptable reproducibility (configs, seeds, CI-able) (5) | 5 | 4 | 2 |
| Integration into a FastAPI service (5) | 5 | 3 | 2 |
| Memory-optimization options for 8 GB (4) | 4 | 5 | 3 |
| Learning-outcome evidence value (understandable code, not a black box) (4) | 5 | 3 | 2 |
| Community-validated LoRA quality (3) | 4 | 5 | 4 |
| **Weighted total (max 105)** | **98** | **83** | **54** |

**Decision:** Hugging Face Diffusers + PEFT + Accelerate (+ Transformers, Safetensors) as the toolchain. **Update 2026-08-04: the kohya-ss fallback is NOT needed** — Diffusers + PEFT LoRA training fits 8 GB comfortably at 512×512 (3133 MiB) and adequately at the deck format (5183 MiB), both at tier 0 with no escalation (EXP-016/EXP-017). **The fine-tuning method WAS decided on 2026-08-04 with measured data → DR-009**, and the base model on 2026-07-30 → DR-007, section D-E below. → `docs/decisions/DR-004-ml-toolchain.md`

---

## D-E: Base model — DECIDED with measured data (DR-007)

Phase 0 deliberately left this open, recording "SD 1.5-class at 512 px runs and trains; SDXL inference works but training is marginal" as a **hypothesis**. Prototype 1 replaced that hypothesis with measurements on the audited RTX 4060 Laptop GPU (8187.5 MiB VRAM). All figures below are **measured**, at memory tier 0, with no tier escalation needed.

| Criterion (weight) | SD 1.5 | SDXL base 1.0 | SD 2.1 base |
|---|---|---|---|
| Fits in 8 GB VRAM at its native resolution (5) | 5 — 2675 MiB allocated | **1 — 10738 MiB allocated vs 8188 MiB physical; only completes via silent WDDM host-memory spill** | not measured (blocked) |
| Interactive latency for a local app (5) | 5 — 4.07 s @512 | 1 — 16.51 s @512, 118.73 s @1024 | not measured (blocked) |
| Headroom left for IP-Adapter + LoRA (Prototypes 2–4) (5) | 5 — ~5.5 GB free @512 | 1 — saturates the device even at 512 | not measured (blocked) |
| Native-resolution visual quality (human scores) (4) | 3 — style_consistency 3, visual_quality 4 | **5 — style_consistency 5, visual_quality 5** | not measured (blocked) |
| Quality under the controlled 512×512 condition (4) | 4 — 3/3/4/3/3/4/3 | 4 — **identical** 3/3/4/3/3/4/3 | not measured (blocked) |
| Adapter/LoRA ecosystem maturity (4) | 5 | 4 | 3 |
| Availability and reproducibility (4) | 5 — ungated, pinned `451f4fe1` | 5 — ungated, pinned `46216598` | **1 — HTTP 401, gated (EXP-003)** |
| Deadline and reliability risk (4) | 5 | 2 | 1 |
| **Weighted total (max 175)** | **166** | **83** | not scoreable |

**Decision:** **Stable Diffusion 1.5** for Prototypes 2–5, pinned at `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`. SDXL base 1.0 is retained as the **visual-quality benchmark**, not the production model.

The decisive point is the Track A row: at the *same* 512×512 resolution the student scored the two models **identically**, so SDXL's genuine quality advantage exists only at a resolution this GPU cannot physically hold. Full reasoning, both tracks reported separately, the WDDM spill finding, and the two-candidate limitation: → `docs/decisions/DR-007-base-model-selection.md`

**Deck format (RQ8):** direct 1:3 generation at **512×1536** (3892 MiB, reliable); square-crop rejected because a 1:3 strip from 512×512 leaves only ~170×512 usable pixels. The Phase 0 hypothesis that direct tall generation would degrade was **refuted**.

---

## D-F: Reference-conditioning method — DECIDED with measured data (DR-008)

**Selected: standard IP-Adapter** (`h94/IP-Adapter`, `ip-adapter_sd15.safetensors` @ `018e402774`),
default scale **0.55**, user-adjustable range **0.40–0.60**. Answers RQ6 and part of RQ7.

The second weighted matrix populated with real hardware figures. Every number was measured on the
audited RTX 4060 Laptop GPU across 299 generations with zero failures, at memory tier 0 throughout.

| Criterion | text-only (control) | **img2img** | **IP-Adapter** ✅ | IP-Adapter-Plus | ControlNet |
|---|---|---|---|---|---|
| Extra VRAM @512×512 | — | **+0.00 MiB** | +1248.69 MiB | +1303.49 MiB | not measured |
| Extra VRAM @512×1536 | — | **+0.00 MiB** | +1248.68 MiB | not measured | not measured |
| Peak device @512×1536 | 6583.5 MiB | 5761.5 MiB | **7965.5 of 8187.5 MiB** ⚠️ | not measured | not measured |
| Median latency @512×512 | 3.248 s | 1.208–3.021 s (step-count artefact) | 3.35–3.47 s | 3.436 s | not measured |
| Bounded below (scale→baseline) | n/a | n/a | **12/12 byte-identical** | not tested | not measured |
| Monotone influence | n/a | 6/6 conditions | 6/6 conditions | not applicable (1 level) | not measured |
| Usable mid-range (ref ≥3 & prompt ≥3) | n/a | yes (0.6–0.65) | yes (0.4–0.6) | yes (0.55) | not measured |
| Human `originality` mean @512×512 | 4.00 (n=1) | **3.12 (n=8)** | **4.11 (n=9)** | 4.00 (n=1) | not measured |
| Human `copy_or_overfitting_risk` | not scored | **3.12 (n=8)** | **4.33 (n=9)** | 4.00 (n=1) | not measured |
| Near-copy flags (dHash ≤ 6) | n/a | **6, all @512×1536** | **0** | 0 | not measured |
| Output geometry coupling | none | **reference forced into output resolution** | independent (224 px CLIP crop) | independent | needs a control map |
| New dependency | none | none | none | none | opencv (~700 MiB) |

**The decisive row is the near-copy count.** Both methods are genuinely controllable — all four
controllability conditions met by each — so the choice is about cost, not capability. img2img is
free in VRAM but produced **every** near-copy flag in the milestone, three at dHash 0–1
(perceptually indistinguishable from the reference), **at the deck geometry the product ships**,
because it forces the reference into the output resolution and nothing is cropped when the aspect
already matches.

⚠️ **IP-Adapter at 512×1536 is feasible but memory-critical: ~222 MiB spare.** This is never to be
described as comfortable headroom, and **a combined SD 1.5 + LoRA + IP-Adapter smoke test at
512×1536 is a mandatory gate** before Prototypes 3–4 rely on the stack (risk R12).

**img2img is retained as a documented zero-extra-VRAM fallback**, not the default path.
**ControlNet was compared on criteria only and never measured** — it conditions on structural edges
rather than on an artwork reference's style and content; deferred, not rejected, for Prototype 5.

Full reasoning, with objective measurements and human scores reported in separate sections:
→ `docs/decisions/DR-008-reference-conditioning-method.md`

---

## ML method feasibility screening — LoRA now MEASURED (DR-009)

**Update 2026-08-04:** the LoRA row below is no longer a hypothesis. Prototype 3 measured it
across 8 experiments and 13 runs, and **DR-009 selects LoRA for Prototypes 4–5**. The other
rows remain screening judgements: from-scratch and full fine-tuning are documented
comparisons that were **never run**, and DreamBooth / Textual Inversion remain Prototype 4
candidates. DR-009 states that evidence limitation explicitly and does **not** claim LoRA is
objectively superior to methods that were never measured.

| Method | 8 GB VRAM feasibility | Empirical test |
|---|---|---|
| Training diffusion model from scratch | Infeasible (multi-GPU-weeks class of compute); documented comparison only — **not measured** | Literature analysis in report |
| Full fine-tuning | Marginal at best; AdamW holds two fp32 moments per trained parameter, ~6.9 GB of optimizer state alone for SD 1.5's ~860 M UNet parameters — **not measured** | Documented calculation; no full run planned |
| DreamBooth | Possible with heavy optimization; subject-driven, less suited to style — **not measured** | Compared in Prototype 4 if time allows |
| Textual Inversion | Feasible (tiny trainable footprint); limited style capacity — **not measured** | Candidate comparison in Prototype 4 |
| **LoRA** | **MEASURED and SELECTED (DR-009).** Rank 8 / alpha 8 on UNet attention, tier 0, no escalation: **3133 MiB @512×512**, **5183 MiB @512×1536** of 8187.5 physical. 300 steps in 91 s. Marginal inference cost **+3.04 MiB**, independent of geometry | **Prototype 3 EXP-016…EXP-019 (done)**, Prototype 4 (styles) |
| img2img without training | Feasible; baseline that "custom training" must beat | Prototype 2 baseline |
| ControlNet | Feasible for inference conditioning | Prototype 2 if relevant |
| IP-Adapter | Feasible; strong reference-image conditioning candidate | Prototype 2 |
| One multi-style LoRA vs. separate LoRAs | Both feasible | Prototype 4 head-to-head (RQ5) |

## System shape (target, validated incrementally)

```
apps/web (React+Vite+TS, R3F 3D viewer)
   │  REST (JSON + multipart upload)
apps/api (FastAPI + Pydantic)
   │  in-process call
ml/inference (Diffusers pipeline: base model + LoRA + image conditioning)
ml/training (Accelerate+PEFT LoRA scripts, configs in ml/configs)
ml/dataset (validation, hashing, captions, splits, contact sheets)
```

Deployment candidates (decided later, RQ12): documented two-process local run vs. Docker Compose. See `docs/08-deployment-strategy.md`.
