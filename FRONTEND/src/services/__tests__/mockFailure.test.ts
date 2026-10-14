import { describe, it, expect, beforeEach, afterEach } from "vitest"
import { setMockErrorRate, setMockMode, apiRequest } from "../apiClient"

describe("mock failure simulation", () => {
  beforeEach(() => {
    setMockMode(true)
  })

  afterEach(() => {
    setMockMode(null)
    setMockErrorRate(null)
  })

  it("throws error when error rate is 1.0 (100% failure rate)", async () => {
    setMockErrorRate(1.0)

    await expect(
      apiRequest("/test-endpoint", { mockFallbackData: { ok: true } })
    ).rejects.toThrow("Simulated backend failure")
  })

  it("succeeds when error rate is 0.0 (0% failure rate)", async () => {
    setMockErrorRate(0.0)

    const res = await apiRequest<{ ok: boolean }>("/test-endpoint", {
      mockFallbackData: { ok: true },
    })
    expect(res.ok).toBe(true)
  })
})
