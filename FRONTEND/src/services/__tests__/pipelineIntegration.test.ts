import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { submitAnalysis, getJobStatus } from "../detectionService"
import { ModelInferenceResponse } from "../../types/api"

// Detection now always calls the real backend (forceReal: true in
// detectionService.ts), even while every other feature stays on mock
// data. That means this test needs to mock `fetch` itself and verify
// detectionService.ts correctly parses the real BACKEND_API_CONTRACT.md
// envelope shape -- which is actually a stronger test than the old
// mock-passthrough version, since it exercises the real parsing path.

const FAKE_RESULT: ModelInferenceResponse = {
  id: "job-test123",
  disease: "Anthracnose",
  confidence: 0.91,
  stage: "Detected",
  severity: "Severe",
  description: "Classified as Anthracnose by the ViT-B/16 model.",
  treatments: [],
  organicControl: [],
  yoloBoxes: [
    { label: "Anthracnose", confidence: 0.91, top: "10%", left: "10%", width: "20%", height: "20%", color: "#dc2626" },
  ],
  modelBreakdown: { cnn: 0.95, vit: 0.91, yolo: 0.88 },
  processedAt: new Date().toISOString(),
  featureMapUrl: "",
  attentionMapUrl: "data:image/png;base64,fake",
  gradCamUrl: "",
}

function envelope(data: unknown) {
  return { success: true, data, error: null, timestamp: new Date().toISOString() }
}

describe("Pipeline Integration & Types (real backend contract)", () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    let callCount = 0
    global.fetch = vi.fn(async (url: string | URL) => {
      const u = url.toString()
      callCount++
      if (u.includes("/detect")) {
        return new Response(
          JSON.stringify(envelope({ job_id: "job-test123", status: "queued", estimatedTimeSeconds: 1 })),
          { status: 200 }
        )
      }
      if (u.includes("/jobs/job-test123")) {
        const body =
          callCount <= 2
            ? envelope({ job_id: "job-test123", status: "processing", progressPercent: 50 })
            : envelope({ job_id: "job-test123", status: "done", progressPercent: 100, result: FAKE_RESULT })
        return new Response(JSON.stringify(body), { status: 200 })
      }
      throw new Error(`Unexpected fetch in test: ${u}`)
    }) as unknown as typeof fetch
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it("resolves full ModelInferenceResponse structure by parsing the real backend envelope", async () => {
    const submitRes = await submitAnalysis("https://example.com/leaf.jpg")
    expect(submitRes.job_id).toBe("job-test123")

    let statusRes = await getJobStatus(submitRes.job_id)
    let attempts = 0
    while (statusRes.status !== "done" && attempts < 10) {
      statusRes = await getJobStatus(submitRes.job_id)
      attempts++
    }

    expect(statusRes.status).toBe("done")
    expect(statusRes.result).toBeDefined()

    const result = statusRes.result as ModelInferenceResponse
    expect(result.disease).toBeDefined()
    expect(result.confidence).toBeGreaterThan(0)
    expect(result.severity).toBeDefined()
    expect(result.stage).toBeDefined()
    expect(Array.isArray(result.treatments)).toBe(true)
    expect(Array.isArray(result.yoloBoxes)).toBe(true)
    expect(result.modelBreakdown).toHaveProperty("cnn")
    expect(result.modelBreakdown).toHaveProperty("vit")
    expect(result.modelBreakdown).toHaveProperty("yolo")
  })
})
