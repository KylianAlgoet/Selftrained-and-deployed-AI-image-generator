import { expect, test } from '@playwright/test'
import { mockApi } from './fixtures/api'

/**
 * The application shell, and the production/review separation.
 *
 * The review separation is the reason this file exists. Two controls - the
 * texture-fit selector and the inverted-UV demonstration - are evidence behind
 * DR-012 and must stay in the codebase, but must never appear in the interface a
 * user or a jury sees. "Hidden from production" is a claim that decays silently
 * unless something checks it, and the vitest suite checks the component while
 * this checks the shipped bundle.
 */

test.describe('application shell', () => {
  test('opens, renders the workspace, and logs no console errors', async ({ page }) => {
    const errors: string[] = []
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text())
    })
    page.on('pageerror', (error) => errors.push(error.message))

    await mockApi(page)
    await page.goto('/')

    await expect(page.getByRole('heading', { name: 'DeckForge AI', level: 1 })).toBeVisible()
    await expect(page.getByRole('form', { name: 'Generate a decal' })).toBeVisible()
    await expect(page.getByRole('region', { name: 'Deck preview' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Generate decal' })).toBeEnabled()

    expect(errors).toEqual([])
  })

  test('renders the 3D deck on a live WebGL context', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')

    const canvas = page.locator('.viewer-wrapper canvas')
    await expect(canvas).toBeVisible()

    // A canvas element proves markup; a context proves the renderer started.
    const hasContext = await canvas.evaluate(
      (node) => Boolean((node as HTMLCanvasElement).getContext('webgl2') ??
        (node as HTMLCanvasElement).getContext('webgl')),
    )
    expect(hasContext).toBe(true)

    const box = await canvas.boundingBox()
    expect(box?.width ?? 0).toBeGreaterThan(100)
    expect(box?.height ?? 0).toBeGreaterThan(100)
  })

  test('the production interface exposes no review-only controls', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')

    await expect(page.getByRole('group', { name: /Texture fit/ })).toHaveCount(0)
    await expect(page.getByLabel(/Inverted-UV demonstration/)).toHaveCount(0)
    await expect(page.getByText('Review mode')).toHaveCount(0)

    // The production feature that lives beside them must still be there.
    await expect(page.getByText('Upload your own decal')).toBeVisible()
  })

  test('?review=1 restores both review tools and labels the mode', async ({ page }) => {
    await mockApi(page)
    await page.goto('/?review=1')

    await expect(page.getByRole('group', { name: /Texture fit/ })).toBeVisible()
    await expect(page.getByLabel(/Inverted-UV demonstration/)).toBeVisible()
    await expect(page.getByText('Review mode')).toBeVisible()
  })

  test('the deck disclosure states the DR-012 stretch openly', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')

    // The accepted cost of full-surface is disclosed in the interface, not
    // buried in a decision record.
    await expect(page.getByText(/1\.3008/)).toBeVisible()
  })

  test('an unreachable service is reported with the command to start it', async ({ page }) => {
    await mockApi(page, { stylesUnavailable: true })
    await page.goto('/')

    await expect(page.getByText(/Could not reach the generation service/)).toBeVisible()
    await expect(page.getByText(/--workers 1/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Generate decal' })).toBeDisabled()
  })
})
