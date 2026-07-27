# Architecture research and decisions

**Created:** 2026-07-27 · Decisions here follow the 13-step research loop. Phase 0 decides only what must be decided before Prototype 0; ML method choices remain open hypotheses until Prototypes 1–4 deliver benchmarks.

Scoring: each criterion weighted 1–5; each alternative scored 1–5; weighted totals justify (not replace) the reasoned decision. Scores are the student/agent's documented judgement given the environment audit (`docs/technical/environment-audit.md`) and the 19-day timeline — hardware-dependent ML scores will be **revised with measured data** after Prototypes 1 and 3.

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

**Decision:** Hugging Face Diffusers + PEFT + Accelerate (+ Transformers, Safetensors) as the toolchain. kohya-ss remains the documented fallback if Diffusers LoRA training underperforms on VRAM in Prototype 3. **The fine-tuning method itself (LoRA vs. alternatives) and the base model are NOT decided here** — see feasibility screening below. → `docs/decisions/DR-004-ml-toolchain.md`

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
