/// <reference types="vite/client" />

/**
 * Build-time only: true when the bundle was built with `VITE_E2E=1`, which the
 * Playwright `webServer` sets and nothing else does. Vite replaces every
 * occurrence with a literal boolean (see `vite.config.ts`), so a `false` value
 * makes the guarded code unreachable and the bundler removes it.
 *
 * Never read this to change what a user sees. It gates test instrumentation
 * only.
 */
declare const __DECKFORGE_E2E__: boolean
