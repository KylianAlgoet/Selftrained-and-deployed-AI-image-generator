/**
 * Client-side preflight for image uploads.
 *
 * Two different uploads share these rules, and they must not be confused:
 *
 * - the **AI reference image**, which is sent to the server as conditioning for
 *   a generation. For that one this check is COURTESY ONLY - the server
 *   re-validates every upload from its bytes (extension, declared type, real
 *   decoded format, dimensions, total pixels), because anything decided in the
 *   browser is attacker-controlled. The value here is a fast, clear message
 *   before a 10 MB round trip, nothing more.
 * - the **user's own decal**, which never leaves the browser. It is decoded
 *   locally and drawn onto a canvas, so there is no server to re-validate it -
 *   which is why the real check for that path is the decode itself
 *   (`imageFromBlob` rejects anything the browser cannot decode as an image),
 *   with this preflight in front of it to reject the obvious cases early.
 *
 * Lives in its own module so the form file exports only its component.
 */

export const MAX_PROMPT_CHARS = 400
export const ALLOWED_UPLOAD_TYPES = ['image/png', 'image/jpeg', 'image/webp']
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024

export function preflightImageUpload(file: File): string | null {
  if (!ALLOWED_UPLOAD_TYPES.includes(file.type)) {
    return 'Choose a PNG, JPEG or WEBP image.'
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return 'That image is larger than the 10 MB limit.'
  }
  return null
}

/** The reference-image path's name for the same rules. */
export const preflightReference = preflightImageUpload
