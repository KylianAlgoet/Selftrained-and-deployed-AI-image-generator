import { expect, test } from '@playwright/test'
import { mockApi } from './fixtures/api'
import { PROGRESS_COLD_LOAD } from './fixtures/responses'

/**
 * Generation progress — and specifically, the honesty rules DR-013 rests on.
 *
 * These are the tests most worth having, because the failure they guard against
 * is not a crash. A progress bar that invents a percentage during model loading
 * works perfectly, looks better, and is a lie about where the time went. Only
 * denoising has a real denominator, so only denoising may show a number.
 */

test.describe('generation progress', () => {
  test('shows the waiting state and disables a second submit', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByLabel('Style', { exact: true }).selectOption('ukiyo-e')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const panel = page.getByRole('status')
    await expect(panel).toBeVisible()
    await expect(panel.getByText('GENERATING DECAL')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Generating…' })).toBeDisabled()

    // The settings actually submitted are frozen and shown, so what is running
    // cannot be confused with what the form currently holds. The style has to
    // be selected explicitly above - the form defaults to the FIRST style, so
    // asserting ukiyo-e without choosing it would have been asserting a value
    // the test never set.
    await expect(panel.getByText('Ukiyo-e woodblock')).toBeVisible()
    await expect(panel.getByText('42')).toBeVisible()
  })

  test('polls the read-only progress endpoint repeatedly, without overlapping', async ({
    page,
  }) => {
    const polls: number[] = []
    page.on('request', (request) => {
      if (request.url().includes('/api/generation-progress')) polls.push(Date.now())
    })

    await mockApi(page)
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible()

    expect(polls.length).toBeGreaterThan(2)
    // Each poll is scheduled only after the previous one settles, so requests
    // cannot pile up behind a slow response. 750 ms interval, generous floor.
    const gaps = polls.slice(1).map((at, index) => at - polls[index])
    expect(Math.min(...gaps)).toBeGreaterThan(300)
  })

  test('renders real denoising step counts from telemetry', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const panel = page.getByRole('status')
    // The exact numbers the fixture publishes - not a percentage the UI invented.
    await expect(panel.getByText('Diffusion step 14 of 30 — 47%')).toBeVisible()
    await expect(panel.getByText('Screen-print pass 14 / 30')).toBeVisible()
    await expect(panel.getByText('Printing the decal…')).toBeVisible()

    const bar = page.getByRole('progressbar', { name: 'Diffusion steps' })
    await expect(bar).toHaveAttribute('aria-valuenow', '47')
  })

  test('publishes an estimate only once steps have been timed', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const panel = page.getByRole('status')
    // First denoising snapshot carries no estimate: the interface says so.
    await expect(panel.getByText('Measuring generation speed…')).toBeVisible()
    // A later one does, and it is hedged rather than promised.
    await expect(panel.getByText(/About \d+ seconds? remaining/)).toBeVisible()
  })

  test('a stage with no denominator shows a stage name and NO percentage', async ({ page }) => {
    // The rule that DR-013 exists for. Model loading exposes no progress signal,
    // so the interface must refuse to imply one.
    await mockApi(page, { generateDelayMs: 6_000, progress: PROGRESS_COLD_LOAD })
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const panel = page.getByRole('status')
    await expect(panel.getByText('Loading the local generation model…').first()).toBeVisible()
    await expect(panel.getByText('No step percentage at this stage')).toBeVisible()
    await expect(panel.getByText(/Diffusion step/)).toHaveCount(0)
    await expect(panel.getByText(/%/)).toHaveCount(0)

    const bar = page.getByRole('progressbar', { name: 'Diffusion steps' })
    await expect(bar).not.toHaveAttribute('aria-valuenow', /.+/)
  })

  test('reaches the finalising stage and only then reports completion', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    // `.progress-stage` specifically: the same sentence is also rendered in the
    // visually-hidden aria-live announcement, so an unscoped text match finds
    // two nodes. Targeting the visible readout is the assertion that was meant.
    await expect(page.locator('.progress-stage')).toHaveText(
      /Finalising the decal…|Finishing the artwork…/,
    )
    // The progress panel then gives way to the result.
    //
    // NOT ASSERTED, DELIBERATELY: the "DECAL GENERATED" headline. It renders
    // only while the decoded PNG is being composed onto the deck, which is
    // roughly a second, and the panel unmounts the moment that finishes. An
    // assertion on it is a race against the application being fast.
    //
    // The fix is NOT to make the state linger. M7 recorded that as a decision:
    // padding a finished result so a label can be read is exactly the
    // dishonesty the progress feature exists to avoid, and accepted limitation
    // 3 says the stage may be visible only briefly. So the test asserts the
    // durable outcome instead, and this comment records why the obvious
    // assertion is missing rather than leaving it looking like an oversight.
    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible()
    await expect(page.getByRole('status')).toHaveCount(0)
  })

  test('losing telemetry degrades the display without failing the generation', async ({
    page,
  }) => {
    await mockApi(page, { generateDelayMs: 3_000 })
    // Telemetry is supplemental: killing it must not turn a working generation
    // into a reported failure.
    await page.route('**/api/generation-progress', (route) => route.abort())
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill('a mountain and a rising sun')
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const panel = page.getByRole('status')
    await expect(panel.getByText('Generating locally…')).toBeVisible()
    await expect(panel.getByText(/Elapsed: \d+ seconds?/)).toBeVisible()

    // And it still completes.
    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible()
  })
})
