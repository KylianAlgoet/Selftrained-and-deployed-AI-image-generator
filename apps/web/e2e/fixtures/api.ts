/**
 * Route handlers standing in for the FastAPI service.
 *
 * The frontend talks to `http://127.0.0.1:8000` by default (see
 * `apiBaseUrl()`), which is a different origin from the preview server, so
 * every fulfilled response carries CORS headers. Without them the browser would
 * reject the mock and the failure would look like an application bug.
 *
 * `recordRequests` returns a live array rather than a count. Several tests
 * assert on what was NOT sent - most importantly that uploading your own decal
 * never issues `POST /api/generate` - and a request log is the only way to prove
 * a negative like that.
 */

import type { Page, Request, Route } from '@playwright/test'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import {
  GENERATE_RESPONSE,
  PROGRESS_IDLE,
  PROGRESS_SEQUENCE,
  STYLES_RESPONSE,
  type ProgressSnapshot,
} from './responses'

const HERE = dirname(fileURLToPath(import.meta.url))
export const DECAL_PNG = join(HERE, 'decal.png')

const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET, POST, OPTIONS',
  'access-control-allow-headers': '*',
}

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    headers: CORS,
    body: JSON.stringify(body),
  })
}

/** Every `/api/**` request the page makes, in order. */
export function recordRequests(page: Page): Request[] {
  const seen: Request[] = []
  page.on('request', (request) => {
    if (request.url().includes('/api/')) seen.push(request)
  })
  return seen
}

export function generateRequests(seen: Request[]): Request[] {
  return seen.filter((r) => r.method() === 'POST' && r.url().includes('/api/generate'))
}

export interface ApiMockOptions {
  /** How long `POST /api/generate` takes to answer. Long enough that the
   *  progress loop polls several times, since that is what is under test. */
  generateDelayMs?: number
  /** Replace the success response with an error status and body. */
  generateError?: { status: number; body: unknown }
  /** The response body for a successful generation. */
  generateResponse?: unknown
  /** Telemetry snapshots. See `progressMode` for how they are served. */
  progress?: ProgressSnapshot[]
  /**
   * How the progress snapshots advance.
   *
   * `'auto'` (default) advances one snapshot per poll — a wall-clock race, and
   * fine for tests that assert polling BEHAVIOUR rather than a specific state.
   *
   * `'gated'` serves whichever snapshot the test selects and **never advances on
   * its own**. This is what makes the state-specific progress assertions
   * deterministic: see the note on `ApiController` below.
   */
  progressMode?: 'auto' | 'gated'
  /**
   * Hold `POST /api/generate` open until `controller.completeGeneration()`.
   *
   * Preferred over `generateDelayMs` for progress tests: a fixed delay is a bet
   * that the browser will render the state under test before the clock runs
   * out, and on a slow runner that bet loses.
   */
  gateGenerate?: boolean
  /** Fail `GET /api/styles`, to exercise the offline banner. */
  stylesUnavailable?: boolean
}

/**
 * Test-side handle on the mocked backend.
 *
 * WHY THIS EXISTS — the defect it fixes.
 *
 * The first version advanced the progress sequence by one snapshot per GET, and
 * the frontend polls about every 750 ms. Every transient state therefore had a
 * wall-clock lifetime of one poll, whether or not the browser had rendered it.
 * Locally that was invisible. On a GitHub runner with no GPU — Chromium falling
 * back to SwiftShader, the same suite taking 14.7 minutes against 84 seconds
 * here — React consistently lagged the polls, so `denoising step 14`,
 * `loading-model` and `decoding` were consumed before they were ever painted,
 * and six progress tests failed on states that the application had produced
 * correctly.
 *
 * The fix removes the clock from the equation: in `'gated'` mode the mock holds
 * one snapshot until the test says otherwise, so a slow renderer makes a test
 * slower and never makes it fail.
 *
 * This is TEST INFRASTRUCTURE ONLY. The production polling interval, the
 * progress hook and the panel are untouched.
 */
export interface ApiController {
  /** Index of the snapshot currently being served. */
  progressIndex(): number
  /** Serve `progress[index]` from now on. Gated mode only. */
  showProgress(index: number): void
  /** Move to the next snapshot, stopping at the last. Gated mode only. */
  advanceProgress(): void
  /** How many progress GETs have been answered since the generation started. */
  progressPolls(): number
  /** Release a gated `POST /api/generate` so it answers. */
  completeGeneration(): void
  /** Whether the POST has been received yet. */
  generateStarted(): boolean
}

/**
 * Install the whole mocked backend on one page.
 *
 * Call before `page.goto`, because the styles request fires on mount.
 */
export async function mockApi(
  page: Page,
  options: ApiMockOptions = {},
): Promise<ApiController> {
  const {
    generateDelayMs = 4_000,
    generateError,
    generateResponse = GENERATE_RESPONSE,
    progress = PROGRESS_SEQUENCE,
    progressMode = 'auto',
    gateGenerate = false,
    stylesUnavailable = false,
  } = options

  let cursor = 0
  let polls = 0
  let started = false

  // Created up front so `completeGeneration()` works whether it is called
  // before or after the POST arrives.
  let releaseGenerate!: () => void
  const generateGate = new Promise<void>((resolve) => {
    releaseGenerate = resolve
  })

  await page.route('**/api/styles', (route) => {
    if (stylesUnavailable) {
      return route.fulfill({
        status: 503,
        contentType: 'application/json',
        headers: CORS,
        body: JSON.stringify({ error: 'model_unavailable', detail: 'unavailable' }),
      })
    }
    return json(route, STYLES_RESPONSE)
  })

  await page.route('**/api/generation-progress', (route) => {
    // Before a generation starts the real endpoint reports idle or the PREVIOUS
    // operation. Serving idle here is what lets the stale-operation guard in
    // `useGenerationProgress` be exercised rather than bypassed.
    if (!started) return json(route, PROGRESS_IDLE)
    polls += 1
    const snapshot = progress[Math.min(cursor, progress.length - 1)]
    // Gated mode NEVER advances here. That is the whole point.
    if (progressMode === 'auto') cursor += 1
    return json(route, snapshot)
  })

  await page.route('**/api/generate', async (route) => {
    started = true
    cursor = 0
    polls = 0
    if (gateGenerate) {
      await generateGate
    } else if (generateDelayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, generateDelayMs))
    }
    if (generateError) {
      return route.fulfill({
        status: generateError.status,
        contentType: 'application/json',
        headers: CORS,
        body: JSON.stringify(generateError.body),
      })
    }
    return json(route, generateResponse)
  })

  await page.route('**/api/generated/**', (route) =>
    route.fulfill({ status: 200, contentType: 'image/png', headers: CORS, path: DECAL_PNG }),
  )

  const controller: ApiController = {
    progressIndex: () => cursor,
    showProgress: (index: number) => {
      cursor = Math.max(0, Math.min(index, progress.length - 1))
    },
    advanceProgress: () => {
      cursor = Math.min(cursor + 1, progress.length - 1)
    },
    progressPolls: () => polls,
    completeGeneration: () => releaseGenerate(),
    generateStarted: () => started,
  }

  await page.route('**/api/health', (route) =>
    json(route, {
      status: 'ok',
      pid: 1234,
      pipeline_loaded: false,
      active_style: null,
      generation_in_progress: false,
      cuda_available: true,
      device_name: 'NVIDIA GeForce RTX 4060 Laptop GPU',
      device_total_mb: 8187.5,
      device_used_mb: 0,
      allocated_mb: 0,
      single_worker_guard: 'enforced',
    }),
  )

  return controller
}

/**
 * Mock a backend that returns one error IMMEDIATELY, with no artificial delay.
 *
 * For tests whose subject is error CLASSIFICATION AND RENDERING - does a 409
 * read as busy rather than broken, does a 504 carry its step counts, does a 503
 * leak a path - the time the server spends before answering is not part of the
 * claim. Simulating it only creates a race.
 *
 * That race was real. On the CI runner (Windows Server 2025, Chromium on
 * software WebGL, the suite taking ~15.9 minutes against 84 seconds locally)
 * even a 200 ms delayed route left the 504 and 503 tests still showing
 * "Generating..." after the 10 second assertion window, while every assertion
 * about the error itself was correct. The application classified and rendered
 * both responses properly; the tests were racing the mock's timer.
 *
 * Loading-state-before-a-slow-response is a separate claim and is covered
 * separately, deterministically, in `progress.spec.ts`.
 */
export async function mockImmediateError(
  page: Page,
  error: { status: number; body: unknown },
  options: Omit<ApiMockOptions, 'generateError' | 'generateDelayMs' | 'gateGenerate'> = {},
): Promise<ApiController> {
  return mockApi(page, { ...options, generateError: error, generateDelayMs: 0 })
}

/** A file the browser will refuse to decode, though its type claims PNG. */
export const CORRUPT_PNG = {
  name: 'broken.png',
  mimeType: 'image/png',
  buffer: Buffer.from('this is definitely not a png', 'utf8'),
}

/** A file the client-side preflight rejects before any decode is attempted. */
export const WRONG_TYPE_FILE = {
  name: 'notes.txt',
  mimeType: 'text/plain',
  buffer: Buffer.from('plain text', 'utf8'),
}
