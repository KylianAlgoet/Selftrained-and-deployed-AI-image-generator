# Session handoff

**Last updated:** 2026-08-01 (M4 / Prototype 2 execution session, under Opus 5)

## M4 (Prototype 2 — text + reference-image conditioning): 🛑 AT THE HUMAN-REVIEW GATE

**All autonomous M4 work is complete. Stopped for Kylian's visual review and rubric scores.**

👉 **Start here: `docs/evidence/prototype-2/HUMAN-REVIEW-GATE.md`** — it lists every sheet to
open in order, the unscored technical summary, the rubric, and the blank forms.

Nothing is scored, no method is selected, DR-008 is unwritten, `experiments/registry.csv` is
not yet updated (its `evaluation`/`conclusion` fields need the scores), issue #5 is open, M4 is
not Done, and **nothing has been pushed**.

**EXP-007 adapter gate: PASSED** (hard gate — nothing downstream ran until it was green).
IP-Adapter and its CLIP image encoder both load at the pinned revision
`018e402774aeeddd60609b4ecdb7e298259dc729`; **16 of 32** UNet attention processors are
`IPAdapterAttnProcessor2_0`, read back from the live UNet. Measured cost against bare
SD 1.5, each in its own process: **+1248.69 MiB peak allocated** (2675.38 → 3924.07),
latency +0.164 s. Peak device used 5695.5 MiB of 8187.5 MiB physical, tier 0, no overflow.

**The eight M4 Phase-1 commits (local only, never pushed):**

```
dd80659 feat(evaluation): add prototype 2 scoring form with aggregate-level rows
1985d8d docs(experiments): record offline similarity indicators and the process-isolation check
aaa0e06 feat(evaluation): add offline similarity indicators for reference conditioning
d15dc17 docs(experiments): record conflicting-reference and deck-format conditioning measurements
331c6aa docs(experiments): record reference-strength sweep measurements for both methods
9053c71 docs(experiments): record the ip-adapter environment gate for prototype 2
9f0d664 feat(inference): add reference-conditioning runner for img2img and ip-adapter
ce681b7 feat(inference): add reference-image registry and conditioning schema for prototype 2
```

**Interruption to be aware of.** A first orchestrator run was killed mid-EXP-009 by a
usage-limit cutoff. Stages 1–4 (EXP-008, EXP-008b) had completed; EXP-009's partial file
was **rewritten from scratch** on resume, because each runner deletes its own results file
at start rather than appending twice. `--start-at N` was added to
`scripts/run_reference_conditioning.py` for exactly this. Nothing was recovered by hand and
no partial data was kept.

**Measured: 299 generation rows, EXP-007 → EXP-013. Zero failures, zero timeouts, memory
tier 0 throughout, no escalation anywhere.** 16 fresh OS processes.

**VRAM — peak allocated per run (fp16, tier 0):**

| geometry | text-only | img2img | IP-Adapter | IP-Adapter-Plus |
|---|---|---|---|---|
| 512×512 | 2675.38 MiB | **2675.38 (+0.00)** | 3924.07 (+1248.69) | 3978.87 (+1303.49) |
| 512×1536 | 3892.01 MiB | **3892.01 (+0.00)** | 5140.69 (+1248.68) | not measured |

**img2img costs exactly zero extra VRAM** at both geometries. **IP-Adapter's overhead is the
same fixed ~1248.7 MiB at both**, consistent with its scale acting on attention rather than on
output size.

⚠️ **Deck-format headroom:** IP-Adapter at 512×1536 reached **7965.5 MiB peak device used of
8187.5 MiB physical — about 222 MiB spare.** All 9 runs succeeded and no overflow flag fired,
but this is not headroom to call comfortable, and **a LoRA stacked on top in Prototypes 3–4
cannot be assumed to fit.** Plan M5/M6 with that in mind.

**Latency (median s):** 512×512 — text-only 3.248 · img2img 3.021 (s=0.90) → 1.208 (s=0.30) ·
IP-Adapter ~3.35–3.47 · Plus 3.436. 512×1536 — text-only 11.837 · img2img 7.980 · IP-Adapter 12.022.

**The img2img latency trap is confirmed, not assumed:** wall-clock *falls* as influence *rises*,
purely because diffusers runs `int(steps × strength)` steps. Seconds-per-effective-step stays
flat at 0.112–0.134, so the speed advantage is **fewer steps, not faster ones**.

**Process isolation ACCEPTED in full:** 6/6 clean-process spot-check pairs at **+0.000 %**
against a 2 % tolerance pre-declared in code before any measurement.

**EXP-010 lower bound — both comparisons maximally positive:** **12/12** IP-Adapter runs at
`scale=0.0` are byte-identical to the text-only baseline, and **12/12** M4 baselines are
byte-identical to Prototype 1's EXP-002 hashes (cross-milestone repeatability; the M4 baseline
provably *is* the M3 baseline).

**Monotonicity (EXP-014, CPU, 297 images in 393 s):** median overall reference-image similarity
rises with influence level in **6/6 conditions for img2img and 6/6 for IP-Adapter** — both clear
the ≥3-of-4 bar. IP-Adapter-Plus is *not applicable* (medium level only by design), not a failure.

⚠️ **Copy risk — the finding to look at:** all **6** flagged outputs (dHash ≤ 6) are **img2img
at 512×1536** on the two references that are natively 512×1536 (R2, R4), three of them at
**dHash 0–1, i.e. perceptually indistinguishable from the reference.** Median dHash for img2img
at medium is **27 at 512×512 but 5 at 512×1536**. Mechanism: img2img forces the reference into
the output resolution, so when the aspect already matches, nothing is cropped and denoising at
`strength=0.65` starts from an essentially intact copy. **This is the production geometry.**
See `copy-risk.md` and `copy-risk-pairs.jpg`; judge under `originality` /
`copy_or_overfitting_risk`.

**Verified separation of measurement from evaluation:** `image_encoder_revision_sha` is
**empty on every text-only and img2img row** — positive evidence from the data that no CLIP
encoder was resident in those measured processes. Pytests guard the boundary in both directions.

### Correction carried against the approved plan

The plan describes C5's reference as *"cresting wave"*. That is the wording of prompt
**P3-ukiyo**, not the content of **R3** (`DS-0103`), which is a landscape ukiyo-e print of a
seated figure at a low desk in an interior. The C5 conflict is real and unchanged; only the
description was wrong. A pytest guards the old label from returning. Recorded also: **R1 is
also a framed, text-dominated poster scan** — R5 is the harder case because it adds landscape
orientation, not because it is the only framed reference.

### M4 facts a new session must know

- `.venv/Scripts/python.exe -m pytest` → **123 tests**, frozen-kit fingerprint `c40749bc…` unchanged.
- **No linter is installed** (`ruff` absent). pytest is the validation gate; do not claim a lint step ran.
- Adapter cache: `h94/IP-Adapter` **2453.8 MiB** downloaded once (2411.2 encoder + 42.6 adapter), outside the repo.
- `scripts/run_reference_conditioning.py --dry-run` prints the 16-stage process plan without running it.
- EXP-008/EXP-009 run the **named levels alongside the sweep in one shared process**, a documented
  extension of the plan's run counts: the sweep values and named levels are different numbers, so
  without this the clean-process spot checks would have had no counterpart to compare against.
- Regenerate any artefact with: `scripts/build_reference_kit.py` · `scripts/run_reference_conditioning.py`
  (`--dry-run`, `--only`, `--start-at`) · `scripts/evaluate_similarity.py` ·
  `scripts/build_p2_analysis.py` · `scripts/build_p2_contact_sheets.py` · `scripts/build_p2_scoring_form.py`.

### After Kylian's scores arrive — the post-approval order

Record the scores at the granularity actually used → **DR-008** with its conclusion and the
ControlNet screen-out reason → `docs/prototypes/prototype-2.md` → finalise
`experiments/registry.csv` (EXP-007…EXP-014) → planning + change log, risk register (R1 gains the
adapter VRAM figure, R8 its first conditioning evidence), testing strategy (new principle:
measurement instrumentation must not enter the workload it measures), traceability (D1, **D4**,
D5, D6), `docs/ai-usage.md`, and the `docs/04-dataset-methodology.md` M4/M6 wording correction →
close issue #5 → board Done → push → M4 milestone report. **Then stop before M5.**

If the outcome is negative — neither method giving visible, monotone, usable control — that is a
legitimate RQ6 answer and gets recorded as one, with Prototype 5 planning for text-only + LoRA.

---

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
