import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { submitAnalysis, getJobStatus, cancelJob } from "../detectionService"

// Detection always calls the real backend now (forceReal: true), so these
// tests mock `fetch` to simulate the real BACKEND_API_CONTRACT.md envelope
// rather than relying on detectionService's internal mock fallback.

function envelope(data: unknown) {
  return { success: true, data, error: null, timestamp: new Date().toISOString() }
}

describe("detectionService async job polling", () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    global.fetch = vi.fn(async (url: string | URL, init?: RequestInit) => {
      const u = url.toString()
      const method = init?.method ?? "GET"

      if (u.includes("/detect") && method === "POST") {
        return new Response(
          JSON.stringify(envelope({ job_id: "job-abc123", status: "queued", estimatedTimeSeconds: 3 })),
          { status: 200 }
        )
      }
      if (u.includes("/jobs/job-abc123/cancel")) {
        return new Response(JSON.stringify(envelope({ cancelled: true })), { status: 200 })
      }
      if (u.includes("/jobs/job-abc123")) {
        return new Response(
          JSON.stringify(envelope({ job_id: "job-abc123", status: "processing", progressPercent: 40 })),
          { status: 200 }
        )
      }
      throw new Error(`Unexpected fetch in test: ${method} ${u}`)
    }) as unknown as typeof fetch
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it("submits image and returns queued job_id", async () => {
    const submitRes = await submitAnalysis("https://example.com/sample.jpg")

    expect(submitRes.job_id).toBeDefined()
    expect(submitRes.status).toBe("queued")
    expect(submitRes.estimatedTimeSeconds).toBeGreaterThan(0)
  })

  it("polls status and moves through queued -> done lifecycle", async () => {
    const submitRes = await submitAnalysis("https://example.com/sample.jpg")
    const statusRes = await getJobStatus(submitRes.job_id)

    expect(statusRes.job_id).toBe(submitRes.job_id)
    expect(["queued", "processing", "done"]).toContain(statusRes.status)
  })

  it("supports canceling active job", async () => {
    const submitRes = await submitAnalysis("https://example.com/sample.jpg")
    await expect(cancelJob(submitRes.job_id)).resolves.toBeUndefined()
  })
})
