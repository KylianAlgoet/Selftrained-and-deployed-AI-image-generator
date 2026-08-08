/**
 * Typed access to the frozen API fixtures.
 *
 * THE DATA LIVES IN `api-fixtures.json`, NOT HERE, and that is deliberate.
 * `apps/api/tests/test_e2e_fixture_contract.py` validates every entry against
 * the real Pydantic models in `apps/api/schemas.py`, so a field renamed in the
 * backend breaks a Python test instead of leaving this suite happily proving
 * that the application works against a response shape the server stopped
 * sending. Keeping the fixtures as plain JSON is what lets that check exist
 * without making the Python suite depend on npm.
 *
 * The file is read at runtime rather than imported, because this package is
 * ESM and a JSON import would need an import attribute that Playwright's
 * transpiler and Node disagree about. A synchronous read in test-support code
 * costs nothing and avoids the whole argument.
 */

import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

export interface ProgressSnapshot {
  operation_id: string | null
  status: 'idle' | 'generating' | 'completed' | 'failed'
  stage:
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
  current_step: number
  total_steps: number
  denoising_fraction: number
  elapsed_seconds: number
  estimated_remaining_seconds: number | null
  pipeline_loaded: boolean
}

export interface ErrorFixture {
  status: number
  body: { error: string; detail: string; field?: string }
}

interface Fixtures {
  GENERATION_ID: string
  OPERATION_ID: string
  STYLES_RESPONSE: {
    styles: {
      key: string
      label: string
      outcome: string
      limitation: string
      trigger: string
      run_id: string
      checkpoint_step: number
      default_lora_weight: number
      lora_weight_min: number
      lora_weight_max: number
    }[]
    default_lora_weight: number
    default_ip_adapter_scale: number
    ip_adapter_scale_min: number
    ip_adapter_scale_max: number
    width: number
    height: number
  }
  GENERATE_RESPONSE: Record<string, unknown>
  GENERATE_RESPONSE_PARTIAL_PASS: Record<string, unknown>
  ERROR_BUSY: ErrorFixture
  ERROR_TIMEOUT: ErrorFixture
  ERROR_MODEL_UNAVAILABLE: ErrorFixture
  ERROR_VALIDATION_PROMPT: ErrorFixture
  PROGRESS_IDLE: ProgressSnapshot
  PROGRESS_SEQUENCE: ProgressSnapshot[]
  PROGRESS_COLD_LOAD: ProgressSnapshot[]
}

const HERE = dirname(fileURLToPath(import.meta.url))

const FIXTURES: Fixtures = JSON.parse(
  readFileSync(join(HERE, 'api-fixtures.json'), 'utf8'),
) as Fixtures

export const GENERATION_ID = FIXTURES.GENERATION_ID
export const OPERATION_ID = FIXTURES.OPERATION_ID
export const STYLES_RESPONSE = FIXTURES.STYLES_RESPONSE
export const GENERATE_RESPONSE = FIXTURES.GENERATE_RESPONSE
export const GENERATE_RESPONSE_PARTIAL_PASS = FIXTURES.GENERATE_RESPONSE_PARTIAL_PASS
export const ERROR_BUSY = FIXTURES.ERROR_BUSY
export const ERROR_TIMEOUT = FIXTURES.ERROR_TIMEOUT
export const ERROR_MODEL_UNAVAILABLE = FIXTURES.ERROR_MODEL_UNAVAILABLE
export const ERROR_VALIDATION_PROMPT = FIXTURES.ERROR_VALIDATION_PROMPT
export const PROGRESS_IDLE = FIXTURES.PROGRESS_IDLE
export const PROGRESS_SEQUENCE = FIXTURES.PROGRESS_SEQUENCE
export const PROGRESS_COLD_LOAD = FIXTURES.PROGRESS_COLD_LOAD
