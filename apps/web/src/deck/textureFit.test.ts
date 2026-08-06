import { describe, expect, it, vi } from 'vitest'
import { DECK_LENGTH, DECK_WIDTH } from './deckGeometry'
import {
  DECK_UV_ASPECT,
  TEXTURE_FIT_MODES,
  UNCOVERED_BAND_COLOR,
  composeDeckTexture,
  describeFit,
  fitDisclosure,
  type CanvasLike,
} from './textureFit'

const DECAL_WIDTH = 512
const DECAL_HEIGHT = 1536

function fakeCanvas() {
  const calls: Array<{ op: string; args: unknown[] }> = []
  const context = {
    fillStyle: '',
    fillRect: (...args: unknown[]) => calls.push({ op: 'fillRect', args }),
    drawImage: (...args: unknown[]) => calls.push({ op: 'drawImage', args }),
  }
  const canvas: CanvasLike = {
    width: 0,
    height: 0,
    getContext: () => context as unknown as CanvasRenderingContext2D,
  }
  return { canvas, context, calls }
}

const image = { width: DECAL_WIDTH, height: DECAL_HEIGHT } as never

describe('deck aspect', () => {
  it('is derived from the geometry constants, not hard-coded', () => {
    expect(DECK_UV_ASPECT).toBe(DECK_LENGTH / DECK_WIDTH)
    expect(DECK_UV_ASPECT).toBeCloseTo(3.9024, 4)
  })

  it('does not match the 1:3 decal, which is why two modes exist', () => {
    expect(DECAL_HEIGHT / DECAL_WIDTH).toBe(3)
    expect(DECK_UV_ASPECT).not.toBeCloseTo(3, 2)
  })

  it('offers exactly the two modes, with neither marked as the default', () => {
    expect([...TEXTURE_FIT_MODES]).toEqual(['full-surface', 'fit-without-stretch'])
  })
})

describe('full-surface', () => {
  const fit = describeFit('full-surface', DECAL_WIDTH, DECAL_HEIGHT)

  it('covers the whole deck', () => {
    expect(fit.coveredFraction).toBe(1)
    expect(fit.uncoveredFraction).toBe(0)
    expect(fit.bandPx).toBe(0)
  })

  it('stretches lengthwise by 1.3008x, and says so', () => {
    expect(fit.stretchFactor).toBeCloseTo(1.3008, 4)
    expect(fitDisclosure(fit)).toContain('1.301')
    expect(fitDisclosure(fit)).toContain('Stretched')
  })

  it('keeps the source dimensions', () => {
    expect(fit.canvasWidth).toBe(DECAL_WIDTH)
    expect(fit.canvasHeight).toBe(DECAL_HEIGHT)
    expect(fit.offsetY).toBe(0)
  })
})

describe('fit-without-stretch', () => {
  const fit = describeFit('fit-without-stretch', DECAL_WIDTH, DECAL_HEIGHT)

  it('applies no stretch at all', () => {
    expect(fit.stretchFactor).toBe(1)
  })

  it('composes onto a deck-shaped 512x1998 canvas', () => {
    expect(fit.canvasWidth).toBe(512)
    expect(fit.canvasHeight).toBe(1998)
    expect(fit.canvasHeight / fit.canvasWidth).toBeCloseTo(DECK_UV_ASPECT, 3)
  })

  it('leaves 23.12% of the length bare, 11.56% at each end', () => {
    expect(fit.uncoveredFraction * 100).toBeCloseTo(23.12, 2)
    expect(fit.coveredFraction * 100).toBeCloseTo(76.88, 2)
    expect(fit.bandPx).toBe(231)
    expect(fitDisclosure(fit)).toContain('23.12%')
    expect(fitDisclosure(fit)).toContain('11.56%')
  })

  it('centres the artwork, so the bands are equal', () => {
    expect(fit.offsetY).toBe(fit.bandPx)
    expect(fit.canvasHeight - fit.offsetY - DECAL_HEIGHT).toBe(fit.bandPx)
  })
})

describe('composition', () => {
  it('draws the decal once, upright and unmirrored, in both modes', () => {
    for (const mode of TEXTURE_FIT_MODES) {
      const { canvas, calls } = fakeCanvas()
      composeDeckTexture(image, mode, () => canvas)

      const draws = calls.filter((c) => c.op === 'drawImage')
      expect(draws).toHaveLength(1)

      const [, dx, dy, dWidth, dHeight] = draws[0].args as number[]
      // Negative width or height would mirror the image; a swap would rotate it.
      expect(dWidth).toBeGreaterThan(0)
      expect(dHeight).toBeGreaterThan(0)
      expect(dx).toBe(0)
      expect(dy).toBeGreaterThanOrEqual(0)
      expect(dWidth).toBe(DECAL_WIDTH)
      expect(dHeight).toBe(DECAL_HEIGHT)
    }
  })

  it('fills the bare ends only in the no-stretch mode', () => {
    const stretched = fakeCanvas()
    composeDeckTexture(image, 'full-surface', () => stretched.canvas)
    expect(stretched.calls.filter((c) => c.op === 'fillRect')).toHaveLength(0)

    const fitted = fakeCanvas()
    composeDeckTexture(image, 'fit-without-stretch', () => fitted.canvas)
    expect(fitted.calls.filter((c) => c.op === 'fillRect')).toHaveLength(1)
    expect(fitted.context.fillStyle).toBe(UNCOVERED_BAND_COLOR)
  })

  it('sizes the canvas before drawing', () => {
    const { canvas } = fakeCanvas()
    composeDeckTexture(image, 'fit-without-stretch', () => canvas)
    expect(canvas.width).toBe(512)
    expect(canvas.height).toBe(1998)
  })

  it('reports both modes for the same image so they are comparable', () => {
    const stretched = describeFit('full-surface', DECAL_WIDTH, DECAL_HEIGHT)
    const fitted = describeFit('fit-without-stretch', DECAL_WIDTH, DECAL_HEIGHT)
    expect(stretched.imageAspect).toBe(fitted.imageAspect)
    expect(stretched.deckAspect).toBe(fitted.deckAspect)
    // The trade-off, stated numerically: stretch or bare ends, never neither.
    expect(stretched.uncoveredFraction).toBe(0)
    expect(stretched.stretchFactor).toBeGreaterThan(1)
    expect(fitted.stretchFactor).toBe(1)
    expect(fitted.uncoveredFraction).toBeGreaterThan(0)
  })

  it('refuses a degenerate image rather than dividing by zero', () => {
    expect(() => describeFit('full-surface', 0, 100)).toThrow()
    expect(() => describeFit('fit-without-stretch', 100, 0)).toThrow()
  })

  it('raises if no 2d context is available', () => {
    const canvas: CanvasLike = { width: 0, height: 0, getContext: () => null }
    expect(() => composeDeckTexture(image, 'full-surface', () => canvas)).toThrow(
      /2d canvas context/,
    )
  })

  it('handles a square image without cropping it', () => {
    const fit = describeFit('fit-without-stretch', 800, 800)
    expect(fit.stretchFactor).toBe(1)
    expect(fit.canvasHeight).toBe(Math.round(800 * DECK_UV_ASPECT))
    const { calls } = (() => {
      const c = fakeCanvas()
      composeDeckTexture({ width: 800, height: 800 } as never, 'fit-without-stretch', () => c.canvas)
      return c
    })()
    const [, , , dWidth, dHeight] = calls.find((c) => c.op === 'drawImage')!.args as number[]
    expect(dWidth).toBe(800)
    expect(dHeight).toBe(800)
  })
})

describe('the default is not chosen in code', () => {
  it('exposes no exported default mode', async () => {
    const module = await import('./textureFit')
    const exported = Object.keys(module)
    expect(exported).not.toContain('DEFAULT_TEXTURE_FIT_MODE')
    expect(exported).not.toContain('PRODUCTION_TEXTURE_FIT_MODE')
    expect(vi.isMockFunction(module.describeFit)).toBe(false)
  })
})
