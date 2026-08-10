/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // The E2E instrumentation gate. A `define` rather than
    // `import.meta.env.VITE_E2E`, because only a define is guaranteed to be
    // substituted literally: `false && <Probe />` is then dead code, and the
    // probe plus the handle name disappear from the bundle instead of merely
    // being switched off inside it. `npm run verify:no-e2e-handle` asserts that
    // after every ordinary build.
    //
    // Set by playwright.config.ts for the suite's own build. Unset everywhere
    // else, including production, where this is exactly `false`.
    __DECKFORGE_E2E__: JSON.stringify(process.env.VITE_E2E === '1'),
  },
  test: {
    // Default to the node environment; DOM-dependent test files opt in to
    // jsdom via a `// @vitest-environment jsdom` docblock.
    //
    // jsdom stays pinned to 26.x. The ORIGINAL reason no longer applies: the
    // pin was taken because jsdom 27's CSS chain needs Node >= 20.19 and the
    // audited Node was 20.18.0, but this machine now runs Node 24.18.0 (the
    // drift is recorded in docs/technical/environment-audit.md, M8 update).
    // It is kept because 26.1.0 is the version the whole vitest suite was
    // validated against and there is no defect asking for the move - not
    // because Node still forbids 27.
    environment: 'node',
    // The Playwright suite lives in e2e/ and its files match vitest's default
    // `*.spec.ts` pattern, so without this vitest collects them, fails to
    // resolve @playwright/test and reports six broken test files. The two
    // runners own different directories: vitest owns src/, Playwright owns e2e/.
    exclude: ['**/node_modules/**', '**/dist/**', 'e2e/**'],
  },
})
