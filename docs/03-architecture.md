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

**Decision:** Hugging Face Diffusers + PEFT + Accelerate (+ Transformers, Safetensors) as the toolchain. kohya-ss remains the documented fallback if Diffusers LoRA training underperforms on VRAM in Prototype 3. **The fine-tuning method itself (LoRA vs. alternatives) is still NOT decided here** — see feasibility screening below. **The base model WAS decided on 2026-07-30 with measured data → DR-007, section D-E below.** → `docs/decisions/DR-004-ml-toolchain.md`

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

## ML method feasibility screening — HYPOTHESIS ONLY

Screening of the assignment-mandated alternatives against the audited constraint (8 GB VRAM, ~19 days). This narrows what gets empirical testing; it decides nothing final.

| Method | 8 GB VRAM feasibility (screening) | Empirical test |
|---|---|---|
| Training diffusion model from scratch | Infeasible (multi-GPU-weeks class of compute); documented comparison only | Literature analysis in report |
| Full fine-tuning | Marginal at best (optimizer states exceed VRAM for SD-class UNets) | Documented calculation; no full run planned |
| DreamBooth | Possible with heavy optimization; subject-driven, less suited to style | Compared in Prototype 4 if time allows |
| Textual Inversion | Feasible (tiny trainable footprint); limited style capacity | Candidate comparison in Prototype 4 |
| **LoRA** | **Feasible; primary hypothesis** | **Prototype 3 (smoke test), Prototype 4 (styles)** |
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
