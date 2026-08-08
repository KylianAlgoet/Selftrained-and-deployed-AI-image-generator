import { expect, test } from '@playwright/test'
import { DECAL_PNG, generateRequests, mockApi, recordRequests } from './fixtures/api'
import { GENERATE_RESPONSE_PARTIAL_PASS, STYLES_RESPONSE } from './fixtures/responses'

/**
 * The generation workflow, from typing a prompt to artwork on the deck.
 *
 * The request assertions matter as much as the rendering ones. A form that
 * looks right but posts the wrong field names produces a 422 in production and a
 * green test suite here, so the multipart body is inspected directly.
 */

test.describe('generation workflow', () => {
  test('lists the three production styles and shows the partial-pass limitation', async ({
    page,
  }) => {
    await mockApi(page)
    await page.goto('/')

    const select = page.getByLabel('Style', { exact: true })
    await expect(select.locator('option')).toHaveCount(3)

    // The partial pass is marked in the option itself, before anyone generates.
    await expect(select.locator('option', { hasText: 'Retro silkscreen poster' })).toHaveText(
      /\(partial\)/,
    )

    await select.selectOption('retro-poster')
    await expect(page.getByText(/pseudo-text, borders and framed composition/)).toBeVisible()

    // Switching away retires the notice - it belongs to the style, not the page.
    await select.selectOption('ukiyo-e')
    await expect(page.getByText(/pseudo-text, borders and framed composition/)).toHaveCount(0)
  })

  test('advanced settings are bounded by the decision records', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')
    await page.getByText('Advanced settings').click()

    // DR-010: 0.4-1.0, default 0.7. Literals, not arithmetic on the fixture -
    // `0.7 - 0.3` is 0.39999999999999997 in IEEE 754 and would never match.
    const weight = page.getByLabel(/Style strength/)
    await expect(weight).toHaveAttribute('min', '0.4')
    await expect(weight).toHaveAttribute('max', '1')
    await expect(weight).toHaveValue(String(STYLES_RESPONSE.default_lora_weight))

    const scale = page.getByLabel(/Reference influence/)
    await expect(scale).toHaveAttribute('min', '0.4')
    await expect(scale).toHaveAttribute('max', '0.6')
    // DR-008: the control means nothing without a reference, so it is disabled.
    await expect(scale).toBeDisabled()

    await expect(page.getByLabel('Seed')).toHaveValue('42')
  })

  test('a reference image can be attached and removed', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')

    await expect(page.getByText('No image attached')).toBeVisible()
    await page.locator('input[type="file"]').first().setInputFiles(DECAL_PNG)

    await expect(page.getByText('Image attached')).toBeVisible()
    await expect(page.getByText('decal.png')).toBeVisible()

    await page.getByText('Advanced settings').click()
    await expect(page.getByLabel(/Reference influence/)).toBeEnabled()

    await page.getByRole('button', { name: 'Remove' }).click()
    await expect(page.getByText('No image attached')).toBeVisible()
    await expect(page.getByLabel(/Reference influence/)).toBeDisabled()
  })

  test('submits the prompt, style and bounded settings as multipart form fields', async ({
    page,
  }) => {
    const seen = recordRequests(page)
    await mockApi(page, { generateDelayMs: 300 })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByLabel('Style', { exact: true }).selectOption('ukiyo-e')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible()

    const posts = generateRequests(seen)
    expect(posts).toHaveLength(1)

    const body = posts[0].postData() ?? ''
    expect(body).toContain('name="prompt"')
    expect(body).toContain('a mountain and a rising sun')
    expect(body).toContain('name="style"')
    expect(body).toContain('ukiyo-e')
    expect(body).toContain('name="lora_weight"')
    expect(body).toContain('0.7')
    expect(body).toContain('name="ip_adapter_scale"')
    expect(body).toContain('name="seed"')
    expect(body).toContain('42')
    // Prompt-only: no reference part may be sent at all.
    expect(body).not.toContain('name="reference_image"')
  })

  test('sends the reference image as a file part when one is attached', async ({ page }) => {
    const seen = recordRequests(page)
    await mockApi(page, { generateDelayMs: 300 })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a fox')
    await page.locator('input[type="file"]').first().setInputFiles(DECAL_PNG)
    await page.getByRole('button', { name: 'Generate decal' }).click()

    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible()

    const body = generateRequests(seen)[0].postData() ?? ''
    expect(body).toContain('name="reference_image"')
    expect(body).toContain('filename="decal.png"')
  })

  test('a completed generation shows the image, the duration and the metadata', async ({
    page,
  }) => {
    await mockApi(page, { generateDelayMs: 300 })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const result = page.getByRole('region', { name: 'Generation result' })
    await expect(result).toBeVisible()
    await expect(result.getByRole('heading', { name: 'Generated decal' })).toBeVisible()
    await expect(result.getByText('12.96s')).toBeVisible()
    await expect(result.locator('img')).toBeVisible()
    await expect(result.getByText('512×1536').first()).toBeVisible()

    // The reproducibility block is what makes an image traceable rather than
    // just a picture, so its identifying facts are asserted, not just its title.
    await result.getByText('Reproducibility metadata').click()
    await expect(result.getByText('EXP-028')).toBeVisible()
    await expect(result.getByText('52381b6052ad71f1…')).toBeVisible()
    await expect(result.getByText('none (prompt only)')).toBeVisible()
  })

  test('offers a PNG download and a metadata download', async ({ page }) => {
    await mockApi(page, { generateDelayMs: 300 })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()
    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible()

    const png = page.waitForEvent('download')
    await page.getByRole('button', { name: 'Download PNG' }).click()
    expect((await png).suggestedFilename()).toBe('deckforge-e2e_fixture_generation.png')

    const meta = page.waitForEvent('download')
    await page.getByRole('button', { name: 'Download metadata' }).click()
    expect((await meta).suggestedFilename()).toBe('deckforge-e2e_fixture_generation.json')
  })

  test('applies the generated artwork to the deck', async ({ page }) => {
    await mockApi(page, { generateDelayMs: 300 })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    // The provenance claim: this result IS what is on the board.
    await expect(page.getByText('Applied to the deck preview →')).toBeVisible()
    await expect(page.locator('.viewer-wrapper canvas')).toBeVisible()
    // `fitDisclosure` rounds to three decimals, so the result panel reads
    // 1.301x while the static viewer note quotes the exact 1.3008x. Both are
    // the same DR-012 stretch; asserting 1.3008 here would be asserting a
    // string the component never produces.
    await expect(page.locator('.fit-disclosure')).toContainText(/1\.301×/)
    await expect(page.locator('.fit-disclosure')).toContainText(/cover the whole surface/)
  })

  test('a partial-pass style returns its limitation as a result warning', async ({ page }) => {
    await mockApi(page, {
      generateDelayMs: 300,
      generateResponse: GENERATE_RESPONSE_PARTIAL_PASS,
    })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain')
    await page.getByLabel('Style', { exact: true }).selectOption('retro-poster')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const result = page.getByRole('region', { name: 'Generation result' })
    await expect(result).toBeVisible()
    // Shipped stated, not hidden - once before generating, once with the result.
    await expect(result.getByText(/pseudo-text, borders and framed composition/)).toBeVisible()
  })
})
