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
  CAMERA_EPSILON,
  E2E_CAMERA_HANDLE,
  SETTLE_EPSILON,
  cameraStatesEqual,
  describeCameraState,
  maxComponentDelta,
} from '../src/viewer/e2eCameraState'
import type { DeckCameraState } from '../src/viewer/e2eCameraState'

/**
 * Read the live viewpoint, after at least one frame has actually rendered.
 *
 * The rAF wait matters. OrbitControls' damping only advances on a rendered
 * frame, so if the render loop stalls - which it does on a software rasteriser
 * - two wall-clock samples can be identical while the camera is still mid-
 * flight, and a settle loop would call that "at rest". Sampling per frame ties
 * the measurement to the thing that moves the camera. The 2 s ceiling stops a
 * genuinely dead render loop from hanging the test instead of failing it.
 */
async function readCameraState(page: Page): Promise<DeckCameraState> {
  return page.evaluate(async (handle) => {
    const probe = (window as unknown as Record<string, { cameraState(): DeckCameraState }>)[handle]
    if (!probe) {
      throw new Error(
        `window.${handle} is missing. The suite's bundle must be built with ` +
          'VITE_E2E=1, which playwright.config.ts sets on the webServer.',
      )
    }
    await new Promise<void>((resolve) => {
      const guard = setTimeout(resolve, 2_000)
      requestAnimationFrame(() => {
        clearTimeout(guard)
        resolve()
      })
    })
    return probe.cameraState()
  }, E2E_CAMERA_HANDLE)
}

/**
 * Wait until the viewpoint has come to rest, then return it.
 *
 * "At rest" is a threshold, not an equality: damping means the camera decays
 * towards its destination and never exactly arrives (see the tolerance note in
 * `e2eCameraState.ts` for the measured decay). Two consecutive samples under
 * the threshold are required, so one stalled frame cannot be mistaken for a
 * camera that has stopped.
 *
 * This is the cheap successor to the old screenshot settle loop: two
 * `page.evaluate` calls per round instead of two WebGL canvas captures.
 */
async function settledCameraState(page: Page): Promise<DeckCameraState> {
  const history: number[] = []
  let previous = await readCameraState(page)
  let quietRounds = 0

  for (let attempt = 0; attempt < 120; attempt += 1) {
    await page.waitForTimeout(100)
    const current = await readCameraState(page)
    const delta = maxComponentDelta(previous, current)
    history.push(delta)
    previous = current

    quietRounds = delta < SETTLE_EPSILON ? quietRounds + 1 : 0
    if (quietRounds >= 2) return current
  }

  const tail = history.slice(-8).map((d) => d.toExponential(1)).join(', ')
  throw new Error(
    `the camera never came to rest within 12 s. Last read ` +
      `${describeCameraState(previous)}; recent per-sample deltas: ${tail}.`,
  )
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

    const atRest = await settledCameraState(page)

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

    const orbited = await settledCameraState(page)

    /**
     * PRECONDITION, kept from the screenshot version.
     *
     * The original version never checked that the drag registered. If the orbit
     * silently did nothing, the camera stayed at its default, "Reset view"
     * became a no-op, and the final assertion failed with a message claiming
     * the texture swap had reset the camera - reporting a drag that never
     * happened as a regression that never happened. This project's own rule is
     * that "not measured" and "failed" must not share a code path.
     */
    expect(
      cameraStatesEqual(atRest, orbited),
      'the orbit drag did not move the camera, so this test cannot say anything ' +
        'about camera preservation yet. It is NOT evidence that the texture swap ' +
        `reset the view. Still at ${describeCameraState(atRest)}.`,
    ).toBe(false)

    // The artwork changes...
    await page.locator('#decal-upload').setInputFiles(DECAL_PNG)
    await expect(page.getByLabel('Decal on the deck')).toBeVisible()
    const afterUpload = await settledCameraState(page)

    // ...and the viewpoint is IDENTICAL, which the pixel comparison could never
    // assert - it could only show that Reset view still had work to do.
    expect(
      cameraStatesEqual(orbited, afterUpload),
      'replacing the decal moved the camera. Before the swap ' +
        `${describeCameraState(orbited)}; after it ${describeCameraState(afterUpload)}; ` +
        `largest component moved by ${maxComponentDelta(orbited, afterUpload).toExponential(2)}, ` +
        `tolerance ${CAMERA_EPSILON}.`,
    ).toBe(true)

    // Reset view still returns to the default pose, and to exactly the pose the
    // page opened at - so the control is proven working rather than assumed.
    await page.getByRole('button', { name: 'Reset view' }).click()
    const afterReset = await settledCameraState(page)
    expect(
      cameraStatesEqual(afterUpload, afterReset),
      'pressing Reset view changed nothing, which means the camera was already ' +
        'at its default pose - the texture swap reset it.',
    ).toBe(false)
    expect(
      cameraStatesEqual(atRest, afterReset),
      `Reset view did not restore the opening viewpoint. Opened at ` +
        `${describeCameraState(atRest)}; reset to ${describeCameraState(afterReset)}.`,
    ).toBe(true)
  })
})
