import { describe, expect, it, vi } from 'vitest'
import { SRGBColorSpace, Texture } from 'three'
import { DECK_TEXTURE_ANISOTROPY, configureTexture, textureFromUrl } from './deckTextures'

describe('configureTexture', () => {
  it('sets the sRGB colour space, so decals are not rendered washed out', () => {
    const texture = configureTexture(new Texture())
    expect(texture.colorSpace).toBe(SRGBColorSpace)
  })

  it('sets anisotropy and marks the texture for upload', () => {
    const texture = new Texture()
    const versionBefore = texture.version
    configureTexture(texture)

    expect(texture.anisotropy).toBe(DECK_TEXTURE_ANISOTROPY)
    // `needsUpdate` is a write-only accessor in three.js - it bumps `version`,
    // and reading it back gives undefined. `version` is the observable effect.
    expect(texture.version).toBeGreaterThan(versionBefore)
  })

  it('leaves flipY at the default the deck UV convention depends on', () => {
    // v = 0 at the tail, v = 1 at the nose: with flipY true the top row of the
    // image lands at the nose. Flipping this silently inverts every decal.
    const texture = configureTexture(new Texture())
    expect(texture.flipY).toBe(true)
  })

  it('does not mirror or rotate the texture', () => {
    const texture = configureTexture(new Texture())
    expect(texture.repeat.x).toBe(1)
    expect(texture.repeat.y).toBe(1)
    expect(texture.offset.x).toBe(0)
    expect(texture.offset.y).toBe(0)
    expect(texture.rotation).toBe(0)
  })
})

describe('textureFromUrl', () => {
  it('configures whatever the loader returns', async () => {
    const loaded = new Texture()
    const loader = { loadAsync: vi.fn(async () => loaded) }
    const texture = await textureFromUrl('/decals/geometric.svg', loader)

    expect(loader.loadAsync).toHaveBeenCalledWith('/decals/geometric.svg')
    expect(texture).toBe(loaded)
    expect(texture.colorSpace).toBe(SRGBColorSpace)
  })

  it('propagates a load failure so the caller can keep the previous decal', async () => {
    const loader = {
      loadAsync: vi.fn(async () => {
        throw new Error('404')
      }),
    }
    await expect(textureFromUrl('/missing.png', loader)).rejects.toThrow('404')
  })
})
