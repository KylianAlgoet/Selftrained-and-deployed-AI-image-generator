# Git and commit protocol

Local branches, commits, and merges are authorized without asking per commit. Commit automatically whenever a coherent, independently valid unit passes validation. Do not create artificial commits to inflate history, and do not wait to be asked.

A commit is required when: a research decision is complete, a reusable foundation is valid, a prototype reaches acceptance criteria, a coherent test suite passes, a dataset tool is complete, a feature works, a bug fix is verified, an experiment is fully documented, or documentation reaches a coherent checkpoint.

## Before every commit

1. `git status`
2. Inspect the relevant diff
3. Stage files deliberately — never `git add .` or `git add -A` blindly
4. Run formatting
5. Run linting
6. Run relevant tests
7. Run the relevant build
8. Scan staged content for secrets
9. Confirm no unwanted large binaries are staged
10. Update the process log
11. Update experiment records where relevant
12. Commit only when valid — if checks fail, diagnose, fix, rerun; document research-relevant failures

## Message format

English Conventional Commits: `type(scope): imperative description`.

Good: `feat(viewer): map decal texture onto interactive deck model` · `docs(research): compare local fine-tuning strategies`.
Forbidden: `update`, `changes`, `stuff`, `final`, `progress`, `work`, `wip`, AI co-author trailers.

## Branches and remotes

- Keep `main` stable; use short-lived English branches when useful.
- No force-push, no rewriting published history.
- No pushes, remote branches, GitHub issues/projects, or remote settings changes until remote operations are explicitly approved once.
