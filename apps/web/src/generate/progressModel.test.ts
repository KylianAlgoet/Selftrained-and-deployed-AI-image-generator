import { describe, expect, it } from 'vitest'
import type { ProgressTelemetry } from '../api/progress'
import {
  buildProgressView,
  formatElapsed,
  formatEta,
  smoothEta,
  type ProgressViewInput,
} from './progressModel'

/**
 * These tests are the honesty rules, written down as assertions.
 *
 * The failure they exist to prevent is not a crash. It is a loading screen that
 * looks informative and is not: a percentage during model loading, a countdown
 * that keeps running past zero, or "100 %" shown while the VAE is still
 * decoding. Every one of those would be indistinguishable from a working
 * feature by eye, so each is pinned here instead.
 */

function telemetry(overrides: Partial<ProgressTelemetry> = {}): ProgressTelemetry {
  return {
    operation_id: 'op-1',
    status: 'generating',
    stage: 'denoising',
    current_step: 0,
    total_steps: 30,
    denoising_fraction: 0,
    elapsed_seconds: 0,
    estimated_remaining_seconds: null,
    pipeline_loaded: true,
    ...overrides,
  }
}

function view(overrides: Partial<ProgressViewInput> = {}) {
  return buildProgressView({
    telemetry: telemetry(),
    telemetryUnavailable: false,
    elapsedMs: 0,
    etaExpired: false,
    imageReady: false,
    applyingTexture: false,
    ...overrides,
  })
}

describe('formatting', () => {
  it('rounds elapsed time to whole seconds and gets the plural right', () => {
    expect(formatElapsed(0)).toBe('Elapsed: 0 seconds')
    expect(formatElapsed(1000)).toBe('Elapsed: 1 second')
    expect(formatElapsed(8400)).toBe('Elapsed: 8 seconds')
  })

  it('hedges the estimate and never counts below one second', () => {
    expect(formatEta(5.9)).toBe('About 6 seconds remaining')
    expect(formatEta(1.4)).toBe('About 1 second remaining')
    expect(formatEta(0.01)).toBe('About 1 second remaining')
    expect(formatEta(-4)).toBe('About 1 second remaining')
  })

  it('ignores sub-second jitter but never hides a real change', () => {
    expect(smoothEta(null, 12)).toBe(12)
    expect(smoothEta(12, 12.4)).toBe(12)
    expect(smoothEta(12, 11.7)).toBe(12)
    // A whole second of movement is real and is shown at once.
    expect(smoothEta(12, 10.5)).toBe(10.5)
    expect(smoothEta(12, 20)).toBe(20)
  })
})

describe('cold model loading', () => {
  const loading = view({ telemetry: telemetry({ stage: 'loading-model' }) })

  it('names the wait instead of guessing a percentage', () => {
    expect(loading.stageLabel).toBe('Loading the local generation model…')
    expect(loading.percent).toBeNull()
    expect(loading.stepLabel).toBeNull()
    expect(loading.trackFraction).toBe(0)
  })

  it('offers no remaining-time estimate for an unmeasurable stage', () => {
    expect(loading.etaLabel).toBe('Loading the local generation model…')
    expect(loading.etaLabel).not.toMatch(/\d/)
  })
})

describe('early denoising', () => {
  const early = view({
    telemetry: telemetry({ current_step: 2, denoising_fraction: 2 / 30 }),
  })

  it('says it is measuring rather than inventing an estimate', () => {
    expect(early.phase).toBe('measuring')
    expect(early.etaLabel).toBe('Measuring generation speed…')
  })

  it('still reports the real step count, which IS known', () => {
    expect(early.stepLabel).toBe('Diffusion step 2 of 30 — 7%')
    expect(early.percent).toBe(7)
  })
})

describe('measured denoising', () => {
  const mid = view({
    telemetry: telemetry({
      current_step: 18,
      denoising_fraction: 0.6,
      estimated_remaining_seconds: 5.9,
    }),
  })

  it('shows the technically accurate step readout', () => {
    expect(mid.stepLabel).toBe('Diffusion step 18 of 30 — 60%')
    expect(mid.percent).toBe(60)
  })

  it('offers the product wording alongside, never instead of, the real numbers', () => {
    expect(mid.printPassLabel).toBe('Screen-print pass 18 / 30')
    expect(mid.stepLabel).not.toBeNull()
  })

  it('shows the estimate as approximate', () => {
    expect(mid.etaLabel).toBe('About 6 seconds remaining')
  })

  it('is not request completion', () => {
    expect(mid.requestComplete).toBe(false)
  })

  it('announces coarsely, in quarters, not every step', () => {
    expect(mid.announcement).toContain('50 percent')
    const next = view({
      telemetry: telemetry({
        current_step: 19,
        denoising_fraction: 19 / 30,
        estimated_remaining_seconds: 5,
      }),
    })
    expect(next.announcement).toBe(mid.announcement)
  })
})

describe('the last diffusion step is not the end of the request', () => {
  const decoding = view({
    telemetry: telemetry({
      stage: 'decoding',
      current_step: 30,
      denoising_fraction: 1,
    }),
  })

  it('stops showing a diffusion percentage once denoising is done', () => {
    expect(decoding.percent).toBeNull()
    expect(decoding.stepLabel).toBeNull()
  })

  it('says it is finalising', () => {
    expect(decoding.phase).toBe('finalising')
    expect(decoding.stageLabel).toBe('Finalising the decal…')
  })

  it('does NOT claim the request is complete', () => {
    expect(decoding.requestComplete).toBe(false)
  })

  it('claims nothing complete while the backend is still saving', () => {
    const saving = view({ telemetry: telemetry({ stage: 'saving', current_step: 30 }) })
    expect(saving.requestComplete).toBe(false)
    expect(saving.percent).toBeNull()
  })

  it('still claims nothing when the backend reports completed but no image is in hand', () => {
    const backendDone = view({
      telemetry: telemetry({ status: 'completed', stage: 'completed', current_step: 30 }),
      imageReady: false,
    })
    expect(backendDone.requestComplete).toBe(false)
  })
})

describe('an expired estimate is retracted', () => {
  it('switches to finishing wording rather than counting past zero', () => {
    const expired = view({
      telemetry: telemetry({ stage: 'decoding', current_step: 30, denoising_fraction: 1 }),
      etaExpired: true,
    })
    expect(expired.phase).toBe('finishing')
    expect(expired.stageLabel).toBe('Finishing the artwork…')
    expect(expired.etaLabel).toBe('Finishing the artwork…')
    expect(expired.etaLabel).not.toMatch(/-/)
  })
})

describe('completion', () => {
  it('is claimed only once the image has decoded in the browser', () => {
    const done = view({ imageReady: true })
    expect(done.phase).toBe('done')
    expect(done.requestComplete).toBe(true)
    expect(done.stageLabel).toBe('Decal generated')
    expect(done.trackFraction).toBe(1)
  })

  it('reports applying the texture as a frontend step, not GPU progress', () => {
    const applying = view({ imageReady: true, applyingTexture: true })
    expect(applying.phase).toBe('applying')
    expect(applying.stageLabel).toBe('Applying the decal to the deck…')
    // The GPU finished before this point, so no step percentage is claimed.
    expect(applying.percent).toBeNull()
  })
})

describe('losing telemetry', () => {
  const blind = view({ telemetry: null, telemetryUnavailable: true, elapsedMs: 12_000 })

  it('falls back to elapsed time and keeps generating', () => {
    expect(blind.etaLabel).toBe('Generating locally…')
    expect(blind.elapsedLabel).toBe('Elapsed: 12 seconds')
  })

  it('never reports a failure just because progress could not be read', () => {
    expect(blind.phase).toBe('starting')
    expect(blind.requestComplete).toBe(false)
  })

  it('still completes when the response arrives without any telemetry at all', () => {
    const done = buildProgressView({
      telemetry: null,
      telemetryUnavailable: true,
      elapsedMs: 13_000,
      etaExpired: false,
      imageReady: true,
      applyingTexture: false,
    })
    expect(done.requestComplete).toBe(true)
  })
})

describe('degenerate telemetry', () => {
  it('shows no percentage when the total step count is unknown', () => {
    const unknown = view({ telemetry: telemetry({ total_steps: 0, current_step: 4 }) })
    expect(unknown.percent).toBeNull()
    expect(unknown.trackFraction).toBe(0)
  })

  it('clamps a fraction that exceeds one', () => {
    const over = view({ telemetry: telemetry({ denoising_fraction: 4, current_step: 30 }) })
    expect(over.trackFraction).toBe(1)
  })

  it('clamps a negative fraction', () => {
    const under = view({ telemetry: telemetry({ denoising_fraction: -2 }) })
    expect(under.trackFraction).toBe(0)
  })
})

describe('no fabricated overall percentage exists anywhere', () => {
  it('produces a percentage in exactly one situation: real denoising steps', () => {
    const stages = [
      'preparing',
      'loading-model',
      'loading-style',
      'preparing-reference',
      'decoding',
      'saving',
      'completed',
    ] as const

    for (const stage of stages) {
      const built = view({ telemetry: telemetry({ stage, current_step: 30 }) })
      expect(built.percent, `${stage} must not report a percentage`).toBeNull()
    }

    expect(view({ telemetry: telemetry({ current_step: 6 }) }).percent).toBe(20)
  })
})
