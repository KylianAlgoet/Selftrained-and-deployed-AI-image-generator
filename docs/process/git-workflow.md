# Git workflow

**Created:** 2026-07-27 · Full protocol: `.claude/rules/git-commit-protocol.md`.

## Branch model

- `main` stays stable and always passes its validation state.
- Short-lived English feature branches (`feat/3d-viewer`, `exp/lora-smoke-test`) when work is risky or parallel; merged locally without force-push.
- No force-push, no rewriting published history, ever.
- Remote operations (push, GitHub Project for public planning) begin only after one-time explicit approval; until then all work is local.

## Commit style

English Conventional Commits — `type(scope): imperative description`. Types in use: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`. Scopes in use: `repo`, `viewer`, `api`, `web`, `dataset`, `training`, `inference`, `evaluation`, `experiments`, `research`, `process`, `technical`, `architecture`, `project`, `deploy`, `report`, `presentation`.

Commits are atomic: one coherent validated unit each, created automatically as soon as the unit passes the pre-commit checklist (status → diff review → deliberate staging → format/lint/test/build where relevant → secret scan → large-binary check → docs updated). Vague messages and AI co-author trailers are forbidden.

## What never enters history

Secrets/`.env`, personal images, raw datasets, model weights and caches, `node_modules`, venvs, build caches, sensitive logs, unapproved large binaries (enforced by `.gitignore` + per-commit staged-content review).
