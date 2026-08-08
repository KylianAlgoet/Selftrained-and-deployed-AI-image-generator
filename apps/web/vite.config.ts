/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
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
  },
})
