# AI usage documentation

Honest record of how Claude Code (Anthropic) is used in this project, per session. The student remains responsible for all decisions, verification, and understanding; this log is jury evidence for that boundary.

## Working agreement

- Claude Code operates under `CLAUDE.md` + `.claude/rules/`: no fabrication, real commands only, atomic commits, English only, no remote operations without approval.
- The student approves plans (Plan mode) before execution, reviews results, and makes final decisions on research direction, dataset/licensing choices, and scope.
- Anything AI-produced that matters (measurements, claims, configs) must be verifiable from repository evidence — and is spot-checked by the student.

## Session log

### 2026-07-27 — Prototype 0 (M1)

**AI assistance:** Plan-mode milestone plan with weighted alternatives; scaffolding `apps/web`; implementation of the deck geometry, viewer scene, controls, and self-authored SVG decals; Vitest suites; diagnosis of real tooling issues (jsdom 27 vs Node 20.18, stale background-tab canvas captures, Chrome multi-download blocking); browser-driven visual verification and evidence capture; documentation and atomic commits.

**Student decisions:** approved the milestone plan (procedural geometry over external models); issued mid-execution corrections that were applied — (1) never manufacture a failed UV iteration, only a labelled controlled demonstration; (2) no Node-canvas assumption, prefer static self-authored SVG decals; watched the live viewer during verification.

**Verification status:** all test/lint/build outputs quoted are from real runs; screenshots are real captures of the running app (stale duplicates were detected by file hash and re-captured with a forced-render hook); the first-render orientation being correct is documented as such, with the inverted-UV image explicitly labelled as a demonstration. Student visual sign-off requested in the M1 milestone report.

### 2026-07-27 — Phase 0

**AI assistance:** repository inspection; execution of environment-audit commands and compilation of verbatim results; drafting of the full Phase 0 documentation set (research plan, planning v1, risk register, architecture matrices, decision records DR-001…004, methodologies, rules, README); repository skeleton; atomic commit preparation.

**Student decisions:** provided the governing master prompt (assignment translation + process rules); chose to run Phase 0 in Plan mode and reviewed/approved the Phase 0 plan before any file was created; set the deadline structure and scope boundaries.

**Verification status:** environment-audit outputs are verbatim from commands run on the student's machine this session. Architecture matrix scores are reasoned judgements (documented as such), to be revised with measured data from Prototypes 1/3. Student review of the Phase 0 document set is the next checkpoint (Phase 0 approval gate).
