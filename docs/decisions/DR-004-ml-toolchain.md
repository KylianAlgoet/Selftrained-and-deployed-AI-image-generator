# DR-004: ML toolchain — Hugging Face Diffusers + PEFT + Accelerate

**Date:** 2026-07-27 · **Status:** accepted as toolchain; **fine-tuning method and base model remain open hypotheses** (RQ1/RQ2)

## Context
Local training and inference must be scriptable, reproducible (configs + seeds in the experiment registry), memory-efficient on 8 GB VRAM, and callable from FastAPI. GUI-only workflows cannot produce the required reproducibility evidence.

## Alternatives
1. **Hugging Face Diffusers + PEFT + Accelerate** (+ Transformers, Safetensors)
2. **kohya-ss sd-scripts**
3. **ComfyUI-based pipeline**

## Criteria and evaluation
Weighted matrix in `docs/03-architecture.md` (D-D): scriptable reproducibility (5), FastAPI integration (5), 8 GB memory options (4), evidence value / code transparency (4), community-validated LoRA quality (3). Diffusers 98/105, kohya 83, ComfyUI 54.

## Decision
Diffusers + PEFT + Accelerate as the toolchain, with Python 3.11 (PyTorch does not support the installed 3.14 default — see environment audit).

## Consequences
- kohya-ss is the documented fallback if Prototype 3 shows Diffusers LoRA training does not fit 8 GB VRAM acceptably.
- Versions are pinned at first install (after Phase 0), recorded in the process log.
- This record does **not** choose LoRA over alternatives or SD 1.5 over SDXL — those are settled empirically in Prototypes 1–4.
