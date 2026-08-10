/**
 * Prove that an ordinary build ships no test instrumentation.
 *
 * The E2E camera read-out (src/viewer/e2eCameraState.ts) is gated on the
 * build-time constant `__DECKFORGE_E2E__`, which Vite replaces with a literal
 * `false` unless VITE_E2E=1 is set. A literal false makes the probe unreachable,
 * and the bundler then drops it along with the handle name.
 *
 * "Should be dropped" is a claim about a minifier, so it is checked rather than
 * trusted: this asserts the built assets do not contain the handle name
 * anywhere. If tree-shaking ever stops removing the probe, this fails at build
 * time instead of quietly shipping a window hook to users.
 *
 * The handle name is READ FROM THE SOURCE rather than duplicated here, so
 * renaming the constant cannot leave this guard silently checking a string that
 * no longer exists.
 *
 * Run after `npm run build`. It will correctly FAIL after a Playwright run,
 * because the suite's webServer rebuilds dist/ with VITE_E2E=1 - that build is
 * supposed to contain the handle. Rebuild without the flag before running it.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const WEB_ROOT = dirname(dirname(fileURLToPath(import.meta.url)))
const DIST = join(WEB_ROOT, 'dist')
const SOURCE = join(WEB_ROOT, 'src', 'viewer', 'e2eCameraState.ts')

function fail(message) {
  console.error(`FAIL: ${message}`)
  process.exit(1)
}

function handleName() {
  const source = readFileSync(SOURCE, 'utf8')
  const match = source.match(/export const E2E_CAMERA_HANDLE = '([^']+)'/)
  if (!match) {
    fail(
      `could not find E2E_CAMERA_HANDLE in ${relative(WEB_ROOT, SOURCE)}. ` +
        'If it was renamed or moved, update this guard - do not delete it.',
    )
  }
  return match[1]
}

function filesUnder(directory) {
  const found = []
  for (const entry of readdirSync(directory)) {
    const path = join(directory, entry)
    if (statSync(path).isDirectory()) found.push(...filesUnder(path))
    else found.push(path)
  }
  return found
}

const handle = handleName()

let assets
try {
  assets = filesUnder(DIST)
} catch {
  fail(`no dist/ directory at ${DIST}. Run "npm run build" first.`)
}

if (assets.length === 0) fail('dist/ is empty; the build produced nothing to check.')

const leaking = assets.filter((path) => readFileSync(path, 'utf8').includes(handle))

if (leaking.length > 0) {
  fail(
    `the production bundle contains the E2E handle "${handle}":\n` +
      leaking.map((path) => `  - ${relative(WEB_ROOT, path)}`).join('\n') +
      '\n\nEither this build set VITE_E2E=1 (a Playwright run does; rebuild ' +
      'without it), or the probe is no longer being tree-shaken and the gate ' +
      'needs fixing before release.',
  )
}

console.log(
  `ok: none of the ${assets.length} built assets contain "${handle}" - ` +
    'the production bundle exposes no E2E handle',
)
