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
 *
 * HOW THESE TESTS AVOID RACING THE RENDERER.
 *
 * Every test here runs the mock in `'gated'` mode and holds `POST /api/generate`
 * open. The mock serves exactly the telemetry snapshot the test selects and
 * never advances on its own, so a state under assertion cannot disappear before
 * the browser has painted it.
 *
 * That is not a convenience. The first version advanced one snapshot per poll,
 * which gave every transient state a wall-clock lifetime of ~750 ms regardless
 * of whether it had rendered. On a GPU-less CI runner — Chromium on SwiftShader,
 * the suite taking 14.7 minutes against 84 seconds locally — React lagged the
 * polls and six of these tests failed on states the application had produced
 * correctly. The application was right and the tests were racing it.
 *
 * The production polling interval, the progress hook and the panel are
 * unchanged. Only the mock's advance policy differs.
 *
 * Snapshot indices in PROGRESS_SEQUENCE:
 *   0 loading-style · 1 denoising 3/30 (no estimate) · 2 denoising 14/30 (est 7)
 *   3 denoising 27/30 (est 2) · 4 decoding · 5 saving · 6 completed
 */

/**
 * Applying the finished 512x1536 PNG to the deck runs a decode plus a WebGL
 * texture upload. CI has no GPU, and that step is measurably slow there.
 *
 * This covers the DURABLE end state only. Every transient assertion above is
 * deterministic by construction, so nothing else needed relaxing — and the
 * application is not slowed to accommodate a runner.
 */
const RESULT_TIMEOUT = 45_000

const PROMPT = 'a mountain and a rising sun'

test.describe('generation progress', () => {
  test('shows the waiting state and disables a second submit', async ({ page }) => {
    const api = await mockApi(page, { progressMode: 'gated', gateGenerate: true })
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill(PROMPT)
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

    api.completeGeneration()
    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible({
      timeout: RESULT_TIMEOUT,
    })
  })

  test('polls the read-only progress endpoint repeatedly, without overlapping', async ({
    page,
  }) => {
    const polls: number[] = []
    page.on('request', (request) => {
      if (request.url().includes('/api/generation-progress')) polls.push(Date.now())
    })

    // Auto mode is wrong here and gated mode is right for the same reason: this
    // test is about the POLLING CADENCE, not about any particular state, so the
    // snapshot is held still and only the request timing is measured.
    const api = await mockApi(page, { progressMode: 'gated', gateGenerate: true })
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill(PROMPT)
    await page.getByRole('button', { name: 'Generate decal' }).click()

    await expect(page.getByRole('status')).toBeVisible()
    await expect.poll(() => api.progressPolls(), { timeout: 20_000 }).toBeGreaterThan(2)

    // Each poll is scheduled only after the previous one settles, so requests
    // cannot pile up behind a slow response. 750 ms interval, generous floor.
    const gaps = polls.slice(1).map((at, index) => at - polls[index])
    expect(Math.min(...gaps)).toBeGreaterThan(300)

    api.completeGeneration()
    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible({
      timeout: RESULT_TIMEOUT,
    })
  })

  test('the gated mock does not advance a state before the test allows it', async ({
    page,
  }) => {
    // The regression test for the determinism fix itself. If the mock ever goes
    // back to advancing on its own, every assertion in this file silently
    // becomes a race again - and it would only show up on a slow machine.
    const api = await mockApi(page, { progressMode: 'gated', gateGenerate: true })
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill(PROMPT)
    await page.getByRole('button', { name: 'Generate decal' }).click()

    api.showProgress(2) // denoising, step 14 of 30
    const panel = page.getByRole('status')
    await expect(panel.getByText('Diffusion step 14 of 30 — 47%')).toBeVisible()

    // Let several more polls happen. The state must not move.
    const before = api.progressPolls()
    await expect.poll(() => api.progressPolls(), { timeout: 20_000 }).toBeGreaterThan(before + 2)

    expect(api.progressIndex()).toBe(2)
    await expect(panel.getByText('Diffusion step 14 of 30 — 47%')).toBeVisible()

    // ...and it moves only when told to.
    api.advanceProgress()
    expect(api.progressIndex()).toBe(3)
    await expect(panel.getByText('Diffusion step 27 of 30 — 90%')).toBeVisible()

    api.completeGeneration()
  })

  test('renders real denoising step counts from telemetry', async ({ page }) => {
    const api = await mockApi(page, { progressMode: 'gated', gateGenerate: true })
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill(PROMPT)
    await page.getByRole('button', { name: 'Generate decal' }).click()

    api.showProgress(2) // denoising, step 14 of 30, estimate 7 s

    const panel = page.getByRole('status')
    // The exact numbers the fixture publishes - not a percentage the UI invented.
    await expect(panel.getByText('Diffusion step 14 of 30 — 47%')).toBeVisible()
    await expect(panel.getByText('Screen-print pass 14 / 30')).toBeVisible()
    await expect(panel.getByText('Printing the decal…')).toBeVisible()

    const bar = page.getByRole('progressbar', { name: 'Diffusion steps' })
    await expect(bar).toHaveAttribute('aria-valuenow', '47')

    api.completeGeneration()
  })

  test('publishes an estimate only once steps have been timed', async ({ page }) => {
    const api = await mockApi(page, { progressMode: 'gated', gateGenerate: true })
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill(PROMPT)
    await page.getByRole('button', { name: 'Generate decal' }).click()

    // Early denoising: steps are running but none have been timed yet, so the
    // fixture publishes a null estimate and the interface must say what it is
    // doing rather than guess a number.
    api.showProgress(1)
    const panel = page.getByRole('status')
    await expect(panel.getByText('Measuring generation speed…')).toBeVisible()

    // Later denoising carries a real estimate, hedged rather than promised.
    api.showProgress(2)
    await expect(panel.getByText(/About \d+ seconds? remaining/)).toBeVisible()

    api.completeGeneration()
  })

  test('a stage with no denominator shows a stage name and NO percentage', async ({ page }) => {
    // The rule that DR-013 exists for. Model loading exposes no progress signal,
    // so the interface must refuse to imply one.
    const api = await mockApi(page, {
      progressMode: 'gated',
      gateGenerate: true,
      progress: PROGRESS_COLD_LOAD,
    })
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill(PROMPT)
    await page.getByRole('button', { name: 'Generate decal' }).click()

    api.showProgress(0)

    const panel = page.getByRole('status')
    await expect(panel.getByText('Loading the local generation model…').first()).toBeVisible()
    await expect(panel.getByText('No step percentage at this stage')).toBeVisible()
    await expect(panel.getByText(/Diffusion step/)).toHaveCount(0)
    await expect(panel.getByText(/%/)).toHaveCount(0)

    const bar = page.getByRole('progressbar', { name: 'Diffusion steps' })
    await expect(bar).not.toHaveAttribute('aria-valuenow', /.+/)

    api.completeGeneration()
  })

  test('reaches the finalising stage and only then reports completion', async ({ page }) => {
    const api = await mockApi(page, { progressMode: 'gated', gateGenerate: true })
    await page.goto('/')
    await page.getByLabel('Describe the artwork').fill(PROMPT)
    await page.getByRole('button', { name: 'Generate decal' }).click()

    api.showProgress(3) // last denoising step
    await expect(page.locator('.progress-stage')).toHaveText('Printing the decal…')

    // Denoising is done; the VAE decode has no denominator, so the stage becomes
    // "Finalising" and the percentage readout disappears. Held here rather than
    // caught in flight - this is the state that used to vanish before it painted.
    api.showProgress(4) // decoding
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
    api.completeGeneration()
    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible({
      timeout: RESULT_TIMEOUT,
    })
    await expect(page.getByRole('status')).toHaveCount(0)
  })

  test('losing telemetry degrades the display without failing the generation', async ({
    page,
  }) => {
    const api = await mockApi(page, { progressMode: 'gated', gateGenerate: true })
    // Telemetry is supplemental: killing it must not turn a working generation
    // into a reported failure.
    await page.route('**/api/generation-progress', (route) => route.abort())
    await page.goto('/')

    await page.getByLabel('Describe the artwork').fill(PROMPT)
    await page.getByRole('button', { name: 'Generate decal' }).click()

    const panel = page.getByRole('status')
    await expect(panel.getByText('Generating locally…')).toBeVisible()
    await expect(panel.getByText(/Elapsed: \d+ seconds?/)).toBeVisible()

    // And it still completes.
    api.completeGeneration()
    await expect(page.getByRole('region', { name: 'Generation result' })).toBeVisible({
      timeout: RESULT_TIMEOUT,
    })
  })
})
