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

  /**
   * BUDGETS: 60 s / 10 s locally, 180 s / 45 s on CI. The CI numbers are floors
   * taken from a measurement, not headroom picked to make something pass.
   *
   * The trace of run #7's last failing attempt
   * (docs/evidence/M8/ci/runner-stall-trace.md) recorded, in one test:
   *
   *   fill into a textbox                21.58 s
   *   click a button                     37.15 s
   *   -> 59.1 s gone before the assertion under test even began
   *   one mocked response fulfilled      12.78 s   (from a frozen fixture, in-process)
   *
   * So a 60 s per-test timeout cannot survive a fill and a click, and a 10 s
   * expect timeout cannot survive a single response fulfilment. Neither limit
   * was measuring the application any more; both were measuring the runner.
   *
   * THIS IS NOT A FIX AND MUST NOT BE REPORTED AS ONE. The stall is real and
   * unexplained - a hypothesis about continuously rendered software-rasterised
   * WebGL starving a two-core runner is recorded in that document and is
   * explicitly unmeasured. Raising a budget accommodates the environment; it
   * does not improve it.
   *
   * Local values are deliberately left alone. A scenario that needs more than
   * 60 s on the validated machine has found something, and hiding that behind a
   * CI-sized budget would remove the suite's only performance signal - the whole
   * suite runs in ~1.4 minutes here.
   */
  timeout: process.env.CI ? 180_000 : 60_000,
  expect: { timeout: process.env.CI ? 45_000 : 10_000 },

  // Serial. The suite drives one application against scripted progress
  // sequences, and parallel workers on one machine make WebGL timing noisy for
  // no gain on a suite this size.
  fullyParallel: false,
  workers: 1,

  /**
   * RETRIES ON CI ONLY, AND WHAT THEY DO AND DO NOT HIDE.
   *
   * Locally this stays 0: a test that fails here has found something, and
   * retrying it would only delay reading the message.
   *
   * On a GitHub runner the suite is measurably marginal, and the evidence is
   * run-to-run variance rather than any one slow test. Between runs #5 and #6 of
   * the same suite:
   *
   *   `?review=1 restores both review tools`   2.6 s  ->  56.8 s   (22x)
   *   `409 is presented as busy`               FAIL   ->   6.4 s
   *   `submits ... multipart form fields`      5.9 s  ->  FAIL
   *
   * Run #4 failed 1 scenario, #5 failed 3, #6 failed 6 - a different subset each
   * time, several of them waiting on a MOCKED 4 s response that never arrived
   * within 45 s. That is the runner stalling, not the application.
   *
   * **This does mask genuine flakiness, and that is a limitation, not a fix.**
   * It is recorded as one in docs/evidence/M8/ci/. What it does not mask is a
   * deterministic defect: that still fails all three attempts. The choice is
   * between a suite whose red/green carries no information because the
   * environment is noisy, and one where red means something.
   */
  retries: process.env.CI ? 2 : 0,

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
