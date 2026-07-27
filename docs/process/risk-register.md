# Risk register

**Created:** 2026-07-27 · Reviewed at every milestone. Likelihood/impact: low / medium / high. Status: open / mitigating / closed / occurred.

| ID | Risk | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|
| R1 | 8 GB VRAM insufficient for chosen base model/training config | medium | high | SD 1.5-class first; 8-bit optimizers, gradient checkpointing, low rank; kohya fallback (DR-004); measure in Prototype 3 before committing | open |
| R2 | Training time exceeds schedule | medium | high | Smoke test before every long run; small datasets first; fixed time-boxes per experiment; prefer fewer well-documented runs | open |
| R3 | Dataset licensing gaps (unusable or undocumentable sources) | medium | high | Public-domain/CC0/self-created only; licence field mandatory in manifest before training; no brand/artist scraping | open |
| R4 | 19-day resit timeline with no buffer | high | high | Original plan front-loads critical path; MVP scope guarded (no accounts/payments/webshop); report written in parallel from M6; daily process-log checkpoints | open |
| R5 | Windows CUDA/tooling friction (PyTorch install, Python 3.14 default, PS 5.1 quirks) | medium | medium | Python 3.11 venv mandated by audit; pin versions; verify `torch.cuda.is_available()` before any training | open |
| R6 | Scope creep beyond MVP | medium | medium | Explicit non-goals in project brief; every addition needs a planning change-log entry | open |
| R7 | Single-machine data loss (no remote backup until push approved) | low | high | Remote push approved 2026-07-27; Phase 0 pushed to origin/main; validated commits pushed after every milestone | mitigating |
| R8 | Model quality plateau (styles not learnable from small dataset) | medium | high | Prototype 4 compares dataset sizes and configs; img2img no-training baseline exists as documented fallback narrative; honest limitation reporting is itself valid research output | open |
| R9 | Evaluation subjectivity undermines conclusions | medium | medium | Fixed-seed grids, pre-defined 1–5 rubric, identical prompts across comparisons, all scores recorded in registry | open |
| R10 | 3D deck model licensing/UV problems | low | medium | Prototype 0 validates model + UV mapping first; fallback: self-modelled simple deck geometry | open |

## Review log

| Date | Reviewed by | Changes |
|---|---|---|
| 2026-07-27 | Phase 0 session | Initial register created |
| 2026-07-27 | Post-push update | R7 downgraded to low/mitigating: remote operations approved, Phase 0 pushed to origin/main |
