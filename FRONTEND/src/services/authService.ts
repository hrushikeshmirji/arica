import { apiRequest, AUTH_TOKEN_KEY } from "./apiClient"
import { AuthResponse, LoginRequest, RegisterRequest, UserTokenPayload } from "../types/api"
import { safeGetItem, safeSetItem, safeRemoveItem } from "../utils/safeStorage"

/**
 * TOKEN STORAGE ARCHITECTURAL DECISION & TRADEOFF NOTE:
 * 
 * Production Recommendation: httpOnly Cookies
 * Using httpOnly, SameSite=Strict cookies is the standard recommended strategy for production backends
 * because it eliminates XSS token exfiltration risk. The browser automatically handles cookie transmission.
 * 
 * Current Development Strategy (Bearer / Memory / Fallback):
 * For API development flexibility, when Bearer authentication token is returned by `/auth/login`,
 * it is stored in `localStorage` under `arecavision_auth_token` and attached in `Authorization` headers.
 * When real backend transitions to httpOnly cookies, `localStorage` calls can be omitted with zero UI changes.
 */

const STORAGE_TOKEN_KEY = AUTH_TOKEN_KEY
const STORAGE_USER_KEY = "arecavision_auth_user"

export async function loginUser(credentials: LoginRequest): Promise<AuthResponse> {
  const res = await apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
    forceReal: true,
  })

  if (res.token) {
    safeSetItem(STORAGE_TOKEN_KEY, res.token)
  }
  safeSetItem(STORAGE_USER_KEY, JSON.stringify(res.user))
  return res
}

export async function registerUser(data: RegisterRequest): Promise<AuthResponse> {
  const res = await apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
    forceReal: true,
  })

  if (res.token) {
    safeSetItem(STORAGE_TOKEN_KEY, res.token)
  }
  safeSetItem(STORAGE_USER_KEY, JSON.stringify(res.user))
  return res
}

export async function logoutUser(): Promise<void> {
  try {
    await apiRequest<void>("/auth/logout", {
      method: "POST",
      forceReal: true,
    })
  } catch {
    // Ignore backend logout errors during offline/mock cleanup
  } finally {
    safeRemoveItem(STORAGE_TOKEN_KEY)
    safeRemoveItem(STORAGE_USER_KEY)
  }
}

export async function refreshUserSession(): Promise<AuthResponse | null> {
  const savedUser = safeGetItem(STORAGE_USER_KEY)
  if (!savedUser) return null

  try {
    const res = await apiRequest<AuthResponse>("/auth/refresh", {
      method: "POST",
      forceReal: true,
    })

    if (res.token) {
      safeSetItem(STORAGE_TOKEN_KEY, res.token)
    }
    safeSetItem(STORAGE_USER_KEY, JSON.stringify(res.user))
    return res
  } catch {
    safeRemoveItem(STORAGE_TOKEN_KEY)
    safeRemoveItem(STORAGE_USER_KEY)
    return null
  }
}

export function getStoredUser(): UserTokenPayload | null {
  try {
    const savedUser = safeGetItem(STORAGE_USER_KEY)
    return savedUser ? JSON.parse(savedUser) : null
  } catch {
    return null
  }
}
