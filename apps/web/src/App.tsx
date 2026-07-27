import { useRef, useState } from 'react'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { DeckViewer } from './viewer/DeckViewer'
import { ViewerControls } from './viewer/ViewerControls'
import { DECALS } from './decals'
import './App.css'

export default function App() {
  const [activeDecalId, setActiveDecalId] = useState(DECALS[0].id)
  const [invertDemo, setInvertDemo] = useState(false)
  const controlsRef = useRef<OrbitControlsImpl | null>(null)

  const activeDecal = DECALS.find((decal) => decal.id === activeDecalId) ?? DECALS[0]

  return (
    <main className="app">
      <header>
        <h1>DeckForge AI — Prototype 0</h1>
        <p>Static interactive 3D skateboard viewer with swappable decal textures.</p>
      </header>
      <ViewerControls
        decals={DECALS}
        activeDecalId={activeDecalId}
        onSelectDecal={setActiveDecalId}
        onResetView={() => controlsRef.current?.reset()}
        invertDemo={invertDemo}
        onToggleInvertDemo={setInvertDemo}
      />
      {invertDemo && (
        <p className="demo-banner">
          Controlled demonstration: the decal is deliberately rendered with an
          inverted UV layout to show what an orientation defect would look like.
        </p>
      )}
      <div className="viewer-wrapper">
        <DeckViewer
          decalUrl={activeDecal.url}
          invertDemo={invertDemo}
          onControlsReady={(controls) => {
            controlsRef.current = controls
          }}
        />
      </div>
      <footer>
        <p>
          Deck geometry and decals are self-created project assets. Drag to
          orbit, scroll to zoom.
        </p>
      </footer>
    </main>
  )
}
