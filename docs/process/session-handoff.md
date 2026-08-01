# Session handoff

**Last updated:** 2026-08-01 (M4 / Prototype 2 execution session, under Opus 5)

## M4 (Prototype 2 — text + reference-image conditioning): COMPLETE

**Human review passed 2026-08-01; conditioning method selected in DR-008.** Issue #5 closure, board
move to Done, and the push to `origin/main` follow this commit — verify their real state with
`gh issue view 5` and `git status -sb` rather than trusting this line.

**Decision (DR-008):** **standard IP-Adapter selected** as the primary reference-conditioning
method for Prototypes 3–5 (`h94/IP-Adapter`, `ip-adapter_sd15.safetensors` @ `018e402774`).
**Default scale 0.55**, user-adjustable **0.40–0.60**; higher values only with an explicit warning
that prompt authority falls and pseudo-text / source-like composition increase. **img2img is a
documented zero-extra-VRAM fallback, not the default path.** IP-Adapter-Plus not selected.
ControlNet stays criteria-only, deferred to Prototype 5 for layout control.

### ⚠️ Two things the next session must not soften

1. **R12 (open, high/high) — the combined stack may not fit.** IP-Adapter alone at 512×1536 peaks
   at **7965.5 MiB of 8187.5 MiB physical, about 222 MiB spare.** **Never describe this as
   comfortable headroom.** A **combined SD 1.5 + selected LoRA + IP-Adapter smoke test at 512×1536
   is a mandatory acceptance item for M5** — it is in the M5 planning row as scope, dependency and
   required evidence. If it fails, record the failure as its own result row and test the approved
   memory tiers in separate runs. **Never silently reduce geometry to make it pass.**
2. **R13 (occurred, mitigated) — img2img reproduces the reference at the deck format.** All six
   copy-risk flags in M4 (dHash ≤ 6) are img2img at 512×1536, three at **dHash 0–1**. Median dHash
   for img2img at medium is 27 @512×512 but **5 @512×1536**. Keep the dHash ≤ 6 flag and the
   copy-risk sheet in every future evaluation. Prototype 5 must not expose an img2img mode at the
   deck format without this warning.

### Measured results (299 generations, zero failures, tier 0 throughout)

| geometry | text-only | img2img | IP-Adapter | Plus |
|---|---|---|---|---|
| 512×512 | 2675.38 MiB | **2675.38 (+0.00)** | 3924.07 (+1248.69) | 3978.87 |
| 512×1536 | 3892.01 MiB | **3892.01 (+0.00)** | 5140.69 (+1248.68) | not measured |

- **img2img costs exactly zero extra VRAM**; IP-Adapter's ~1249 MiB overhead is **identical at both
  geometries**, because its scale acts on attention rather than on output size.
- **Latency trap:** img2img wall-clock *falls* as influence rises (3.021 s → 1.208 s) because
  diffusers runs `int(steps × strength)` steps. Per-effective-step cost is flat at 0.112–0.134.
  **Fewer steps, not faster ones** — never quote img2img as intrinsically faster.
- **Process isolation accepted in full:** 6/6 spot-check pairs at +0.000 % against a 2 % tolerance
  pre-declared in code.
- **Lower bound met exactly:** 12/12 IP-Adapter runs at `scale=0.0` byte-identical to the text-only
  baseline; 12/12 M4 baselines byte-identical to Prototype 1's EXP-002, so **M3 and M4 figures are
  directly comparable**.
- **Monotone in 6/6 conditions for both methods.** IP-Adapter-Plus is *not applicable* (one level
  by design), never "failed".

### Human scores (Kylian, 2026-08-01) — read before re-scoring anything

Recorded at **aggregate (method × level × resolution)**, which is exactly the form's row granularity,
so unlike M3 they are entered directly rather than marked "not individually scored".
`docs/evidence/EXP-015-scoring/human-scores.csv` is authoritative; the form and probe are generated
from it.

**29 cells are NOT SCORED. A blank is never a zero and must never be back-filled.** They are
excluded from every mean and the surviving `n` is printed beside each figure.

- `reference_influence` / `copy_or_overfitting_risk` blank for **text-only** — it uses no reference.
- `diversity_across_seeds` has **n=1 per method** — not load-bearing, do not lean on it.
- **`text-only` at 512×1536 is entirely unscored. Do not substitute an M3 value** — the M3 review
  used different sheets and answered a different question.

Means at 512×512 (blanks excluded): originality **img2img 3.12 (n=8) vs ip-adapter 4.11 (n=9)**;
copy risk **3.12 vs 4.33**. At the deck format img2img scored originality 1 / copy risk 1;
IP-Adapter 4 / 4.

### M4 facts a new session must know

- `.venv/Scripts/python.exe -m pytest` → **123 tests**; frozen-kit fingerprint `c40749bc…` unchanged.
- **No linter is installed** (`ruff` absent). pytest is the validation gate — never claim a lint step ran.
- Adapter cache: `h94/IP-Adapter` **2453.8 MiB**, outside the repo. Both adapter and image encoder are
  pinned to `018e402774…`; **diffusers 0.39.0 does not forward `revision` to the image encoder**, so
  the runner registers a pinned encoder itself before `load_ip_adapter`. Do not remove that workaround.
- **Measurement instrumentation must never enter the workload it measures.** Phase 1 (generation) and
  Phase 2 (similarity) are separate processes; pytests enforce the import boundary in both directions.
- Regenerate anything with `scripts/`: `build_reference_kit.py` · `run_reference_conditioning.py`
  (`--dry-run`, `--only`, `--start-at`) · `evaluate_similarity.py` · `build_p2_analysis.py` ·
  `build_p2_contact_sheets.py` · `build_p2_scoring_form.py` · `summarise_p2_human_scores.py`.
- `deliverables/` is **git-ignored** — a derived upload package duplicating tracked evidence.

## Prior state (M3, completed 2026-07-30)

Phase 0, public planning (issues #1–#12), **M1 (Prototype 0)**, and **M2 (dataset)** complete and pushed.

**M3 (Prototype 1 — base-model benchmark): COMPLETE.** Human review passed 2026-07-30; issue #4 closed as completed; board shows M3 Done.

**Decision (DR-007):** **SD 1.5 selected** as the base model for Prototypes 2–5 (pinned `451f4fe1`). SDXL base 1.0 is the **visual-quality winner at native 1024×1024** but is retained as a benchmark, not the production model. **Deck format: direct 1:3 at 512×1536**; square-crop rejected. Third candidate SD 2.1 base **blocked** (HTTP 401), so the comparison rests on **two** measured candidates — a limitation that must be stated in the report.

## Uncommitted changes

None expected at handoff — verify with `git status`.

## Latest commits (M3 sequence, 2026-07-30)

```
5bf0f40 docs(process): close prototype 1 across planning, risks, testing, and traceability
67ca695 docs(decisions): select stable diffusion 1.5 as the base model for prototypes 2-5
34b05d8 docs(experiments): record human rubric scores at the granularity actually used
3765c5c docs(experiments): correct the literal-decal observation as resolution-dependent
5994305 docs(experiments): record aspect-ratio findings and prototype 1 evidence
bffb813 feat(benchmark): add deck aspect-ratio comparison with per-strategy isolation
8829664 docs(experiments): record base-model benchmark measurements for prototype 1
e25f1e0 feat(benchmark): add benchmark orchestrator and blank rubric scoring form
eae6e41 feat(benchmark): add base-model benchmark runner with vram and timing measurement
f646ee9 feat(evaluation): add frozen prompt and seed kit with hash-locked tests
1d51ccc feat(inference): add cuda environment smoke test with json evidence
37650b6 chore(ml): pin pytorch and diffusers inference dependencies for prototype 1
e5684f1 fix(dataset): rename retro-comic style to retro-poster to match wpa poster evidence
```

## Human scores (Kylian, 2026-07-30) — read before re-scoring anything

Recorded at **aggregate model/track level**, not per unit. `docs/evidence/EXP-006-scoring/human-scores.md` is authoritative; per-unit cells in `scoring-form.md` read "not individually scored" **on purpose** — do not back-fill them with the aggregates.

- Track A (both @512): SD 1.5 and SDXL scored **identically** 3/3/4/3/3/4/3.
- Track B native: SD 1.5 3/3/4/3/3/4/3 · SDXL **4/5/5/4/4/4/3**.
- `reference_influence` = **N/A** until Prototype 2. `diversity_across_seeds` = **not scored**, because the review sheets showed only the fixed seed-42 comparison. **Do not invent a value** — a multi-seed sheet is needed first.

## Measured results (all at tier 0; no escalation needed)

All at memory tier 0; no tier escalation was needed anywhere.

| Experiment | Result |
|---|---|
| EXP-001 | CUDA PASS. torch 2.13.0+cu126, bundled runtime 12.6, driver 610.88, RTX 4060 Laptop sm_89, 8187.5 MiB |
| EXP-002 SD 1.5 | 30/30 ok. 512×512 median **4.07 s**, alloc 2675 MiB. 512×768 median 6.81 s, alloc 2979 MiB |
| EXP-003 SD 2.1 base | **BLOCKED** — HTTP 401, repository gated. Two candidates by Kylian's decision |
| EXP-004 SDXL base | 30/30 ok. 512×512 median 16.51 s, alloc 7859 MiB. 1024×1024 median **118.73 s**, alloc **10738 MiB** |
| EXP-005 aspect ratio | 24/24 ok. 512×1536 median 15.24 s in 3892 MiB; square-crop leaves only **170×512 usable** |

**Do not report SDXL as "works on 8 GB".** Its 1024×1024 peak allocated (10738 MiB) and reserved (14510 MiB) exceed the 8187.5 MiB physical VRAM; WDDM spilled silently into host RAM instead of raising a CUDA OOM, so nothing failed and no tier escalated. It degraded quietly. ~29× SD 1.5's cost per 512 px image.

## Facts a new session must know

- Repo root: `C:\Expert Lab\Selftrained-and-deployed-AI-image-generator`; **8 GB VRAM** is the hard constraint.
- **Python:** `.venv` at repo root is **Python 3.11** (`.venv/Scripts/python.exe`). Never use system Python 3.14. Run tests with `.venv/Scripts/python.exe -m pytest` (66 tests, `pytest.ini`, testpaths=ml). Set `PYTHONIOENCODING=utf-8` for scripts that print non-ASCII.
- **pip 22.3 shipped in the venv cannot resolve torch** (rejects underscore-normalised wheel metadata). It was upgraded to 26.2; do not downgrade.
- **PyTorch install is NOT from PyPI:** `--index-url https://download.pytorch.org/whl/cu126`, `torch==2.13.0+cu126 torchvision==0.28.0+cu126`. See `ml/requirements-inference.txt` for the full rationale. `nvidia-smi`'s CUDA version is the **driver's max supported API**, not a toolkit to match. No xformers (torch SDPA is the Diffusers default). No nightlies.
- **Frozen evaluation kit** in `ml/evaluation/prompt_kit.py`, fingerprint `c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228`, hash-locked by pytest. **Never edit it to fix a benchmark** — record deviations per run instead. Changing it invalidates comparability with every earlier experiment.
- **One configuration per OS process** whenever VRAM or timing is measured. Adopted after a real contamination incident: the caching allocator retains its pool across `reset_peak_memory_stats()`, which corrupted EXP-005's first run. See `docs/evidence/EXP-005/measurement-methodology-correction.md`.
- **Model revisions are pinned to commit SHAs:** SD 1.5 `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`, SDXL `462165984030d82259a11f4367a4eed129e94a7b`. HF cache lives outside the repo at `C:\Users\kylia\.cache\huggingface` (~14 GB for SDXL alone).
- **`outputs/` is git-ignored** — 84 full-resolution PNGs live there. Only manifests, summaries, and contact sheets (≤300 KB) are committed.
- **Style identifiers** are `retro-poster`, `minimal-geometric`, `ukiyo-e`. `retro-poster` was renamed from `retro-comic` on 2026-07-30 because the material is WPA silkscreen posters, not comics. Never reintroduce `retro-comic`; pytest regression guards enforce this.
- **Dataset:** 148 items, splits 124/17/7, manifest `data/manifests/dataset-v1.csv`, raw images git-ignored.
- `apps/web`: React 19 + Vite 6.4.3 + R3F viewer (M1); `npm run dev/test/build`.

## Blockers

- None. M3 is closed.

## Next action

**M4 — Prototype 2: text + reference-image conditioning** (issue #5, planned Aug 4–6; can start early — roughly four days of critical-path buffer exist). Start in **Plan mode**, per the project's milestone rule.

Scope reminders for M4:
- Target **SD 1.5** per DR-007, with ~5.5 GB VRAM headroom at 512×512.
- Compare **img2img vs IP-Adapter** (ControlNet if relevant) on a fixed prompt + reference kit; strength sweeps with fixed seeds (RQ6, RQ7).
- Prototype 2 is where `reference_influence` becomes scoreable for the first time.
- Reuse the **frozen kit** (`c40749bc…`) so results stay comparable to the Prototype 1 baselines; extend it with reference images rather than editing it, and expect the hash-lock test to require a deliberate, documented update if the kit itself changes.
- Two open items inherited from M3: build a **multi-seed contact sheet** so `diversity_across_seeds` can finally be scored, and address the possible **repetition/vertical stretching** at 512×1536 that Kylian flagged.
- Two M2 dataset findings still awaiting M4 decisions: framed/matted scans in `retro-poster`, and the text-dominated source material (see `docs/04-dataset-methodology.md`).
