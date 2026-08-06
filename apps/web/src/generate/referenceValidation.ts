/**
 * Client-side preflight for the reference upload.
 *
 * This is COURTESY ONLY. The server re-validates every upload from its bytes -
 * extension, declared type, real decoded format, dimensions and total pixels -
 * because anything decided in the browser is attacker-controlled. The value
 * here is a fast, clear message before a 10 MB round trip, nothing more.
 *
 * Lives in its own module so the form file exports only its component.
 */

export const MAX_PROMPT_CHARS = 400
export const ALLOWED_UPLOAD_TYPES = ['image/png', 'image/jpeg', 'image/webp']
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024

export function preflightReference(file: File): string | null {
  if (!ALLOWED_UPLOAD_TYPES.includes(file.type)) {
    return 'Choose a PNG, JPEG or WEBP image.'
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return 'That image is larger than the 10 MB limit.'
  }
  return null
}
