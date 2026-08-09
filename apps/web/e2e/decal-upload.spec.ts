import { expect, test } from '@playwright/test'
import {
  CORRUPT_PNG,
  DECAL_PNG,
  WRONG_TYPE_FILE,
  generateRequests,
  mockApi,
  recordRequests,
} from './fixtures/api'

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
    // This test settles the WebGL canvas four times and screenshots it each
    // time. On CI that is genuinely expensive - it was measured at 56.3 s
    // against the 60 s default, which is a pass with almost no headroom rather
    // than a comfortable one. Raised for THIS test only, on that measurement;
    // the suite default stays at 60 s.
    test.setTimeout(150_000)

    await mockApi(page)
    await page.goto('/')

    const canvas = page.locator('.viewer-wrapper canvas')
    await expect(canvas).toBeVisible()

    /**
     * Wait until the scene stops changing on its own.
     *
     * R3F needs a few frames to settle, and orbiting a scene that is still
     * fading in makes every later pixel comparison meaningless - the frame
     * would differ because of the fade, not because of the camera.
     */
    const settle = async () => {
      let previous = await canvas.screenshot()
      for (let attempt = 0; attempt < 20; attempt += 1) {
        await page.waitForTimeout(250)
        const current = await canvas.screenshot()
        if (Buffer.compare(previous, current) === 0) return current
        previous = current
      }
      return previous
    }

    const atRest = await settle()

    // Orbit the deck away from its default pose. Slow, with the pointer moved
    // onto the canvas first: OrbitControls listens for pointerdown on the
    // canvas, and a drag that starts before the pointer has arrived is silently
    // ignored.
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

    const orbitedBefore = await settle()

    /**
     * PRECONDITION, and the reason this test was rewritten in M8.
     *
     * The original version never checked that the drag registered. If the orbit
     * silently did nothing, the camera stayed at its default, "Reset view"
     * became a no-op, and the final assertion failed with a message claiming
     * the texture swap had reset the camera - reporting a drag that never
     * happened as a regression that never happened. This project's own rule is
     * that "not measured" and "failed" must not share a code path.
     *
     * This failure was reproduced locally by removing the SwiftShader launch
     * flags, which is the closest available approximation of a GPU-less CI
     * runner.
     */
    expect(
      Buffer.compare(atRest, orbitedBefore),
      'the orbit drag did not change the rendered frame, so the camera never moved. ' +
        'This test cannot say anything about camera preservation until the drag ' +
        'registers - it is NOT evidence that the texture swap reset the view.',
    ).not.toBe(0)

    // The artwork changes...
    await page.locator('#decal-upload').setInputFiles(DECAL_PNG)
    await expect(page.getByLabel('Decal on the deck')).toBeVisible()
    const afterUpload = await settle()
    expect(Buffer.compare(orbitedBefore, afterUpload)).not.toBe(0)

    // ...but the viewpoint does not. "Reset view" must still have work to do,
    // which it cannot if the texture swap had already snapped the camera back.
    await page.getByRole('button', { name: 'Reset view' }).click()
    const afterReset = await settle()
    expect(
      Buffer.compare(afterUpload, afterReset),
      'pressing Reset view changed nothing, which means the camera was already ' +
        'at its default pose - the texture swap reset it.',
    ).not.toBe(0)
  })
})
