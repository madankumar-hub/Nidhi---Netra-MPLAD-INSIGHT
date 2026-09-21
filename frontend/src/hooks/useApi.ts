import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '@/api/client'

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: ApiError | null
  reload: () => void
}

/**
 * Runs an API call on mount (and whenever `deps` change), with abort support,
 * so every page can render explicit loading / error / empty states.
 */
export function useApi<T>(
  loader: (signal: AbortSignal) => Promise<T>,
  deps: unknown[] = [],
  options: { enabled?: boolean } = {},
): AsyncState<T> {
  const enabled = options.enabled ?? true
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(enabled)
  const [error, setError] = useState<ApiError | null>(null)
  const [nonce, setNonce] = useState(0)
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  useEffect(() => {
    if (!enabled) {
      setLoading(false)
      return
    }
    const controller = new AbortController()
    let active = true
    setLoading(true)
    setError(null)

    loaderRef
      .current(controller.signal)
      .then((result) => {
        if (!active) return
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        if (!active) return
        if ((err as Error)?.name === 'AbortError') return
        setError(
          err instanceof ApiError
            ? err
            : new ApiError(0, 'unknown_error', (err as Error)?.message ?? 'Unexpected error'),
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
      controller.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, nonce, ...deps])

  const reload = useCallback(() => setNonce((value) => value + 1), [])
  return { data, loading, error, reload }
}

/** For user-triggered mutations: tracks pending state and the last error. */
export function useMutation<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>,
) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const run = useCallback(
    async (...args: TArgs): Promise<TResult | null> => {
      setPending(true)
      setError(null)
      try {
        return await action(...args)
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err
            : new ApiError(0, 'unknown_error', (err as Error)?.message ?? 'Unexpected error'),
        )
        return null
      } finally {
        setPending(false)
      }
    },
    [action],
  )

  return { run, pending, error, clearError: () => setError(null) }
}
