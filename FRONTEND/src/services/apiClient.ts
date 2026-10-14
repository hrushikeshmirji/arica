import { ApiResponse } from "../types/api"
import { safeGetItem } from "../utils/safeStorage"

export const AUTH_TOKEN_KEY = "arecavision_auth_token"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"
let mockModeOverride: boolean | null = null

export function setMockMode(enabled: boolean | null) {
  mockModeOverride = enabled
}

export function isMockModeActive(): boolean {
  if (mockModeOverride !== null) return mockModeOverride
  return import.meta.env.VITE_USE_MOCK_DATA === "true" || import.meta.env.VITE_DEMO_MODE === "true"
}

const DEFAULT_ERROR_RATE = parseFloat(import.meta.env.VITE_MOCK_ERROR_RATE || "0.0")

type UnauthorizedListener = () => void
const unauthorizedListeners: Set<UnauthorizedListener> = new Set()

export function onUnauthorized(listener: UnauthorizedListener): () => void {
  unauthorizedListeners.add(listener)
  return () => {
    unauthorizedListeners.delete(listener)
  }
}

function notifyUnauthorized() {
  unauthorizedListeners.forEach((cb) => {
    try {
      cb()
    } catch (e) {
      console.error(e)
    }
  })
}

let mockErrorRateOverride: number | null = null

export function setMockErrorRate(rate: number | null) {
  mockErrorRateOverride = rate
}

function shouldSimulateMockError(errorRateOverride?: number, bypassErrorSimulation?: boolean): boolean {
  if (!isMockModeActive() || bypassErrorSimulation) return false
  const rate = errorRateOverride ?? mockErrorRateOverride ?? DEFAULT_ERROR_RATE
  if (rate <= 0) return false
  return Math.random() < rate
}

export async function simulateMockLatency(minMs = 300, maxMs = 800): Promise<void> {
  const duration = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs
  await new Promise((resolve) => setTimeout(resolve, duration))
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit & {
    mockFallbackData?: T
    errorRate?: number
    bypassErrorSimulation?: boolean
    /**
     * When true, always hits the real backend for THIS call regardless of
     * the global VITE_USE_MOCK_DATA flag.
     */
    forceReal?: boolean
  } = {}
): Promise<T> {
  const { mockFallbackData, errorRate, bypassErrorSimulation, forceReal, signal, headers, ...fetchOptions } = options

  // Mock Mode Execution Path (only when isMockModeActive() is explicitly true and not forceReal)
  if (isMockModeActive() && !forceReal) {
    await simulateMockLatency()

    if (signal?.aborted) {
      const abortErr = new Error("Request aborted by client")
      abortErr.name = "AbortError"
      throw abortErr
    }

    if (shouldSimulateMockError(errorRate, bypassErrorSimulation)) {
      throw new Error(`[MOCK ERROR 500]: Simulated backend failure for endpoint ${endpoint}`)
    }

    if (mockFallbackData !== undefined) {
      return mockFallbackData
    }

    throw new Error(`[MOCK CONFIG ERROR]: No mock fallback data provided for ${endpoint}`)
  }

  // Real REST Backend API Execution Path
  const authToken = safeGetItem(AUTH_TOKEN_KEY)
  const reqHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string>),
  }

  if (fetchOptions.body instanceof FormData) {
    delete reqHeaders["Content-Type"]
  }

  if (authToken) {
    reqHeaders["Authorization"] = `Bearer ${authToken}`
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...fetchOptions,
      signal,
      headers: reqHeaders,
    })
  } catch (networkErr: unknown) {
    if (signal?.aborted || (networkErr as { name?: string })?.name === "AbortError") {
      const abortErr = new Error("Request aborted by client")
      abortErr.name = "AbortError"
      throw abortErr
    }
    const errObj = networkErr as { message?: string }
    const rawMsg = errObj?.message || ""
    if (rawMsg === "Failed to fetch" || rawMsg.includes("NetworkError") || rawMsg.includes("Load failed")) {
      throw new Error(`Unable to reach ArecaVision AI backend at ${API_BASE_URL}. Please ensure the FastAPI server is running (port 8000).`)
    }
    throw new Error(rawMsg || `Failed to connect to backend at ${API_BASE_URL}. Ensure FastAPI server is running.`)
  }

  if (response.status === 401) {
    notifyUnauthorized()
    throw new Error("Session expired or unauthorized (401). Redirecting to login...")
  }

  if (response.status === 204) {
    return undefined as T
  }

  if (!response.ok) {
    let errorMsg = `API Request failed with status ${response.status}`
    try {
      const errJson: ApiResponse<unknown> = await response.json()
      if (errJson.error?.message) {
        errorMsg = errJson.error.message
      }
    } catch {
      // Ignore JSON parse errors on failure response
    }
    throw new Error(errorMsg)
  }

  const json: ApiResponse<T> = await response.json()
  if (!json.success) {
    throw new Error(json.error?.message || "Unknown backend error occurred")
  }

  return json.data as T
}

export async function apiRequestBlob(
  endpoint: string,
  options: RequestInit & { mockFallbackData?: Blob; errorRate?: number; bypassErrorSimulation?: boolean } = {}
): Promise<Blob> {
  const { mockFallbackData, errorRate, bypassErrorSimulation, signal, headers, ...fetchOptions } = options

  // Mock Mode Execution Path
  if (isMockModeActive()) {
    await simulateMockLatency()

    if (signal?.aborted) {
      const abortErr = new Error("Request aborted by client")
      abortErr.name = "AbortError"
      throw abortErr
    }

    if (shouldSimulateMockError(errorRate, bypassErrorSimulation)) {
      throw new Error(`[MOCK ERROR 500]: Simulated backend failure for endpoint ${endpoint}`)
    }

    if (mockFallbackData !== undefined) {
      return mockFallbackData
    }

    throw new Error(`[MOCK CONFIG ERROR]: No mock fallback data provided for ${endpoint}`)
  }

  // Real REST Backend API Execution Path
  const authToken = safeGetItem(AUTH_TOKEN_KEY)
  const reqHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string>),
  }

  if (authToken) {
    reqHeaders["Authorization"] = `Bearer ${authToken}`
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    signal,
    headers: reqHeaders,
  })

  if (response.status === 401) {
    notifyUnauthorized()
    throw new Error("Session expired or unauthorized (401). Redirecting to login...")
  }

  if (!response.ok) {
    let errorMsg = `API Request failed with status ${response.status}`
    try {
      const errJson: ApiResponse<unknown> = await response.json()
      if (errJson.error?.message) {
        errorMsg = errJson.error.message
      }
    } catch {
      // Ignore JSON parse errors on failure response
    }
    throw new Error(errorMsg)
  }

  return response.blob()
}

