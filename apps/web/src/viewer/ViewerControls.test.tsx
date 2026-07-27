// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach } from 'vitest'
import { ViewerControls } from './ViewerControls'
import { DECALS } from '../decals'

afterEach(cleanup)

function renderControls(overrides: Partial<Parameters<typeof ViewerControls>[0]> = {}) {
  const props = {
    decals: DECALS,
    activeDecalId: DECALS[0].id,
    onSelectDecal: vi.fn(),
    onResetView: vi.fn(),
    invertDemo: false,
    onToggleInvertDemo: vi.fn(),
    ...overrides,
  }
  render(<ViewerControls {...props} />)
  return props
}

describe('ViewerControls', () => {
  it('renders a button per decal and marks the active one', () => {
    renderControls()
    const active = screen.getByRole('button', { name: DECALS[0].label })
    const inactive = screen.getByRole('button', { name: DECALS[1].label })
    expect(active.getAttribute('aria-pressed')).toBe('true')
    expect(inactive.getAttribute('aria-pressed')).toBe('false')
  })

  it('reports decal selection', () => {
    const props = renderControls()
    fireEvent.click(screen.getByRole('button', { name: DECALS[1].label }))
    expect(props.onSelectDecal).toHaveBeenCalledWith(DECALS[1].id)
  })

  it('reports reset view clicks', () => {
    const props = renderControls()
    fireEvent.click(screen.getByRole('button', { name: 'Reset view' }))
    expect(props.onResetView).toHaveBeenCalledTimes(1)
  })

  it('toggles the labelled inverted-UV demonstration', () => {
    const props = renderControls()
    fireEvent.click(screen.getByRole('checkbox'))
    expect(props.onToggleInvertDemo).toHaveBeenCalledWith(true)
  })

  it('exposes two distinct self-created decals', () => {
    expect(DECALS).toHaveLength(2)
    expect(new Set(DECALS.map((d) => d.url)).size).toBe(2)
    for (const decal of DECALS) expect(decal.url).toMatch(/^\/decals\/.+\.svg$/)
  })
})
