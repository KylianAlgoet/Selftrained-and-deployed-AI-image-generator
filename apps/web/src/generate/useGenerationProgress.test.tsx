// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import type { ProgressTelemetry } from '../api/progress'
import { useGenerationProgress } from './useGenerationProgress'

/**
 * The polling loop, tested for the things that would hurt the server or lie to
 * the user: overlapping requests, adopting another operation's telemetry, and
 * treating a lost poll as a lost generation.
 */

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.restoreAllMocks()
})

function telemetry(overrides: Partial<ProgressTelemetry> = {}): ProgressTelemetry {
  return {
    operation_id: 'op-current',
    status: 'generating',
    stage: 'denoising',
    current_step: 5,
    total_steps: 30,
    denoising_fraction: 5 / 30,
    elapsed_seconds: 2,
    estimated_remaining_seconds: null,
    pipeline_loaded: true,
    ...overrides,
  }
}

/** A fetch stub that answers with whatever the test queues up next. */
function progressFetch(sequence: Array<ProgressTelemetry | Error>) {
  let index = 0
  const calls: number[] = []
  const impl = vi.fn(async () => {
    const item = sequence[Math.min(index, sequence.length - 1)]
    index += 1
    calls.push(index)
    if (item instanceof Error) throw item
    return {
      ok: true,
      json: async () => item,
    } as unknown as Response
  })
  return { impl, callCount: () => impl.mock.calls.length, calls }
}

describe('polling lifecycle', () => {
  it('does not poll before a generation is submitted', async () => {
    const fetcher = progressFetch([telemetry()])
    renderHook(() => useGenerationProgress({ fetchImpl: fetcher.impl }))
    await new Promise((resolve) => setTimeout(resolve, 20))
    expect(fetcher.callCount()).toBe(0)
  })

  it('starts polling on begin and stops on end', async () => {
    const fetcher = progressFetch([telemetry()])
    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: fetcher.impl, pollIntervalMs: 5 }),
    )

    act(() => result.current.begin())
    await waitFor(() => expect(fetcher.callCount()).toBeGreaterThan(1))

    act(() => result.current.end())
    const afterStop = fetcher.callCount()
    await new Promise((resolve) => setTimeout(resolve, 40))
    // At most the one request already in flight when end() was called.
    expect(fetcher.callCount()).toBeLessThanOrEqual(afterStop + 1)
    expect(result.current.polling).toBe(false)
  })

  it('never overlaps polls: the next is scheduled only after the last settles', async () => {
    let inFlight = 0
    let maxConcurrent = 0
    const impl = vi.fn(async () => {
      inFlight += 1
      maxConcurrent = Math.max(maxConcurrent, inFlight)
      await new Promise((resolve) => setTimeout(resolve, 10))
      inFlight -= 1
      return { ok: true, json: async () => telemetry() } as unknown as Response
    })

    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: impl, pollIntervalMs: 1 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(impl.mock.calls.length).toBeGreaterThan(2))
    act(() => result.current.end())

    expect(maxConcurrent).toBe(1)
  })

  it('stops polling when the component unmounts', async () => {
    const fetcher = progressFetch([telemetry()])
    const { result, unmount } = renderHook(() =>
      useGenerationProgress({ fetchImpl: fetcher.impl, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(fetcher.callCount()).toBeGreaterThan(1))

    unmount()
    const afterUnmount = fetcher.callCount()
    await new Promise((resolve) => setTimeout(resolve, 40))
    expect(fetcher.callCount()).toBeLessThanOrEqual(afterUnmount + 1)
  })

  it('aborts the in-flight request when it stops', async () => {
    const signals: AbortSignal[] = []
    const impl = vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.signal) signals.push(init.signal)
      return { ok: true, json: async () => telemetry() } as unknown as Response
    })
    const { result, unmount } = renderHook(() =>
      useGenerationProgress({ fetchImpl: impl as unknown as typeof fetch, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(signals.length).toBeGreaterThan(0))
    unmount()
    expect(signals[0].aborted).toBe(true)
  })
})

describe('operation identity', () => {
  it('adopts a live operation and follows it', async () => {
    const fetcher = progressFetch([telemetry({ current_step: 12 })])
    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: fetcher.impl, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(result.current.telemetry?.current_step).toBe(12))
    act(() => result.current.end())
  })

  it('ignores a completed snapshot left over from a previous operation', async () => {
    const fetcher = progressFetch([
      telemetry({ operation_id: 'op-previous', status: 'completed', stage: 'completed' }),
      telemetry({ operation_id: 'op-previous', status: 'completed', stage: 'completed' }),
    ])
    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: fetcher.impl, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(fetcher.callCount()).toBeGreaterThan(2))

    // The stale completed state was never adopted, so nothing claims this
    // generation has finished.
    expect(result.current.telemetry).toBeNull()
    act(() => result.current.end())
  })

  it('ignores an idle snapshot from before the server started work', async () => {
    const fetcher = progressFetch([
      telemetry({ operation_id: null, status: 'idle', stage: 'idle' }),
    ])
    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: fetcher.impl, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(fetcher.callCount()).toBeGreaterThan(2))
    expect(result.current.telemetry).toBeNull()
    act(() => result.current.end())
  })

  it('ignores telemetry from a different operation once one is adopted', async () => {
    const fetcher = progressFetch([
      telemetry({ operation_id: 'op-a', current_step: 4 }),
      telemetry({ operation_id: 'op-b', current_step: 27 }),
      telemetry({ operation_id: 'op-b', current_step: 28 }),
    ])
    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: fetcher.impl, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(result.current.telemetry?.current_step).toBe(4))
    await waitFor(() => expect(fetcher.callCount()).toBeGreaterThan(3))

    expect(result.current.telemetry?.operation_id).toBe('op-a')
    expect(result.current.telemetry?.current_step).toBe(4)
    act(() => result.current.end())
  })

  it('does not re-adopt an operation it already followed', async () => {
    const first = progressFetch([telemetry({ operation_id: 'op-a', current_step: 9 })])
    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: first.impl, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(result.current.telemetry?.current_step).toBe(9))
    act(() => result.current.end())

    // A second generation begins, but the server is still reporting the FIRST
    // operation. Nothing may be adopted from it.
    act(() => result.current.begin())
    await waitFor(() => expect(first.callCount()).toBeGreaterThan(2))
    expect(result.current.telemetry).toBeNull()
    act(() => result.current.end())
  })
})

describe('failure tolerance', () => {
  it('marks telemetry unavailable without failing the generation', async () => {
    const fetcher = progressFetch([new Error('network down')])
    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: fetcher.impl, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(result.current.unavailable).toBe(true))
    // Still polling: a transient failure is not a reason to give up.
    expect(result.current.polling).toBe(true)
    act(() => result.current.end())
  })

  it('recovers when polling starts working again', async () => {
    const fetcher = progressFetch([new Error('blip'), telemetry({ current_step: 7 })])
    const { result } = renderHook(() =>
      useGenerationProgress({ fetchImpl: fetcher.impl, pollIntervalMs: 5 }),
    )
    act(() => result.current.begin())
    await waitFor(() => expect(result.current.telemetry?.current_step).toBe(7))
    expect(result.current.unavailable).toBe(false)
    act(() => result.current.end())
  })
})

describe('elapsed time and estimate expiry', () => {
  // Real timers with an injected clock. Vitest's fake timers deadlock against
  // React 19's scheduler, which queues its own work on the same timer queue -
  // so the elapsed reading is driven by a controllable `now` instead.

  it('reports elapsed time from the injected clock', async () => {
    let clock = 1_000_000
    const impl = vi.fn(
      async () => ({ ok: true, json: async () => telemetry() }) as unknown as Response,
    )
    const { result } = renderHook(() =>
      useGenerationProgress({
        fetchImpl: impl,
        pollIntervalMs: 100_000,
        tickIntervalMs: 5,
        now: () => clock,
      }),
    )

    act(() => result.current.begin())
    expect(result.current.elapsedMs).toBe(0)

    clock += 3000
    await waitFor(() => expect(result.current.elapsedMs).toBe(3000))
    act(() => result.current.end())
  })

  it('flags an estimate as expired once its time has passed', async () => {
    let clock = 1_000_000
    const impl = vi.fn(
      async () =>
        ({
          ok: true,
          json: async () => telemetry({ estimated_remaining_seconds: 2 }),
        }) as unknown as Response,
    )
    const { result } = renderHook(() =>
      useGenerationProgress({
        fetchImpl: impl,
        pollIntervalMs: 100_000,
        tickIntervalMs: 5,
        now: () => clock,
      }),
    )

    act(() => result.current.begin())
    await waitFor(() => expect(result.current.telemetry).not.toBeNull())
    expect(result.current.etaExpired).toBe(false)

    // Five seconds pass against a two-second estimate.
    clock += 5000
    await waitFor(() => expect(result.current.etaExpired).toBe(true))
    act(() => result.current.end())
  })
})
