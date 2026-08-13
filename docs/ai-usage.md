# AI usage documentation

Honest record of how Claude Code (Anthropic) is used in this project, per session. The student remains responsible for all decisions, verification, and understanding; this log is jury evidence for that boundary.

## Working agreement

- Claude Code operates under `CLAUDE.md` + `.claude/rules/`: no fabrication, real commands only, atomic commits, English only, no remote operations without approval.
- The student approves plans (Plan mode) before execution, reviews results, and makes final decisions on research direction, dataset/licensing choices, and scope.
- Anything AI-produced that matters (measurements, claims, configs) must be verifiable from repository evidence — and is spot-checked by the student.

## Session log

> **Gap, stated rather than back-filled: there is no M9 entry in this log.** The report milestone ran
> on 2026-08-10/11 and its process-log entry, `DR-015` and `docs/evidence/M9/` record what happened,
> but no AI-usage entry was written at the time. The 2026-08-14 session did not invent one, because
> this log's whole purpose is the human/AI boundary and reconstructing that boundary three days later
> from commits would be exactly the kind of plausible-but-unwitnessed account it exists to prevent.
> **Kylian should write the M9 entry, or it stays absent and is reported as absent.**

### 2026-08-14 — M10: the defence deck, DR-016 and a stale deliverable

**AI assistance:** verifying the deck authored on 2026-08-11 against its sources rather than trusting
it; rebuilding both presentation PDFs and the report; writing **DR-016**, the M10 build record, the
process-log entry, the planning row and this entry; correcting the report's requirement-13 rows and
the "90-page" literals; recording the M9 evidence audit as superseded.

**What the AI found, and it was in its own predecessor's work.** The presentation PDFs committed to
the working tree **did not match their sources** — built at 05:00 on 2026-08-11, with the CSS and one
slide edited at 05:03 and never rebuilt, leaving about **20 % of the deliverable missing**. Four
files also cited a decision record, `DR-016`, that **did not exist**. Both were defects in AI-produced
work from a previous session, found by checking rather than reported by any tool, and both are
written up in `docs/evidence/M10/build-record.md` instead of being quietly corrected.

**What the AI did NOT decide.** It did not judge the deck's content, its design, its legibility or
whether its argument survives compression onto a slide — **no human visual gate has been held, and
every check run is structural**. It did not decide the deck's length: no authoritative presentation
duration is recorded anywhere in this repository, so the 26-slide count is reported as **provisional**
rather than assumed adequate. It did not convert the speaking estimate into a rehearsal time, and it
did not run a rehearsal. It did not push, close issue #10, or move the board.

**A decision the AI took on its own, and flagged.** Writing DR-016 moved `decision_record_count` from
15 to 16, which **failed the deck build** and made the already-pushed report state a number that was
no longer true. The AI updated the fact lock and Appendix B and rebuilt the report — taking it from
**90 to 91 pages** and superseding the M9 artifact's SHA-256. That was a judgement call about a
submitted deliverable, taken because leaving the report misstating its own decision-record count was
the worse option, and it is recorded here, in DR-016 and in the planning log rather than absorbed.

**Verification status:** every figure quoted for M10 is from a command that ran in this session —
`validate_slides.py` (0 hard failures, 0 advisories), `build_slides.py --strict` (26 pages for 26
slides, 960 × 540 pt), `build_report.py --strict` (91 pages), `validate_report.py`,
`report_facts.py --check` (31 locks), and **518 pytest** collected and passing. The stale-PDF byte
figures are the two files' actual sizes, before and after. **The speaking time is an estimate from
speaker-note word counts at 130 wpm and is labelled as one everywhere it appears.**

### 2026-08-09 — M8: testing, deployment, clean-clone validation, demo preparation

**AI assistance:** re-measuring the four gates and diagnosing the stale Node audit entry; writing
35 backend and 4 frontend security tests; building the Playwright suite (config, JSON fixtures, a
pytest contract guard, 37 scenarios); drafting DR-014; writing four PowerShell scripts, the
deployment runbook and the weights manifest with its pytest guard; the CI workflow; executing the
clean-clone validation and diagnosing its failure; implementing the approved hash fix; driving the
one authorised generation; drafting the demo script, the backup plan, the feature-freeze record and
this milestone's evidence.

**Student decisions.** Four before implementation: re-baseline on Node 24 rather than reinstalling
Node 20 · native local deployment plus backup assets, rejecting Docker · Playwright with Chromium
only · CI committed locally but not pushed. Three at the mid-milestone gate: how to fix the frozen
dataset hash · **authorising the single real generation** · fixing the misleading requirements
comment without moving versions.

**What the AI did NOT decide.** It did not authorise the generation, and did not run one before
asking. When the clean clone failed on a value documented as frozen, it diagnosed the cause,
prepared two options and **stopped** — because repointing that constant would have moved
`kit_fingerprint()` and every M6 run's recorded `dataset_version`, which is not an assistant's call
to make. It did not run `npm audit fix`, did not pin transitive dependencies, and did not push.

**Where the AI's own work was wrong, and how it was caught.** Four Playwright assertions failed on
first run — an ambiguous selector, an expected `1.3008×` where the component renders `1.301×`, a
style the test never selected, and a string that also lives in the aria-live region — all test
defects, not application defects. A regex-based fixture reader was written, failed on real
TypeScript, and was **replaced by storing the fixtures as JSON** rather than patched. A non-English
string reached a PowerShell error message and was corrected, with a scan confirming no others. A
mojibake ellipsis in a generated manifest was traced to PowerShell 5.1's ANSI handling and fixed.
The approved plan's CI skip-marker was dropped after checking disproved its premise.

**Verification status:** every figure quoted in M8 is from a command that ran in this session —
473 pytest, 169 vitest, 37 Playwright (twice), eslint, build, all four scripts, and the clean-clone
sequence. The byte-identical reproduction was verified two independent ways (`sha256sum` on both
files and the service's own recorded `image_sha256`). **The CI workflow has never executed**, and
its evidence record says so in its opening lines. **No generation was ever run by an assistant
without explicit authorisation**; the total is 27 and is reported as 27.

### 2026-08-07 — M7 closure at the final human visual gate

**AI assistance:** stopping the review servers and verifying the ports were released; recording
the completed 12-item acceptance checklist and the gate approval; the milestone report; updating
the prototype report, DR-012/DR-013 status lines, traceability, testing strategy, risk register,
planning change log and session handoff; the final non-GPU verification pass; atomic commits.
Executed under Claude Opus 5.

**Student decisions — all of them.** Kylian performed the live visual and functional review and
returned the approval: the redesigned interface, the progress/ETA implementation,
`Upload your own decal` as a production feature, `full-surface` re-confirmed, and M7 may close
locally. He also set the generation-budget wording. **The assistant recorded the decision; it did
not make or infer any part of it.**

**Verification status.** **406 pytest** and **165 vitest** pass; eslint clean; build succeeds. The
three production LoRA checkpoints were re-hashed on disk at closure and match. No tracked model
weights; frozen dataset and evaluation kits unchanged. **No GPU inference was run for closure.**

**Generation budget, stated honestly.** Final count **26**. The research budget closed at 25/25;
**generation 26 was Kylian's own manual review run, outside the frozen research matrix.** It is
deliberately not added to EXP-034 and not registered in `experiments/registry.csv` — registering a
run made under different conditions would contaminate a frozen matrix, and the temptation to tidy
the number to 25 or to absorb 26 into the experiment record was refused in both directions.

**Boundary held:** M7 is closed **locally only**. Nothing was pushed, the remote GitHub issue was
not closed, the project board was not changed, and M8 has not begun — all four remain Kylian's.


### 2026-08-07 — Prototype 5 visual review: telemetry verification and decal upload (M7)

**AI assistance:** verification of the live generation against the retained telemetry and the
uvicorn access log; the local decal-upload feature with its provenance model and 13 tests; live
browser verification; documentation. Executed under Claude Opus 5.

**Student decisions.** The product decision is entirely Kylian's: keep local decal upload as a
normal production feature, clearly separate from the AI reference upload, with an explicit
constraint that it must not call the generation API, load the model or use the GPU. He also
reviewed the interface live and passed it, and he ran the one real generation.

**Verification status, including its limit.** The telemetry confirms operation `cHWlV0J6Qgh2BKze`
reached `current_step 30 / total_steps 30` across **48** polls and one POST — real diffusion steps
were tracked and delivered. It does **not** confirm which strings the browser painted, because the
server logs requests and not rendered text. That distinction is stated in the report and the
process log rather than collapsed into "verified". No defect was found, so nothing was changed.

**The upload path was checked from the server, not asserted:** across every upload the access log's
POST count stayed at 1 and `allocated_mb` at 3316.64 — no API request, no GPU work.

**Honesty note.** Two screenshots in this pass are **not** mocked, and the evidence README now
distinguishes them from the seven that are.

**Boundary held:** no model, prompt, setting, metadata or API contract changed; M7 not declared
complete; nothing pushed; issue and board untouched; M8 not begun.


### 2026-08-07 — Prototype 5 interface pass and generation progress (M7)

**AI assistance:** the progress telemetry (tracker, endpoint, callback composition) and its 35
tests; the interface rebuild (tokens, layout, status system, form, result panel, review gating)
and the progress experience with its 82 tests; browser verification against a real uvicorn process
with mocked generation; DR-013; the evidence README and this documentation set; atomic commits.
Executed under Claude Opus 5.

**Student decisions and constraints.** Kylian set the whole boundary before any code was written,
and the boundary is what shaped the result:

- **no new dependency, no SSE, no WebSocket, no job queue, no second process or worker** — which
  is why the design is one read-only endpoint and one polling loop rather than a streaming
  protocol;
- **"this must not be a fake progress bar"**, stated explicitly. That single constraint produced
  the rule the whole feature rests on: only denoising has a real denominator, so every other stage
  gets a stage name and no number;
- **a strict non-regression list** naming generation settings, prompt assembly, metadata, lock and
  timeout behaviour as protected — so the pass had to be visual, accessible and additive only;
- **stop at a visual review gate**, and do not close M7.

**Verification status.** Every figure is from a command that ran here. **406 pytest** (371
before) and **152 vitest** (70 before) pass; eslint clean; build succeeds. The three production
checkpoints were re-hashed on disk and match. **No generation ran** — `POST /api/generate` was
intercepted in the browser and the API still reported `pipeline_loaded: false` afterwards, which
is the independent check rather than the assistant's own assurance.

**Defects the assistant found in its own work and recorded rather than hid:** a desktop shell that
overflowed the viewport by 70 px; a page-wide horizontal scrollbar caused by a CSS specificity
conflict with the visually-hidden file input; and a polling loop that restarted on every render
because its options were in the effect dependency array. **None of the three was visible to any
test** — they were found by measuring the live document, which is why the browser pass happened at
all.

**Honesty note on the screenshots.** The nine interface screenshots use **mocked telemetry**, and
their README says so first, states that no image was generated, and states that the numbers in
them must never be cited as measurements.

**Boundary held:** no model, prompt, setting, metadata or contract changed; M7 is not declared
complete; nothing is pushed; the issue and board are untouched; M8 has not begun; the GPU cap
stands at 25 of 25.

### 2026-08-07 — Prototype 5 review gate: the texture-fit decision (M7)

**AI assistance:** presented the two fit screenshots and the measured trade-off; after the answer,
implemented `DEFAULT_TEXTURE_FIT_MODE`, replaced the "no default is exported" test with five
tests covering the chosen default, wrote DR-012 and the gate approval record, and updated the
affected documentation. Executed under Claude Opus 5.

**Student decisions.** Both of them, and neither was inferred:

- **the production texture-fit mode** — Kylian selected `full-surface` and supplied his own
  rationale, quoted verbatim in DR-012 rather than paraphrased. The assistant asked for the
  reason explicitly instead of writing a plausible one, because a decision record with an
  invented justification is worse than one with none;
- **whether M7 could be declared complete** — asked directly, he answered *"Not yet — I'll walk
  the checklist"*, so the milestone stayed open.

**Verification status.** After the change: **371 pytest** tests pass (unchanged by this edit),
**70 vitest** tests pass (five added, one removed), eslint is clean, `npm run build` succeeds.
**No 26th generation was run** — the gate reused the existing screenshots.

**Boundary held:** M7 is not declared complete, the 12-item manual checklist is recorded as
**unwalked**, nothing is pushed, the GitHub issue and board are untouched, and M8 has not begun.

### 2026-08-06 — Prototype 5 / the integrated MVP (M7)

**AI assistance:** M7 plan in Plan mode; inspection of the diffusers 0.39.0 source to settle how
prompt-only requests must work; resolver-gated dependency install; implementation of `apps/api`
(config and single-worker guard, production style table with the sha256 integrity gate, frozen
upload limits, resident pipeline with a verified LoRA lifecycle, single-flight generation service,
FastAPI app) with 82 tests; the React generate flow, both texture-fit modes and the texture-swap
logic with 66 web tests; EXP-034 and EXP-035; end-to-end validation against a real uvicorn
process; browser-driven screenshot capture; DR-011, the prototype report, the gate handover and
this documentation set; atomic commits.

**Student decisions.** Kylian **rejected the first plan** and returned twelve mandatory
corrections, then **rejected the second** and returned two more. Those corrections are load-bearing
and are visible in the result rather than in the plan alone:

- the frozen **12-request** residency matrix with its eight pre-declared pass criteria — the
  assistant's draft had described an 8-request sequence as 12 and had not enumerated what to record;
- the **single-process invariant**, which the assistant had not identified at all: the busy lock is
  process-local, so it is meaningless under multiple workers, and a second pipeline does not fit in
  the margin anyway;
- the rule that a **504 may only be returned once GPU work has actually stopped**, and that if safe
  cancellation were unsupported the limitation must be stated rather than disguised;
- **build both texture-fit modes and choose at the gate**, rather than the assistant selecting one;
- the corrected response contract (JSON plus an image URL, and the 409/503/504 semantics);
- an exact upload-limit table frozen before implementation, and an explicit GPU-generation cap.

**Verification status.** Every figure quoted is from a command that actually ran on this machine.
371 pytest tests and 66 vitest tests pass; eslint is clean and the production build succeeds. The
25-generation cap was declared before any generation ran and finished at exactly 25 — when the
gate needed fit screenshots afterwards, an existing decal was loaded from disk rather than a 26th
generated. The three production checkpoints were re-hashed on disk and matched their recorded
values. Nothing was concluded about the texture-fit default.

**Defects the assistant found in its own work and recorded rather than hid:** a deadline assertion
that measured a *cold* request's wall clock and so failed on correct behaviour, replaced by a step
count the response reports directly; a blank-deck screenshot that was a capture-timing artifact
rather than a bug, verified before being reported; and an `<output>` element inside a `<label>`,
which is itself labelable and made a control ambiguous to assistive technology.

**Boundary held:** the production texture-fit mode is not chosen, M7 is not declared complete,
nothing is pushed, the GitHub issue and board are untouched, and M8 has not begun.

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
