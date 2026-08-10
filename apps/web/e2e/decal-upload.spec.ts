import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import {
  CORRUPT_PNG,
  DECAL_PNG,
  WRONG_TYPE_FILE,
  generateRequests,
  mockApi,
  recordRequests,
} from './fixtures/api'
import {
  DISTINCT_VIEWPOINT,
  E2E_CAMERA_HANDLE,
  MAX_RESIDUAL_DRIFT,
  describeCameraState,
  maxComponentDelta,
  toleranceForDrift,
} from '../src/viewer/e2eCameraState'
import type { DeckCameraState } from '../src/viewer/e2eCameraState'

/**
 * Frames to let the damping decay after a real drag before measuring. At 90
 * frames the measured drift is ~1.3e-3 per 5 frames, comfortably inside
 * `MAX_RESIDUAL_DRIFT`. Counted in frames, not milliseconds, so it means the
 * same thing on a 120 Hz laptop and on a software rasteriser.
 */
const FRAMES_AFTER_DRAG = 90
/** Frames to wait when the camera should already be still - it drifts ~1e-9. */
const FRAMES_WHEN_STILL = 3
/** Frames the residual drift is measured over. */
const DRIFT_FRAMES = 4

interface CameraProbe {
  /** The pose at the end of the probe. */
  state: DeckCameraState
  /** How far the camera moved on its own over the last `DRIFT_FRAMES` frames. */
  drift: number
  /** Wall-clock cost, and with it the runner's effective frame rate. */
  elapsedMs: number
  /** Frames actually observed - short of the request means the guard fired. */
  frames: number
}

/**
 * Wait a fixed number of RENDERED FRAMES, then measure the pose and how fast it
 * is still changing.
 *
 * Everything happens inside one `page.evaluate`. The previous version polled
 * from Node and cost ~120 round trips per phase, which is what blew the 60 s
 * budget on CI; this costs one. Waiting in frames rather than milliseconds is
 * the other half: OrbitControls' damping only advances when a frame renders, so
 * a frame count behaves the same on a 120 Hz laptop and on a software
 * rasteriser, where a millisecond count does not.
 *
 * The returned `drift` is what makes the comparison honest. Rather than
 * assuming the camera has settled, the caller derives its tolerance from how
 * much the camera is demonstrably still moving, measured on the machine running
 * the test.
 */
async function probeCamera(page: Page, settleFrames: number): Promise<CameraProbe> {
  const { first, second, frames, elapsedMs } = await page.evaluate(
    async ({ handle, settleFrames, driftFrames }) => {
      const probe = (window as unknown as Record<string, { cameraState(): DeckCameraState }>)[
        handle
      ]
      if (!probe) {
        throw new Error(
          `window.${handle} is missing. The suite's bundle must be built with ` +
            'VITE_E2E=1, which playwright.config.ts sets on the webServer.',
        )
      }

      // A dead or crawling render loop must fail the test with a diagnosis, not
      // hang it until the suite timeout reports nothing useful.
      const started = Date.now()
      const deadline = started + 15_000
      let frames = 0
      const nextFrame = () =>
        new Promise<void>((resolve) => {
          const guard = setTimeout(resolve, 1_000)
          requestAnimationFrame(() => {
            clearTimeout(guard)
            frames += 1
            resolve()
          })
        })

      for (let i = 0; i < settleFrames && Date.now() < deadline; i += 1) await nextFrame()
      const first = probe.cameraState()
      for (let i = 0; i < driftFrames && Date.now() < deadline; i += 1) await nextFrame()
      const second = probe.cameraState()

      return { first, second, frames, elapsedMs: Date.now() - started }
    },
    { handle: E2E_CAMERA_HANDLE, settleFrames, driftFrames: DRIFT_FRAMES },
  )

  return { state: second, drift: maxComponentDelta(first, second), frames, elapsedMs }
}

/**
 * `Upload your own decal` — the production feature that needs no GPU.
 *
 * Two claims are worth proving in a browser rather than in a unit test.
 *
 * First, that it genuinely does not call the model. The feature's whole value is
 * that someone who already owns artwork can see it on the board without spending
 * a generation, and it is also the demo's live fallback if CUDA fails on stage.
 * A request log is the only way to prove that negative.
 *
 * Second, that a failed decode preserves what is already on the deck. Blanking
 * the board on a bad file would be a worse outcome than the bad file itself.
 */

test.describe('user decal upload', () => {
  test('applies uploaded artwork without ever calling POST /api/generate', async ({ page }) => {
    const seen = recordRequests(page)
    await mockApi(page)
    await page.goto('/')

    await page.locator('#decal-upload').setInputFiles(DECAL_PNG)

    const source = page.getByLabel('Decal on the deck')
    await expect(source).toBeVisible()
    await expect(source.getByText('User-uploaded artwork')).toBeVisible()
    await expect(source.getByText('decal.png')).toBeVisible()

    // The claim, asserted rather than asserted-about.
    expect(generateRequests(seen)).toHaveLength(0)

    // The button relabels, because the deck now holds the user's own artwork.
    await expect(page.getByText('Replace decal')).toBeVisible()
  })

  test('uploaded artwork carries no reproducibility metadata', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')
    await page.locator('#decal-upload').setInputFiles(DECAL_PNG)

    await expect(page.getByLabel('Decal on the deck')).toBeVisible()
    // There is no generation, so there is nothing to attribute - and the
    // interface must not manufacture an attribution for somebody's own file.
    await expect(page.getByRole('region', { name: 'Generation result' })).toHaveCount(0)
    await expect(page.getByText('Reproducibility metadata')).toHaveCount(0)
  })

  test('an undecodable file preserves the previous decal', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')

    // Establish a known good decal first, so "preserved" means something.
    await page.locator('#decal-upload').setInputFiles(DECAL_PNG)
    await expect(page.getByLabel('Decal on the deck')).toBeVisible()

    await page.locator('#decal-upload').setInputFiles(CORRUPT_PNG)

    await expect(page.getByText(/could not be read as an image/)).toBeVisible()
    await expect(page.getByText(/previous decal is still shown/)).toBeVisible()
    // The good decal is still the one on the board.
    await expect(page.getByLabel('Decal on the deck').getByText('decal.png')).toBeVisible()
    await expect(page.locator('.viewer-wrapper canvas')).toBeVisible()
  })

  test('the client preflight rejects a wrong type before any decode', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')

    await page.locator('#decal-upload').setInputFiles(WRONG_TYPE_FILE)
    await expect(page.getByText('Choose a PNG, JPEG or WEBP image.')).toBeVisible()
    await expect(page.getByLabel('Decal on the deck')).toHaveCount(0)
  })

  test('a generated decal can be restored after an upload, with no new generation', async ({
    page,
  }) => {
    const seen = recordRequests(page)
    await mockApi(page, { generateDelayMs: 300 })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()
    await expect(page.getByText('Applied to the deck preview →')).toBeVisible()
    expect(generateRequests(seen)).toHaveLength(1)

    await page.locator('#decal-upload').setInputFiles(DECAL_PNG)
    await expect(page.getByText(/Uploaded artwork is on the deck/)).toBeVisible()

    await page.getByRole('button', { name: 'Show generated decal' }).click()
    await expect(page.getByText('Applied to the deck preview →')).toBeVisible()

    // Restoring reuses the decoded image that was kept - it is not a re-request.
    expect(generateRequests(seen)).toHaveLength(1)
  })

  test('replacing the decal does not reset the camera', async ({ page }) => {
    /**
     * MEASURED STRUCTURALLY, NOT PHOTOGRAPHICALLY.
     *
     * This test used to settle the WebGL canvas four times and compare
     * screenshots. On a GPU-less GitHub runner, where Chromium software-
     * rasterises through SwiftShader, that timed out after 300 000 ms and was
     * the last red job in M8's CI. The measurement was the problem: a pixel diff
     * is an expensive and indirect way to ask where a camera is, and it can only
     * ever conclude "the frame changed" - never "the camera is in the same
     * place", which is the actual claim.
     *
     * It now reads the camera position, orientation and orbit target directly
     * from the scene, so the assertions get stronger as well as cheaper. The
     * timeout override is gone; this runs inside the suite's 60 s default.
     */
    await mockApi(page)
    await page.goto('/')

    const canvas = page.locator('.viewer-wrapper canvas')
    await expect(canvas).toBeVisible()
    await page.waitForFunction((handle) => handle in window, E2E_CAMERA_HANDLE)

    const atRest = await probeCamera(page, FRAMES_WHEN_STILL)

    // Orbit the deck away from its default pose. A REAL interaction, unchanged:
    // the point is to move the camera the way a user does, not to call
    // OrbitControls directly. The pointer is moved onto the canvas first
    // because OrbitControls listens for pointerdown there, and a drag that
    // starts before the pointer has arrived is silently ignored.
    const box = await canvas.boundingBox()
    if (!box) throw new Error('the viewer canvas has no layout box')
    const cx = box.x + box.width / 2
    const cy = box.y + box.height / 2
    await page.mouse.move(cx, cy)
    await page.waitForTimeout(100)
    await page.mouse.down()
    await page.mouse.move(cx + 60, cy + 30, { steps: 15 })
    await page.mouse.move(cx + 130, cy + 65, { steps: 15 })
    await page.waitForTimeout(100)
    await page.mouse.up()

    const orbited = await probeCamera(page, FRAMES_AFTER_DRAG)

    /**
     * TWO PRECONDITIONS, both of which keep "not measured" off the same code
     * path as "failed".
     *
     * The first is inherited from the screenshot version: if the drag silently
     * did nothing, the camera stayed at its default, and every later assertion
     * would report a drag that never happened as a regression that never
     * happened.
     *
     * The second is new, and is what makes this rule frame-rate independent. If
     * the camera is still visibly coasting on its damping, no comparison of two
     * poses means anything - so the test says so, rather than blaming the
     * texture swap for movement the drag caused.
     */
    expect(
      maxComponentDelta(atRest.state, orbited.state),
      'the orbit drag did not move the camera, so this test cannot say anything ' +
        'about camera preservation yet. It is NOT evidence that the texture swap ' +
        `reset the view. Still at ${describeCameraState(atRest.state)}.`,
    ).toBeGreaterThan(DISTINCT_VIEWPOINT)

    expect(
      orbited.drift,
      `the camera was still moving ${orbited.drift.toExponential(2)} per ` +
        `${DRIFT_FRAMES} frames after ${orbited.frames} of a requested ` +
        `${FRAMES_AFTER_DRAG + DRIFT_FRAMES} damping frames (${orbited.elapsedMs} ms, ` +
        `~${Math.round((orbited.frames / Math.max(orbited.elapsedMs, 1)) * 1000)} fps), ` +
        'which is too much for a pose comparison to mean anything. This is an ' +
        'UNMEASURED result, not a camera-preservation failure. If the frame count ' +
        'fell short, the render loop is slower than the probe budget allows.',
    ).toBeLessThan(MAX_RESIDUAL_DRIFT)

    // The tolerance is derived from drift observed on THIS machine, not assumed.
    const tolerance = toleranceForDrift(orbited.drift)

    // The artwork changes...
    await page.locator('#decal-upload').setInputFiles(DECAL_PNG)
    await expect(page.getByLabel('Decal on the deck')).toBeVisible()
    const afterUpload = await probeCamera(page, FRAMES_WHEN_STILL)

    // ...and the viewpoint does not, which the pixel comparison could never
    // assert - it could only show that Reset view still had work to do.
    expect(
      maxComponentDelta(orbited.state, afterUpload.state),
      'replacing the decal moved the camera. Before the swap ' +
        `${describeCameraState(orbited.state)}; after it ` +
        `${describeCameraState(afterUpload.state)}. Tolerance ` +
        `${tolerance.toExponential(2)}, from a measured drift of ` +
        `${orbited.drift.toExponential(2)}.`,
    ).toBeLessThan(tolerance)

    // And the decisive form of the same claim: a swap that had reset the camera
    // would have put it back at the opening pose, 3.7 units away.
    expect(
      maxComponentDelta(atRest.state, afterUpload.state),
      'after replacing the decal the camera is back at the pose the page opened ' +
        'at, which is exactly what a texture swap resetting the view looks like.',
    ).toBeGreaterThan(DISTINCT_VIEWPOINT)

    // Reset view still returns to the opening pose - so the control is proven
    // working rather than assumed. `reset()` snaps, so no decay to wait out.
    await page.getByRole('button', { name: 'Reset view' }).click()
    const afterReset = await probeCamera(page, FRAMES_WHEN_STILL)

    expect(
      maxComponentDelta(afterUpload.state, afterReset.state),
      'pressing Reset view changed nothing, which means the camera was already ' +
        'at its default pose - the texture swap reset it.',
    ).toBeGreaterThan(DISTINCT_VIEWPOINT)

    expect(
      maxComponentDelta(atRest.state, afterReset.state),
      'Reset view did not restore the opening viewpoint. Opened at ' +
        `${describeCameraState(atRest.state)}; reset to ` +
        `${describeCameraState(afterReset.state)}.`,
    ).toBeLessThan(toleranceForDrift(afterReset.drift))
  })
})
