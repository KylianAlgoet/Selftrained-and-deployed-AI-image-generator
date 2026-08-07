// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { GenerateResponse, StylesResponse } from './api/client'
import type { ProgressTelemetry } from './api/progress'

/**
 * The assembled application, with the GPU, the model and WebGL all replaced.
 *
 * What is genuinely under test here is the wiring the unit tests cannot see:
 * that review-only tools are absent from the production interface, that the
 * previous decal survives a generation, that the viewer is never remounted (a
 * remount is what silently resets the camera), and that polling stops on every
 * exit path.
 */

// --- module doubles ----------------------------------------------------------

let lastViewerTexture: string | null = null

vi.mock('./viewer/DeckViewer', () => ({
  DeckViewer: ({ texture }: { texture: { name?: string } | null }) => {
    lastViewerTexture = texture?.name ?? null
    return <div data-testid="deck-viewer" data-texture={texture?.name ?? 'none'} />
  },
}))

vi.mock('./viewer/deckTextures', () => ({
  imageFromBlob: vi.fn(async () => ({ width: 512, height: 1536 })),
  textureFromCanvas: vi.fn(async () => ({ name: 'generated-texture', dispose: vi.fn() })),
  textureFromUrl: vi.fn(async () => ({ name: 'starter-decal', dispose: vi.fn() })),
}))

vi.mock('./deck/textureFit', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./deck/textureFit')>()
  return {
    ...actual,
    // jsdom has no 2D canvas context, so the real compositor cannot run here.
    // The composition itself is covered by textureFit.test.ts.
    composeDeckTexture: vi.fn(() => ({
      canvas: { width: 512, height: 1536 },
      fit: actual.describeFit(actual.DEFAULT_TEXTURE_FIT_MODE, 512, 1536),
    })),
  }
})

const fetchStyles = vi.fn()
const generate = vi.fn()
const fetchGeneratedImage = vi.fn()

vi.mock('./api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api/client')>()
  return {
    ...actual,
    fetchStyles: (...args: unknown[]) => fetchStyles(...args),
    generate: (...args: unknown[]) => generate(...args),
    fetchGeneratedImage: (...args: unknown[]) => fetchGeneratedImage(...args),
  }
})

const fetchProgress = vi.fn()
vi.mock('./api/progress', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api/progress')>()
  return { ...actual, fetchProgress: (...args: unknown[]) => fetchProgress(...args) }
})

const isReviewMode = vi.fn(() => false)
vi.mock('./reviewMode', () => ({ isReviewMode: () => isReviewMode() }))

import App from './App'

// --- fixtures ----------------------------------------------------------------

const STYLES: StylesResponse = {
  styles: [
    {
      key: 'minimal-geometric',
      label: 'Minimal geometric',
      outcome: 'PASS',
      limitation: '',
      trigger: 'xgeo',
      run_id: 'EXP-027',
      checkpoint_step: 300,
      default_lora_weight: 0.7,
      lora_weight_min: 0.4,
      lora_weight_max: 1.0,
    },
    {
      key: 'retro-poster',
      label: 'Retro silkscreen poster',
      outcome: 'PARTIAL PASS',
      limitation: 'Partial pass: pseudo-text, borders and framed composition can appear.',
      trigger: 'xpst',
      run_id: 'EXP-029',
      checkpoint_step: 300,
      default_lora_weight: 0.7,
      lora_weight_min: 0.4,
      lora_weight_max: 1.0,
    },
  ],
  default_lora_weight: 0.7,
  default_ip_adapter_scale: 0.55,
  ip_adapter_scale_min: 0.4,
  ip_adapter_scale_max: 0.6,
  width: 512,
  height: 1536,
}

const RESPONSE: GenerateResponse = {
  generation_id: 'abcdefghijklmnopqrstuv',
  status: 'completed',
  image_url: '/api/generated/abcdefghijklmnopqrstuv',
  warnings: ['Partial pass: pseudo-text, borders and framed composition can appear.'],
  metadata: {
    generation_id: 'abcdefghijklmnopqrstuv',
    created_utc: '2026-08-07T10:00:00Z',
    style: 'minimal-geometric',
    style_label: 'Minimal geometric',
    style_outcome: 'PASS',
    style_limitation: '',
    prompt: 'xgeo minimal geometric style skateboard decal artwork, a mountain',
    prompt_sha256: 'a'.repeat(64),
    negative_prompt_sha256: 'b'.repeat(64),
    seed: 42,
    steps: 30,
    steps_run: 30,
    guidance_scale: 7.5,
    scheduler: 'DPMSolverMultistep',
    width: 512,
    height: 1536,
    base_model_repo_id: 'runwayml/stable-diffusion-v1-5',
    base_model_revision: '451f4fe161',
    lora_run_id: 'EXP-027',
    lora_checkpoint_step: 300,
    lora_sha256: '2d425838cce59adc51c894e29439b695b98b9e40ef5d7ae667bd5216cb96a8ff',
    lora_weight: 0.7,
    active_adapters: ['minimal-geometric'],
    live_lora_modules: 128,
    ip_adapter_repo_id: 'h94/IP-Adapter',
    ip_adapter_revision: '018e402774',
    ip_adapter_scale: 0.0,
    reference_present: false,
    generate_seconds: 12.9,
    peak_allocated_mb: 5143.73,
    peak_device_used_mb: 7987.5,
    device_total_mb: 8187.5,
    spare_device_mb: 200.0,
    image_sha256: 'c'.repeat(64),
  },
}

function telemetry(overrides: Partial<ProgressTelemetry> = {}): ProgressTelemetry {
  return {
    operation_id: 'op-1',
    status: 'generating',
    stage: 'denoising',
    current_step: 18,
    total_steps: 30,
    denoising_fraction: 0.6,
    elapsed_seconds: 8,
    estimated_remaining_seconds: 5.9,
    pipeline_loaded: true,
    ...overrides,
  }
}

/** A deferred promise so a test can hold the generation open. */
function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

beforeEach(() => {
  lastViewerTexture = null
  isReviewMode.mockReturnValue(false)
  fetchStyles.mockResolvedValue(STYLES)
  fetchGeneratedImage.mockResolvedValue(new Blob(['png']))
  fetchProgress.mockResolvedValue(telemetry())
  generate.mockResolvedValue(RESPONSE)
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

async function renderApp() {
  render(<App />)
  await screen.findByRole('button', { name: /Generate decal/ })
}

async function submitPrompt(text = 'a mountain') {
  fireEvent.change(screen.getByLabelText(/Describe the artwork/), { target: { value: text } })
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /Generate decal/ }))
  })
}

// --- layout ------------------------------------------------------------------

describe('production layout', () => {
  it('renders the branded workspace with the deck preview as its own region', async () => {
    await renderApp()
    expect(screen.getByRole('heading', { name: 'DeckForge AI', level: 1 })).toBeTruthy()
    expect(screen.getByText('Design a decal. Generate it locally. Preview it on the deck.')).toBeTruthy()
    expect(screen.getByRole('region', { name: 'Deck preview' })).toBeTruthy()
    // The control rail is an <aside>, which maps to `complementary`.
    expect(screen.getByRole('complementary', { name: 'Create a decal' })).toBeTruthy()
    expect(screen.getByTestId('deck-viewer')).toBeTruthy()
  })

  it('keeps the creation form and its accessible name', async () => {
    await renderApp()
    expect(screen.getByRole('form', { name: 'Generate a decal' })).toBeTruthy()
    expect(screen.getByLabelText(/Describe the artwork/)).toBeTruthy()
    expect(screen.getByLabelText('Style')).toBeTruthy()
    expect(screen.getByLabelText(/Reference image/)).toBeTruthy()
  })

  it('states the production texture fit without offering a choice', async () => {
    await renderApp()
    expect(screen.getByText(/DR-012/)).toBeTruthy()
    expect(screen.getByText(/1\.3008/)).toBeTruthy()
  })
})

// --- review-only controls ----------------------------------------------------

describe('review-only controls', () => {
  it('are absent from the production interface', async () => {
    await renderApp()
    expect(screen.queryByText('Texture fit')).toBeNull()
    expect(screen.queryByText(/Inverted-UV demonstration/)).toBeNull()
    expect(screen.queryByText(/Load decal/)).toBeNull()
    expect(screen.queryByText('Review mode')).toBeNull()
    // Reset view is a real user control and stays.
    expect(screen.getByRole('button', { name: 'Reset view' })).toBeTruthy()
  })

  it('appear, all three, when review mode is on', async () => {
    isReviewMode.mockReturnValue(true)
    await renderApp()
    expect(screen.getByText('Full surface (stretched)')).toBeTruthy()
    expect(screen.getByText('Fit without stretching')).toBeTruthy()
    expect(screen.getByText(/Inverted-UV demonstration/)).toBeTruthy()
    expect(screen.getByText(/Load decal/)).toBeTruthy()
    expect(screen.getByText('Review mode')).toBeTruthy()
  })

  it('still default to full surface in review mode, with the other mode selectable', async () => {
    isReviewMode.mockReturnValue(true)
    await renderApp()
    const [fullSurface, withoutStretch] = screen.getAllByRole('radio') as HTMLInputElement[]
    expect(fullSurface.value).toBe('full-surface')
    expect(fullSurface.checked).toBe(true)
    expect(withoutStretch.value).toBe('fit-without-stretch')
    expect(withoutStretch.checked).toBe(false)
  })
})

// --- generation flow ---------------------------------------------------------

describe('generating a decal', () => {
  it('shows the progress panel with real telemetry after submitting', async () => {
    const pending = deferred<GenerateResponse>()
    generate.mockReturnValue(pending.promise)

    await renderApp()
    await submitPrompt()

    await waitFor(() => expect(screen.getByText('Diffusion step 18 of 30 — 60%')).toBeTruthy())
    expect(screen.getByText('GENERATING DECAL')).toBeTruthy()
    expect(screen.getByText('About 6 seconds remaining')).toBeTruthy()
    expect(screen.getByText('Screen-print pass 18 / 30')).toBeTruthy()

    await act(async () => {
      pending.resolve(RESPONSE)
    })
  })

  it('disables Generate while working and keeps its text readable', async () => {
    const pending = deferred<GenerateResponse>()
    generate.mockReturnValue(pending.promise)

    await renderApp()
    await submitPrompt()

    const button = screen.getByRole('button', { name: /Generating/ }) as HTMLButtonElement
    expect(button.disabled).toBe(true)
    expect(button.textContent).toBe('Generating…')

    await act(async () => {
      pending.resolve(RESPONSE)
    })
  })

  it('cannot be submitted twice for one generation', async () => {
    const pending = deferred<GenerateResponse>()
    generate.mockReturnValue(pending.promise)

    await renderApp()
    await submitPrompt()

    await act(async () => {
      fireEvent.submit(screen.getByRole('form', { name: 'Generate a decal' }))
    })
    expect(generate).toHaveBeenCalledTimes(1)

    await act(async () => {
      pending.resolve(RESPONSE)
    })
  })

  it('keeps the previous decal on the deck while generating', async () => {
    const pending = deferred<GenerateResponse>()
    generate.mockReturnValue(pending.promise)

    await renderApp()
    await waitFor(() => expect(lastViewerTexture).toBe('starter-decal'))
    await submitPrompt()

    // Mid-generation the board still shows the decal it had.
    expect(screen.getByTestId('deck-viewer').getAttribute('data-texture')).toBe('starter-decal')

    await act(async () => {
      pending.resolve(RESPONSE)
    })
    await waitFor(() =>
      expect(screen.getByTestId('deck-viewer').getAttribute('data-texture')).toBe(
        'generated-texture',
      ),
    )
  })

  it('shows the result panel with downloads and metadata once finished', async () => {
    await renderApp()
    await submitPrompt()

    await waitFor(() => expect(screen.getByRole('button', { name: 'Download PNG' })).toBeTruthy())
    expect(screen.getByRole('button', { name: 'Download metadata' })).toBeTruthy()
    expect(screen.getByText('Reproducibility metadata')).toBeTruthy()
    // Named in the summary line and again in the metadata table.
    expect(screen.getAllByText(/Minimal geometric/).length).toBeGreaterThan(0)
    // The retro-poster style limitation reaches the user, as a note not an alert.
    expect(screen.getByText(/pseudo-text/)).toBeTruthy()
  })

  it('never remounts the viewer, which is what would reset the camera', async () => {
    await renderApp()
    const before = screen.getByTestId('deck-viewer')
    await submitPrompt()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Download PNG' })).toBeTruthy())
    // Same DOM node throughout: React reused it rather than remounting.
    expect(screen.getByTestId('deck-viewer')).toBe(before)
  })

  it('stops polling once the generation succeeds', async () => {
    await renderApp()
    await submitPrompt()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Download PNG' })).toBeTruthy())

    const afterSuccess = fetchProgress.mock.calls.length
    await new Promise((resolve) => setTimeout(resolve, 900))
    expect(fetchProgress.mock.calls.length).toBeLessThanOrEqual(afterSuccess + 1)
  })
})

// --- failure -----------------------------------------------------------------

describe('failure handling', () => {
  it('shows the error, keeps the previous decal, and stops polling', async () => {
    const { ApiError } = await import('./api/client')
    generate.mockRejectedValue(
      new ApiError(504, 'generation_timeout', 'Generation took too long and was stopped after 14 of 30 steps.'),
    )

    await renderApp()
    await submitPrompt()

    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy())
    expect(screen.getByRole('alert').textContent).toContain('14 of 30 steps')
    expect(screen.getByTestId('deck-viewer').getAttribute('data-texture')).toBe('starter-decal')

    const afterFailure = fetchProgress.mock.calls.length
    await new Promise((resolve) => setTimeout(resolve, 900))
    expect(fetchProgress.mock.calls.length).toBeLessThanOrEqual(afterFailure + 1)
  })

  it('re-enables Generate after a failure so the user can retry', async () => {
    const { ApiError } = await import('./api/client')
    generate.mockRejectedValue(new ApiError(503, 'model_unavailable', 'The generation model could not be prepared.'))

    await renderApp()
    await submitPrompt()

    await waitFor(() => {
      const button = screen.getByRole('button', { name: /Generate decal/ }) as HTMLButtonElement
      expect(button.disabled).toBe(false)
    })
  })

  it('reports a busy GPU as a wait, not as a failure', async () => {
    const { ApiError } = await import('./api/client')
    generate.mockRejectedValue(
      new ApiError(409, 'generation_in_progress', 'The GPU is busy with another generation. Try again in a moment.'),
    )

    await renderApp()
    await submitPrompt()

    await waitFor(() => expect(screen.getByText(/finishing another decal/)).toBeTruthy())
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('completes normally when progress telemetry is unavailable throughout', async () => {
    fetchProgress.mockRejectedValue(new Error('progress endpoint down'))

    await renderApp()
    await submitPrompt()

    await waitFor(() => expect(screen.getByRole('button', { name: 'Download PNG' })).toBeTruthy())
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('completes when the response arrives before any telemetry is observed', async () => {
    // The endpoint only ever reports an idle server: nothing is adoptable.
    fetchProgress.mockResolvedValue(
      telemetry({ operation_id: null, status: 'idle', stage: 'idle' }),
    )

    await renderApp()
    await submitPrompt()

    await waitFor(() => expect(screen.getByRole('button', { name: 'Download PNG' })).toBeTruthy())
  })

  it('ignores a completed snapshot belonging to a previous operation', async () => {
    const pending = deferred<GenerateResponse>()
    generate.mockReturnValue(pending.promise)
    fetchProgress.mockResolvedValue(
      telemetry({ operation_id: 'op-previous', status: 'completed', stage: 'completed' }),
    )

    await renderApp()
    await submitPrompt()

    // The stale "completed" must not be shown as this generation finishing.
    await waitFor(() => expect(screen.getByText('GENERATING DECAL')).toBeTruthy())
    expect(screen.queryByText('DECAL GENERATED')).toBeNull()

    await act(async () => {
      pending.resolve(RESPONSE)
    })
  })
})

// --- service unavailable -----------------------------------------------------

describe('when the service is unreachable', () => {
  it('explains how to start it and disables generation', async () => {
    fetchStyles.mockRejectedValue(new Error('offline'))
    render(<App />)

    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy())
    expect(screen.getByRole('alert').textContent).toContain('uvicorn')
    expect((screen.getByRole('button', { name: /Generate decal/ }) as HTMLButtonElement).disabled).toBe(true)
  })
})
