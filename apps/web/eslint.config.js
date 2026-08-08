import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist', 'playwright-report', 'test-results'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
    },
  },
  {
    // The E2E suite and the Playwright config run in Node, not in the browser:
    // they use Buffer, setTimeout from the Node timers, and import from
    // 'node:path'. Without this they would be linted against browser globals
    // only, and the honest fix is to tell ESLint where the code runs rather
    // than to sprinkle eslint-disable comments through the tests.
    files: ['e2e/**/*.ts', 'playwright.config.ts'],
    languageOptions: {
      globals: { ...globals.node, ...globals.browser },
    },
  },
)
