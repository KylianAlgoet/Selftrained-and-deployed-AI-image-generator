import { describe, expect, it } from 'vitest'
import { isReviewMode } from './reviewMode'

/**
 * The flag decides whether evidence tools are visible. It is tested for one
 * property above all: it is OFF unless someone explicitly asked for it.
 */

describe('isReviewMode', () => {
  it('is off by default', () => {
    expect(isReviewMode('')).toBe(false)
  })

  it('is on with ?review=1', () => {
    expect(isReviewMode('?review=1')).toBe(true)
    expect(isReviewMode('?foo=bar&review=1')).toBe(true)
  })

  it('is off for any other value, including truthy-looking ones', () => {
    expect(isReviewMode('?review=0')).toBe(false)
    expect(isReviewMode('?review=true')).toBe(false)
    expect(isReviewMode('?review')).toBe(false)
    expect(isReviewMode('?preview=1')).toBe(false)
  })

  it('stays off rather than throwing on a malformed query string', () => {
    expect(isReviewMode('?%')).toBe(false)
  })
})
