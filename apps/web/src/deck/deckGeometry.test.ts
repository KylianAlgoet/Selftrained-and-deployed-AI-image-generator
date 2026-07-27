import { describe, expect, it } from 'vitest'
import { Vector3 } from 'three'
import {
  createDeckGeometry,
  DECK_LENGTH,
  DECK_WIDTH,
  DECK_THICKNESS,
  NOSE_KICK_RISE,
  TAIL_KICK_RISE,
  CONCAVE_DEPTH,
} from './deckGeometry'

const EPS = 1e-5

describe('createDeckGeometry', () => {
  const geometry = createDeckGeometry()
  const pos = geometry.getAttribute('position')
  const uv = geometry.getAttribute('uv')
  const index = geometry.getIndex()!

  it('defines two material groups with the decal face as group 0', () => {
    expect(geometry.groups).toHaveLength(2)
    expect(geometry.groups[0].materialIndex).toBe(0)
    expect(geometry.groups[1].materialIndex).toBe(1)
    expect(geometry.groups[0].start).toBe(0)
    expect(geometry.groups[0].count + geometry.groups[1].count).toBe(index.count)
  })

  it('spans the full [0,1] UV range on the decal face', () => {
    let minU = Infinity, maxU = -Infinity, minV = Infinity, maxV = -Infinity
    for (let k = 0; k < uv.count; k++) {
      minU = Math.min(minU, uv.getX(k))
      maxU = Math.max(maxU, uv.getX(k))
      minV = Math.min(minV, uv.getY(k))
      maxV = Math.max(maxV, uv.getY(k))
    }
    expect(minU).toBeCloseTo(0, 5)
    expect(maxU).toBeCloseTo(1, 5)
    expect(minV).toBeCloseTo(0, 5)
    expect(maxV).toBeCloseTo(1, 5)
  })

  it('maps v=1 to the nose (+Z) and v=0 to the tail (-Z)', () => {
    for (let k = 0; k < uv.count; k++) {
      const v = uv.getY(k)
      const z = pos.getZ(k)
      if (Math.abs(v - 1) < EPS) expect(z).toBeCloseTo(DECK_LENGTH / 2, 5)
      if (Math.abs(v) < EPS) expect(z).toBeCloseTo(-DECK_LENGTH / 2, 5)
    }
  })

  it('inverts only the V coordinate when the demonstration flag is set', () => {
    const inverted = createDeckGeometry({ invertV: true })
    const uvInv = inverted.getAttribute('uv')
    for (let k = 0; k < uv.count; k++) {
      expect(uvInv.getX(k)).toBeCloseTo(uv.getX(k), 6)
      expect(uvInv.getY(k)).toBeCloseTo(1 - uv.getY(k), 6)
    }
  })

  it('stays within the expected bounding box', () => {
    for (let k = 0; k < pos.count; k++) {
      expect(Math.abs(pos.getX(k))).toBeLessThanOrEqual(DECK_WIDTH / 2 + EPS)
      expect(Math.abs(pos.getZ(k))).toBeLessThanOrEqual(DECK_LENGTH / 2 + EPS)
      expect(pos.getY(k)).toBeGreaterThanOrEqual(-EPS)
      expect(pos.getY(k)).toBeLessThanOrEqual(
        NOSE_KICK_RISE + CONCAVE_DEPTH + DECK_THICKNESS + EPS,
      )
    }
  })

  it('raises the nose kick higher than the tail kick (physical asymmetry)', () => {
    expect(NOSE_KICK_RISE).toBeGreaterThan(TAIL_KICK_RISE)
    let noseMax = -Infinity
    let tailMax = -Infinity
    for (let k = 0; k < pos.count; k++) {
      const z = pos.getZ(k)
      const y = pos.getY(k)
      if (z > DECK_LENGTH * 0.4) noseMax = Math.max(noseMax, y)
      if (z < -DECK_LENGTH * 0.4) tailMax = Math.max(tailMax, y)
    }
    expect(noseMax).toBeGreaterThan(tailMax)
  })

  it('winds the first decal-face triangle to face downward (-Y)', () => {
    const a = new Vector3().fromBufferAttribute(pos, index.getX(0))
    const b = new Vector3().fromBufferAttribute(pos, index.getX(1))
    const c = new Vector3().fromBufferAttribute(pos, index.getX(2))
    const normal = new Vector3().crossVectors(b.sub(a), c.sub(a))
    expect(normal.y).toBeLessThan(0)
  })

  it('is deterministic across calls', () => {
    const again = createDeckGeometry()
    const posAgain = again.getAttribute('position')
    expect(posAgain.count).toBe(pos.count)
    for (let k = 0; k < pos.count; k++) {
      expect(posAgain.getX(k)).toBe(pos.getX(k))
      expect(posAgain.getY(k)).toBe(pos.getY(k))
      expect(posAgain.getZ(k)).toBe(pos.getZ(k))
    }
  })
})
