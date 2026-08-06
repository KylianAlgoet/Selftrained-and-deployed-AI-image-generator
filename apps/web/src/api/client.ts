/**
 * Typed client for the DeckForge AI backend.
 *
 * The backend answers with JSON and a URL, never with an image body, so a
 * result is a small object plus a link the browser fetches separately.
 */

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000'

export function apiBaseUrl(): string {
  const configured = import.meta.env?.VITE_API_BASE_URL
  return (configured && String(configured)) || DEFAULT_BASE_URL
}

export function absoluteUrl(path: string): string {
  return path.startsWith('http') ? path : `${apiBaseUrl()}${path}`
}

export interface GenerationMetadata {
  generation_id: string
  created_utc: string
  style: string
  style_label: string
  style_outcome: string
  style_limitation: string
  prompt: string
  prompt_sha256: string
  negative_prompt_sha256: string
  seed: number
  steps: number
  steps_run: number
  guidance_scale: number
  scheduler: string
  width: number
  height: number
  base_model_repo_id: string
  base_model_revision: string
  lora_run_id: string
  lora_checkpoint_step: number
  lora_sha256: string
  lora_weight: number
  active_adapters: string[]
  live_lora_modules: number
  ip_adapter_repo_id: string
  ip_adapter_revision: string
  ip_adapter_scale: number
  reference_present: boolean
  generate_seconds: number
  peak_allocated_mb: number
  peak_device_used_mb: number
  device_total_mb: number
  spare_device_mb: number
  image_sha256: string
}

export interface GenerateResponse {
  generation_id: string
  status: string
  image_url: string
  metadata: GenerationMetadata
  warnings: string[]
}

export interface StyleInfo {
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
}

export interface StylesResponse {
  styles: StyleInfo[]
  default_lora_weight: number
  default_ip_adapter_scale: number
  ip_adapter_scale_min: number
  ip_adapter_scale_max: number
  width: number
  height: number
}

/** A failure the UI can act on: `code` decides the message, `field` the focus. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly field?: string

  constructor(status: number, code: string, message: string, field?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.field = field
  }

  /** Busy is not a failure: the request was refused so the GPU stays sane. */
  get isBusy(): boolean {
    return this.status === 409
  }

  get isTimeout(): boolean {
    return this.status === 504
  }

  get isUnavailable(): boolean {
    return this.status === 503
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let code = 'request_failed'
  let detail = `The server responded with ${response.status}.`
  let field: string | undefined
  try {
    const body = await response.json()
    if (body?.error) code = String(body.error)
    if (body?.detail) detail = String(body.detail)
    if (body?.field) field = String(body.field)
  } catch {
    // A non-JSON error body is itself only worth the status code.
  }
  return new ApiError(response.status, code, detail, field)
}

export interface GenerateParams {
  prompt: string
  style: string
  seed?: number
  loraWeight: number
  ipAdapterScale: number
  referenceImage?: File | null
}

export async function generate(
  params: GenerateParams,
  init: { signal?: AbortSignal; fetchImpl?: typeof fetch } = {},
): Promise<GenerateResponse> {
  const form = new FormData()
  form.append('prompt', params.prompt)
  form.append('style', params.style)
  if (params.seed !== undefined && params.seed !== null && !Number.isNaN(params.seed)) {
    form.append('seed', String(params.seed))
  }
  form.append('lora_weight', String(params.loraWeight))
  form.append('ip_adapter_scale', String(params.ipAdapterScale))
  if (params.referenceImage) {
    form.append('reference_image', params.referenceImage)
  }

  const doFetch = init.fetchImpl ?? fetch
  const response = await doFetch(`${apiBaseUrl()}/api/generate`, {
    method: 'POST',
    body: form,
    signal: init.signal,
  })

  if (!response.ok) throw await parseError(response)
  return (await response.json()) as GenerateResponse
}

export async function fetchStyles(
  init: { fetchImpl?: typeof fetch } = {},
): Promise<StylesResponse> {
  const doFetch = init.fetchImpl ?? fetch
  const response = await doFetch(`${apiBaseUrl()}/api/styles`)
  if (!response.ok) throw await parseError(response)
  return (await response.json()) as StylesResponse
}

/** Fetch the finished PNG as a blob so it can be composed and downloaded. */
export async function fetchGeneratedImage(
  imageUrl: string,
  init: { fetchImpl?: typeof fetch } = {},
): Promise<Blob> {
  const doFetch = init.fetchImpl ?? fetch
  const response = await doFetch(absoluteUrl(imageUrl))
  if (!response.ok) throw await parseError(response)
  return await response.blob()
}
