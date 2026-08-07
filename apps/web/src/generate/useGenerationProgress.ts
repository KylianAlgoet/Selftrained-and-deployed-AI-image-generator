/**
 * One polling loop, owned by the component that started the generation.
 *
 * Design constraints that are not negotiable, because the server has one GPU
 * and a process-local lock:
 *
 * - **Never overlapping.** The next poll is scheduled only after the previous
 *   one settles, so a slow response cannot pile up requests behind it.
 * - **Never authoritative.** A failed poll sets `unavailable` and nothing else.
 *   A generation that is working must not be reported as failed because a
 *   telemetry request timed out.
 * - **Never a second generation.** This hook issues GETs only. It cannot
 *   submit, cancel, or release the server lock; stopping it just stops asking.
 * - **Always cleaned up.** Unmount aborts the in-flight fetch and clears the
 *   timer, so a component that goes away stops polling immediately.
 *
 * Stale-operation handling is the subtle part. The endpoint reports the LAST
 * operation when idle, so a poll that lands before the server has begun would
 * otherwise show the previous generation's completed state as if it were this
 * one's. The hook therefore adopts an operation id only when it sees a live
 * `generating` snapshot, ignores every id but the adopted one afterwards, and
 * refuses to re-adopt an id it has already tracked.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchProgress, type ProgressTelemetry } from '../api/progress'
import { POLL_INTERVAL_MS, POLL_SAFETY_TIMEOUT_MS, smoothEta } from './progressModel'

export interface UseGenerationProgressOptions {
  fetchImpl?: typeof fetch
  pollIntervalMs?: number
  /**
   * How often the elapsed counter and the estimate-expiry check re-run.
   *
   * One second in the application, and that is a requirement rather than a
   * default: a countdown that redraws several times a second is noise. It is
   * injectable only so tests can drive it with real timers - fake timers
   * deadlock against React 19's scheduler, which schedules on the same queue.
   */
  tickIntervalMs?: number
  now?: () => number
}

export interface GenerationProgress {
  telemetry: ProgressTelemetry | null
  unavailable: boolean
  elapsedMs: number
  etaExpired: boolean
  begin: () => void
  end: () => void
  polling: boolean
}

export function useGenerationProgress(
  options: UseGenerationProgressOptions = {},
): GenerationProgress {
  const {
    fetchImpl,
    pollIntervalMs = POLL_INTERVAL_MS,
    tickIntervalMs = 1000,
    now = Date.now,
  } = options

  const [polling, setPolling] = useState(false)
  const [telemetry, setTelemetry] = useState<ProgressTelemetry | null>(null)
  const [unavailable, setUnavailable] = useState(false)
  const [elapsedMs, setElapsedMs] = useState(0)
  const [etaExpired, setEtaExpired] = useState(false)

  // The collaborators live in refs, and the effects below depend only on
  // `polling`. Without this, an inline `fetchImpl` or `now` would be a new
  // reference on every render, tearing down and restarting the poll loop each
  // time - which fires a request per render instead of one per interval.
  const fetchRef = useRef(fetchImpl)
  fetchRef.current = fetchImpl
  const nowRef = useRef(now)
  nowRef.current = now

  const startedAtRef = useRef<number | null>(null)
  // The operation this hook is following, and the ones it has already followed:
  // an id in `seenRef` is never adopted again, which is what stops a stale
  // completed snapshot from being mistaken for the new request's result.
  const adoptedRef = useRef<string | null>(null)
  const seenRef = useRef<Set<string>>(new Set())
  const etaDeadlineRef = useRef<number | null>(null)
  const smoothedEtaRef = useRef<number | null>(null)

  const begin = useCallback(() => {
    startedAtRef.current = nowRef.current()
    adoptedRef.current = null
    etaDeadlineRef.current = null
    smoothedEtaRef.current = null
    setTelemetry(null)
    setUnavailable(false)
    setElapsedMs(0)
    setEtaExpired(false)
    setPolling(true)
  }, [])

  const end = useCallback(() => {
    setPolling(false)
  }, [])

  // --- the poll loop --------------------------------------------------------

  useEffect(() => {
    if (!polling) return

    let cancelled = false
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    const deadline = nowRef.current() + POLL_SAFETY_TIMEOUT_MS

    const apply = (snapshot: ProgressTelemetry) => {
      const id = snapshot.operation_id

      if (adoptedRef.current === null) {
        // Adopt only a LIVE operation we have not already followed. An idle,
        // completed or failed snapshot at this point belongs to a previous
        // request and says nothing about this one.
        if (snapshot.status !== 'generating' || !id || seenRef.current.has(id)) return
        adoptedRef.current = id
        seenRef.current.add(id)
      } else if (id !== adoptedRef.current) {
        return
      }

      if (snapshot.estimated_remaining_seconds != null) {
        const smoothed = smoothEta(
          smoothedEtaRef.current,
          snapshot.estimated_remaining_seconds,
        )
        smoothedEtaRef.current = smoothed
        etaDeadlineRef.current = nowRef.current() + smoothed * 1000
        setEtaExpired(false)
        setTelemetry({ ...snapshot, estimated_remaining_seconds: smoothed })
        return
      }
      setTelemetry(snapshot)
    }

    const tick = async () => {
      try {
        const snapshot = await fetchProgress({
          signal: controller.signal,
          fetchImpl: fetchRef.current,
        })
        if (cancelled) return
        setUnavailable(false)
        apply(snapshot)
      } catch {
        if (cancelled) return
        // Telemetry is supplemental. Losing it downgrades the display to
        // elapsed time; it never turns a running generation into a failure.
        setUnavailable(true)
      }
      if (cancelled) return
      if (nowRef.current() > deadline) {
        setPolling(false)
        return
      }
      timer = setTimeout(() => void tick(), pollIntervalMs)
    }

    void tick()

    return () => {
      cancelled = true
      controller.abort()
      if (timer !== undefined) clearTimeout(timer)
    }
  }, [polling, pollIntervalMs])

  // --- the one-second display tick -----------------------------------------

  useEffect(() => {
    if (!polling) return
    const update = () => {
      const startedAt = startedAtRef.current
      if (startedAt !== null) setElapsedMs(nowRef.current() - startedAt)
      const deadline = etaDeadlineRef.current
      if (deadline !== null && nowRef.current() > deadline) setEtaExpired(true)
    }
    update()
    // Once per second: the countdown must not flicker several times a second,
    // and nothing here is worth a shorter interval.
    const interval = setInterval(update, tickIntervalMs)
    return () => clearInterval(interval)
  }, [polling, tickIntervalMs])

  return { telemetry, unavailable, elapsedMs, etaExpired, begin, end, polling }
}
