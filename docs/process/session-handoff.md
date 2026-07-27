# Session handoff

**Last updated:** 2026-07-27 (Prototype 0 / M1 session)

## Current state

Phase 0 complete and pushed. Public planning live (project + issues #1–#12; M0 closed). **Prototype 0 (M1) implemented and validated**: interactive 3D deck viewer in `apps/web` (React 19 + Vite 6.4.3 + R3F), procedural deck geometry with documented UV convention (v=1 = nose), correct first-render orientation (honestly documented; labelled inverted-UV demonstration for the defect illustration), runtime decal swap, orbit/zoom/reset, 13 passing Vitest tests, evidence in `docs/evidence/prototype-0/`, DR-005 recorded.

## Uncommitted changes

None expected at handoff — verify with `git status`.

## Latest commits (M1 sequence, 2026-07-27)

```
(docs process commit — see git log)
2dba9d4 docs(prototypes): record prototype 0 results, evidence, and deck-source decision
634ff59 feat(viewer): render interactive deck scene with swappable decal textures
148a2c9 feat(viewer): raise nose kick above tail kick for physical orientation asymmetry
b10608c feat(viewer): add procedural skateboard deck geometry with explicit UV mapping
36150ef feat(web): scaffold React + Vite + TypeScript viewer app
```

## Blockers

- None technical. Awaiting Kylian's visual sign-off on the viewer (requested in the M1 milestone report) and approval to start M2.

## Facts a new session must know

- Repo root: `C:\Expert Lab\Selftrained-and-deployed-AI-image-generator`; use `py -V:3.11` for ML (default 3.14 is PyTorch-incompatible); 8 GB VRAM constraint.
- `apps/web`: `npm run dev` (port 5173), `npm run test`, `npm run build`. jsdom pinned to 26.x (jsdom 27 needs Node ≥20.19). Vitest default env is `node`; DOM tests opt in via docblock.
- Deck UV convention: decal face u∈[0,1] across width, v=1 at nose; Three.js default flipY puts image top at the nose. Dev-only `window.__deckforge` render hook exists for evidence/E2E captures.
- Issue #2 (M1) to be closed on sign-off; board auto-moves it to Done.

## Next action

M2 — dataset research and dataset pipeline (issue #3, planned Jul 30–Aug 3, can start early given the ~1.5-day buffer gained). Start in Plan mode: style definitions, licence-safe sources, manifest schema implementation, validation scripts.
