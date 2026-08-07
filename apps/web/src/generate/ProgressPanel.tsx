import type { ProgressView } from './progressModel'

/**
 * The waiting state, as a deck being screen printed.
 *
 * The metaphor is doing real work rather than decorating: the ink fills a deck
 * silhouette from tail to nose in proportion to the actual diffusion steps
 * reported by the pipeline. Nothing here animates on a timer of its own, so
 * when the GPU stalls the ink stops - which is the honest behaviour, and the
 * opposite of a spinner that keeps spinning through a hang.
 *
 * What it deliberately does not do: preview the unfinished latent (an early
 * denoising step is a misleading picture of the result), fake a percentage for
 * stages that have none, or type text out character by character.
 *
 * Accessibility: the whole panel is a live region, but the text it announces is
 * `view.announcement` - stage changes and quarter progress, not all thirty
 * steps. The numeric readouts stay visible for sighted users at every stage.
 */

export interface ProgressPanelProps {
  view: ProgressView
  /** The settings actually submitted, frozen at submission. */
  submitted: {
    styleLabel: string
    referencePresent: boolean
    seed: number | undefined
    width: number
    height: number
  }
}

export function ProgressPanel({ view, submitted }: ProgressPanelProps) {
  // The headline turns positive once the bytes are in the browser and stays
  // that way while the texture is composed - the artwork exists by then, so
  // reverting to "GENERATING" would be a step backwards for the reader.
  const settled = view.phase === 'done' || view.phase === 'applying'
  const percentText = view.percent === null ? null : `${view.percent}%`

  return (
    <section
      className={`progress-panel${settled ? ' is-complete' : ''}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <p className="progress-headline">{settled ? 'DECAL GENERATED' : 'GENERATING DECAL'}</p>

      {/* Announced text is coarse; the detailed readouts below are visual. */}
      <p className="visually-hidden">{view.announcement}</p>

      <div className="print-stage" aria-hidden="true">
        <div className="print-marks" />
        <div className="print-deck">
          <div
            className="print-ink"
            style={{ transform: `scaleY(${view.trackFraction})` }}
            data-testid="print-ink"
          />
        </div>
        <div className="print-marks" />
      </div>

      <div
        className="diffusion-track"
        role="progressbar"
        aria-label="Diffusion steps"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={view.percent ?? undefined}
        aria-valuetext={view.stepLabel ?? view.stageLabel}
      >
        <div className="diffusion-fill" style={{ width: `${view.trackFraction * 100}%` }} />
      </div>

      <p className="progress-stage">{view.stageLabel}</p>

      {view.printPassLabel && <p className="progress-pass">{view.printPassLabel}</p>}
      {/* The technically accurate readout is always present whenever a step
          count exists — the product wording never replaces it. */}
      {view.stepLabel && (
        <p className="progress-steps">
          <span className="mono">{view.stepLabel}</span>
        </p>
      )}
      {percentText === null && !settled && (
        <p className="progress-steps progress-steps-none">No step percentage at this stage</p>
      )}

      <div className="progress-timing">
        {/* For stages with no estimate the two slots would otherwise print the
            same sentence twice - "Loading the local generation model…" as both
            the stage and the time remaining. One statement, once. */}
        {view.etaLabel && view.etaLabel !== view.stageLabel && (
          <span className="progress-eta">{view.etaLabel}</span>
        )}
        <span className="progress-elapsed">{view.elapsedLabel}</span>
      </div>

      <dl className="progress-submitted">
        <div>
          <dt>Style</dt>
          <dd>{submitted.styleLabel}</dd>
        </div>
        <div>
          <dt>Reference image</dt>
          <dd>{submitted.referencePresent ? 'Yes' : 'No'}</dd>
        </div>
        <div>
          <dt>Seed</dt>
          <dd className="mono">{submitted.seed ?? 'default'}</dd>
        </div>
        <div>
          <dt>Output</dt>
          <dd className="mono">
            {submitted.width}×{submitted.height}
          </dd>
        </div>
        <div>
          <dt>Generation</dt>
          <dd>Local</dd>
        </div>
      </dl>
    </section>
  )
}
