/**
 * The review flag: one boolean, two ways to set it, no configuration system.
 *
 * Three controls exist for examining the project rather than for using it - the
 * texture-fit selector, the inverted-UV demonstration, and loading a decal from
 * disk. They are evidence tools. A visitor who just wants a decal should never
 * be asked to choose a UV convention, and DR-012 already settled the fit, so the
 * production interface must not re-open it.
 *
 * They are hidden, never deleted: the fit comparison is the evidence behind
 * DR-012 and has to stay reproducible.
 *
 * `?review=1` in the URL is the reviewer's path - no rebuild, no environment
 * variable, and it survives being written down in a handover document.
 * `VITE_REVIEW_MODE=1` is the developer's path for a dev server. Either is
 * enough; neither is on by default.
 */

export const REVIEW_QUERY_PARAM = 'review'
export const REVIEW_ENV_VAR = 'VITE_REVIEW_MODE'

export function isReviewMode(search?: string): boolean {
  if (import.meta.env?.[REVIEW_ENV_VAR] === '1') return true

  const raw = search ?? (typeof window === 'undefined' ? '' : window.location.search)
  if (!raw) return false
  try {
    return new URLSearchParams(raw).get(REVIEW_QUERY_PARAM) === '1'
  } catch {
    // A malformed query string is not a reason to expose review controls.
    return false
  }
}
