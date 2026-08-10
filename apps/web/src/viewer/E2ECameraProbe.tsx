import { useEffect } from 'react'
import type { RefObject } from 'react'
import { useThree } from '@react-three/fiber'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { E2E_CAMERA_HANDLE, readCameraState } from './e2eCameraState'
import type { DeckCameraState } from './e2eCameraState'

/**
 * Read-only camera instrumentation for the Playwright suite. See
 * `e2eCameraState.ts` for why it exists and what it replaced.
 *
 * Mounted only when `__DECKFORGE_E2E__` is true, which happens only when the
 * bundle is built with `VITE_E2E=1` - the Playwright `webServer` does that and
 * nothing else does. The guard is repeated inside the effect so that the handle
 * cannot be installed even if this component were ever rendered unguarded.
 */
export interface DeckE2EHandle {
  /** A fresh snapshot of the live camera and orbit target. */
  cameraState(): DeckCameraState
}

interface E2ECameraProbeProps {
  controlsRef: RefObject<OrbitControlsImpl | null>
}

export function E2ECameraProbe({ controlsRef }: E2ECameraProbeProps) {
  const { camera } = useThree()

  useEffect(() => {
    if (!__DECKFORGE_E2E__) return

    const handle: DeckE2EHandle = {
      cameraState: () => readCameraState(camera, controlsRef.current),
    }
    const target = window as unknown as Record<string, unknown>
    target[E2E_CAMERA_HANDLE] = handle

    return () => {
      delete target[E2E_CAMERA_HANDLE]
    }
  }, [camera, controlsRef])

  return null
}
