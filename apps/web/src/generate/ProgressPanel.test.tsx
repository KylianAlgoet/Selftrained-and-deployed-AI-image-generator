// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import type { ProgressTelemetry } from '../api/progress'
import { ProgressPanel } from './ProgressPanel'
import { buildProgressView, type ProgressViewInput } from './progressModel'

afterEach(cleanup)

const SUBMITTED = {
  styleLabel: 'Ukiyo-e',
  referencePresent: true,
  seed: 42,
  width: 512,
  height: 1536,
}

function telemetry(overrides: Partial<ProgressTelemetry> = {}): ProgressTelemetry {
  return {
    operation_id: 'op-1',
    status: 'generating',
    stage: 'denoising',
    current_step: 18,
    total_steps: 30,
    denoising_fraction: 0.6,
    elapsed_seconds: 8.4,
    estimated_remaining_seconds: 5.9,
    pipeline_loaded: true,
    ...overrides,
  }
}

function renderPanel(overrides: Partial<ProgressViewInput> = {}) {
  const view = buildProgressView({
    telemetry: telemetry(),
    telemetryUnavailable: false,
    elapsedMs: 8400,
    etaExpired: false,
    imageReady: false,
    applyingTexture: false,
    ...overrides,
  })
  render(<ProgressPanel view={view} submitted={SUBMITTED} />)
  return view
}

describe('accessibility', () => {
  it('is a polite live region', () => {
    renderPanel()
    const region = screen.getByRole('status')
    expect(region.getAttribute('aria-live')).toBe('polite')
  })

  it('exposes the diffusion track as a labelled progressbar', () => {
    renderPanel()
    const bar = screen.getByRole('progressbar', { name: 'Diffusion steps' })
    expect(bar.getAttribute('aria-valuenow')).toBe('60')
    expect(bar.getAttribute('aria-valuetext')).toBe('Diffusion step 18 of 30 — 60%')
  })

  it('announces coarse progress, not every individual step', () => {
    renderPanel()
    // Announced text is quartered; the precise step count stays visual.
    expect(screen.getByText(/50 percent of the diffusion steps/)).toBeTruthy()
  })

  it('drops aria-valuenow when there is no honest percentage', () => {
    renderPanel({ telemetry: telemetry({ stage: 'loading-model' }) })
    const bar = screen.getByRole('progressbar')
    expect(bar.getAttribute('aria-valuenow')).toBeNull()
    expect(bar.getAttribute('aria-valuetext')).toBe('Loading the local generation model…')
  })

  it('conveys the stage in text, not only through the ink graphic', () => {
    renderPanel()
    expect(screen.getByText('Printing the decal…')).toBeTruthy()
    // The decorative print stage is hidden from assistive technology.
    expect(screen.getByTestId('print-ink').closest('[aria-hidden="true"]')).toBeTruthy()
  })
})

describe('what the panel shows while denoising', () => {
  it('shows the technically accurate step count and the product wording', () => {
    renderPanel()
    expect(screen.getByText('Diffusion step 18 of 30 — 60%')).toBeTruthy()
    expect(screen.getByText('Screen-print pass 18 / 30')).toBeTruthy()
  })

  it('shows the estimate as approximate and the real elapsed time', () => {
    renderPanel()
    expect(screen.getByText('About 6 seconds remaining')).toBeTruthy()
    expect(screen.getByText('Elapsed: 8 seconds')).toBeTruthy()
  })

  it('fills the ink in proportion to the reported steps', () => {
    renderPanel()
    expect(screen.getByTestId('print-ink').getAttribute('style')).toContain('scaleY(0.6)')
  })

  it('summarises what was actually submitted', () => {
    renderPanel()
    expect(screen.getByText('Ukiyo-e')).toBeTruthy()
    expect(screen.getByText('42')).toBeTruthy()
    expect(screen.getByText('512×1536')).toBeTruthy()
    expect(screen.getByText('Yes')).toBeTruthy()
    expect(screen.getByText('Local')).toBeTruthy()
  })

  it('does not claim completion', () => {
    renderPanel()
    expect(screen.getByText('GENERATING DECAL')).toBeTruthy()
    expect(screen.queryByText('DECAL GENERATED')).toBeNull()
    expect(screen.queryByText(/100%/)).toBeNull()
  })
})

describe('cold model loading', () => {
  it('names the wait and shows no percentage at all', () => {
    renderPanel({ telemetry: telemetry({ stage: 'loading-model', current_step: 0 }) })
    // Stage line, estimate slot and announcement all say the same true thing.
    expect(screen.getAllByText('Loading the local generation model…').length).toBe(3)
    expect(screen.queryByText(/Diffusion step/)).toBeNull()
    expect(screen.queryByText(/%/)).toBeNull()
    expect(screen.getByText('No step percentage at this stage')).toBeTruthy()
  })
})

describe('early denoising', () => {
  it('says it is measuring instead of showing an estimate', () => {
    renderPanel({
      telemetry: telemetry({
        current_step: 2,
        denoising_fraction: 2 / 30,
        estimated_remaining_seconds: null,
      }),
    })
    expect(screen.getByText('Measuring generation speed…')).toBeTruthy()
    expect(screen.queryByText(/remaining/)).toBeNull()
    // The real step count is known and is shown.
    expect(screen.getByText('Diffusion step 2 of 30 — 7%')).toBeTruthy()
  })
})

describe('after the last diffusion step', () => {
  it('shows finalising and withdraws the percentage', () => {
    renderPanel({
      telemetry: telemetry({ stage: 'decoding', current_step: 30, denoising_fraction: 1 }),
    })
    expect(screen.getAllByText('Finalising the decal…').length).toBeGreaterThan(0)
    expect(screen.queryByText(/Diffusion step/)).toBeNull()
    expect(screen.queryByText(/100%/)).toBeNull()
    expect(screen.queryByText('DECAL GENERATED')).toBeNull()
  })

  it('switches to finishing wording when the estimate has run out', () => {
    renderPanel({
      telemetry: telemetry({ stage: 'saving', current_step: 30, denoising_fraction: 1 }),
      etaExpired: true,
    })
    expect(screen.getAllByText('Finishing the artwork…').length).toBeGreaterThan(0)
    expect(screen.queryByText(/-\d/)).toBeNull()
  })
})

describe('completion', () => {
  it('celebrates only once the image is in the browser', () => {
    renderPanel({ imageReady: true })
    expect(screen.getByText('DECAL GENERATED')).toBeTruthy()
    expect(screen.getByText('Decal generated')).toBeTruthy()
  })

  it('keeps the positive headline while the texture is applied', () => {
    renderPanel({ imageReady: true, applyingTexture: true })
    expect(screen.getByText('DECAL GENERATED')).toBeTruthy()
    expect(screen.getByText('Applying the decal to the deck…')).toBeTruthy()
  })
})

describe('telemetry loss', () => {
  it('falls back to elapsed time without claiming failure', () => {
    renderPanel({ telemetry: null, telemetryUnavailable: true, elapsedMs: 12_000 })
    expect(screen.getByText('Generating locally…')).toBeTruthy()
    expect(screen.getByText('Elapsed: 12 seconds')).toBeTruthy()
    expect(screen.getByText('GENERATING DECAL')).toBeTruthy()
  })
})
