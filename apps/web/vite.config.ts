/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    // Default to the node environment; DOM-dependent test files opt in to
    // jsdom via a `// @vitest-environment jsdom` docblock. jsdom is pinned to
    // 26.x because jsdom 27's CSS chain requires Node >= 20.19 (audited Node
    // is 20.18.0, see docs/technical/environment-audit.md).
    environment: 'node',
  },
})
