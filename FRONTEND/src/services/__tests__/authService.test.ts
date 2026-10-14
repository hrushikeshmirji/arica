import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { loginUser, logoutUser, refreshUserSession, getStoredUser } from "../authService"

describe("authService", () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    localStorage.clear()
    global.fetch = vi.fn(async (url: string | URL) => {
      const u = url.toString()
      if (u.includes("/auth/login") || u.includes("/auth/refresh")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              token: "mock-jwt-token-xyz123",
              user: { id: "user-1", email: "test@arecavision.ai", name: "Farmer", role: "farmer" },
            },
            error: null,
          }),
          { status: 200 }
        )
      }
      if (u.includes("/auth/logout")) {
        return new Response(JSON.stringify({ success: true, data: null, error: null }), { status: 200 })
      }
      return new Response(JSON.stringify({ success: true }), { status: 200 })
    }) as unknown as typeof fetch
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it("authenticates user and returns AuthResponse payload", async () => {
    const res = await loginUser({ email: "test@arecavision.ai" })

    expect(res.user).toBeDefined()
    expect(res.user.email).toBe("test@arecavision.ai")
    expect(res.token).toContain("mock-jwt-token-")
    expect(getStoredUser()?.email).toBe("test@arecavision.ai")
  })

  it("cleans up user session on logout", async () => {
    await loginUser({ email: "test@arecavision.ai" })
    expect(getStoredUser()).not.toBeNull()

    await logoutUser()
    expect(getStoredUser()).toBeNull()
  })

  it("refreshes user session when stored user exists", async () => {
    await loginUser({ email: "test@arecavision.ai" })
    const refreshRes = await refreshUserSession()

    expect(refreshRes).not.toBeNull()
    expect(refreshRes?.user.email).toBe("test@arecavision.ai")
  })
})
