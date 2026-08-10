import { describe, expect, it } from 'vitest'
import {
  CAMERA_EPSILON,
  cameraStatesEqual,
  describeCameraState,
  readCameraState,
} from './e2eCameraState'
import type { DeckCameraState } from './e2eCameraState'

/**
 * The E2E camera read-out is the only measurement behind
 * `replacing the decal does not reset the camera`, so its comparison rule is
 * worth testing where a failure is cheap to read - in vitest, not in a browser.
 *
 * The risk being covered is a comparison that is too lax. If `cameraStatesEqual`
 * ever returned true for a camera that had moved, the E2E test would pass while
 * the viewpoint was being reset on every texture swap, which is exactly the
 * regression it exists to catch.
 */

function camera(position: [number, number, number], quaternion: [number, number, number, number]) {
  return {
    position: { x: position[0], y: position[1], z: position[2] },
    quaternion: { x: quaternion[0], y: quaternion[1], z: quaternion[2], w: quaternion[3] },
  }
}

const DEFAULT_POSE = camera([1.5, -2.1, 2.4], [0.1, 0.2, 0.3, 0.9])
const AT_ORIGIN = { target: { x: 0, y: 0, z: 0 } }

describe('readCameraState', () => {
  it('copies the camera pose and the orbit target', () => {
    const state = readCameraState(DEFAULT_POSE, { target: { x: 0, y: 0.5, z: -1 } })

    expect(state.position).toEqual([1.5, -2.1, 2.4])
    expect(state.quaternion).toEqual([0.1, 0.2, 0.3, 0.9])
    expect(state.target).toEqual([0, 0.5, -1])
  })

  it('falls back to the origin before OrbitControls has attached', () => {
    // The window between the canvas mounting and the controls ref arriving.
    // OrbitControls' own default target is the origin, so this is consistent
    // rather than invented.
    expect(readCameraState(DEFAULT_POSE, null).target).toEqual([0, 0, 0])
  })

  it('does not touch what it measures', () => {
    // The whole safety argument for shipping this behind a flag is that it is
    // read-only. A probe that nudged the camera would change the behaviour the
    // suite is asserting about.
    const live = camera([1, 2, 3], [0, 0, 0, 1])
    const controls = { target: { x: 4, y: 5, z: 6 } }
    const before = JSON.stringify({ live, controls })

    readCameraState(live, controls)

    expect(JSON.stringify({ live, controls })).toBe(before)
  })

  it('returns a fresh snapshot rather than a live view', () => {
    // three.js reuses its Vector3 instances, so a snapshot that kept references
    // would silently change under the test between two reads.
    const live = { position: { x: 1, y: 1, z: 1 }, quaternion: { x: 0, y: 0, z: 0, w: 1 } }
    const first = readCameraState(live, AT_ORIGIN)
    live.position.x = 99
    const second = readCameraState(live, AT_ORIGIN)

    expect(first.position[0]).toBe(1)
    expect(second.position[0]).toBe(99)
  })
})

describe('cameraStatesEqual', () => {
  const base: DeckCameraState = {
    position: [1.5, -2.1, 2.4],
    quaternion: [0.1, 0.2, 0.3, 0.9],
    target: [0, 0, 0],
  }

  it('accepts an identical viewpoint', () => {
    expect(cameraStatesEqual(base, { ...base })).toBe(true)
  })

  it('tolerates a final-bit difference', () => {
    const nudged: DeckCameraState = { ...base, position: [1.5 + CAMERA_EPSILON / 2, -2.1, 2.4] }
    expect(cameraStatesEqual(base, nudged)).toBe(true)
  })

  it.each([
    ['position', { ...base, position: [1.6, -2.1, 2.4] } as DeckCameraState],
    ['quaternion', { ...base, quaternion: [0.1, 0.2, 0.4, 0.9] } as DeckCameraState],
    ['target', { ...base, target: [0, 0.3, 0] } as DeckCameraState],
  ])('rejects a change in %s', (_field, moved) => {
    expect(cameraStatesEqual(base, moved)).toBe(false)
  })

  it('rejects a difference just above the tolerance', () => {
    const moved: DeckCameraState = { ...base, position: [1.5 + CAMERA_EPSILON * 10, -2.1, 2.4] }
    expect(cameraStatesEqual(base, moved)).toBe(false)
  })

  it('rejects an orbit-sized move by a wide margin', () => {
    // Representative of the drag the E2E test performs: whole units, not noise.
    const orbited: DeckCameraState = {
      position: [2.9, -0.4, 1.7],
      quaternion: [0.31, 0.05, -0.12, 0.94],
      target: [0, 0, 0],
    }
    expect(cameraStatesEqual(base, orbited)).toBe(false)
  })
})

describe('describeCameraState', () => {
  it('names the real numbers, so a failure message is diagnosable', () => {
    const described = describeCameraState({
      position: [1.5, -2.1, 2.4],
      quaternion: [0, 0, 0, 1],
      target: [0, 0, 0],
    })

    expect(described).toContain('1.5000')
    expect(described).toContain('-2.1000')
    expect(described).toContain('position')
    expect(described).toContain('quaternion')
    expect(described).toContain('target')
  })
})
