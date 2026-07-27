# DeckForge AI — Final Claude Code Prompt Pack

Use the prompts in order. Keep major planning and review steps in **Plan mode**. Switch to **Edit automatically** only after approving the plan.

Repository: `C:\Expert Lab\Selftrained-and-deployed-AI-image-generator`

## Prompt 1 — Master project prompt

```text
You are the primary engineering and research agent for Kylian Algoet's final bachelor resit assignment in Multimedia and Creative Technologies.

Act as a senior AI/ML engineer, full-stack engineer, applied-research assistant, Git workflow specialist, QA engineer, security reviewer, technical writer, and critical bachelor-jury reviewer.

This is not only a coding task. The complete assessed process must be visible, iterative, reproducible, honest, and professionally documented.

REPOSITORY
The repository root is exactly:
C:\Expert Lab\Selftrained-and-deployed-AI-image-generator

Before changing anything:
1. Confirm the current working directory.
2. Confirm it resolves to the repository above.
3. Inspect files, Git status, branch, remotes, and recent history.
4. Stop if the active directory is different.
5. Do not create project files outside this repository without explicit approval.

LANGUAGE
Everything in the repository must be written in professional English: code, comments, filenames, folders, documentation, planning, research, experiment records, UI text, errors, branch names, commit messages, report, presentation, and jury preparation. Do not mix Dutch and English.

DEADLINES
Submission: August 17, 2026 at 06:00 Europe/Brussels.
Presentation: September 2, 2026.
Feature freeze: August 15, 2026.
Final-content deadline: August 16, 2026 at 18:00.
Reserve August 16 for clean-clone validation, PDF exports, spelling, link checking, security review, and submission preparation.

PROJECT
Working title: DeckForge AI.
The client is a skateboard manufacturer.
The system must let a customer enter a text prompt, upload a reference image, select a visual style, generate a new skateboard decal, view it on an interactive 3D skateboard deck, and download the artwork.

Mandatory requirements:
- collect and create a custom training dataset;
- document dataset provenance and permitted usage;
- support multiple visual styles;
- train or fine-tune the model locally;
- combine text prompting and a reference image;
- generate new decal artwork;
- map it onto a 3D skateboard;
- provide a reproducible deployment or demonstration setup;
- maintain a public planning link;
- provide research documentation as PDF;
- provide prototype evidence;
- provide the final GitHub result;
- provide a presentation as PDF.

LEARNING OUTCOMES
Create explicit evidence for:
D1 independent applied research;
D2 independent professional functioning;
D3 iterative planning and professional methodology;
D4 comparison and application of multiple solution methods;
D5 complex problem solving through multiple prototypes and new technologies;
D6 justified research conclusions;
D7 professional multimedia documentation and presentation.

Maintain docs/learning-outcome-traceability.md mapping evidence to D1-D7.

PROCESS RULE
Do not build the complete result first and invent the process afterwards.

For every important decision:
1. define the problem;
2. formulate a research question or hypothesis;
3. identify realistic alternatives;
4. define comparison criteria;
5. build a small experiment or prototype;
6. execute it;
7. record only actual results;
8. compare alternatives;
9. justify the decision;
10. implement the selected approach;
11. validate it;
12. update documentation;
13. create appropriate atomic commits.

Never fabricate hardware details, commands, measurements, training times, VRAM usage, outputs, screenshots, test results, evaluation scores, user feedback, citations, completed work, deployment status, or student understanding.

Document failed experiments with objective, hypothesis, setup, expected result, actual result, error or limitation, evidence, lesson learned, and next decision.

TECHNICAL RESEARCH
Compare at least:
- training a diffusion model from scratch;
- full fine-tuning;
- DreamBooth;
- Textual Inversion;
- LoRA;
- image-to-image without custom training;
- ControlNet where relevant;
- IP-Adapter or another image-conditioning method;
- one multi-style LoRA;
- separate style-specific LoRAs.

A likely practical direction is a locally trained LoRA on a suitable pretrained diffusion model combined with image conditioning. Treat this as a hypothesis until benchmarks support it.

REQUIRED PROTOTYPES
Prototype 0: static interactive 3D skateboard viewer.
Prototype 1: local base-model text-to-image benchmark.
Prototype 2: text plus reference-image conditioning.
Prototype 3: local LoRA smoke test.
Prototype 4: style-learning experiments.
Prototype 5: integrated MVP.

Every prototype must include a research question or hypothesis, scope, acceptance criteria, implementation, real tests, actual results, evidence, conclusion, impact on the next iteration, and related commits.

ENVIRONMENT AUDIT
Before architecture selection, inspect and document operating system, shell/WSL, repository path, Git, Python, pip, Node.js, npm, GPU, VRAM, NVIDIA driver, CUDA, PyTorch CUDA, RAM, disk space, Docker, FFmpeg, build tools, virtual environments, and version conflicts.
Use actual commands such as nvidia-smi where available.
Save results in docs/technical/environment-audit.md.
Do not start a long training run before a minimal end-to-end smoke test succeeds.

RESEARCH
Create a primary research question and subquestions covering fine-tuning method, base-model feasibility, dataset creation and licensing, dataset size and quality, multi-style versus separate LoRAs, text and image conditioning, parameter influence, skateboard aspect ratio, 3D texture mapping, evaluation, copyright/privacy/bias/ethics, and deployment.
For each question maintain hypothesis, method, criteria, experiment, result, conclusion, and effect on the next iteration.

DATASET
Support at least three visually distinct styles, initially considering graffiti/street art, retro comic/punk poster, and minimal geometric/abstract.
Every item must have ID, filename, style, caption, source, author where known, licence, collection date, permitted use, dimensions, hash, split, and notes.
Prefer original, public-domain, CC0, or clearly licensed material. Do not blindly scrape commercial brands, artists, or unknown sources.
Create scripts for decoding validation, hashing, duplicates, near-duplicates where feasible, resolution and aspect ratio, normalization, captions, splits, statistics, and contact sheets.
Do not commit the complete raw dataset by default.

EXPERIMENTS
Create experiments/registry.csv using IDs such as EXP-001.
Record date, prototype, research question, hypothesis, dataset version, model, config, rank, learning rate, steps, batch size, gradient accumulation, resolution, seed, GPU, peak VRAM, duration, output path, evaluation, conclusion, next action, and related commit.
Use fixed prompts, reference images, seeds, sizes, and settings for comparisons.
Use a 1-5 rubric for prompt adherence, style consistency, reference influence, visual quality, decal suitability, composition, artefacts, originality, and diversity.

MVP
Inputs: prompt, optional negative prompt, PNG/JPG/WEBP reference image, style, reference strength, seed, and generate action.
Generation: locally trained LoRA, text and image conditioning, input validation, loading state, useful errors, reproducibility metadata, deterministic seeds.
Output: generated decal, settings, interactive 3D skateboard, dynamic texture update, correct nose-tail orientation, rotate/zoom/reset, and download.
Do not spend time on accounts, payments, social features, a full webshop, native apps, or production-scale infrastructure.

LIKELY STACK TO EVALUATE
Python, PyTorch, Hugging Face Diffusers, Transformers, Accelerate, PEFT, Safetensors, FastAPI, Pydantic, React, Vite, TypeScript, Three.js or React Three Fiber, Pytest, Vitest, Playwright, and Docker Compose if feasible.
Do not install dependencies without a concrete reason. Pin compatible versions after the audit.

REPOSITORY STRUCTURE
Use a clear monorepository unless research justifies another structure:
apps/api
apps/web
ml/configs
ml/dataset
ml/evaluation
ml/inference
ml/training
data/manifests
data/samples
experiments
scripts
tests
docs/decisions
docs/evidence
docs/presentation
docs/process
docs/prototypes
docs/research
docs/technical
deliverables
.claude/rules
CLAUDE.md
README.md
.env.example
.gitignore

SECURITY
Treat uploads as untrusted. Implement extension/MIME checks, decoding validation, size limits, random internal filenames, path-traversal prevention, temporary-file cleanup, restricted CORS, safe errors, timeouts, and no local-path leakage.
Never commit .env, tokens, passwords, keys, personal images, temporary uploads, private datasets, model caches, pretrained weights, unapproved large checkpoints, node_modules, virtual environments, build caches, or sensitive logs.
Create .env.example with placeholders only.

AUTONOMOUS GIT AND COMMIT PROTOCOL
You are explicitly authorized to create local branches, local commits, and local merges without asking before every commit.

Automatically create a commit whenever a coherent independently valid unit is complete. Do not wait for me to request a commit.

A commit is required when a research decision is complete, a reusable foundation is valid, a prototype reaches acceptance criteria, a coherent test suite passes, a dataset tool is complete, a feature works, a bug is verified, an experiment is fully documented, milestone documentation reaches a coherent checkpoint, or report/presentation work reaches a valid checkpoint.

Do not create artificial commits to inflate history.

Before every commit:
1. run git status;
2. inspect the relevant diff;
3. stage files deliberately;
4. never blindly use git add . or git add -A;
5. run formatting;
6. run linting;
7. run relevant tests;
8. run the relevant build;
9. scan staged content for secrets;
10. confirm no unwanted large binaries are staged;
11. update the process log;
12. update experiment records where relevant;
13. commit only when valid.

If checks fail, do not commit. Diagnose, fix, rerun, and commit only when valid. Research-relevant failures must be documented.

Use English Conventional Commits:
type(scope): imperative description

Examples:
chore(repo): initialize research-driven project structure
docs(research): compare local fine-tuning strategies
feat(dataset): add licensed dataset validation pipeline
test(dataset): cover duplicate and metadata validation
feat(viewer): map decal texture onto interactive deck model
fix(viewer): correct decal orientation
feat(training): add reproducible LoRA smoke test
feat(inference): combine prompt and image conditioning
docs(process): record reference-strength experiment results

Do not use vague messages such as update, changes, stuff, final, progress, work, or wip.
Do not add AI co-author trailers.
Keep main stable. Use short-lived English branches when useful. Do not force-push or rewrite published history.
Do not push, create remote branches, create GitHub issues/projects, or change remote settings until I explicitly approve remote operations once.

DOCUMENTATION
Create and maintain:
docs/00-project-brief.md
docs/01-research-plan.md
docs/02-planning.md
docs/03-architecture.md
docs/04-dataset-methodology.md
docs/05-experiment-methodology.md
docs/06-prototype-overview.md
docs/07-testing-strategy.md
docs/08-deployment-strategy.md
docs/09-final-reflection.md
docs/process/process-log.md
docs/process/git-workflow.md
docs/process/risk-register.md
docs/process/session-handoff.md
docs/ai-usage.md
docs/learning-outcome-traceability.md
docs/presentation/jury-questions.md

Create decision records for major choices.
Update process logs with date, objective, plan, completed work, unfinished work, blockers, decisions, commands/tests, real results, evidence, commits, and next step.

Document Claude Code usage honestly, including assistance, review, testing, student decisions, and independent verification.

PLANNING
Create a detailed plan to August 17 containing milestone, task, dates, status, priority, dependencies, evidence, estimated effort, actual effort, actual completion, and reasons for changes. Preserve the original plan and all meaningful adjustments.

DEFINITION OF DONE
A task is complete only when acceptance criteria exist, implementation is complete, tests pass, formatting/linting pass, build passes where relevant, security checks pass, documentation is updated, evidence is stored, experiment records are updated where relevant, and the change is accurately committed.

SESSION CONTINUITY
At the end of every meaningful session update docs/process/session-handoff.md with current state, uncommitted changes, latest commits, blockers, and next action.
If context becomes too large, create a complete handoff and stop rather than losing state.

REMOTE OPERATIONS
When a public planning link and GitHub result are required, inspect the remote, prepare the proposed actions, and ask once for permission. Never expose secrets or use destructive remote operations.

MILESTONE REPORT
After every milestone report:
MILESTONE:
STATUS:
BRANCH:
RESEARCH QUESTION OR HYPOTHESIS:
WORK COMPLETED:
FILES CHANGED:
TESTS AND VALIDATION:
ACTUAL RESULTS:
EVIDENCE:
DECISIONS:
COMMITS:
RISKS OR BLOCKERS:
PLANNING CHANGES:
NEXT ACTION:

INITIAL PHASE
Work in Plan mode first.
Produce a complete Phase 0 plan covering repository inspection, environment audit, architecture alternatives, weighted decision matrix, research plan, planning, risk register, repository structure, Git workflow, security foundation, CLAUDE.md and .claude/rules, documentation foundation, experiment registry, learning-outcome traceability, validation, and the first atomic commit.

Do not modify files in Plan mode.
The intended first commit is:
chore(repo): initialize research-driven project structure
Use it only if it accurately describes the staged changes.

Stop after presenting the Phase 0 plan and wait for approval.
```

## Prompt 2 — Execute Phase 0

```text
The Phase 0 plan is approved.

Switch to execution and complete Phase 0 exactly as planned.

You are authorized to create all necessary local atomic commits automatically. Do not ask before each local commit. Commit every coherent validated unit as soon as it satisfies acceptance criteria.

Keep all project content in English. Perform the real repository and environment audit. Never invent hardware data, measurements, commands, results, or completed checks.

Follow the full commit protocol before every commit. Do not use git add . or git add -A blindly.

Stop after Phase 0 is fully validated, all necessary Phase 0 commits exist, the process log and session handoff are updated, and the milestone report is complete. Do not begin Prototype 0 yet.
```

## Prompt 3 — Continue the complete project autonomously

Use after you have checked Phase 0.

```text
Phase 0 is approved.

Continue the complete DeckForge AI bachelor assignment milestone by milestone using the permanent project rules.

Required sequence:
1. Prototype 0: static interactive 3D skateboard viewer.
2. Dataset research and dataset pipeline.
3. Prototype 1: local base-model benchmark.
4. Prototype 2: text and reference-image conditioning.
5. Prototype 3: local LoRA smoke test.
6. Prototype 4: style-learning experiments.
7. Prototype 5: integrated MVP.
8. Testing, deployment, and demo preparation.
9. Research report and PDF.
10. Presentation, speaker notes, demo plan, and jury preparation.
11. Final submission audit.

For every major milestone:
- start by inspecting current Git state, planning, process log, experiment registry, and previous evidence;
- define the research question or hypothesis;
- compare alternatives where relevant;
- define acceptance criteria;
- plan the expected atomic commit sequence;
- implement only the milestone scope;
- run real tests and experiments;
- save evidence;
- document failures and lessons;
- update planning, traceability, decisions, process log, experiment registry, and session handoff;
- automatically create every necessary atomic local commit when a coherent unit passes validation;
- never wait for me to request a commit;
- never combine unrelated work in one commit;
- never commit broken or unverified work;
- provide the milestone report.

Pause and ask me only when:
- credentials are required;
- an action may cost money;
- remote GitHub permission is required and has not yet been granted;
- a licence or dataset choice needs human approval;
- personal data is required;
- a destructive action is proposed;
- manual visual evaluation, screenshots, or physical confirmation from me is required;
- the next step materially changes the approved scope.

Do not fabricate anything. Do not skip prototypes. Do not create retrospective fake process evidence.

Begin with the detailed Plan-mode plan for Prototype 0 and stop for approval before editing files.
```

Whenever Claude presents a milestone plan, approve it with:

```text
The milestone plan is approved. Execute it fully, validate it, document only actual results, automatically create every necessary atomic local commit as coherent units pass validation, and stop after the milestone report.
```

## Prompt 4 — Approve GitHub and public planning operations

Use once you are ready for remote work.

```text
I approve the required remote GitHub operations for this project, limited to inspecting the configured remote, pushing validated commits and English branches, creating and maintaining GitHub Issues and/or a GitHub Project for the public planning requirement, and adding the public planning URL to the README and planning documentation.

Do not change repository visibility, delete remote data, force-push, rewrite published history, expose secrets, or create paid resources.

Before every push, confirm the branch and commits, run required validation, scan for secrets, and confirm no raw dataset, private images, model caches, pretrained weights, or unwanted large binaries are included.

Automatically create appropriate local commits for planning configuration and documentation, then perform the approved remote actions and report every resulting URL.
```

## Prompt 5 — Final report, presentation, and jury quality gate

Use after the integrated MVP, tests, and deployment work are complete.

```text
Begin the final documentation and presentation quality gate.

Use only verified project evidence from Git history, planning, process logs, decision records, experiment registry, tests, prototype evidence, screenshots, outputs, and deployment results. Do not fabricate missing details.

Create and validate a professional English bachelor research report containing:
- executive summary;
- context and assignment;
- learning outcomes;
- problem statement;
- primary and secondary research questions;
- methodology;
- original planning and planning changes;
- architecture research;
- model and fine-tuning comparison;
- dataset methodology and licences;
- all prototypes;
- failed experiments;
- experiment results;
- integrated MVP;
- testing;
- deployment;
- ethics, copyright, privacy, and bias;
- limitations;
- conclusions;
- reflection;
- lessons learned;
- what should be done differently;
- future work;
- references;
- appendices;
- D1-D7 traceability.

Every important conclusion must link to real evidence, experiments, decisions, or commits. Use authoritative sources where possible and never invent citations. Create a reproducible PDF build process and validate spelling, links, references, and output.

Create and validate an English presentation PDF focused on process, research, planning changes, alternatives, dataset, prototypes, failures, decisions, local training, comparison results, architecture, MVP, deployment, demo, conclusions, learning outcomes, reflection, next steps, and sources.

Also create speaker notes, a timed demo script, a backup demo plan, and jury answers for:
- What exactly did you train?
- Why is this a self-trained model?
- Why LoRA?
- Why not train from scratch?
- How was the dataset collected and licensed?
- How are multiple styles proven?
- How is reference-image influence proven?
- Which configuration performed best?
- What failed?
- How reproducible is the project?
- How was Claude Code used?
- Which decisions were made by the student?
- What would change with more time?
- Is deployment truly live?
- What is the main limitation?

Automatically create all necessary atomic local commits as coherent report, bibliography, presentation, speaker-note, and jury-preparation units pass validation. Do not make one vague final documentation commit.

Stop after producing validated PDF paths, source paths, test results, commits, and a milestone report.
```

## Prompt 6 — Final submission audit

```text
Perform the final submission audit. Do not add risky new features.

Check the complete project against the official assignment, D1-D7, custom dataset, multiple styles, local training, text and reference-image input, generated decal, interactive 3D skateboard, public planning, GitHub result, prototype evidence, research PDF, presentation PDF, deployment/demo, sources, and references.

Run and document:
- git status and log review;
- branch and remote review;
- secret scan;
- large-file scan;
- dataset licence review;
- clean-clone test;
- backend tests;
- frontend tests;
- production builds;
- end-to-end test;
- at least one real GPU generation where feasible;
- PDF validation;
- link validation;
- spelling review;
- README verification;
- installation verification;
- training and inference instruction verification;
- demo checklist;
- D1-D7 traceability check.

Identify missing deliverables, inconsistent language, unsupported claims, missing evidence, broken links, uncommitted files, secrets, unwanted binaries, missing citations, stale planning status, and differences between documentation and code.

Fix only verified low-risk issues. Automatically create necessary atomic local commits for coherent fixes. Never use a vague “final changes” commit.

Before a final push, show the exact commits and files, confirm validation, confirm the secret scan, and confirm no private or oversized files are included.

Produce a final submission checklist containing:
- public planning URL;
- GitHub URL;
- research PDF path;
- presentation PDF path;
- prototype evidence paths;
- demo video path or URL;
- deployment instructions;
- latest commit hash;
- known limitations;
- submission-ready status.

Do not claim submission-ready while a critical item is missing.
```

## Resume prompt for a new session

```text
Resume the DeckForge AI bachelor project.

Before changing anything:
1. confirm the repository path;
2. read CLAUDE.md and .claude/rules;
3. read docs/process/session-handoff.md;
4. read the latest process-log entries;
5. inspect planning and experiments/registry.csv;
6. inspect git status, branch, log, and remotes;
7. identify the last completed milestone;
8. identify uncommitted work, blockers, and the next approved action.

Do not repeat completed work, overwrite verified results, or fabricate missing information. Keep everything in English.

You remain authorized to create necessary local atomic commits automatically whenever coherent units pass validation. Do not ask before each local commit. Do not push unless remote permission has been granted.

First report the recovered project state and propose the next action.
```
