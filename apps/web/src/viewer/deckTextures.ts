import { CanvasTexture, SRGBColorSpace, Texture, TextureLoader } from 'three'

/**
 * Building deck textures.
 *
 * Every texture that reaches the deck goes through `configureTexture`, so the
 * colour space and filtering are set in exactly one place. Getting the colour
 * space wrong is the kind of defect that looks like "the model produced washed
 * out colours" rather than like a bug, so it is set explicitly and asserted in
 * a test rather than left to a default.
 *
 * `flipY` is deliberately left at three.js' default of `true`. The deck's UV
 * convention depends on it: v = 0 at the tail and v = 1 at the nose, so with
 * flipY the TOP row of the decal image lands at the NOSE
 * (see `deckGeometry.ts:9-13`). Changing it here would silently invert every
 * decal top-to-bottom.
 */

export const DECK_TEXTURE_ANISOTROPY = 8

export function configureTexture<T extends Texture>(texture: T): T {
  texture.colorSpace = SRGBColorSpace
  texture.anisotropy = DECK_TEXTURE_ANISOTROPY
  texture.needsUpdate = true
  return texture
}

export function textureFromCanvas(canvas: HTMLCanvasElement): CanvasTexture {
  return configureTexture(new CanvasTexture(canvas))
}

export async function textureFromUrl(
  url: string,
  loader: { loadAsync: (u: string) => Promise<Texture> } = new TextureLoader(),
): Promise<Texture> {
  return configureTexture(await loader.loadAsync(url))
}

/** Decode a blob into an image element the canvas compositor can draw. */
export function imageFromBlob(blob: Blob): Promise<HTMLImageElement> {
  const objectUrl = URL.createObjectURL(blob)
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => {
      URL.revokeObjectURL(objectUrl)
      resolve(image)
    }
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl)
      reject(new Error('the generated image could not be decoded'))
    }
    image.src = objectUrl
  })
}
