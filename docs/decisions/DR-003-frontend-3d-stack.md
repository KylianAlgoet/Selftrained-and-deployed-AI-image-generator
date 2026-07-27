# DR-003: Frontend and 3D stack — React + Vite + TypeScript + React Three Fiber

**Date:** 2026-07-27 · **Status:** accepted, **to be validated by Prototype 0**

## Context
The UI needs a generation form (prompt, negative prompt, upload, style, strength, seed) tightly coupled to an interactive 3D skateboard viewer with runtime texture swapping and correct nose–tail orientation.

## Alternatives
1. **React + Vite + TS + React Three Fiber (drei)**
2. **Plain Three.js + vanilla TypeScript**
3. **SvelteKit + Threlte**

## Criteria and evaluation
Weighted matrix in `docs/03-architecture.md` (D-C): 3D+UI state integration (5), ecosystem (4), type safety (4), testing (4), time-to-first-prototype (4). R3F stack 101/105, Threlte 72, plain Three.js 66.

## Decision
React + Vite + TypeScript with React Three Fiber and drei helpers.

## Consequences
- Prototype 0 is the immediate validation gate; if texture swapping or deck-model loading fails under R3F, the documented fallback is plain Three.js inside the same React shell.
- Vitest for unit tests, Playwright for the E2E flow.
