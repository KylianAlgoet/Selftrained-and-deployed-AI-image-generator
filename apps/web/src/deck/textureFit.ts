import { DECK_LENGTH, DECK_WIDTH } from './deckGeometry'

/**
 * Fitting a 1:3 decal onto a 1:3.902 deck.
 *
 * The generated decal is 512×1536 — exactly 1:3, the deck format DR-007 selected
 * for generation. The deck's decal face maps its UV domain over the full
 * length and width of the board, and those are not in the same ratio:
 *
 *   DECK_LENGTH / DECK_WIDTH = 3.2 / 0.82 = 3.9024…
 *
 * There is no fit that is simply correct. Filling the surface stretches the
 * artwork lengthwise by ~1.30×; preserving the artwork leaves ~23 % of the deck
 * length uncovered. Both are implemented and both are measured here rather than
 * described.
 *
 * A caveat that belongs to neither mode: the Prototype-0 UV convention already
 * compresses the texture horizontally toward the tapered nose and tail, because
 * `u` is normalised across the *profiled* half-width. That is a pre-existing
 * property of the deck geometry and it applies to both modes equally.
 */

export type TextureFitMode = 'full-surface' | 'fit-without-stretch'

export const TEXTURE_FIT_MODES: readonly TextureFitMode[] = [
  'full-surface',
  'fit-without-stretch',
] as const

/**
 * The production default, selected by Kylian at the M7 review gate on
 * 2026-08-07 from the two screenshots in
 * `docs/evidence/prototype-5/screenshots/`. Recorded in DR-012.
 *
 * This is a chosen trade-off, not a correct fit: it accepts a 1.3008×
 * lengthwise stretch in exchange for a fully covered deck. The other mode
 * remains selectable, and `fitDisclosure` states the cost of whichever is
 * active — the stretch is disclosed to the user, never hidden.
 */
export const DEFAULT_TEXTURE_FIT_MODE: TextureFitMode = 'full-surface'

export const TEXTURE_FIT_LABELS: Record<TextureFitMode, string> = {
  'full-surface': 'Full surface (stretched)',
  'fit-without-stretch': 'Fit without stretching',
}

/** 3.9024…, derived from the geometry constants rather than hard-coded. */
export const DECK_UV_ASPECT = DECK_LENGTH / DECK_WIDTH

/**
 * Colour of the uncovered ends in `fit-without-stretch`. Matches material-1
 * (the deck's top and rim), so an uncovered end reads as bare deck rather than
 * as a rendering fault.
 */
export const UNCOVERED_BAND_COLOR = '#242424'

export interface FitDescription {
  mode: TextureFitMode
  /** height ÷ width of the source image; 3 for a 512×1536 decal. */
  imageAspect: number
  deckAspect: number
  /** Lengthwise scale applied to the artwork. 1 means none. */
  stretchFactor: number
  /** Fraction of the deck length showing artwork. */
  coveredFraction: number
  /** Fraction of the deck length left bare. */
  uncoveredFraction: number
  /** Canvas the texture is composed onto. */
  canvasWidth: number
  canvasHeight: number
  /** Bare band at each end, in canvas pixels. 0 for full-surface. */
  bandPx: number
  /** Where the artwork starts vertically on the canvas. */
  offsetY: number
}

export function describeFit(
  mode: TextureFitMode,
  imageWidth: number,
  imageHeight: number,
): FitDescription {
  if (imageWidth <= 0 || imageHeight <= 0) {
    throw new Error('image dimensions must be positive')
  }

  const imageAspect = imageHeight / imageWidth

  if (mode === 'full-surface') {
    // The artwork covers the whole UV domain, so the UV mapping does the
    // stretching. Nothing is cropped and nothing is rotated — the image is
    // scaled along its length only.
    return {
      mode,
      imageAspect,
      deckAspect: DECK_UV_ASPECT,
      stretchFactor: DECK_UV_ASPECT / imageAspect,
      coveredFraction: 1,
      uncoveredFraction: 0,
      canvasWidth: imageWidth,
      canvasHeight: imageHeight,
      bandPx: 0,
      offsetY: 0,
    }
  }

  // Preserve the artwork's own aspect by composing it, centred, onto a canvas
  // that already has the deck's aspect. Compositing rather than a UV offset is
  // deliberate: offsetting the UVs would sample outside the image and smear its
  // edge pixels down the deck.
  const canvasHeight = Math.round(imageWidth * DECK_UV_ASPECT)
  const spare = canvasHeight - imageHeight
  const bandPx = Math.round(spare / 2)

  return {
    mode,
    imageAspect,
    deckAspect: DECK_UV_ASPECT,
    stretchFactor: 1,
    coveredFraction: imageHeight / canvasHeight,
    uncoveredFraction: spare / canvasHeight,
    canvasWidth: imageWidth,
    canvasHeight,
    bandPx,
    offsetY: bandPx,
  }
}

/** Human-readable disclosure of what the selected mode does to the artwork. */
export function fitDisclosure(fit: FitDescription): string {
  if (fit.mode === 'full-surface') {
    return `Stretched ${fit.stretchFactor.toFixed(3)}× along the deck to cover the whole surface.`
  }
  return `Aspect preserved; ${(fit.uncoveredFraction * 100).toFixed(2)}% of the deck length is left bare (${(fit.uncoveredFraction * 50).toFixed(2)}% at each end).`
}

export interface CanvasLike {
  width: number
  height: number
  getContext(contextId: '2d'): CanvasRenderingContext2D | null
}

export type ImageSource = CanvasImageSource & { width: number; height: number }

/**
 * Compose the decal onto a canvas for the given mode.
 *
 * Always draws the image once, upright and unmirrored, at its natural
 * orientation — the only difference between modes is the canvas it lands on.
 */
export function composeDeckTexture(
  image: ImageSource,
  mode: TextureFitMode,
  createCanvas: () => CanvasLike = () => document.createElement('canvas'),
): { canvas: CanvasLike; fit: FitDescription } {
  const fit = describeFit(mode, image.width, image.height)
  const canvas = createCanvas()
  canvas.width = fit.canvasWidth
  canvas.height = fit.canvasHeight

  const context = canvas.getContext('2d')
  if (!context) throw new Error('could not obtain a 2d canvas context')

  if (fit.bandPx > 0) {
    context.fillStyle = UNCOVERED_BAND_COLOR
    context.fillRect(0, 0, fit.canvasWidth, fit.canvasHeight)
  }

  // Positive width and height, no transform: the image cannot be mirrored or
  // flipped by this call.
  context.drawImage(image, 0, fit.offsetY, fit.canvasWidth, image.height)

  return { canvas, fit }
}
