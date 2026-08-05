# AI usage documentation

Honest record of how Claude Code (Anthropic) is used in this project, per session. The student remains responsible for all decisions, verification, and understanding; this log is jury evidence for that boundary.

## Working agreement

- Claude Code operates under `CLAUDE.md` + `.claude/rules/`: no fabrication, real commands only, atomic commits, English only, no remote operations without approval.
- The student approves plans (Plan mode) before execution, reviews results, and makes final decisions on research direction, dataset/licensing choices, and scope.
- Anything AI-produced that matters (measurements, claims, configs) must be verifiable from repository evidence — and is spot-checked by the student.

## Session log

### 2026-08-05 — Prototype 4 gate 2: production selection and milestone closure (M6)

**AI assistance:** verification of the completed Gate-2 scoring artifact against its supplied sha256; resolution of the selected checkpoint paths, hashes, byte sizes and tensor inventories from the recorded evidence; the R14 runner fix and its four regression tests; finalising DR-010 from Kylian's decisions; the documentation and registry pass; atomic commits. Executed under Claude Opus 5.

**Student decisions:** **Kylian Algoet is the final human approver of Gate 2.** He reviewed the 21 labelled contact sheets — **with ChatGPT assisting the visual analysis** — inspected the review material, and approved every conclusion and production decision himself. **No automated indicator selected any checkpoint, weight, style or verdict.**

Three of his decisions went against the tidier reading:

- **Two of the three production checkpoints are step 300, not the step 600 the runs trained to.** More training was not better for `minimal-geometric` or `retro-poster`, and his scores show it — prompt adherence fell from 4 to 3 at step 600 in both while style consistency stayed at 5.
- **`retro-poster` is recorded as a PARTIAL PASS and explicitly not upgraded**, with H4 confirmed against it.
- **The multi-style adapter is recorded as viable but not selected**, rather than as a failed experiment — it was competitive and showed no severe token bleed; it simply lost on flexibility.

He also required that the R14 reproducibility fix be **forward-looking only**: the runner is seeded for future training, but EXP-027…EXP-030 are neither rerun nor replaced, and the historical finding is not softened by the fix.

**Verification status:** every checkpoint hash in the approval record and DR-010 was re-read from the file on disk and compared against the value recorded at training time — none was copied from a draft. The scoring artifact was hashed before it was read and is now asserted by pytest. **No score was invented or altered, and the assistant selected nothing.**

### 2026-08-05 — Prototype 4: style learning, both phases (M6)

**AI assistance:** Plan-mode M6 plan, revised after Kylian issued **eight mandatory corrections**. Implementation of the frozen style kit, five per-style manifests, the caption audit, the per-style and balanced multi-style training paths, the capped pilot and final validation matrices, the memorisation and diversity indicators, the blinded gate-1 package and the labelled gate-2 package; running all fourteen Prototype-4 experiments; documentation, eleven registry rows, the DR-010 draft, and atomic commits. Executed under Claude Opus 5.

**Student decisions:** Kylian's plan review caught a **contradiction in the assistant's own plan** — it promised an intermediate human review gate and then authorised full training runs, contingency adjustments and the final validation matrix before he had seen anything. He required a hard Phase A / Phase B split with an explicit list of things not to do before the gate, and that split is what made gate 1 a real decision point rather than a formality. Three further corrections were substantive:

- **RQ4 was not actually being answered.** Training only 36–44-image sets can show those counts worked; it cannot establish the *effect* of count. Kylian required a controlled nested 12 ⊂ 24 ⊂ 44 experiment, which cost two extra runs.
- **An unfalsifiable hypothesis.** H2 claimed style-only captions were "at least as strong" as verbatim, while treating equality as a refutation. Equality cannot refute "at least as strong". He required four explicit verdict rules instead.
- **An unfair multi-style comparison.** "Matched steps" would have given each style roughly a third of the exposure it received in its own run. He required exposure-matched sampling, which the runner now asserts.

He then scored the blinded pilot sheets, fixed the scores, supplied their sha256 **before** the blinding map was opened, and made all six gate-1 decisions himself — including leaving the dataset-size result at **O5 inconclusive** rather than accepting a tidier reading of a non-monotonic ordering.

**Three defects in the assistant's own work, found and recorded rather than quietly patched:** trigger tokens in the approved plan that collided with the caption corpus (caught against the live tokenizer before any GPU time was spent); 24 duplicated generations in the final matrix that were biasing a diversity indicator toward zero; and a missing `.gitattributes` rule that would have rewritten the hash-locked scoring artifact to CRLF on checkout and invalidated the integrity check protecting Kylian's scores.

**Verification status:** every measurement quoted is read back from a recorded run row or re-read from the artifact on disk; no figure was retyped by hand into the registry or the decision record. Two figures the assistant mis-transcribed into a draft DR-010 table were caught by re-reading the source rows and corrected. **No rubric score was invented, no production checkpoint was selected, no style was declared a winner, and DR-010 carries no conclusion** — all of which wait on Kylian's gate-2 review.

### 2026-08-04 — Prototype 3: LoRA smoke test (M5)

**AI assistance:** Plan-mode M5 plan, revised after Kylian issued **twelve mandatory corrections and then a thirteenth**. Implementation of the PEFT dependency gating, the frozen smoke-test manifest and validation kit, the training schema and tier ladder, the training runner and its process-isolating orchestrator, the load-and-generate verifier, the two-phase effect evaluator, and the combined-stack runner; running all eight experiments; documentation, eight registry rows, DR-009 drafting, and atomic commits. Executed under Claude Opus 5.

**Student decisions:** chose to **measure both training geometries** in separate processes rather than assume the deck format's cost, and chose **automated technical gates only** for M5, deferring all visual judgement to Prototype 4. Then issued twelve pre-execution corrections that materially changed the plan, including several the assistant had got wrong:

- **Gate design.** Byte equality at LoRA weight 0.0 had been written as a *pass condition*; Kylian required it be demoted to a **diagnostic**, on the correct reasoning that loading an inactive adapter may legitimately change the execution graph. He likewise required that a differing PNG hash alone never count as proof of change, and that a decreasing loss never gate a short, noisy run.
- **A technical error in the assistant's tier ladder.** The draft listed "increase gradient accumulation" as a VRAM-reduction tier. Kylian identified that at micro-batch 1 this changes effective batch size and training semantics but does **not** reduce the peak memory of one forward/backward micro-step, and required it be removed from the ladder entirely. The measured EXP-016/EXP-017 phase peaks later confirmed his reasoning: activations scale with geometry, optimizer state does not.
- **Dependency protection**, **micro-run gating with hard wall-clock limits**, **the 512×512-before-512×1536 ordering** for the combined stack, **phase-separated resource recording**, and a requirement that **DR-009 not claim LoRA is superior to methods that were never measured**.

**Boundary actually enforced:** the assistant produced measurements and evidence only. It made **no visual-quality claim anywhere** in M5, assigned no rubric score, and did not close issue #6 or push. The 512×1536 arm was held to feasibility probes and never expanded into a long training run, because that expansion was reserved as a separate decision for Kylian. One defect in the assistant's own EXP-019 runner (unpacking `preprocess_for_adapter`'s `(image, note)` return as one value) is preserved in the results as a failed row rather than deleted, and is labelled as a runner defect rather than a finding about the stack.

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
