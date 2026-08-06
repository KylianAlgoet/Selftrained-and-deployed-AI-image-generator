/**
 * Swapping the deck texture safely.
 *
 * Three rules, each of which exists because breaking it is silently wrong
 * rather than loudly broken:
 *
 * 1. **Dispose the old GPU texture.** Three.js textures hold a GPU allocation
 *    that garbage collection does not release. Swapping decals repeatedly
 *    without disposing leaks until the context is lost.
 * 2. **Revoke an object URL only AFTER the replacement has resolved.** Revoking
 *    on swap-start races the loader: if the new image fails, the old URL is
 *    already dead and there is nothing to fall back to.
 * 3. **A failed load must keep the previous texture visible.** Blanking the deck
 *    on failure loses the user's last good result and looks like a crash.
 *
 * The logic lives here, free of React and WebGL, so all three are testable.
 */

export interface DisposableTexture {
  dispose(): void
}

export interface TextureSlot<T extends DisposableTexture> {
  texture: T | null
  /** Object URL backing `texture`, if it came from a blob. */
  objectUrl: string | null
}

export interface SwapDeps<T extends DisposableTexture> {
  load: (source: unknown) => Promise<T>
  revokeObjectUrl?: (url: string) => void
}

export interface SwapRequest {
  source: unknown
  /** Object URL to revoke once the swap has settled, either way. */
  objectUrl?: string | null
}

export interface SwapResult<T extends DisposableTexture> {
  slot: TextureSlot<T>
  ok: boolean
  error?: Error
}

export function emptySlot<T extends DisposableTexture>(): TextureSlot<T> {
  return { texture: null, objectUrl: null }
}

/**
 * Load `request.source` and, only on success, replace the slot's texture.
 *
 * On failure the slot is returned unchanged - same texture, same URL - so the
 * caller keeps rendering the last good decal while it shows the error.
 */
export async function swapTexture<T extends DisposableTexture>(
  slot: TextureSlot<T>,
  request: SwapRequest,
  deps: SwapDeps<T>,
): Promise<SwapResult<T>> {
  const revoke = deps.revokeObjectUrl ?? ((url: string) => URL.revokeObjectURL(url))

  let loaded: T
  try {
    loaded = await deps.load(request.source)
  } catch (cause) {
    // The new URL is now known to be useless, so it may go; the previous one
    // must NOT, because it is still on screen.
    if (request.objectUrl) revoke(request.objectUrl)
    return {
      slot,
      ok: false,
      error: cause instanceof Error ? cause : new Error(String(cause)),
    }
  }

  // Only now is the replacement real: release the old texture and its URL.
  if (slot.texture) slot.texture.dispose()
  if (slot.objectUrl) revoke(slot.objectUrl)

  return {
    slot: { texture: loaded, objectUrl: request.objectUrl ?? null },
    ok: true,
  }
}

/** Release everything a slot holds. For unmount. */
export function releaseSlot<T extends DisposableTexture>(
  slot: TextureSlot<T>,
  revokeObjectUrl: (url: string) => void = (url) => URL.revokeObjectURL(url),
): TextureSlot<T> {
  if (slot.texture) slot.texture.dispose()
  if (slot.objectUrl) revokeObjectUrl(slot.objectUrl)
  return emptySlot<T>()
}
