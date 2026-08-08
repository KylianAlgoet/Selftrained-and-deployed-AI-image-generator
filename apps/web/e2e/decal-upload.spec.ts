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
    await mockApi(page)
    await page.goto('/')

    const canvas = page.locator('.viewer-wrapper canvas')
    await expect(canvas).toBeVisible()

    // Orbit the deck away from its default pose.
    const box = await canvas.boundingBox()
    if (!box) throw new Error('the viewer canvas has no layout box')
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
    await page.mouse.down()
    await page.mouse.move(box.x + box.width / 2 + 120, box.y + box.height / 2 + 60, { steps: 12 })
    await page.mouse.up()
    await page.waitForTimeout(300)

    // The canvas is the only stable handle on camera state from outside the
    // React tree, so the comparison is a rendered-pixel one: replacing a texture
    // must change the decal without moving the viewpoint.
    const before = await canvas.screenshot()

    await page.locator('#decal-upload').setInputFiles(DECAL_PNG)
    await expect(page.getByLabel('Decal on the deck')).toBeVisible()
    await page.waitForTimeout(500)
    const after = await canvas.screenshot()

    // Different artwork, so the images must differ...
    expect(Buffer.compare(before, after)).not.toBe(0)

    // ...but the deck must still be in the orbited pose, not snapped back to the
    // default. Resetting the view is what the Reset button is for, and pressing
    // it here must visibly change the frame - which it cannot do if the texture
    // swap had already reset it.
    const orbited = await canvas.screenshot()
    await page.getByRole('button', { name: 'Reset view' }).click()
    await page.waitForTimeout(500)
    const reset = await canvas.screenshot()
    expect(Buffer.compare(orbited, reset)).not.toBe(0)
  })
})
