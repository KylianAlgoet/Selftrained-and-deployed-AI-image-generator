import { describe, expect, it, vi } from 'vitest'
import { ApiError, absoluteUrl, apiBaseUrl, fetchStyles, generate } from './client'

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    blob: async () => new Blob(),
  } as Response
}

/** Await a call that must reject, and return the ApiError it rejected with. */
async function rejection(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise
  } catch (error) {
    return error as ApiError
  }
  throw new Error('expected the request to reject, but it resolved')
}

const params = {
  prompt: 'a coiled serpent',
  style: 'minimal-geometric',
  seed: 42,
  loraWeight: 0.7,
  ipAdapterScale: 0.55,
}

describe('base url', () => {
  it('falls back to the local API when nothing is configured', () => {
    expect(apiBaseUrl()).toMatch(/^http/)
  })

  it('leaves an absolute url alone and prefixes a relative one', () => {
    expect(absoluteUrl('https://example.test/x.png')).toBe('https://example.test/x.png')
    expect(absoluteUrl('/api/generated/abc')).toBe(`${apiBaseUrl()}/api/generated/abc`)
  })
})

describe('generate', () => {
  it('posts multipart form data with the expected fields', async () => {
    let captured: FormData | undefined
    const fetchImpl = vi.fn(async (_url: string, init?: RequestInit) => {
      captured = init?.body as FormData
      return jsonResponse({ generation_id: 'x', status: 'completed', image_url: '/i', metadata: {}, warnings: [] })
    }) as unknown as typeof fetch

    await generate(params, { fetchImpl })

    expect(captured?.get('prompt')).toBe('a coiled serpent')
    expect(captured?.get('style')).toBe('minimal-geometric')
    expect(captured?.get('seed')).toBe('42')
    expect(captured?.get('lora_weight')).toBe('0.7')
    expect(captured?.get('ip_adapter_scale')).toBe('0.55')
    expect(captured?.get('reference_image')).toBeNull()
  })

  it('omits the seed when it is not supplied, so the server default applies', async () => {
    let captured: FormData | undefined
    const fetchImpl = vi.fn(async (_url: string, init?: RequestInit) => {
      captured = init?.body as FormData
      return jsonResponse({ generation_id: 'x', status: 'completed', image_url: '/i', metadata: {}, warnings: [] })
    }) as unknown as typeof fetch

    await generate({ ...params, seed: undefined }, { fetchImpl })
    expect(captured?.get('seed')).toBeNull()
  })

  it('attaches a reference image when one is chosen', async () => {
    let captured: FormData | undefined
    const fetchImpl = vi.fn(async (_url: string, init?: RequestInit) => {
      captured = init?.body as FormData
      return jsonResponse({ generation_id: 'x', status: 'completed', image_url: '/i', metadata: {}, warnings: [] })
    }) as unknown as typeof fetch

    const file = new File([new Uint8Array([1, 2, 3])], 'ref.png', { type: 'image/png' })
    await generate({ ...params, referenceImage: file }, { fetchImpl })
    expect(captured?.get('reference_image')).toBeInstanceOf(File)
  })

  it('surfaces a validation failure with its field', async () => {
    const fetchImpl = (async () =>
      jsonResponse({ error: 'validation_failed', detail: 'Describe what to generate.', field: 'prompt' }, 422)) as unknown as typeof fetch

    await expect(generate(params, { fetchImpl })).rejects.toMatchObject({
      status: 422,
      code: 'validation_failed',
      field: 'prompt',
    })
  })

  it('marks a busy response as busy rather than as a failure', async () => {
    const fetchImpl = (async () =>
      jsonResponse({ error: 'generation_in_progress', detail: 'The GPU is busy.' }, 409)) as unknown as typeof fetch

    const error = await rejection(generate(params, { fetchImpl }))
    expect(error).toBeInstanceOf(ApiError)
    expect(error.isBusy).toBe(true)
    expect(error.isTimeout).toBe(false)
    expect(error.isUnavailable).toBe(false)
  })

  it('recognises a timeout and an unavailable backend', async () => {
    const timeout = (async () => jsonResponse({ error: 'generation_timeout', detail: 'too long' }, 504)) as unknown as typeof fetch
    const unavailable = (async () => jsonResponse({ error: 'model_unavailable', detail: 'no model' }, 503)) as unknown as typeof fetch

    const t = await rejection(generate(params, { fetchImpl: timeout }))
    expect(t.status).toBe(504)
    expect(t.isTimeout).toBe(true)

    const u = await rejection(generate(params, { fetchImpl: unavailable }))
    expect(u.isUnavailable).toBe(true)
  })

  it('still produces a usable error when the body is not JSON', async () => {
    const fetchImpl = (async () =>
      ({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('not json')
        },
      }) as unknown as Response) as unknown as typeof fetch

    const error = await rejection(generate(params, { fetchImpl }))
    expect(error.status).toBe(500)
    expect(error.message).toContain('500')
  })
})

describe('fetchStyles', () => {
  it('returns the style list', async () => {
    const fetchImpl = (async () =>
      jsonResponse({
        styles: [{ key: 'ukiyo-e', label: 'Ukiyo-e woodblock', outcome: 'PASS' }],
        default_lora_weight: 0.7,
        default_ip_adapter_scale: 0.55,
        width: 512,
        height: 1536,
      })) as unknown as typeof fetch

    const styles = await fetchStyles({ fetchImpl })
    expect(styles.styles[0].key).toBe('ukiyo-e')
    expect(styles.default_lora_weight).toBe(0.7)
    expect(styles.height).toBe(1536)
  })

  it('throws an ApiError when the backend is down', async () => {
    const fetchImpl = (async () => jsonResponse({ error: 'model_unavailable', detail: 'down' }, 503)) as unknown as typeof fetch
    await expect(fetchStyles({ fetchImpl })).rejects.toBeInstanceOf(ApiError)
  })
})
