# Research plan

**Created:** 2026-07-27 · **Status:** active · All results/conclusions below start empty and are filled only from executed experiments (see `experiments/registry.csv`).

## Primary research question

> **How can a locally fine-tuned diffusion model, conditioned on both a text prompt and a reference image, generate skateboard-decal artwork in multiple visually distinct styles with reproducible quality on consumer hardware (8 GB VRAM)?**

## Working hypothesis (not a decision)

A LoRA fine-tune of a pretrained SD 1.5-class diffusion model, trained locally per style (or as one multi-style LoRA), combined with an image-conditioning method (img2img, IP-Adapter, or ControlNet), will produce acceptable multi-style decal artwork within the hardware and time budget. **This remains a hypothesis until Prototypes 1–4 provide benchmark evidence.**

## Subquestions

Each subquestion follows: hypothesis → method → criteria → experiment → result → conclusion → effect on next iteration. Results and conclusions are recorded in the linked prototype/experiment documents as they happen.

| ID | Subquestion | Hypothesis | Method | Answered by |
|---|---|---|---|---|
| RQ1 | Which fine-tuning method (from scratch, full fine-tune, DreamBooth, Textual Inversion, LoRA) is feasible and most effective on 8 GB VRAM? | LoRA is the only method that fits VRAM + 19-day budget while capturing style | Literature/spec comparison + empirical smoke tests of the shortlisted methods | Prototype 3, EXP records |
| RQ2 | Which pretrained base model is feasible on the audited hardware (SD 1.5 vs. SDXL vs. smaller)? | SD 1.5-class at 512px runs and trains; SDXL inference works but training is marginal | Benchmark identical prompts/seeds; measure VRAM, speed, quality rubric | Prototype 1 |
| RQ3 | How can a legally usable custom dataset be created (provenance, licences)? | Public-domain/CC0 sources + self-created images can cover 3 styles | Source audit per style, manifest with licence fields, validation scripts | Dataset milestone |
| RQ4 | How many images per style and what quality/caption standards are needed? | 20–50 curated, well-captioned images per style suffice for LoRA style learning | Vary dataset size/quality between LoRA runs, compare rubric scores | Prototype 4 |
| RQ5 | Is one multi-style LoRA or separate style-specific LoRAs better? | Separate LoRAs give cleaner style separation at this dataset size | Train both configurations on the same data, fixed-seed comparison grid | Prototype 4 |
| RQ6 | How should text and reference-image conditioning be combined (img2img, ControlNet, IP-Adapter)? | IP-Adapter or img2img strength control gives usable reference influence without extra training | Same prompt/reference across methods; rubric on reference influence vs. prompt adherence | Prototype 2 |
| RQ7 | Which generation parameters (steps, CFG, strength, rank, LR) most influence decal quality? | Reference strength and CFG dominate perceived control; LoRA rank ≥ 8 needed for style | Controlled parameter sweeps with fixed seeds | Prototypes 2–4 |
| RQ8 | How should the skateboard-deck aspect ratio (~1:3.6) be handled in a square-biased model? | Generate at supported ratio then outpaint/crop, or train/generate at tall ratios directly | Compare tall-ratio generation vs. post-crop on composition rubric | Prototypes 1, 5 |
| RQ9 | How is the decal correctly mapped onto a 3D deck (UV mapping, orientation, dynamic texture updates)? | A UV-mapped deck model in Three.js/R3F can swap textures at runtime with correct nose–tail orientation | Build viewer with test texture; verify orientation and live updates | Prototype 0 |
| RQ10 | How should generated decals be evaluated objectively and reproducibly? | A fixed-prompt/fixed-seed grid + 1–5 rubric across 9 dimensions gives comparable scores | Define rubric before experiments; apply identically to all runs | All prototypes |
| RQ11 | What are the copyright, privacy, bias, and ethics constraints and mitigations? | Licence-tracked dataset + no scraping of brands/artists + upload consent note mitigates main risks | Licence audit, bias check of dataset composition, documented limitations | Dataset milestone, report |
| RQ12 | What deployment/demonstration setup is reproducible on this hardware? | Local Docker Compose (or documented two-process local run) is reproducible and demoable | Clean-clone test following only the README | Deployment milestone |

## Method principles

- Comparisons use **fixed prompts, reference images, seeds, resolutions, and settings** so differences are attributable to the variable under test.
- Every experiment is registered in `experiments/registry.csv` (EXP-###) with config, hardware readings, duration, output paths, rubric scores, conclusion, and commit.
- Failures are documented with the full failure template (see `.claude/rules/honesty-and-evidence.md`) — a failed run that answers a subquestion is a valid result.
- Evaluation rubric (1–5 per dimension): prompt adherence, style consistency, reference influence, visual quality, decal suitability, composition, artefacts, originality, diversity (defined in `docs/05-experiment-methodology.md`).

## Alternatives that must be compared (from the assignment)

Training from scratch · full fine-tuning · DreamBooth · Textual Inversion · LoRA · image-to-image without custom training · ControlNet (where relevant) · IP-Adapter or another image-conditioning method · one multi-style LoRA · separate style-specific LoRAs. The comparison matrix lives in `docs/03-architecture.md` (feasibility screening) and is settled empirically in Prototypes 1–4.
