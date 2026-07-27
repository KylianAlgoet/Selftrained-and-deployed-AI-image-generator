# Prototype overview

**Created:** 2026-07-27 · Each prototype gets a detailed document in `docs/prototypes/` when it starts, containing: research question/hypothesis, scope, acceptance criteria, implementation notes, real tests, actual results, evidence, conclusion, impact on next iteration, related commits. No prototype may be skipped.

| # | Prototype | Research question | Scope sketch | Draft acceptance criteria | Status |
|---|---|---|---|---|---|
| 0 | Static interactive 3D skateboard viewer | RQ9: deck UV mapping, orientation, dynamic textures | React+Vite+TS+R3F scene, self-created procedural deck (DR-005), orbit/zoom/reset, runtime texture swap | Deck renders; rotate/zoom/reset work; test decal maps with correct nose–tail orientation; texture swaps without reload | **completed 2026-07-27** — hypothesis confirmed, 13 tests passing, [results](prototypes/prototype-0.md), [evidence](evidence/prototype-0/) |
| 1 | Local base-model text-to-image benchmark | RQ2, RQ8: which base model fits 8 GB VRAM; aspect-ratio handling | Python 3.11 venv, pinned Diffusers stack, CUDA smoke test, fixed prompt/seed benchmark of candidate base models | CUDA verified; ≥ 2 base models benchmarked with measured VRAM/speed + rubric grid; aspect-ratio test recorded; EXP rows complete | not started |
| 2 | Text + reference-image conditioning | RQ6, RQ7: best conditioning method and its controllability | img2img vs. IP-Adapter (ControlNet if relevant) on fixed prompt+reference kit; strength sweeps | Reference influence visibly controllable; methods compared on rubric with fixed seeds; strength sweep documented; EXP rows complete | not started |
| 3 | Local LoRA smoke test | RQ1: is local LoRA training viable end-to-end on this machine | Tiny dataset, minimal steps, train → save → load → generate; measure VRAM/duration | Training completes without OOM; LoRA visibly affects output; peak VRAM + duration measured; reproducible via config + seed | not started |
| 4 | Style-learning experiments | RQ1, RQ4, RQ5: real style capture; multi-style vs. per-style | Train on the 3 curated styles; vary dataset size/rank/LR; multi-style vs. separate head-to-head | Each style distinguishable in fixed-seed grids; multi-vs-separate comparison scored; best config selected with justification; EXP rows complete | not started |
| 5 | Integrated MVP | Primary RQ end-to-end | FastAPI + validation/security, React UI, full generate flow, 3D preview with dynamic texture, download, reproducibility metadata | Full flow works locally: inputs → generation with LoRA + reference → 3D preview correct orientation → download; errors/loading handled; seeds reproduce | not started |

Statuses update as work happens; completed prototypes link their evidence and commits here.
