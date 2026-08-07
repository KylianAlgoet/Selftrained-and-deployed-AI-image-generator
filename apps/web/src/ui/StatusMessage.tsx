/**
 * One shape for every message the application shows.
 *
 * Before this, information, busy, warning and error notices each had their own
 * ad-hoc styling, and one of them was unreadable: the banner set a pale
 * background but no colour, so the inherited near-white body text landed on it
 * whenever the OS was in dark mode.
 *
 * Two rules hold here and are testable:
 *
 * - **Meaning is never carried by colour alone.** Every message renders a text
 *   label ("Warning", "Error", …) alongside its tint, so the tone survives
 *   greyscale, colour blindness and a screen reader.
 * - **The role matches the severity.** Errors are `alert`; everything else is a
 *   polite `status`. A warning about a style's known limitation must not
 *   interrupt like a failure, because it is not one.
 */

export type StatusTone = 'info' | 'busy' | 'warning' | 'error' | 'success'

const TONE_LABEL: Record<StatusTone, string> = {
  info: 'Information',
  busy: 'Waiting',
  warning: 'Warning',
  error: 'Error',
  success: 'Success',
}

export interface StatusMessageProps {
  tone: StatusTone
  children: React.ReactNode
  className?: string
  /**
   * Overrides the default role. Used for the style limitation, which is a
   * standing note about the selected style rather than an event that just
   * happened - `note` says that, where a live `status` would re-announce a
   * fact the user already read every time the region updated.
   */
  role?: string
}

export function StatusMessage({ tone, children, className, role }: StatusMessageProps) {
  const isError = tone === 'error'
  return (
    <p
      className={`status-message status-${tone}${className ? ` ${className}` : ''}`}
      role={role ?? (isError ? 'alert' : 'status')}
    >
      <span className="status-tone">{TONE_LABEL[tone]}</span>
      <span className="status-body">{children}</span>
    </p>
  )
}
