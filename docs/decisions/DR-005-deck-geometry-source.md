# DR-005: Deck model source — procedural geometry with self-made UVs

**Date:** 2026-07-27 · **Status:** accepted (validated by working Prototype 0)

## Context
Prototype 0 needs a 3D skateboard deck whose decal face has a fully controlled UV layout (the research core of RQ9), with zero licensing ambiguity (risk R10) under a 19-day deadline.

## Alternatives
1. **R3F + procedural deck geometry** (self-coded outline, concave, kicktails, explicit UVs)
2. R3F + external glTF deck model (CC0/CC-BY download, per-asset licence verification)
3. Plain Three.js + procedural geometry
4. `<model-viewer>` web component

## Criteria and evaluation
Weighted matrix in the approved M1 plan (criteria: implementation time 4, texture/UV control 5, testability 4, licensing 4, React/MVP integration 4, performance 3, deadline risk 4): procedural+R3F **131/140**, plain Three.js 112, external glTF 86, model-viewer 77.

## Decision
Procedural geometry (`apps/web/src/deck/deckGeometry.ts`): pure function, deterministic, documented UV convention (decal face v=1 at nose), asymmetric nose/tail kicks, material groups separating the decal face. Both test decals are self-authored SVG assets.

## Validation (actual)
13 passing unit tests over UV/geometry invariants; correct first-render orientation confirmed visually in Chrome; runtime texture swap works. See `docs/prototypes/prototype-0.md`.

## Consequences
- No external asset licences to track for the viewer; R10 closed for this component.
- Realism ceiling is lower than a sculpted model; if later milestones need more visual fidelity, the documented fallback is a strictly licence-verified CC0 glTF (the UV convention and texture pipeline stay unchanged).
- Geometry constants become the reference for decal aspect-ratio work (RQ8).
