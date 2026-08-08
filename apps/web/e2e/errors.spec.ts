import { expect, test } from '@playwright/test'
import { mockApi } from './fixtures/api'
import {
  ERROR_BUSY,
  ERROR_MODEL_UNAVAILABLE,
  ERROR_TIMEOUT,
  ERROR_VALIDATION_PROMPT,
} from './fixtures/responses'

/**
 * Every failure the service can return, rendered as what it actually is.
 *
 * The distinction that matters most is 409. A refused request is the
 * single-flight lock working exactly as designed - the GPU holds one resident
 * pipeline with about 200 MiB spare, so refusing is correct behaviour. Showing
 * it as an error would teach a user that a healthy system is broken.
 */

test.describe('error handling', () => {
  test('409 is presented as busy, not as a failure', async ({ page }) => {
    await mockApi(page, { generateDelayMs: 200, generateError: ERROR_BUSY })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    await expect(page.getByText(/GPU is finishing another decal/)).toBeVisible()
    // The form comes straight back - retrying is the expected next action.
    await expect(page.getByRole('button', { name: 'Generate decal' })).toBeEnabled()
    await expect(page.getByRole('region', { name: 'Generation result' })).toHaveCount(0)
  })

  test('504 reports how far the generation actually got', async ({ page }) => {
    await mockApi(page, { generateDelayMs: 200, generateError: ERROR_TIMEOUT })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    // The step count is what makes the early stop verifiable from the response
    // rather than inferred from a stopwatch.
    await expect(page.getByText(/stopped after 14 of 30 steps/)).toBeVisible()
  })

  test('503 says the model is unavailable and leaks no path', async ({ page }) => {
    await mockApi(page, { generateDelayMs: 200, generateError: ERROR_MODEL_UNAVAILABLE })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    await expect(page.getByText(/trained style is unavailable on this machine/)).toBeVisible()

    // A checkpoint path in the browser would be an information leak; the server
    // log carries the detail instead.
    const body = (await page.textContent('body')) ?? ''
    expect(body).not.toContain('outputs/lora')
    expect(body).not.toContain('C:\\')
    expect(body).not.toContain('.safetensors')
  })

  test('422 attaches the message to the field that caused it', async ({ page }) => {
    await mockApi(page, { generateDelayMs: 200, generateError: ERROR_VALIDATION_PROMPT })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('   ')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const alert = page.getByRole('alert')
    await expect(alert).toBeVisible()
    await expect(alert).toHaveText('Describe what to generate.')
  })

  test('a network failure is reported without blaming the user', async ({ page }) => {
    await mockApi(page)
    await page.route('**/api/generate', (route) => route.abort())
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    await expect(page.getByText(/Check that the service is running/)).toBeVisible()
  })

  test('a failed generation leaves the deck and the form usable', async ({ page }) => {
    await mockApi(page, { generateDelayMs: 200, generateError: ERROR_TIMEOUT })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain')
    await page.getByRole('button', { name: 'Generate decal' }).click()
    await expect(page.getByText(/stopped after 14 of 30 steps/)).toBeVisible()

    // The starter decal is still rendered and a retry is possible.
    await expect(page.locator('.viewer-wrapper canvas')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Generate decal' })).toBeEnabled()
  })
})
