/**
 * Thin fetch wrapper: base URL, bearer token, uniform error shape.
 * Every function in `src/api/*` goes through this.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api'

const ACCESS_TOKEN_KEY = 'mplad.access_token'
const REFRESH_TOKEN_KEY = 'mplad.refresh_token'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly detail?: string

  constructor(status: number, code: string, message: string, detail?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.detail = detail
  }

  get isUnauthorized(): boolean {
    return this.status === 401
  }

  get isForbidden(): boolean {
    return this.status === 403
  }

  get isNotFound(): boolean {
    return this.status === 404
  }
}

export const tokenStore = {
  get access(): string | null {
    try {
      return localStorage.getItem(ACCESS_TOKEN_KEY)
    } catch {
      return null
    }
  },
  get refresh(): string | null {
    try {
      return localStorage.getItem(REFRESH_TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(access: string, refresh: string) {
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, access)
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    } catch {
      /* storage unavailable (private mode) - the session stays in memory */
    }
  },
  clear() {
    try {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    } catch {
      /* ignore */
    }
  },
}

type QueryValue = string | number | boolean | undefined | null

export function buildQuery(params: Record<string, QueryValue>): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    search.append(key, String(value))
  })
  const query = search.toString()
  return query ? `?${query}` : ''
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
  auth?: boolean
  /** Internal: set when a call is already a retry after a token refresh. */
  _retried?: boolean
}

/**
 * Silent token refresh.
 *
 * The access token is short-lived by design; without this, an officer who
 * leaves a review open past its expiry is thrown back to the sign-in screen
 * mid-edit. On the first 401 we exchange the refresh token once and replay
 * the original request.
 *
 * Concurrent 401s share a single in-flight refresh, so a page with several
 * panels does not fire one refresh per panel and invalidate its own tokens.
 */
let refreshInFlight: Promise<boolean> | null = null

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = tokenStore.refresh
  if (!refreshToken) return false

  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!response.ok) {
      tokenStore.clear()
      return false
    }
    const data = (await response.json()) as { access_token: string; refresh_token: string }
    tokenStore.set(data.access_token, data.refresh_token)
    return true
  } catch {
    // Network failure: keep the tokens, the next attempt may succeed.
    return false
  }
}

function ensureRefresh(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = refreshAccessToken().finally(() => {
      refreshInFlight = null
    })
  }
  return refreshInFlight
}

async function parseError(response: Response): Promise<ApiError> {
  let code = 'http_error'
  let message = `Request failed with status ${response.status}.`
  let detail: string | undefined
  try {
    const data = await response.json()
    if (data && typeof data === 'object') {
      code = (data.code as string) ?? code
      message = (data.message as string) ?? (data.detail as string) ?? message
      detail = typeof data.detail === 'string' ? data.detail : undefined
    }
  } catch {
    /* non-JSON error body */
  }
  if (response.status === 403 && code === 'http_error') {
    message = 'You do not have permission to view this information.'
  }
  return new ApiError(response.status, code, message, detail)
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal, auth = true, _retried = false } = options
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const token = tokenStore.access
  if (auth && token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if ((error as Error)?.name === 'AbortError') throw error
    throw new ApiError(0, 'network_error', 'Could not reach the server. Check that the API is running.')
  }

  // An expired access token is recoverable exactly once per request.
  if (response.status === 401 && auth && !_retried && tokenStore.refresh) {
    const refreshed = await ensureRefresh()
    if (refreshed) {
      return request<T>(path, { ...options, _retried: true })
    }
  }

  if (!response.ok) throw await parseError(response)
  if (response.status === 204) return undefined as T

  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    return (await response.text()) as unknown as T
  }
  return (await response.json()) as T
}

/** Downloads a file (used for the CSV export) with the bearer token attached. */
export async function downloadFile(path: string, filename: string): Promise<void> {
  const token = tokenStore.access
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok) throw await parseError(response)
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
