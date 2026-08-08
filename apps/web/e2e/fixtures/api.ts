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
  /** Telemetry, consumed one snapshot per poll; the last one repeats. */
  progress?: ProgressSnapshot[]
  /** Fail `GET /api/styles`, to exercise the offline banner. */
  stylesUnavailable?: boolean
}

/**
 * Install the whole mocked backend on one page.
 *
 * Call before `page.goto`, because the styles request fires on mount.
 */
export async function mockApi(page: Page, options: ApiMockOptions = {}): Promise<void> {
  const {
    generateDelayMs = 4_000,
    generateError,
    generateResponse = GENERATE_RESPONSE,
    progress = PROGRESS_SEQUENCE,
    stylesUnavailable = false,
  } = options

  // The progress cursor advances per poll and then holds on the final snapshot,
  // so a slow machine polling extra times sees a stable end state rather than
  // running off the end of the array.
  let cursor = 0
  let generateStarted = false

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
    if (!generateStarted) return json(route, PROGRESS_IDLE)
    const snapshot = progress[Math.min(cursor, progress.length - 1)]
    cursor += 1
    return json(route, snapshot)
  })

  await page.route('**/api/generate', async (route) => {
    generateStarted = true
    cursor = 0
    if (generateDelayMs > 0) {
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
