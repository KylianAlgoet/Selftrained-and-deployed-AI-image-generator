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
 */

export interface ResultPanelProps {
  metadata: GenerationMetadata
  warnings: string[]
  imageUrl: string
  fit: FitDescription | null
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

export function ResultPanel({
  metadata,
  warnings,
  imageUrl,
  fit,
  onDownloadImage,
  onDownloadMetadata,
}: ResultPanelProps) {
  return (
    <section className="result-panel" aria-label="Generation result">
      <div className="result-preview">
        <img src={imageUrl} alt={`Generated decal: ${metadata.prompt}`} />
      </div>

      {warnings.map((warning) => (
        <p className="warning" role="note" key={warning}>
          {warning}
        </p>
      ))}

      {fit && <p className="fit-disclosure">{fitDisclosure(fit)}</p>}

      <div className="downloads">
        <button type="button" onClick={onDownloadImage}>
          Download PNG
        </button>
        <button type="button" onClick={onDownloadMetadata}>
          Download metadata
        </button>
      </div>

      <details className="metadata">
        <summary>Reproducibility metadata</summary>
        <dl>
          <Row label="Style">
            {metadata.style_label} ({metadata.style_outcome})
          </Row>
          <Row label="Prompt">{metadata.prompt}</Row>
          <Row label="Seed">{metadata.seed}</Row>
          <Row label="Size">
            {metadata.width}×{metadata.height}
          </Row>
          <Row label="Steps">
            {metadata.steps_run}/{metadata.steps} at guidance {metadata.guidance_scale}
          </Row>
          <Row label="Scheduler">{metadata.scheduler}</Row>
          <Row label="Base model">
            {metadata.base_model_repo_id} @ {metadata.base_model_revision.slice(0, 10)}
          </Row>
          <Row label="Adapter">
            {metadata.lora_run_id} step {metadata.lora_checkpoint_step} at weight{' '}
            {metadata.lora_weight}
          </Row>
          <Row label="Adapter sha256">
            <code>{metadata.lora_sha256.slice(0, 16)}…</code>
          </Row>
          <Row label="Reference">
            {metadata.reference_present
              ? `IP-Adapter at ${metadata.ip_adapter_scale}`
              : 'none (prompt only)'}
          </Row>
          <Row label="Image sha256">
            <code>{metadata.image_sha256.slice(0, 16)}…</code>
          </Row>
          <Row label="Generated in">{metadata.generate_seconds}s</Row>
          <Row label="Peak VRAM">
            {metadata.peak_allocated_mb} MiB allocated · {metadata.spare_device_mb} MiB spare of{' '}
            {metadata.device_total_mb}
          </Row>
        </dl>
      </details>
    </section>
  )
}
