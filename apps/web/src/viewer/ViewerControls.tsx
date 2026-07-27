import type { Decal } from '../decals'

export interface ViewerControlsProps {
  decals: Decal[]
  activeDecalId: string
  onSelectDecal: (id: string) => void
  onResetView: () => void
  invertDemo: boolean
  onToggleInvertDemo: (value: boolean) => void
}

/**
 * Plain-DOM control bar for the viewer (kept free of Canvas/WebGL so it is
 * testable under jsdom).
 */
export function ViewerControls({
  decals,
  activeDecalId,
  onSelectDecal,
  onResetView,
  invertDemo,
  onToggleInvertDemo,
}: ViewerControlsProps) {
  return (
    <div className="viewer-controls">
      <div className="decal-buttons" role="group" aria-label="Decal selection">
        {decals.map((decal) => (
          <button
            key={decal.id}
            onClick={() => onSelectDecal(decal.id)}
            aria-pressed={decal.id === activeDecalId}
            className={decal.id === activeDecalId ? 'active' : ''}
          >
            {decal.label}
          </button>
        ))}
      </div>
      <button onClick={onResetView}>Reset view</button>
      <label className="invert-demo" title="Controlled demonstration of an inverted UV layout — not a real defect">
        <input
          type="checkbox"
          checked={invertDemo}
          onChange={(event) => onToggleInvertDemo(event.target.checked)}
        />
        Inverted-UV demonstration
      </label>
    </div>
  )
}
