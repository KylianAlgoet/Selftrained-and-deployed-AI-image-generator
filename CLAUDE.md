# CLAUDE.md — DeckForge AI permanent operating rules

DeckForge AI is Kylian Algoet's final bachelor resit assignment (Multimedia & Creative Technologies): a skateboard-decal generator using a locally trained model, text + reference-image conditioning, and an interactive 3D deck preview. The assessed deliverable is the **honest, iterative, reproducible research process** (learning outcomes D1–D7), not only the code.

The full governing instruction is `docs/prompts/DeckForge_AI_Final_Claude_Code_Prompts.md` (Prompt 1). Detailed rules live in `.claude/rules/`. This file is the condensed permanent contract.

## Non-negotiable rules

1. **Repository path.** Work only inside `C:\Expert Lab\Selftrained-and-deployed-AI-image-generator`. Verify the working directory before changing anything. Never create project files elsewhere without explicit approval.
2. **English only.** All code, comments, filenames, docs, commits, branches, UI text, and errors are professional English. Never mix Dutch and English.
3. **Never fabricate.** No invented hardware data, commands, measurements, training times, VRAM figures, outputs, screenshots, test results, scores, feedback, citations, or completion claims. Failed experiments are documented honestly (see `.claude/rules/honesty-and-evidence.md`).
4. **Research process first.** Every important decision follows the 13-step loop: problem → research question → alternatives → criteria → experiment → execution → real results → comparison → justification → implementation → validation → documentation → atomic commits (see `.claude/rules/research-process.md`).
5. **Commit protocol.** Local commits are authorized and automatic when a coherent unit passes validation. Never `git add .`/`-A` blindly; run checks first; Conventional Commits in English; no vague messages; no AI co-author trailers (see `.claude/rules/git-commit-protocol.md`).
6. **No remote operations** (push, remote branches, GitHub issues/projects, settings) until explicitly approved once. Never force-push or rewrite published history. Keep `main` stable.
7. **Security.** Uploads are untrusted. Never commit secrets, `.env`, personal images, raw datasets, model weights/caches, `node_modules`, venvs, or large binaries (see `.claude/rules/security.md`).
8. **Session continuity.** End every meaningful session by updating `docs/process/session-handoff.md` (state, uncommitted changes, latest commits, blockers, next action). Resume sessions by reading it plus the latest process-log entries first.
9. **Deadlines.** Feature freeze 2026-08-15 · final content 2026-08-16 18:00 · submission 2026-08-17 06:00 (Europe/Brussels) · presentation 2026-09-02.

## Key locations

| What | Where |
|---|---|
| Research plan and questions | `docs/01-research-plan.md` |
| Planning to submission | `docs/02-planning.md` |
| Architecture decisions | `docs/03-architecture.md`, `docs/decisions/` |
| Experiment registry | `experiments/registry.csv` |
| Process log / handoff | `docs/process/` |
| Environment audit | `docs/technical/environment-audit.md` |
| Learning-outcome traceability | `docs/learning-outcome-traceability.md` |

## Environment facts (audited 2026-07-27)

Windows 11 Home, PowerShell 5.1, 16 GB RAM, NVIDIA RTX 4060 Laptop (8 GB VRAM, driver 610.74, CUDA 13.3), Python 3.14 default + 3.11 available via `py -V:3.11` (use 3.11 for PyTorch work), Node 20.18.0, Docker 29.1.3, no FFmpeg/nvcc/conda. Details: `docs/technical/environment-audit.md`.
