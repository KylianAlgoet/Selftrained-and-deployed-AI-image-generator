# AI usage documentation

Honest record of how Claude Code (Anthropic) is used in this project, per session. The student remains responsible for all decisions, verification, and understanding; this log is jury evidence for that boundary.

## Working agreement

- Claude Code operates under `CLAUDE.md` + `.claude/rules/`: no fabrication, real commands only, atomic commits, English only, no remote operations without approval.
- The student approves plans (Plan mode) before execution, reviews results, and makes final decisions on research direction, dataset/licensing choices, and scope.
- Anything AI-produced that matters (measurements, claims, configs) must be verifiable from repository evidence — and is spot-checked by the student.

## Session log

### 2026-07-30 — Prototype 1: base-model benchmark (M3)

**AI assistance:** Plan-mode M3 plan, revised after Kylian issued seven mandatory corrections (two-track fairness, immutable revision pinning, a correctly scoped reproducibility claim, a hard human-review gate, safety-checker comparability, and resolving a style-label inconsistency first). Implementation of the inference dependency pinning, the CUDA smoke test, the hash-locked frozen evaluation kit, the benchmark schema and runner, the aspect-ratio experiment, two process-isolating orchestrators, and the scoring-form generator; running all experiments; diagnosing three real defects; documentation, registry rows, DR-007 drafting, and atomic commits. Executed under Claude Opus 5.

**Student decisions:** issued the seven pre-execution corrections, including catching that the dataset style label `retro-comic` contradicted its own evidence (WPA silkscreen posters, no comics) — a defect that had already propagated into the draft benchmark prompt kit and would have invalidated later LoRA comparisons. Chose to proceed with **two candidates** when SD 2.1 base proved gated, explicitly declining an HF account, an unverifiable community mirror, and a substitute model. Performed the **entire qualitative evaluation**: inspected the three contact sheets, supplied all rubric scores, selected SD 1.5 as the base model and direct 1:3 as the deck strategy, and rejected square-crop.

**Boundary actually enforced:** the assistant produced measurements and evidence only, then **stopped at a hard gate** and asked for scores. It did not assign any quality score, choose the winning model, write DR-007's conclusion, close issue #4, or push before Kylian's review. A pytest asserts the measurement summary contains no quality verdict, so the tooling cannot pre-empt the student's judgement. Kylian's scores were recorded at the granularity actually used — aggregate per model/track — with per-unit cells marked "not individually scored" rather than back-filled, and `diversity_across_seeds` left unscored with the reason stated, on Kylian's explicit instruction not to imply per-unit review that did not happen.

**Verification status:** every figure is from a real run on this machine. Three self-corrections are recorded rather than hidden: (1) an instrumentation bug (`self._stop` shadowing `threading.Thread._stop()`) caught by the mandated one-image smoke test before ~90 min of GPU time was spent; (2) an over-generalised claim that both models read "skateboard decal artwork" literally — retracted after the Track B sheet showed the behaviour is resolution-dependent; (3) a measurement contamination in EXP-005's first run whose obvious cause (thermal throttling) was **tested and refuted** before the real cause (caching-allocator state) was fixed by process isolation. The assistant also flagged its own deviation from the approved plan (using `mem_get_info` instead of repeatedly spawning `nvidia-smi`) and renamed the affected schema field rather than keeping a misleading name.

### 2026-07-27 — Dataset pipeline (M2)

**AI assistance:** Plan-mode M2 plan with weighted sourcing comparison; implementation of the `ml/dataset` pipeline modules and 34 pytest tests; the collection and build scripts; running collection from approved sources; visual review of contact sheets; documentation and atomic commits. Part of this milestone was executed under Claude Opus 4.8 after Claude Fable 5 became unavailable mid-session; the handoff was via the process log, session-handoff, and untracked-script review (no work repeated, no unreviewed scripts committed).

**Student decisions:** chose the third style (ukiyo-e over graffiti) and the ~50/style target; approved the concrete source registry with conditions A–D before any download; set the exclusion/privacy/licence rules the pipeline enforces.

**Verification status:** all counts, licences, and test results are from real runs (162 candidates → 148 accepted; 34 tests pass). Two approved sources were genuinely unavailable (Digital Comic Museum Cloudflare challenge; Art Institute of Chicago image CDN 403) and were handled by shifting to already-approved sources per conditions A/B — documented honestly in the process log and planning change log rather than papered over. One off-style item was removed by human-in-the-loop visual review and logged. No raw images are committed; provenance for every item is in the manifest.

### 2026-08-01 — Prototype 2 (M4)

**AI assistance:** implementation of the reference registry, conditioning schema, Phase-1 runner, Phase-2 similarity evaluator, orchestrator, contact-sheet builder, analysis scripts and the blank scoring instruments; execution of EXP-007…EXP-014 (299 generations, 297 offline evaluations); generation of all evidence, sheets and unscored summaries; documentation, registry rows, DR-008 drafting from the approved decision, and atomic commits.

**Student decisions:** approved the M4 plan and its scope (four measured arms; ControlNet criteria-only); issued six measurement-validity corrections *before* execution, one of which caught a real defect in the first draft — it would have loaded the 2.35 GiB CLIP metric encoder inside the text-only and img2img processes purely to compute indicators, inflating exactly the VRAM figures the comparison rests on; performed the entire visual review; supplied every rubric score and failure-mode observation; **made the method selection and wrote the decision recorded in DR-008.** The assistant proposed no method and assigned no score.

**Corrections the assistant made to the approved plan, rather than following it blindly:** the plan described condition C5's reference as a "cresting wave"; opening the actual image showed a figurative ukiyo-e interior scene, and that phrase belonged to a *prompt*, not the reference. The label was corrected, a regression test added, and the related observation recorded that R1 is also a framed, text-dominated scan — so R5 is the harder case by orientation, not by being the only framed reference.

**Defects the assistant found in its own work and fixed:** a runner path that would have crashed the text-only baseline arm at launch; a failure handler that raised on an empty exception message, destroying the very failure row the honesty rules require; a level-spec design under which the clean-process spot checks would have had nothing to compare against; and an analysis report that stated "REJECTED — a pair exceeded the tolerance" when the pairs were merely *missing*, which is reporting absent data as a failed check.

**Verification status:** every figure quoted is from a command that actually ran on this machine; 123 tests pass and the frozen prompt-kit fingerprint `c40749bc…` is unchanged. No score was invented, estimated, or back-filled: 29 rubric cells are recorded as NOT SCORED and excluded from every mean, and text-only at 512×1536 was left unscored rather than reusing an M3 value. Objective measurements and human judgements are reported in separate sections throughout. The interruption that killed the first experiment run is documented, and the partial data it left was discarded rather than salvaged.

### 2026-07-27 — Prototype 0 (M1)

**AI assistance:** Plan-mode milestone plan with weighted alternatives; scaffolding `apps/web`; implementation of the deck geometry, viewer scene, controls, and self-authored SVG decals; Vitest suites; diagnosis of real tooling issues (jsdom 27 vs Node 20.18, stale background-tab canvas captures, Chrome multi-download blocking); browser-driven visual verification and evidence capture; documentation and atomic commits.

**Student decisions:** approved the milestone plan (procedural geometry over external models); issued mid-execution corrections that were applied — (1) never manufacture a failed UV iteration, only a labelled controlled demonstration; (2) no Node-canvas assumption, prefer static self-authored SVG decals; watched the live viewer during verification.

**Verification status:** all test/lint/build outputs quoted are from real runs; screenshots are real captures of the running app (stale duplicates were detected by file hash and re-captured with a forced-render hook); the first-render orientation being correct is documented as such, with the inverted-UV image explicitly labelled as a demonstration. Student visual sign-off requested in the M1 milestone report.

### 2026-07-27 — Phase 0

**AI assistance:** repository inspection; execution of environment-audit commands and compilation of verbatim results; drafting of the full Phase 0 documentation set (research plan, planning v1, risk register, architecture matrices, decision records DR-001…004, methodologies, rules, README); repository skeleton; atomic commit preparation.

**Student decisions:** provided the governing master prompt (assignment translation + process rules); chose to run Phase 0 in Plan mode and reviewed/approved the Phase 0 plan before any file was created; set the deadline structure and scope boundaries.

**Verification status:** environment-audit outputs are verbatim from commands run on the student's machine this session. Architecture matrix scores are reasoned judgements (documented as such), to be revised with measured data from Prototypes 1/3. Student review of the Phase 0 document set is the next checkpoint (Phase 0 approval gate).
