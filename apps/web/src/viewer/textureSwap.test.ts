import { describe, expect, it, vi } from 'vitest'
import {
  emptySlot,
  releaseSlot,
  swapTexture,
  type DisposableTexture,
  type TextureSlot,
} from './textureSwap'

function texture(name: string) {
  return { name, dispose: vi.fn() } as DisposableTexture & { name: string }
}

describe('swapTexture', () => {
  it('installs the new texture on success', async () => {
    const next = texture('next')
    const result = await swapTexture(emptySlot(), { source: 'a' }, { load: async () => next })
    expect(result.ok).toBe(true)
    expect(result.slot.texture).toBe(next)
  })

  it('disposes the replaced texture', async () => {
    const old = texture('old')
    const next = texture('next')
    const slot: TextureSlot<DisposableTexture> = { texture: old, objectUrl: null }

    await swapTexture(slot, { source: 'b' }, { load: async () => next })

    expect(old.dispose).toHaveBeenCalledTimes(1)
    expect(next.dispose).not.toHaveBeenCalled()
  })

  it('revokes the previous object URL only after the new texture has loaded', async () => {
    const revoked: string[] = []
    const order: string[] = []
    const old = texture('old')

    await swapTexture(
      { texture: old, objectUrl: 'blob:old' },
      { source: 'c', objectUrl: 'blob:new' },
      {
        load: async () => {
          order.push('load-start')
          // Nothing may be revoked while the load is still in flight.
          expect(revoked).toEqual([])
          await Promise.resolve()
          order.push('load-end')
          return texture('next')
        },
        revokeObjectUrl: (url) => {
          order.push(`revoke:${url}`)
          revoked.push(url)
        },
      },
    )

    expect(order).toEqual(['load-start', 'load-end', 'revoke:blob:old'])
    expect(revoked).toEqual(['blob:old'])
  })

  it('keeps the previous texture visible when the load fails', async () => {
    const old = texture('old')
    const slot: TextureSlot<DisposableTexture> = { texture: old, objectUrl: 'blob:old' }

    const result = await swapTexture(
      slot,
      { source: 'broken', objectUrl: 'blob:new' },
      {
        load: async () => {
          throw new Error('404 while loading the decal')
        },
        revokeObjectUrl: vi.fn(),
      },
    )

    expect(result.ok).toBe(false)
    expect(result.slot.texture).toBe(old)
    expect(old.dispose).not.toHaveBeenCalled()
    expect(result.slot.objectUrl).toBe('blob:old')
  })

  it('reports an actionable error on failure', async () => {
    const result = await swapTexture(
      emptySlot(),
      { source: 'broken' },
      {
        load: async () => {
          throw new Error('404 while loading the decal')
        },
      },
    )
    expect(result.error?.message).toContain('404')
  })

  it('revokes only the failed URL, never the one still on screen', async () => {
    const revoke = vi.fn()
    await swapTexture(
      { texture: texture('old'), objectUrl: 'blob:old' },
      { source: 'broken', objectUrl: 'blob:new' },
      {
        load: async () => {
          throw new Error('decode failed')
        },
        revokeObjectUrl: revoke,
      },
    )
    expect(revoke).toHaveBeenCalledWith('blob:new')
    expect(revoke).not.toHaveBeenCalledWith('blob:old')
  })

  it('normalises a non-Error rejection', async () => {
    const result = await swapTexture(
      emptySlot(),
      { source: 'x' },
      {
        load: async () => {
          throw 'plain string'
        },
      },
    )
    expect(result.error).toBeInstanceOf(Error)
    expect(result.error?.message).toBe('plain string')
  })

  it('survives repeated swaps without leaking a texture', async () => {
    let slot: TextureSlot<DisposableTexture> = emptySlot()
    const made: Array<DisposableTexture & { name: string }> = []

    for (let index = 0; index < 5; index += 1) {
      const next = texture(`t${index}`)
      made.push(next)
      const result = await swapTexture(
        slot,
        { source: index, objectUrl: `blob:${index}` },
        { load: async () => next, revokeObjectUrl: vi.fn() },
      )
      slot = result.slot
    }

    // Every texture except the one still displayed has been disposed exactly once.
    const current = made[made.length - 1]
    for (const item of made.slice(0, -1)) {
      expect(item.dispose).toHaveBeenCalledTimes(1)
    }
    expect(current.dispose).not.toHaveBeenCalled()
    expect(slot.texture).toBe(current)
  })
})

describe('releaseSlot', () => {
  it('disposes the texture and revokes its URL', () => {
    const revoke = vi.fn()
    const current = texture('current')
    const result = releaseSlot({ texture: current, objectUrl: 'blob:current' }, revoke)

    expect(current.dispose).toHaveBeenCalledTimes(1)
    expect(revoke).toHaveBeenCalledWith('blob:current')
    expect(result.texture).toBeNull()
    expect(result.objectUrl).toBeNull()
  })

  it('is safe on an empty slot', () => {
    const revoke = vi.fn()
    expect(() => releaseSlot(emptySlot(), revoke)).not.toThrow()
    expect(revoke).not.toHaveBeenCalled()
  })
})
