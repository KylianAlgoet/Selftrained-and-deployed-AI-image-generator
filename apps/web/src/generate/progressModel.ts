/**
 * Turning telemetry into words, without inventing any of them.
 *
 * This module is pure on purpose: every rule about what the loading screen may
 * claim is a function of its inputs, so each rule is a test rather than a
 * promise made in a code review.
 *
 * The rules, in the order they bite:
 *
 * 1. **A percentage exists only while denoising.** Diffusers reports "step 18 of
 *    30", which is a measurement. Model loading, LoRA loading, VAE decoding and
 *    PNG encoding report nothing, so they get a stage name and no number. There
 *    is no weighted overall percentage anywhere in this file.
 * 2. **The diffusion percentage is not request completion.** Denoising finishing
 *    means the VAE decode is about to start. `requestComplete` is false until the
 *    response has arrived AND the PNG has decoded in the browser.
 * 3. **An estimate is shown only once steps have been timed.** Before that the
 *    interface says it is measuring, because it is.
 * 4. **An expired estimate is retracted, not counted down past zero.**
 * 5. **Losing telemetry is not losing the generation.** With no progress data at
 *    all, the panel falls back to the one thing it still knows first-hand: how
 *    long the user has been waiting.
 */

import type { ProgressTelemetry } from '../api/progress'

export type ProgressPhase =
  | 'starting'
  | 'loading-model'
  | 'loading-style'
  | 'preparing-reference'
  | 'measuring'
  | 'denoising'
  | 'finalising'
  | 'finishing'
  | 'applying'
  | 'done'

export interface ProgressViewInput {
  telemetry: ProgressTelemetry | null
  /** True once polling has failed and no snapshot is being received. */
  telemetryUnavailable: boolean
  /** Milliseconds since submission, measured in the browser. */
  elapsedMs: number
  /** True when a previously displayed estimate has run out and work continues. */
  etaExpired: boolean
  /** The response arrived and its PNG finished decoding in the browser. */
  imageReady: boolean
  /** The decoded image is being composed onto the deck. */
  applyingTexture: boolean
}

export interface ProgressView {
  phase: ProgressPhase
  /** Stage sentence, e.g. "Loading the local generation model…". */
  stageLabel: string
  /** Technically accurate step readout, or null when there is no honest one. */
  stepLabel: string | null
  /** Product wording for the same real numbers. Null when steps are unknown. */
  printPassLabel: string | null
  /** Denoising percent 0–100, or null outside denoising. Never a request %. */
  percent: number | null
  /** 0–1 fill of the diffusion track. Reaches 1 when DENOISING is done. */
  trackFraction: number
  /** "About 6 seconds remaining", or the honest substitute for it. */
  etaLabel: string
  elapsedLabel: string
  /** Coarse text for aria-live; changes at stages and 25% intervals only. */
  announcement: string
  /** True only when the whole request is finished and the image is in hand. */
  requestComplete: boolean
}

export const POLL_INTERVAL_MS = 750
/** Polling gives up long before this; it exists so a lost response cannot leave
 *  a timer running for the lifetime of the tab. */
export const POLL_SAFETY_TIMEOUT_MS = 5 * 60 * 1000

function wholeSeconds(ms: number): number {
  return Math.max(0, Math.round(ms / 1000))
}

function plural(value: number, unit: string): string {
  return `${value} ${unit}${value === 1 ? '' : 's'}`
}

export function formatElapsed(elapsedMs: number): string {
  return `Elapsed: ${plural(wholeSeconds(elapsedMs), 'second')}`
}

/**
 * "About 6 seconds remaining".
 *
 * Rounded to whole seconds, never below one while work continues, and always
 * hedged: the label says "about", because an EMA over past steps is an
 * extrapolation and not a commitment.
 */
export function formatEta(seconds: number): string {
  const rounded = Math.max(1, Math.round(seconds))
  return `About ${plural(rounded, 'second')} remaining`
}

/**
 * Suppress sub-second jitter in the displayed estimate.
 *
 * Adopted only when the change is smaller than the display's own resolution:
 * anything of a second or more is shown immediately, so a genuine slowdown is
 * never hidden by smoothing.
 */
export function smoothEta(previous: number | null, next: number): number {
  if (previous === null) return next
  return Math.abs(next - previous) < 1 ? previous : next
}

function phaseFor(input: ProgressViewInput): ProgressPhase {
  if (input.imageReady && !input.applyingTexture) return 'done'
  if (input.applyingTexture) return 'applying'

  const telemetry = input.telemetry
  if (!telemetry || telemetry.status === 'idle') return 'starting'

  switch (telemetry.stage) {
    case 'loading-model':
      return 'loading-model'
    case 'loading-style':
      return 'loading-style'
    case 'preparing-reference':
      return 'preparing-reference'
    case 'denoising':
      return telemetry.estimated_remaining_seconds === null ? 'measuring' : 'denoising'
    case 'decoding':
    case 'saving':
    case 'completed':
      return input.etaExpired ? 'finishing' : 'finalising'
    default:
      return 'starting'
  }
}

const STAGE_LABELS: Record<ProgressPhase, string> = {
  starting: 'Preparing the request…',
  'loading-model': 'Loading the local generation model…',
  'loading-style': 'Loading the trained style…',
  'preparing-reference': 'Preparing the reference image…',
  measuring: 'Printing the decal…',
  denoising: 'Printing the decal…',
  finalising: 'Finalising the decal…',
  finishing: 'Finishing the artwork…',
  applying: 'Applying the decal to the deck…',
  done: 'Decal generated',
}

function announcementFor(phase: ProgressPhase, percent: number | null): string {
  if (phase === 'done') return 'Decal generated.'
  if (phase === 'applying') return 'Applying the decal to the deck.'
  if (percent === null) return STAGE_LABELS[phase]
  // Coarse on purpose: a screen reader announcing all 30 steps would be
  // unusable, so denoising is announced in quarters.
  const quarter = Math.floor(percent / 25) * 25
  return `Printing the decal, ${quarter} percent of the diffusion steps complete.`
}

export function buildProgressView(input: ProgressViewInput): ProgressView {
  const phase = phaseFor(input)
  const telemetry = input.telemetry
  const elapsedLabel = formatElapsed(input.elapsedMs)

  const denoisingNow = phase === 'denoising' || phase === 'measuring'
  const hasSteps = Boolean(telemetry && telemetry.total_steps > 0)

  const percent =
    denoisingNow && hasSteps && telemetry
      ? Math.min(100, Math.round((telemetry.current_step / telemetry.total_steps) * 100))
      : null

  const stepLabel =
    denoisingNow && hasSteps && telemetry
      ? `Diffusion step ${telemetry.current_step} of ${telemetry.total_steps} — ${percent}%`
      : null

  const printPassLabel =
    denoisingNow && hasSteps && telemetry
      ? `Screen-print pass ${telemetry.current_step} / ${telemetry.total_steps}`
      : null

  // The track is the DIFFUSION track and is labelled as such in the DOM. It
  // legitimately fills when the last denoising step lands, which is also the
  // moment the percentage readout disappears and the stage becomes "Finalising".
  let trackFraction = 0
  if (phase === 'done' || phase === 'applying') trackFraction = 1
  else if (phase === 'finalising' || phase === 'finishing') trackFraction = 1
  else if (telemetry && telemetry.total_steps > 0) {
    trackFraction = Math.min(1, Math.max(0, telemetry.denoising_fraction))
  }

  let etaLabel: string
  if (phase === 'done') etaLabel = ''
  else if (phase === 'applying') etaLabel = 'Almost there'
  else if (phase === 'finishing') etaLabel = 'Finishing the artwork…'
  else if (phase === 'finalising') etaLabel = 'Finalising the decal…'
  else if (input.telemetryUnavailable && !telemetry) etaLabel = 'Generating locally…'
  else if (phase === 'loading-model') etaLabel = 'Loading the local generation model…'
  else if (phase === 'measuring') etaLabel = 'Measuring generation speed…'
  else if (telemetry?.estimated_remaining_seconds != null) {
    etaLabel = formatEta(telemetry.estimated_remaining_seconds)
  } else etaLabel = 'Measuring generation speed…'

  return {
    phase,
    stageLabel: STAGE_LABELS[phase],
    stepLabel,
    printPassLabel,
    percent,
    trackFraction,
    etaLabel,
    elapsedLabel,
    announcement: announcementFor(phase, percent),
    // The single gate on any completion claim: the bytes are in the browser.
    requestComplete: phase === 'done',
  }
}
