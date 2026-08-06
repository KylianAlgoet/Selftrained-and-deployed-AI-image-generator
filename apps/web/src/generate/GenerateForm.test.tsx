// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { GenerateForm } from './GenerateForm'
import { preflightReference } from './referenceValidation'
import type { StylesResponse } from '../api/client'

afterEach(cleanup)

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

function renderForm(overrides: Partial<Parameters<typeof GenerateForm>[0]> = {}) {
  const props = {
    styles: STYLES,
    busy: false,
    fieldError: null,
    onSubmit: vi.fn(),
    ...overrides,
  }
  render(<GenerateForm {...props} />)
  return props
}

describe('GenerateForm', () => {
  it('submits the reviewed defaults when nothing is changed', () => {
    const props = renderForm()
    fireEvent.change(screen.getByLabelText(/Describe the artwork/), {
      target: { value: 'a coiled serpent' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Generate decal/ }))

    expect(props.onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        prompt: 'a coiled serpent',
        style: 'minimal-geometric',
        seed: 42,
        loraWeight: 0.7,
        ipAdapterScale: 0.55,
        referenceImage: null,
      }),
    )
  })

  it('bounds the sliders by the decision-record ranges', () => {
    renderForm()
    const weight = screen.getByLabelText(/Style strength/) as HTMLInputElement
    expect(weight.min).toBe('0.4')
    expect(weight.max).toBe('1')

    const scale = screen.getByLabelText(/Reference influence/) as HTMLInputElement
    expect(scale.min).toBe('0.4')
    expect(scale.max).toBe('0.6')
  })

  it('shows the partial-pass limitation when that style is selected', () => {
    renderForm()
    expect(screen.queryByRole('note')).toBeNull()

    fireEvent.change(screen.getByLabelText('Style'), { target: { value: 'retro-poster' } })
    expect(screen.getByRole('note').textContent).toContain('pseudo-text')
  })

  it('marks the partial-pass style in the option list', () => {
    renderForm()
    expect(screen.getByRole('option', { name: /Retro silkscreen poster \(partial\)/ })).toBeTruthy()
    expect(screen.getByRole('option', { name: 'Minimal geometric' })).toBeTruthy()
  })

  it('disables reference influence until a reference is attached', () => {
    renderForm()
    expect((screen.getByLabelText(/Reference influence/) as HTMLInputElement).disabled).toBe(true)
  })

  it('shows a server field error against the prompt', () => {
    renderForm({ fieldError: { field: 'prompt', message: 'Describe what to generate.' } })
    expect(screen.getByRole('alert').textContent).toBe('Describe what to generate.')
    expect(screen.getByLabelText(/Describe the artwork/).getAttribute('aria-invalid')).toBe('true')
  })

  it('reports progress and blocks resubmission while busy', () => {
    renderForm({ busy: true })
    const button = screen.getByRole('button', { name: /Generating/ }) as HTMLButtonElement
    expect(button.disabled).toBe(true)
  })

  it('cannot be submitted before the styles have loaded', () => {
    renderForm({ styles: null })
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true)
  })

  it('leaves the seed out when the field is cleared', () => {
    const props = renderForm()
    fireEvent.change(screen.getByLabelText(/Describe the artwork/), { target: { value: 'a fox' } })
    fireEvent.change(screen.getByLabelText('Seed'), { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: /Generate decal/ }))
    expect(props.onSubmit).toHaveBeenCalledWith(expect.objectContaining({ seed: undefined }))
  })

  it('caps the prompt length in the control itself', () => {
    renderForm()
    expect((screen.getByLabelText(/Describe the artwork/) as HTMLTextAreaElement).maxLength).toBe(400)
  })
})

describe('preflightReference', () => {
  it('accepts the allowed image types', () => {
    for (const type of ['image/png', 'image/jpeg', 'image/webp']) {
      expect(preflightReference(new File([new Uint8Array([1])], 'r', { type }))).toBeNull()
    }
  })

  it('rejects another type', () => {
    const file = new File([new Uint8Array([1])], 'r.gif', { type: 'image/gif' })
    expect(preflightReference(file)).toMatch(/PNG, JPEG or WEBP/)
  })

  it('rejects a file over the 10 MB limit', () => {
    const file = new File([new Uint8Array(1)], 'big.png', { type: 'image/png' })
    Object.defineProperty(file, 'size', { value: 11 * 1024 * 1024 })
    expect(preflightReference(file)).toMatch(/10 MB/)
  })
})
