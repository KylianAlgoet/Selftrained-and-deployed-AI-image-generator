# Risk register

**Created:** 2026-07-27 · Reviewed at every milestone. Likelihood/impact: low / medium / high. Status: open / mitigating / closed / occurred.

| ID | Risk | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|
| R1 | 8 GB VRAM insufficient for chosen base model/training config | medium | high | **Partly quantified 2026-07-30 (Prototype 1).** For *inference* the risk is now measured, not assumed: SD 1.5 needs 2675 MiB @512 and 3892 MiB @512×1536, leaving ~5.5 GB headroom; SDXL needs 10738 MiB @1024 against 8188 MiB physical and only completes via silent WDDM host-memory spill. SD 1.5 selected (DR-007), which is the low-risk branch. **Training remains unmeasured** — the SDXL figures are direct evidence that LoRA at 1024 is not viable here, so Prototype 3 must smoke-test LoRA VRAM before any long run; 8-bit optimizers, gradient checkpointing, low rank, kohya fallback (DR-004) still stand | mitigating (inference measured; training still open) |
| R2 | Training time exceeds schedule | medium | high | Smoke test before every long run; small datasets first; fixed time-boxes per experiment; prefer fewer well-documented runs | open |
| R3 | Dataset licensing gaps (unusable or undocumentable sources) | medium | high | Public-domain/CC0/self-created only; licence field mandatory in manifest before training; no brand/artist scraping | open |
| R4 | 19-day resit timeline with no buffer | high | high | Original plan front-loads critical path; MVP scope guarded (no accounts/payments/webshop); report written in parallel from M6; daily process-log checkpoints | open |
| R5 | Windows CUDA/tooling friction (PyTorch install, Python 3.14 default, PS 5.1 quirks) | medium | medium | **Occurred and resolved 2026-07-30.** The install did hit a real blocker: the venv's pip 22.3 cannot resolve modern torch wheels at all (rejects underscore-normalised metadata names); upgrading to pip 26.2 fixed it. `torch.cuda.is_available()` now verified (EXP-001, VERDICT PASS) with torch 2.13.0+cu126. Two audit corrections recorded: driver is 610.88 not 610.74, and `nvidia-smi`'s CUDA version is the driver's max supported API, not a toolkit PyTorch must match. Exact install command and pins in `ml/requirements-inference.txt` | closed (recurrence covered by the pinned requirements file) |
| R6 | Scope creep beyond MVP | medium | medium | Explicit non-goals in project brief; every addition needs a planning change-log entry | open |
| R7 | Single-machine data loss (no remote backup until push approved) | low | high | Remote push approved 2026-07-27; Phase 0 pushed to origin/main; validated commits pushed after every milestone | mitigating |
| R8 | Model quality plateau (styles not learnable from small dataset) | medium | high | Prototype 4 compares dataset sizes and configs; img2img no-training baseline exists as documented fallback narrative; honest limitation reporting is itself valid research output | open |
| R9 | Evaluation subjectivity undermines conclusions | medium | medium | Fixed-seed grids, pre-defined 1–5 rubric, identical prompts across comparisons, all scores recorded in registry | open |
| R10 | 3D deck model licensing/UV problems | low | medium | Prototype 0 validates model + UV mapping first; fallback: self-modelled simple deck geometry | closed (Prototype 0: procedural self-made geometry, DR-005) |
| R11 | Third-party model/dataset hosting becomes unavailable mid-project (gating, WAF, withdrawal) | **high** | medium | **Already occurred three times:** Digital Comic Museum (Cloudflare) and Art Institute of Chicago (CDN 403) in M2; `stabilityai/stable-diffusion-2-1-base` (HTTP 401 gating) in M3. Also note the original `runwayml/stable-diffusion-v1-5` repo was withdrawn, so a mirror is used. Mitigations: pin immutable commit SHAs for every model actually used; keep weights in the local HF cache once downloaded; verify availability at the moment of use rather than assuming; document each block as a first-class result and a reproducibility caveat; never substitute a source or model without explicit approval | occurred (mitigating) |

## Review log

| Date | Reviewed by | Changes |
|---|---|---|
| 2026-07-27 | Phase 0 session | Initial register created |
| 2026-07-27 | Post-push update | R7 downgraded to low/mitigating: remote operations approved, Phase 0 pushed to origin/main |
| 2026-07-30 | Prototype 1 (M3) | R1 → mitigating (inference VRAM measured; SD 1.5 selected as the low-risk branch; training still unmeasured). R5 → closed (occurred as a pip-22.3 blocker, resolved; CUDA verified). **R11 added**: third-party model/dataset hosting can become unavailable mid-project — two of five approved dataset sources were blocked in M2 and one of three approved base models in M3 |
