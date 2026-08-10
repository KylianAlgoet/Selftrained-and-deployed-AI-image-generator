import { defineConfig, devices } from '@playwright/test'

/**
 * End-to-end configuration for DeckForge AI (M8).
 *
 * THREE DECISIONS, EACH LOAD-BEARING.
 *
 * 1. **The suite runs against the BUILT frontend, never the dev server.** The
 *    `webServer` command builds and then previews, so what is exercised is the
 *    bundle that ships - with production minification, the production
 *    `import.meta.env` values and the real asset pipeline. A dev-server suite
 *    would pass happily while the built application was broken.
 *
 * 2. **The API boundary is mocked; nothing above it is.** Every `/api/**` call is
 *    intercepted (see `e2e/fixtures/api.ts`) and answered from frozen fixtures.
 *    React, React Three Fiber, the WebGL canvas, the texture pipeline, the
 *    progress polling loop and the download paths all run for real. The mock sits
 *    exactly at the contract, which is the boundary worth testing at.
 *
 * 3. **No GPU, no model, no weights, no network.** The suite must pass on a
 *    machine that has never downloaded a checkpoint - that is what lets it run in
 *    CI, and it is why the M8 acceptance criterion can be met without spending
 *    generation budget. The real model path is evidenced separately by
 *    `scripts/validate_p5_api.py` against an actual uvicorn process.
 *
 * Chromium only, deliberately. Cross-browser rendering is not an M8 acceptance
 * criterion, and three browser downloads would cost roughly 900 MB to answer a
 * question nobody asked.
 */

export default defineConfig({
  testDir: './e2e',
  // The deck viewer initialises WebGL; a cold first paint is legitimately slow.
  timeout: 60_000,
  expect: { timeout: 10_000 },

  // Serial. The suite drives one application against scripted progress
  // sequences, and parallel workers on one machine make WebGL timing noisy for
  // no gain on a suite this size.
  fullyParallel: false,
  workers: 1,
  retries: 0,

  reporter: [['list'], ['json', { outputFile: 'test-results/e2e-results.json' }]],

  use: {
    baseURL: 'http://localhost:4173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 },
        // The viewer needs a real GL context. Chromium's headless SwiftShader
        // provides one; without this the canvas silently fails to initialise
        // and every viewer assertion becomes a false negative.
        launchOptions: {
          args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
        },
      },
    },
  ],

  webServer: {
    // Build every run. A stale `dist/` would let the suite pass against code
    // that is no longer in `src/`, which is the one failure a build-then-preview
    // suite exists to prevent.
    command: 'npm run build && npm run preview -- --port 4173 --strictPort',
    // The ONE difference between the suite's bundle and the shipped one: it
    // carries the read-only camera read-out that `camera-preservation` measures
    // against (see src/viewer/e2eCameraState.ts). Nothing else in the build
    // changes, and the flag is set here rather than in a script so it cannot
    // leak into a manual `npm run build`.
    env: { VITE_E2E: '1' },
    url: 'http://localhost:4173',
    reuseExistingServer: false,
    timeout: 180_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
})
