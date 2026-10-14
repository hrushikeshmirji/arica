import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { submitAnalysis, getJobStatus } from "../detectionService"

describe("Stage 1A Honesty: Failed Backend Yields Error State, Never Silent Diagnosis", () => {
  const originalFetch = global.fetch

  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it("proves network failure on submitAnalysis throws an error and never returns a fake job or diagnosis", async () => {
    // Simulate unreachable backend / network failure
    global.fetch = vi.fn().mockRejectedValue(new Error("Failed to connect to backend at http://localhost:8000/api/v1"))

    await expect(submitAnalysis("sample-banana.jpg")).rejects.toThrow(
      /Failed to connect to backend/i
    )
  })

  it("proves 500 server error on submitAnalysis throws and does not fall back to mock data", async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: false,
          data: null,
          error: { code: "INTERNAL_ERROR", message: "Inference pipeline crashed" },
        }),
        { status: 500 }
      )
    )

    await expect(submitAnalysis("sample-banana.jpg")).rejects.toThrow(
      /Inference pipeline crashed|API Request failed with status 500/i
    )
  })

  it("proves network failure during getJobStatus throws error and does NOT return a canned diagnosis profile", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network connection dropped during polling"))

    await expect(getJobStatus("real-job-999")).rejects.toThrow(
      /Network connection dropped during polling/i
    )
  })
})
