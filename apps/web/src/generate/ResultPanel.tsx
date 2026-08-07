import type { GenerationMetadata } from '../api/client'
import type { FitDescription } from '../deck/textureFit'
import { fitDisclosure } from '../deck/textureFit'

/**
 * What was actually produced, and under what settings.
 *
 * The metadata table is not decoration: it carries the pinned model revisions,
 * the adapter hash, the seed and the measured cost, which is what makes a
 * result traceable back to the recorded experiments rather than an
 * unattributable picture. The download offers the PNG and a JSON sidecar
 * holding the same facts.
 *
 * Two presentation rules, both load-bearing rather than cosmetic:
 *
 * - **Monospace is reserved for values a reader compares character by
 *   character** - hashes, seeds, revisions, model ids, dimensions. Prose stays
 *   in the body face so the technical values stand out by contrast.
 * - **Truncation is visual only.** Long hashes are shortened in the table with
 *   the full value in `title`, and the JSON download is generated from the
 *   metadata object, never from what is rendered - so nothing copied or
 *   downloaded is ever the abbreviated form.
 */

export interface ResultPanelProps {
  metadata: GenerationMetadata
  warnings: string[]
  imageUrl: string
  fit: FitDescription | null
  /** Whether THIS result is the artwork currently on the deck. */
  onDeck?: boolean
  onDownloadImage: () => void
  onDownloadMetadata: () => void
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="meta-row">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  )
}

function Hash({ value }: { value: string }) {
  return (
    <code className="mono truncate" title={value}>
      {value.slice(0, 16)}…
    </code>
  )
}

export function ResultPanel({
  metadata,
  warnings,
  imageUrl,
  fit,
  onDeck = true,
  onDownloadImage,
  onDownloadMetadata,
}: ResultPanelProps) {
  return (
    <section className="result-panel" aria-label="Generation result">
      <div className="result-head">
        <h2>Generated decal</h2>
        <p className="result-summary">
          <span className="result-style">{metadata.style_label}</span>
          <span className="dot" aria-hidden="true">
            ·
          </span>
          <span className="mono">{metadata.generate_seconds}s</span>
        </p>
      </div>

      <div className="result-body">
        <div className="result-preview">
          <img src={imageUrl} alt={`Generated decal: ${metadata.prompt}`} />
          <span className="result-dimensions mono">
            {metadata.width}×{metadata.height}
          </span>
        </div>

        <div className="result-side">
          <p className="result-applied">
            {onDeck
              ? 'Applied to the deck preview →'
              : 'Uploaded artwork is on the deck. This generation is kept here.'}
          </p>
          {fit && <p className="fit-disclosure">{fitDisclosure(fit)}</p>}

          <div className="downloads">
            <button type="button" className="button-download" onClick={onDownloadImage}>
              Download PNG
            </button>
            <button type="button" className="button-download" onClick={onDownloadMetadata}>
              Download metadata
            </button>
          </div>
        </div>
      </div>

      {warnings.map((warning) => (
        <p className="status-message status-warning" role="note" key={warning}>
          <span className="status-tone">Known limitation</span>
          <span className="status-body">{warning}</span>
        </p>
      ))}

      <details className="metadata">
        <summary>Reproducibility metadata</summary>
        <dl>
          <Row label="Style">
            {metadata.style_label} ({metadata.style_outcome})
          </Row>
          <Row label="Prompt">{metadata.prompt}</Row>
          <Row label="Seed">
            <span className="mono">{metadata.seed}</span>
          </Row>
          <Row label="Size">
            <span className="mono">
              {metadata.width}×{metadata.height}
            </span>
          </Row>
          <Row label="Steps">
            <span className="mono">
              {metadata.steps_run}/{metadata.steps}
            </span>{' '}
            at guidance <span className="mono">{metadata.guidance_scale}</span>
          </Row>
          <Row label="Scheduler">
            <span className="mono">{metadata.scheduler}</span>
          </Row>
          <Row label="Base model">
            <span className="mono truncate" title={metadata.base_model_repo_id}>
              {metadata.base_model_repo_id}
            </span>{' '}
            @ <span className="mono">{metadata.base_model_revision.slice(0, 10)}</span>
          </Row>
          <Row label="Adapter">
            <span className="mono">{metadata.lora_run_id}</span> step{' '}
            <span className="mono">{metadata.lora_checkpoint_step}</span> at weight{' '}
            <span className="mono">{metadata.lora_weight}</span>
          </Row>
          <Row label="Adapter sha256">
            <Hash value={metadata.lora_sha256} />
          </Row>
          <Row label="Reference">
            {metadata.reference_present ? (
              <>
                IP-Adapter at <span className="mono">{metadata.ip_adapter_scale}</span>
              </>
            ) : (
              'none (prompt only)'
            )}
          </Row>
          <Row label="Image sha256">
            <Hash value={metadata.image_sha256} />
          </Row>
          <Row label="Peak VRAM">
            <span className="mono">{metadata.peak_allocated_mb}</span> MiB allocated ·{' '}
            <span className="mono">{metadata.spare_device_mb}</span> MiB spare of{' '}
            <span className="mono">{metadata.device_total_mb}</span>
          </Row>
        </dl>
      </details>
    </section>
  )
}
