import { expect, test } from '@playwright/test'
import { mockApi } from './fixtures/api'

/**
 * Layout at the two viewports that actually matter for this project.
 *
 * The desktop size is the one the demo runs at. The narrow one is not a claim
 * that DeckForge AI is a mobile application - it is not, and it never claimed to
 * be - but a layout that overflows horizontally looks broken to a jury on any
 * screen, and horizontal body scroll is the cheapest possible thing to regress.
 */

const NO_HORIZONTAL_OVERFLOW = async (page: import('@playwright/test').Page) => {
  return page.evaluate(() => {
    const doc = document.documentElement
    // One pixel of tolerance for sub-pixel rounding in the layout engine.
    return doc.scrollWidth <= doc.clientWidth + 1
  })
}

test.describe('layout', () => {
  test('the demo viewport (1440x900) shows both columns without overflow', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await mockApi(page)
    await page.goto('/')

    await expect(page.getByRole('form', { name: 'Generate a decal' })).toBeVisible()
    await expect(page.getByRole('region', { name: 'Deck preview' })).toBeVisible()
    await expect(page.locator('.viewer-wrapper canvas')).toBeVisible()

    expect(await NO_HORIZONTAL_OVERFLOW(page)).toBe(true)
  })

  test('a narrow viewport (390x844) stays usable and does not scroll sideways', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await mockApi(page)
    await page.goto('/')

    // Everything needed to actually generate must still be reachable.
    await expect(page.getByLabel('Describe the artwork')).toBeVisible()
    await expect(page.getByLabel('Style', { exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Generate decal' })).toBeVisible()
    await expect(page.locator('.viewer-wrapper canvas')).toBeVisible()

    expect(await NO_HORIZONTAL_OVERFLOW(page)).toBe(true)
  })

  test('the result panel does not overflow at the narrow viewport', async ({ page }) => {
    // Long hashes and a 512x1536 image are the realistic overflow risk, and they
    // only exist once a generation has completed.
    await page.setViewportSize({ width: 390, height: 844 })
    await mockApi(page, { generateDelayMs: 300 })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const result = page.getByRole('region', { name: 'Generation result' })
    await expect(result).toBeVisible()
    await result.getByText('Reproducibility metadata').click()
    await expect(result.getByText('EXP-028')).toBeVisible()

    expect(await NO_HORIZONTAL_OVERFLOW(page)).toBe(true)
  })
})
