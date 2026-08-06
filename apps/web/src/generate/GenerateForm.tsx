import { useId, useState } from 'react'
import type { StyleInfo, StylesResponse } from '../api/client'
import { MAX_PROMPT_CHARS, preflightReference } from './referenceValidation'

/**
 * The generation form.
 *
 * The two numeric controls are bounded by the ranges the decision records set,
 * not by taste: LoRA weight 0.4–1.0 with a default of 0.7 (DR-010, chosen by
 * Kylian at gate 2), IP-Adapter scale 0.40–0.60 with a default of 0.55
 * (DR-008, above which prompt authority falls and source-like composition
 * increases). The form cannot express a value outside them.
 */

export interface GenerateFormValues {
  prompt: string
  style: string
  seed: number | undefined
  loraWeight: number
  ipAdapterScale: number
  referenceImage: File | null
}

export interface GenerateFormProps {
  styles: StylesResponse | null
  busy: boolean
  disabled?: boolean
  fieldError?: { field?: string; message: string } | null
  onSubmit: (values: GenerateFormValues) => void
}

export function GenerateForm({
  styles,
  busy,
  disabled = false,
  fieldError,
  onSubmit,
}: GenerateFormProps) {
  const ids = useId()
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('')
  const [seed, setSeed] = useState('42')
  const [loraWeight, setLoraWeight] = useState(0.7)
  const [ipAdapterScale, setIpAdapterScale] = useState(0.55)
  const [referenceImage, setReferenceImage] = useState<File | null>(null)
  const [referenceError, setReferenceError] = useState<string | null>(null)

  const available: StyleInfo[] = styles?.styles ?? []
  const selectedStyle = available.find((item) => item.key === style) ?? available[0]
  const effectiveStyle = style || selectedStyle?.key || ''

  const weightMin = selectedStyle?.lora_weight_min ?? 0.4
  const weightMax = selectedStyle?.lora_weight_max ?? 1.0
  const scaleMin = styles?.ip_adapter_scale_min ?? 0.4
  const scaleMax = styles?.ip_adapter_scale_max ?? 0.6

  function handleReference(file: File | null) {
    if (!file) {
      setReferenceImage(null)
      setReferenceError(null)
      return
    }
    const problem = preflightReference(file)
    setReferenceError(problem)
    setReferenceImage(problem ? null : file)
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (referenceError) return
    const parsedSeed = seed.trim() === '' ? undefined : Number(seed)
    onSubmit({
      prompt,
      style: effectiveStyle,
      seed: Number.isNaN(parsedSeed as number) ? undefined : parsedSeed,
      loraWeight,
      ipAdapterScale,
      referenceImage,
    })
  }

  const promptError = fieldError?.field === 'prompt' ? fieldError.message : null

  return (
    <form className="generate-form" onSubmit={handleSubmit} aria-label="Generate a decal">
      <div className="field">
        <label htmlFor={`${ids}-prompt`}>Describe the artwork</label>
        <textarea
          id={`${ids}-prompt`}
          value={prompt}
          maxLength={MAX_PROMPT_CHARS}
          rows={3}
          placeholder="a mountain and a rising sun"
          onChange={(event) => setPrompt(event.target.value)}
          aria-invalid={promptError ? true : undefined}
          aria-describedby={promptError ? `${ids}-prompt-error` : undefined}
        />
        <p className="hint">
          {prompt.length}/{MAX_PROMPT_CHARS} — the style wording is added for you.
        </p>
        {promptError && (
          <p className="field-error" id={`${ids}-prompt-error`} role="alert">
            {promptError}
          </p>
        )}
      </div>

      <div className="field">
        <label htmlFor={`${ids}-style`}>Style</label>
        <select
          id={`${ids}-style`}
          value={effectiveStyle}
          onChange={(event) => setStyle(event.target.value)}
        >
          {available.map((item) => (
            <option key={item.key} value={item.key}>
              {item.label}
              {item.outcome === 'PARTIAL PASS' ? ' (partial)' : ''}
            </option>
          ))}
        </select>
        {selectedStyle?.limitation && (
          <p className="limitation" role="note">
            {selectedStyle.limitation}
          </p>
        )}
      </div>

      <div className="field">
        <label htmlFor={`${ids}-reference`}>Reference image (optional)</label>
        <input
          id={`${ids}-reference`}
          type="file"
          accept=".png,.jpg,.jpeg,.webp"
          onChange={(event) => handleReference(event.target.files?.[0] ?? null)}
        />
        {referenceError && (
          <p className="field-error" role="alert">
            {referenceError}
          </p>
        )}
      </div>

      <details className="advanced">
        <summary>Advanced</summary>

        <div className="field">
          <label htmlFor={`${ids}-seed`}>Seed</label>
          <input
            id={`${ids}-seed`}
            type="number"
            value={seed}
            onChange={(event) => setSeed(event.target.value)}
          />
          <p className="hint">The same seed and settings reproduce the same image.</p>
        </div>

        <div className="field">
          {/* A <span>, not an <output>: <output> is itself a labelable element,
              so it would make this label ambiguous to assistive technology. */}
          <label htmlFor={`${ids}-weight`}>
            Style strength <span className="value">{loraWeight.toFixed(2)}</span>
          </label>
          <input
            id={`${ids}-weight`}
            type="range"
            min={weightMin}
            max={weightMax}
            step={0.05}
            value={loraWeight}
            onChange={(event) => setLoraWeight(Number(event.target.value))}
          />
          <p className="hint">0.70 is the reviewed default, not a universal optimum.</p>
        </div>

        <div className="field">
          <label htmlFor={`${ids}-scale`}>
            Reference influence <span className="value">{ipAdapterScale.toFixed(2)}</span>
          </label>
          <input
            id={`${ids}-scale`}
            type="range"
            min={scaleMin}
            max={scaleMax}
            step={0.05}
            value={ipAdapterScale}
            disabled={!referenceImage}
            onChange={(event) => setIpAdapterScale(Number(event.target.value))}
          />
          <p className="hint">
            {referenceImage
              ? 'Higher values follow the reference more and the prompt less.'
              : 'Applies only when a reference image is attached.'}
          </p>
        </div>
      </details>

      <button type="submit" disabled={disabled || busy || available.length === 0}>
        {busy ? 'Generating…' : 'Generate decal'}
      </button>
    </form>
  )
}
