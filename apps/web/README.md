# DeckForge AI — frontend

React + TypeScript + Vite, with React Three Fiber for the interactive 3D deck preview.
Stack rationale and the alternatives weighed against it: [`DR-003`](../../docs/decisions/DR-003-frontend-3d-stack.md).

This is one half of a two-process application. It talks to the FastAPI service on
port 8000 and does no model work of its own. **Start both together with
[`scripts/start-demo.ps1`](../../scripts/start-demo.ps1)** rather than running this
package alone — the full procedure is in the
[deployment runbook](../../docs/deployment/runbook.md).

## Commands

```bash
npm ci                  # install from the lockfile
npm run dev             # dev server on http://localhost:5173
npm run build           # tsc -b && vite build
npm run preview         # serve the built bundle on 4173
npm run lint            # eslint
npm run test            # vitest
npm run test:e2e        # Playwright, against the BUILT frontend with /api/** mocked
npm run typecheck:e2e   # type-check the e2e project separately
```

`npx playwright install chromium` is needed once before the first E2E run.

## Layout

```
src/viewer      the 3D deck: geometry, UV convention, texture swap, camera probe
src/deck        deck geometry and the two texture-fit strategies
src/generate    the generation form, progress display and result panel
src/api         the typed client for the FastAPI service
src/ui          the shared status-message component
e2e             Playwright specs and the frozen API fixtures they answer from
```

The E2E suite mocks the API at the network boundary and never loads the model, so it
runs without a GPU. A pytest validates those fixtures against the real Pydantic
models, so the mock cannot drift away from the contract it stands in for.

## Notes worth knowing before changing anything

- **Review-only controls** (the texture-fit selector and the inverted-UV
  demonstration) are hidden in production and restored with `?review=1`. A test
  asserts the production interface exposes neither.
- **The decal is 1:3 and the deck UV domain is 1:3.902.** `full-surface` is the
  production default and stretches by 1.3008×; the interface states this to the user.
  [`DR-012`](../../docs/decisions/DR-012-deck-texture-fit.md) records the decision and
  the rejected alternative, which is still selectable in review mode.
- **Progress reporting never invents a number.** Only denoising has a real
  denominator; every other stage publishes a name and no percentage
  ([`DR-013`](../../docs/decisions/DR-013-generation-progress-telemetry.md)).

Project overview and research documentation: [repository README](../../README.md).
