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
 * THE COMPARISON RULE, AND WHY IT IS NOT A FIXED TOLERANCE.
 *
 * OrbitControls runs with damping (drei enables it by default), so after a drag
 * the camera does not stop - it decays towards rest geometrically, roughly 5 %
 * of the remaining delta per **rendered frame**. It is never exactly still.
 *
 * Two rules were tried and both were wrong, for recorded reasons:
 *
 * 1. "Two identical reads" - a state this scene never reaches. Failed 3/3
 *    locally.
 * 2. "Poll every 100 ms until consecutive samples differ by < 1e-5" - correct
 *    locally in 6.6 s, but it cost ~120 browser round trips per phase and, on a
 *    GPU-less CI runner, blew the 60 s test timeout. Decay is measured in
 *    FRAMES, and a software rasteriser produces far fewer of them per second,
 *    so any rule with a hard-coded settling time is a bet on the frame rate.
 *
 * The rule here makes no such bet. Each probe waits a fixed number of **frames**
 * and then measures how far the camera moves on its own over a few more - the
 * residual drift, observed on the machine that is actually running the test.
 * The tolerance for "the viewpoint did not change" is then derived from that
 * measurement rather than assumed, and `MAX_RESIDUAL_DRIFT` refuses the
 * comparison outright if the camera is still moving too much for it to mean
 * anything. "Not measured" and "failed" stay on separate code paths.
 *
 * Reference numbers, from a real trace on the development machine recorded in
 * `docs/evidence/M8/ci/camera-damping-trace.md`:
 *
 *   the orbit drag moves the camera 3.7 world units and the quaternion by 0.6
 *   ~90 frames after release, drift is ~1.6e-3 per 6 frames
 *   after the texture swap, drift is ~1e-8 - the swap moves nothing at all
 *   after Reset view, the pose is the opening pose exactly, drift ~1e-9
 */

/** Floor for "the viewpoint did not change" when the camera is already still. */
export const CAMERA_EPSILON = 1e-3

/**
 * Multiplier applied to the observed drift to get the working tolerance. The
 * remaining decay is a geometric series, so allowing an order of magnitude more
 * than one sample's worth of drift covers the whole tail with room to spare.
 */
export const DRIFT_TOLERANCE_FACTOR = 20

/**
 * Above this, the camera is still in flight and no comparison is meaningful.
 * A probe that reports more drift than this fails as UNMEASURED rather than
 * being reported as a camera that moved.
 *
 * It is 5e-3 rather than the 0.05 first written here, because a unit test
 * caught that 0.05 x `DRIFT_TOLERANCE_FACTOR` came to exactly
 * `DISTINCT_VIEWPOINT`: at the worst drift the test would accept, the derived
 * tolerance would have been wide enough to swallow an entire change of
 * viewpoint. At 5e-3 the worst-case tolerance is 0.1 - a 10x margin under
 * `DISTINCT_VIEWPOINT` and 37x under the 3.7-unit move a camera reset makes.
 *
 * It is comfortably reachable: the measured decay is ~1.3e-3 per 5 frames once
 * 90 frames have passed, and because the decay is counted in frames rather than
 * milliseconds that figure does not depend on how fast the machine renders.
 */
export const MAX_RESIDUAL_DRIFT = 5e-3

/**
 * How far apart two poses must be to count as genuinely different viewpoints.
 * The drag and a camera reset both move ~3.7 units, so this has a 3.7x margin
 * while sitting far above any damping residue.
 */
export const DISTINCT_VIEWPOINT = 1.0

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

/**
 * The tolerance to compare two poses with, given the drift measured alongside
 * them. Never tighter than `CAMERA_EPSILON`, so a perfectly still camera does
 * not get an absurdly small budget.
 */
export function toleranceForDrift(drift: number): number {
  return Math.max(drift * DRIFT_TOLERANCE_FACTOR, CAMERA_EPSILON)
}

/** A one-line rendering for assertion messages, so a failure names real numbers. */
export function describeCameraState(state: DeckCameraState): string {
  const round = (values: readonly number[]) => values.map((v) => v.toFixed(4)).join(', ')
  return `position(${round(state.position)}) quaternion(${round(state.quaternion)}) target(${round(state.target)})`
}
