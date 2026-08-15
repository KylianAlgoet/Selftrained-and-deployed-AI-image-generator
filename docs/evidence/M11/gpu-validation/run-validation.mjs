/**
 * M11 final GPU validation - drives ONE real generation through the whole chain.
 *
 *   browser -> frontend -> FastAPI -> SD 1.5 + production LoRA -> RTX 4060 -> PNG
 *           -> frontend -> 3D skateboard deck
 *
 * NOTHING is mocked. This is not part of the Playwright suite: the suite answers
 * every /api/** call from frozen fixtures, which is the opposite of what this
 * run is for.
 *
 * ONE GENERATION. `Generate decal` is clicked exactly once, the POST count is
 * asserted, and there is no retry machinery anywhere in this file. If it fails,
 * it fails - a mismatch is an audit finding, not a reason to run again.
 *
 * Run (with `scripts/start-demo.ps1` already running):
 *   node docs/evidence/M11/gpu-validation/run-validation.mjs
 */
import { createHash } from 'node:crypto'
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const REPO = resolve(HERE, '../../../..')

// playwright lives in apps/web/node_modules; ESM will not find it from here, so
// resolve it from the frontend package rather than copying a dependency around.
const require = createRequire(resolve(REPO, 'apps/web/package.json'))
const { chromium } = require('playwright')

const APP = 'http://localhost:5173'
const PROMPT = 'a mountain and a rising sun'
const STYLE = 'minimal-geometric'
const SEED = '42'

const EXPECTED_SHA = '46bbf160e4270429e6692467dc6c59577e99bf3178dedd8d38193d0335fb6d7f'
const EXPECTED_BYTES = 1089939

const SHOTS = resolve(HERE, 'screenshots')
const PNG_DIR = resolve(REPO, 'outputs/m11-gpu-validation')
mkdirSync(SHOTS, { recursive: true })
mkdirSync(PNG_DIR, { recursive: true })

const record = {
  milestone: 'M11',
  purpose: 'final submission audit - deployment/reproducibility validation',
  classification: 'NOT a research experiment; no EXP-### id; not in experiments/registry.csv',
  started_utc: new Date().toISOString(),
  started_local: new Date().toString(),
  driver: 'playwright chromium (headed), no API mocking',
  config: { prompt: PROMPT, style: STYLE, seed: SEED, reference_image: 'none' },
  expected: { sha256: EXPECTED_SHA, bytes: EXPECTED_BYTES },
}

const browser = await chromium.launch({ headless: false })
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const page = await context.newPage()

let generatePosts = 0
const consoleErrors = []
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()) })
page.on('request', (r) => {
  if (r.method() === 'POST' && r.url().includes('/api/generate')) generatePosts += 1
})

let apiResponse = null
page.on('response', async (r) => {
  if (r.url().includes('/api/generate') && r.request().method() === 'POST') {
    record.api_status = r.status()
    try { apiResponse = await r.json() } catch { /* body read after nav */ }
  }
})

console.log('1. loading the app ...')
await page.goto(APP, { waitUntil: 'domcontentloaded' })
await page.getByRole('region', { name: 'Deck preview' }).waitFor({ state: 'visible', timeout: 60000 })

// The deck must already be rendering BEFORE any generation - proves the viewer
// is live rather than something the result panel conjures into existence.
const canvas = page.locator('.viewer-wrapper canvas')
await canvas.waitFor({ state: 'visible', timeout: 60000 })
record.webgl_context_before = await canvas.evaluate((n) =>
  Boolean(n.getContext('webgl2') ?? n.getContext('webgl')))
await page.screenshot({ path: resolve(SHOTS, '00-app-loaded.png') })

console.log('2. entering the configuration ...')
await page.getByLabel('Describe the artwork').fill(PROMPT)
await page.getByLabel('Style', { exact: true }).selectOption(STYLE)

// Seed and style strength live behind the `Advanced settings` disclosure. It is
// expanded rather than bypassed so the recorded values are the ones a human
// would actually see on screen before pressing Generate.
await page.getByText('Advanced settings').click()
await page.getByLabel('Seed').waitFor({ state: 'visible', timeout: 15000 })
await page.getByLabel('Seed').fill(SEED)

record.form_readback = {
  prompt: await page.getByLabel('Describe the artwork').inputValue(),
  style: await page.getByLabel('Style', { exact: true }).inputValue(),
  seed: await page.getByLabel('Seed').inputValue(),
  style_strength: await page.getByLabel(/Style strength/).inputValue(),
}
await page.screenshot({ path: resolve(SHOTS, '01-configured.png') })

console.log('3. clicking Generate decal - ONCE ...')
const t0 = Date.now()
await page.getByRole('button', { name: 'Generate decal' }).click()

// Catch the honest cold-load state: a stage name and NO percentage (DR-013).
await page.waitForTimeout(6000)
try {
  record.progress_text_at_6s = await page
    .getByRole('region', { name: 'Generation result' })
    .innerText({ timeout: 3000 })
} catch {
  record.progress_text_at_6s = await page.locator('body').innerText()
}
await page.screenshot({ path: resolve(SHOTS, '02-generating.png') })

console.log('4. waiting for the result (cold load, allow 5 min) ...')
const result = page.getByRole('region', { name: 'Generation result' })
await result.getByRole('heading', { name: 'Generated decal' })
  .waitFor({ state: 'visible', timeout: 300000 })
record.browser_wall_clock_seconds = Number(((Date.now() - t0) / 1000).toFixed(2))

record.result_panel_text = await result.innerText()
await page.screenshot({ path: resolve(SHOTS, '03-result-and-deck.png') })

// The decal must be on the deck, not merely in the result panel.
record.applied_to_deck = await page
  .getByText('Applied to the deck preview →').isVisible().catch(() => false)
record.webgl_context_after = await canvas.evaluate((n) =>
  Boolean(n.getContext('webgl2') ?? n.getContext('webgl')))

console.log('5. downloading PNG and metadata through the app buttons ...')
const pngWait = page.waitForEvent('download', { timeout: 60000 })
await page.getByRole('button', { name: 'Download PNG' }).click()
const png = await pngWait
const pngPath = resolve(PNG_DIR, 'm11-gpu-validation.png')
await png.saveAs(pngPath)

const metaWait = page.waitForEvent('download', { timeout: 60000 })
await page.getByRole('button', { name: 'Download metadata' }).click()
const meta = await metaWait
const metaPath = resolve(HERE, 'metadata.json')
await meta.saveAs(metaPath)

console.log('6. orbiting the deck ...')
const box = await canvas.boundingBox()
await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
await page.mouse.down()
await page.mouse.move(box.x + box.width / 2 + 140, box.y + box.height / 2 + 60, { steps: 24 })
await page.mouse.up()
await page.waitForTimeout(1500)
await page.screenshot({ path: resolve(SHOTS, '04-deck-orbited.png') })

// ---- the pre-declared comparison -------------------------------------------
const bytes = readFileSync(pngPath)
const actualSha = createHash('sha256').update(bytes).digest('hex')

record.generate_post_count = generatePosts
record.console_errors = consoleErrors
record.actual = { sha256: actualSha, bytes: bytes.length }
record.byte_identical = actualSha === EXPECTED_SHA && bytes.length === EXPECTED_BYTES
record.verdict = record.byte_identical ? 'MATCH' : 'MISMATCH'
record.api_response = apiResponse
record.png_path = 'outputs/m11-gpu-validation/m11-gpu-validation.png (git-ignored)'
record.finished_utc = new Date().toISOString()

writeFileSync(resolve(HERE, 'generation-record.json'), JSON.stringify(record, null, 2))

await browser.close()

console.log('\n================ M11 GPU VALIDATION ================')
console.log('POST /api/generate calls :', generatePosts, generatePosts === 1 ? '(exactly one)' : '(!!)')
console.log('browser wall clock       :', record.browser_wall_clock_seconds, 's')
console.log('applied to deck          :', record.applied_to_deck)
console.log('expected sha256          :', EXPECTED_SHA)
console.log('actual   sha256          :', actualSha)
console.log('expected bytes           :', EXPECTED_BYTES)
console.log('actual   bytes           :', bytes.length)
console.log('VERDICT                  :', record.verdict)
console.log('====================================================')
