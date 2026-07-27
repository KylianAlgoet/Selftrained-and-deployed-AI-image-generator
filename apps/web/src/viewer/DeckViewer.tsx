import { Suspense, useEffect, useMemo, useRef } from 'react'
import { Canvas, useLoader, useThree } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { SRGBColorSpace, TextureLoader } from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { createDeckGeometry } from '../deck/deckGeometry'

/**
 * Dev-only hook: exposes a synchronous render trigger on window so evidence
 * screenshots and future E2E tests can force a fresh frame before reading the
 * canvas (requestAnimationFrame is paused in background tabs, which otherwise
 * yields stale captures). Not included in production builds.
 */
function EvidenceCaptureHook() {
  const { gl, scene, camera } = useThree()
  useEffect(() => {
    if (!import.meta.env.DEV) return
    const handle = { render: () => gl.render(scene, camera), canvas: gl.domElement }
    ;(window as unknown as Record<string, unknown>).__deckforge = handle
    return () => {
      delete (window as unknown as Record<string, unknown>).__deckforge
    }
  }, [gl, scene, camera])
  return null
}

interface DeckMeshProps {
  decalUrl: string
  /** Demonstration-only: renders the decal deliberately nose/tail inverted. */
  invertDemo: boolean
}

function DeckMesh({ decalUrl, invertDemo }: DeckMeshProps) {
  const texture = useLoader(TextureLoader, decalUrl)
  texture.colorSpace = SRGBColorSpace
  texture.anisotropy = 8

  const geometry = useMemo(
    () => createDeckGeometry({ invertV: invertDemo }),
    [invertDemo],
  )

  return (
    <mesh geometry={geometry}>
      {/* Material index 0: decal face (deck underside) */}
      <meshStandardMaterial attach="material-0" map={texture} roughness={0.55} />
      {/* Material index 1: top (grip tape) and rim */}
      <meshStandardMaterial attach="material-1" color="#242424" roughness={0.95} />
    </mesh>
  )
}

export interface DeckViewerProps extends DeckMeshProps {
  /** Receives the controls instance so the page can trigger a camera reset. */
  onControlsReady?: (controls: OrbitControlsImpl) => void
}

/**
 * Interactive 3D skateboard viewer. The default camera looks at the deck
 * underside (the decal face). Orbit = drag, zoom = scroll; reset is exposed
 * through onControlsReady.
 */
export function DeckViewer({ decalUrl, invertDemo, onControlsReady }: DeckViewerProps) {
  const controlsRef = useRef<OrbitControlsImpl | null>(null)

  return (
    <Canvas
      camera={{ position: [1.5, -2.1, 2.4], fov: 45 }}
      style={{ background: '#e8e6e1' }}
      gl={{ preserveDrawingBuffer: true }}
    >
      <ambientLight intensity={0.9} />
      <directionalLight position={[4, -6, 5]} intensity={1.6} />
      <directionalLight position={[-4, 6, -3]} intensity={0.7} />
      <Suspense fallback={null}>
        <DeckMesh decalUrl={decalUrl} invertDemo={invertDemo} />
      </Suspense>
      {import.meta.env.DEV && <EvidenceCaptureHook />}
      <OrbitControls
        ref={(instance) => {
          controlsRef.current = instance
          if (instance && onControlsReady) onControlsReady(instance)
        }}
        enablePan={false}
        minDistance={1.2}
        maxDistance={8}
      />
    </Canvas>
  )
}
