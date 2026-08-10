import { useEffect, useMemo, useRef } from 'react'
import { Canvas, useThree } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import type { Texture } from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { createDeckGeometry } from '../deck/deckGeometry'
import { E2ECameraProbe } from './E2ECameraProbe'

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
  /**
   * The decal texture, owned and disposed by the caller (see `textureSwap.ts`).
   * `null` renders the bare deck rather than a blank map, which is what a
   * first load or a failed swap with no previous texture should look like.
   */
  texture: Texture | null
  /** Demonstration-only: renders the decal deliberately nose/tail inverted. */
  invertDemo: boolean
}

function DeckMesh({ texture, invertDemo }: DeckMeshProps) {
  const geometry = useMemo(
    () => createDeckGeometry({ invertV: invertDemo }),
    [invertDemo],
  )

  return (
    <mesh geometry={geometry}>
      {/* Material index 0: decal face (deck underside) */}
      <meshStandardMaterial
        attach="material-0"
        map={texture}
        color={texture ? '#ffffff' : '#b9b4ab'}
        roughness={0.55}
      />
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
 *
 * The camera and the controls are mounted once and are NOT keyed on the
 * texture, so swapping a decal leaves the user's viewpoint exactly where they
 * put it. Remounting here would silently reset the camera on every generation.
 */
export function DeckViewer({ texture, invertDemo, onControlsReady }: DeckViewerProps) {
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
      <DeckMesh texture={texture} invertDemo={invertDemo} />
      {import.meta.env.DEV && <EvidenceCaptureHook />}
      {/* E2E builds only, and read-only. `__DECKFORGE_E2E__` is replaced with a
          literal `false` in an ordinary build, so this branch and everything it
          imports are removed from the shipped bundle. */}
      {__DECKFORGE_E2E__ && <E2ECameraProbe controlsRef={controlsRef} />}
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
