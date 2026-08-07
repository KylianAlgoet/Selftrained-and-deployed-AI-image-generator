/**
 * Client for the read-only generation-progress endpoint.
 *
 * Supplemental, never authoritative. `POST /api/generate` is the request that
 * decides whether a generation succeeded; this endpoint only describes how far
 * along it is. Every caller here must therefore treat a failure as "no
 * telemetry", not as "the generation failed" - see `useGenerationProgress`.
 */

import { apiBaseUrl } from './client'

/** The stages the backend owns. `applying-texture` is deliberately absent: it
 *  happens in the browser after the response arrives, so it is not GPU progress
 *  and the server never claims it. */
export type ProgressStage =
  | 'idle'
  | 'preparing'
  | 'loading-model'
  | 'loading-style'
  | 'preparing-reference'
  | 'denoising'
  | 'decoding'
  | 'saving'
  | 'completed'
  | 'failed'

export type ProgressStatus = 'idle' | 'generating' | 'completed' | 'failed'

export interface ProgressTelemetry {
  operation_id: string | null
  status: ProgressStatus
  stage: ProgressStage
  current_step: number
  total_steps: number
  denoising_fraction: number
  elapsed_seconds: number
  /** Null whenever no honest estimate exists — which is most of the time. */
  estimated_remaining_seconds: number | null
  pipeline_loaded: boolean
}

export const PROGRESS_ENDPOINT = '/api/generation-progress'

export async function fetchProgress(
  init: { signal?: AbortSignal; fetchImpl?: typeof fetch } = {},
): Promise<ProgressTelemetry> {
  const doFetch = init.fetchImpl ?? fetch
  const response = await doFetch(`${apiBaseUrl()}${PROGRESS_ENDPOINT}`, {
    signal: init.signal,
  })
  if (!response.ok) throw new Error(`progress unavailable (${response.status})`)
  return (await response.json()) as ProgressTelemetry
}
