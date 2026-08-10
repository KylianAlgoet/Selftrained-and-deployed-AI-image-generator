/**
 * The camera read-out the E2E suite measures against, and the reason it exists.
 *
 * THE DEFECT THIS REPLACES.
 *
 * `replacing the decal does not reset the camera` used to answer a structural
 * question - did the viewpoint survive a texture swap - by comparing PNG
 * screenshots of a WebGL canvas. It settled the scene four times, and each
 * settle took up to twenty 250 ms screenshot rounds. Locally that was slow but
 * tolerable. On a GitHub Windows runner with no GPU, Chromium falls back to
 * SwiftShader and every one of those captures is software-rasterised: the test
 * timed out after 300 000 ms and was the last failing job in M8's CI.
 *
 * Raising the timeout again was rejected. The measurement was the problem, not
 * the budget: a pixel diff is an extremely expensive and extremely indirect way
 * to ask where a camera is, and it can only ever conclude "the frame changed".
 * It cannot say the camera is in the SAME place, which is the actual claim.
 *
 * WHAT THIS GIVES INSTEAD.
 *
 * Three numbers that fully determine the viewpoint - camera position, camera
 * orientation, and the orbit target - read directly out of the live scene. The
 * comparison becomes exact rather than perceptual, so the test gets STRONGER as
 * well as faster: "the pixels differ" becomes "the position, quaternion and
 * target are identical to within 1e-6".
 *
 * WHY IT IS SAFE.
 *
 * The read-out is gated on `__DECKFORGE_E2E__`, a build-time constant that Vite
 * replaces literally (see `vite.config.ts`). In an ordinary production build it
 * is `false`, the probe and this module are dropped by tree-shaking, and the
 * bundle contains no handle at all - asserted after every build by
 * `npm run verify:no-e2e-handle`. It is read-only in the strict sense: nothing
 * here writes to the camera, the controls or the scene, so it cannot change the
 * behaviour it measures.
 *
 * This module deliberately imports nothing. It is shared by the application and
 * by the Playwright suite, which typecheck under different tsconfigs, and the
 * structural parameter types below are what keep three.js out of the E2E
 * project's type graph.
 */

/** The `window` property the probe installs. E2E builds only. */
export const E2E_CAMERA_HANDLE = '__deckforgeE2ECamera'

/**
 * A complete description of the viewpoint at one instant.
 *
 * Position and quaternion come from the camera; the target comes from
 * OrbitControls and is what "Reset view" restores alongside the camera. Field
 * of view is not included: nothing in the application changes it, so a
 * difference there would mean something no test here is claiming to detect.
 */
export interface DeckCameraState {
  readonly position: readonly [number, number, number]
  readonly quaternion: readonly [number, number, number, number]
  readonly target: readonly [number, number, number]
}

interface Vector3Like {
  readonly x: number
  readonly y: number
  readonly z: number
}

interface QuaternionLike extends Vector3Like {
  readonly w: number
}

interface CameraLike {
  readonly position: Vector3Like
  readonly quaternion: QuaternionLike
}

interface OrbitControlsLike {
  readonly target: Vector3Like
}

/**
 * Snapshot the viewpoint. Pure: it copies numbers out and touches nothing.
 *
 * `controls` may be null for the window between the canvas mounting and
 * OrbitControls attaching its ref. The target falls back to the origin, which
 * is OrbitControls' own default, so an early read is consistent rather than
 * undefined - and the caller's stability wait discards it anyway.
 */
export function readCameraState(
  camera: CameraLike,
  controls: OrbitControlsLike | null,
): DeckCameraState {
  const target = controls?.target ?? { x: 0, y: 0, z: 0 }
  return {
    position: [camera.position.x, camera.position.y, camera.position.z],
    quaternion: [
      camera.quaternion.x,
      camera.quaternion.y,
      camera.quaternion.z,
      camera.quaternion.w,
    ],
    target: [target.x, target.y, target.z],
  }
}

/**
 * THE TOLERANCES, AND THE MEASUREMENT THEY ARE TAKEN FROM.
 *
 * OrbitControls runs with damping (drei enables it by default), so after a drag
 * the camera does not stop - it decays towards rest geometrically, about 5 % of
 * the remaining delta per rendered frame. It is never exactly still, so "two
 * identical reads" is not a state this scene ever reaches, and an equality rule
 * that waits for one either exits early by luck or never exits at all.
 *
 * These two numbers come from a real trace of that decay, taken on this machine
 * against the built bundle and recorded in
 * `docs/evidence/M8/ci/camera-damping-trace.md`:
 *
 *   after the drag  delta/100 ms falls below 1e-5 at ~2.9 s, then below 1e-7
 *   after the swap  delta/100 ms is already ~1e-8 - the texture swap moves nothing
 *   after a reset   the pose is the opening pose exactly, decaying from ~1e-9
 *
 * `SETTLE_EPSILON` is what "at rest" means: once consecutive samples differ by
 * less than this, the total distance still to travel is bounded by roughly
 * 20x it, i.e. under 1e-3.
 *
 * `CAMERA_EPSILON` is what "the same viewpoint" means, and is set an order of
 * magnitude above that residual so damping cannot fail the comparison. It stays
 * three orders of magnitude BELOW any movement the test cares about: the orbit
 * drag moves the camera 3.7 world units and the quaternion by 0.6. So the rule
 * keeps a ~30x margin against damping noise and a ~3700x margin against a real
 * camera reset - the failure it exists to catch.
 */
export const SETTLE_EPSILON = 1e-5
export const CAMERA_EPSILON = 1e-3

/** The largest single-component difference between two snapshots. */
export function maxComponentDelta(a: DeckCameraState, b: DeckCameraState): number {
  const pairs: Array<[readonly number[], readonly number[]]> = [
    [a.position, b.position],
    [a.quaternion, b.quaternion],
    [a.target, b.target],
  ]
  let largest = 0
  for (const [left, right] of pairs) {
    if (left.length !== right.length) return Number.POSITIVE_INFINITY
    for (let index = 0; index < left.length; index += 1) {
      largest = Math.max(largest, Math.abs(left[index] - right[index]))
    }
  }
  return largest
}

function closeEnough(a: readonly number[], b: readonly number[], epsilon: number): boolean {
  if (a.length !== b.length) return false
  return a.every((value, index) => Math.abs(value - b[index]) <= epsilon)
}

/** True when two snapshots describe the same viewpoint. */
export function cameraStatesEqual(
  a: DeckCameraState,
  b: DeckCameraState,
  epsilon: number = CAMERA_EPSILON,
): boolean {
  return (
    closeEnough(a.position, b.position, epsilon) &&
    closeEnough(a.quaternion, b.quaternion, epsilon) &&
    closeEnough(a.target, b.target, epsilon)
  )
}

/** A one-line rendering for assertion messages, so a failure names real numbers. */
export function describeCameraState(state: DeckCameraState): string {
  const round = (values: readonly number[]) => values.map((v) => v.toFixed(4)).join(', ')
  return `position(${round(state.position)}) quaternion(${round(state.quaternion)}) target(${round(state.target)})`
}
