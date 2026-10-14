import { apiRequest } from "./apiClient"
import {
  InferenceJobSubmitResponse,
  InferenceJobStatusResponse,
  ModelInferenceResponse,
} from "../types/api"

// Mock Job Store for Development Adapter
interface StoredMockJob {
  job_id: string
  createdAt: number
  fileName: string
}

const mockJobsStore: Map<string, StoredMockJob> = new Map()

const MOCK_DISEASE_PROFILES: ModelInferenceResponse[] = [
  {
    id: "demo-001",
    disease: "Anthracnose",
    confidence: 96.4,
    stage: "Middle Stage (Stage 2)",
    severity: "Severe",
    description: "Fungal infection (Colletotrichum gloeosporioides) causing leaf blight, dieback, and dark sunken lesions on developing nuts.",
    treatments: [
      "Apply Copper Oxychloride 50 WP (2.5g/L) or 1% Bordeaux mixture",
      "Prune infected fronds and improve plantation aeration",
      "Maintain optimal field drainage during heavy rains",
    ],
    organicControl: [
      "Neem oil spray (5ml/L) at 15-day intervals",
      "Bio-control with Trichoderma harzianum soil enrichment",
    ],
    yoloBoxes: [
      { label: "Anthracnose (96.4%)", confidence: 96.4, top: "12%", left: "15%", width: "30%", height: "28%", color: "#dc2626" },
      { label: "Anthracnose (94.2%)", confidence: 94.2, top: "32%", left: "52%", width: "26%", height: "30%", color: "#dc2626" },
    ],
    modelBreakdown: { cnn: 99.1, vit: 96.4, yolo: 95.3 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-002",
    disease: "BudBorer",
    confidence: 91.5,
    stage: "Active Infestation",
    severity: "Critical",
    description: "Larval pest infestation boring into tender spindle and crown tissues, causing shoot rot and foliage wilting.",
    treatments: [
      "Dust leaf axils with a 1:1 mixture of powdered neem cake and coarse river sand (250g/palm)",
      "Clear dead debris and frass around leaf axils to eliminate oviposition sites",
      "Notice: Synthetic organophosphate crown spraying (Chlorpyrifos) is restricted under S.O. 4294(E)",
    ],
    organicControl: [
      "Application of Beauveria bassiana bio-pesticide",
      "Crown dusting with neem cake and coarse sand mixture",
    ],
    yoloBoxes: [
      { label: "BudBorer (91.5%)", confidence: 91.5, top: "18%", left: "28%", width: "42%", height: "38%", color: "#dc2626" },
    ],
    modelBreakdown: { cnn: 98.6, vit: 91.5, yolo: 90.2 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-003",
    disease: "FruitRot",
    confidence: 94.8,
    stage: "Active Infection (Koleroga)",
    severity: "Critical",
    description: "Koleroga / Mahali (Phytophthora meadii) causing water-soaked dark lesions and mass premature shedding of nuts during monsoons.",
    treatments: [
      "Prophylactic spray of 1% Bordeaux mixture covering fruit bunches before monsoon onset",
      "Repeat Bordeaux spray after 40-45 days if rainfall continues",
      "Ensure drainage channels in plantation are clear of waterlogging",
    ],
    organicControl: [
      "Collect and deeply bury or burn all fallen infected nuts immediately",
      "Apply Pseudomonas fluorescens bio-fungicide to tree base",
    ],
    yoloBoxes: [
      { label: "FruitRot (94.8%)", confidence: 94.8, top: "20%", left: "30%", width: "40%", height: "35%", color: "#dc2626" },
    ],
    modelBreakdown: { cnn: 99.4, vit: 94.8, yolo: 93.2 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-004",
    disease: "Healthy",
    confidence: 98.7,
    stage: "Optimal Condition",
    severity: "Healthy",
    description: "Canopy and nuts show optimal vigor, healthy green pigmentation, and no detectable pathological symptoms.",
    treatments: [
      "Continue standard seasonal nutrition (100g N, 40g P2O5, 140g K2O per palm/year)",
      "Maintain regular drip or basin irrigation scheduling",
    ],
    organicControl: [
      "Apply well-decomposed farmyard manure or vermicompost (12-15 kg/palm)",
      "Mulch tree basins with dry arecanut leaves to conserve soil moisture",
    ],
    yoloBoxes: [],
    modelBreakdown: { cnn: 99.9, vit: 98.7, yolo: 0.0 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-005",
    disease: "LeafSpotComplex",
    confidence: 88.3,
    stage: "Foliar Necrosis",
    severity: "Moderate",
    description: "Complex fungal pathology causing necrotic circular and irregular spots on leaves, reducing photosynthetic efficiency.",
    treatments: [
      "Prune and burn severely spotted lower fronds; regulate shade tree canopy for aeration",
      "Apply protective 1% Bordeaux mixture (10g/L) or Copper Oxychloride 50 WP (2.5g/L); unverified systemic triazoles withheld",
      "Ensure proper crown sunlight penetration by thinning overhanging shade trees",
    ],
    organicControl: [
      "Spray fermented cow urine and asafoetida concoction (1:10 dilution)",
      "Foliar application of Trichoderma viride culture",
    ],
    yoloBoxes: [
      { label: "LeafSpotComplex (88.3%)", confidence: 88.3, top: "15%", left: "20%", width: "35%", height: "30%", color: "#f59e0b" },
    ],
    modelBreakdown: { cnn: 97.8, vit: 88.3, yolo: 86.5 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-006",
    disease: "NutCracking",
    confidence: 92.1,
    stage: "Physiological Stage",
    severity: "Moderate",
    description: "Physiological disorder resulting from sudden moisture fluctuation or boron deficiency, exposing kernel to secondary decay.",
    treatments: [
      "Apply Borax (15-20g per palm annually) around root zone",
      "Maintain uniform, regular irrigation intervals to avoid water stress",
    ],
    organicControl: [
      "Heavy mulching around the basin to regulate soil moisture levels",
      "Soil application of wood ash and rich compost for micronutrients",
    ],
    yoloBoxes: [
      { label: "NutCracking (92.1%)", confidence: 92.1, top: "25%", left: "35%", width: "30%", height: "28%", color: "#f59e0b" },
    ],
    modelBreakdown: { cnn: 98.2, vit: 92.1, yolo: 91.0 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-007",
    disease: "PhytoplasmaYellowLeaf",
    confidence: 90.4,
    stage: "Systemic Decline",
    severity: "Severe",
    description: "Systemic phytoplasma pathogen causing intense yellowing of inner whorl leaflets, crown reduction, and kernel blackening.",
    treatments: [
      "Apply balanced NPK enriched with Zinc Sulfate (50g) and Magnesium Sulfate (100g/palm)",
      "Chemical fungicides have ZERO efficacy against phytoplasmas and are strictly prohibited",
      "Eradicate and burn severely stunted palms beyond economic recovery to protect healthy palms",
    ],
    organicControl: [
      "Neem oil spray (5ml/L) to suppress vector populations",
      "Application of mycorrhizal fungi to bolster root nutrient absorption",
    ],
    yoloBoxes: [
      { label: "PhytoplasmaYellowLeaf (90.4%)", confidence: 90.4, top: "10%", left: "15%", width: "45%", height: "40%", color: "#dc2626" },
    ],
    modelBreakdown: { cnn: 98.9, vit: 90.4, yolo: 89.1 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-008",
    disease: "SootyMold",
    confidence: 93.6,
    stage: "Foliar Coating",
    severity: "Mild",
    description: "Superficial black fungal coating (Capnodium spp.) thriving on honeydew excreted by sap-sucking scale insects and mealybugs.",
    treatments: [
      "Spray 2% boiled starch paste during bright sunshine; flakes off naturally removing the black mold",
      "Manage sap-sucking vectors using Fish Oil Rosin Soap (FORS 20g/L) or botanical Neem Oil (5ml/L)",
      "Notice: Synthetic organophosphate sprays (Dimethoate/Chlorpyrifos) are withheld due to lack of approved label claims",
    ],
    organicControl: [
      "Fish oil rosin soap spray (20g/L)",
      "High-pressure water jets to dislodge insect colonies followed by neem spray",
    ],
    yoloBoxes: [
      { label: "SootyMold (93.6%)", confidence: 93.6, top: "30%", left: "22%", width: "38%", height: "32%", color: "#f59e0b" },
    ],
    modelBreakdown: { cnn: 97.5, vit: 93.6, yolo: 91.8 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-009",
    disease: "StemBleeding",
    confidence: 89.2,
    stage: "Trunk Lesion",
    severity: "Severe",
    description: "Thielaviopsis paradoxa fungal infection causing exudation of dark reddish-brown gummy fluid from trunk cracks.",
    treatments: [
      "Chisel off affected bark tissue cleanly to healthy wood and immediately burn shavings",
      "Notice: Topical chemical wound dressings are under agronomic review; obsolete coal tar and banned Tridemorph are strictly prohibited",
      "Consult local Krishi Vigyan Kendra (KVK) or ICAR-CPCRI specialist for site-specific treatment guidance",
    ],
    organicControl: [
      "Apply Trichoderma viride organic paste to scraped wounds",
      "Avoid mechanical damage to trunk during weeding and intercultural operations",
    ],
    yoloBoxes: [
      { label: "StemBleeding (89.2%)", confidence: 89.2, top: "40%", left: "30%", width: "25%", height: "40%", color: "#dc2626" },
    ],
    modelBreakdown: { cnn: 98.0, vit: 89.2, yolo: 87.4 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-010",
    disease: "StemCracking",
    confidence: 87.9,
    stage: "Structural Splitting",
    severity: "Moderate",
    description: "Longitudinal splits on palm trunk caused by intense solar radiation (sun scorch), drought stress, or sap pressure surges.",
    treatments: [
      "Whitewash trunk up to 2.5 meters with lime wash (slaked lime 1kg + zinc sulfate 50g per 10L)",
      "Apply copper oxychloride paste over active fissures to prevent fungal entry",
    ],
    organicControl: [
      "Plant protective shade trees on south-west plantation borders",
      "Wrap trunk lower section with dry fronds or arecanut sheaths during peak summer",
    ],
    yoloBoxes: [
      { label: "StemCracking (87.9%)", confidence: 87.9, top: "35%", left: "32%", width: "22%", height: "45%", color: "#f59e0b" },
    ],
    modelBreakdown: { cnn: 97.2, vit: 87.9, yolo: 85.8 },
    processedAt: new Date().toISOString(),
  },
  {
    id: "demo-011",
    disease: "YellowLeaf",
    confidence: 91.2,
    stage: "Progressive Chlorosis",
    severity: "Moderate",
    description: "Progressive chlorosis and yellowing of foliage from lower to upper fronds, stunting nut development.",
    treatments: [
      "Soil application of micronutrient mixture (Zn, B, Mg) twice a year",
      "Regulate field drainage to eliminate waterlogging around root crowns",
    ],
    organicControl: [
      "Green manuring with Sunn hemp or Cowpea in palm interspaces",
      "Apply organic compost and bio-fertilizers (Azospirillum + PSB)",
    ],
    yoloBoxes: [
      { label: "YellowLeaf (91.2%)", confidence: 91.2, top: "15%", left: "20%", width: "40%", height: "35%", color: "#f59e0b" },
    ],
    modelBreakdown: { cnn: 98.4, vit: 91.2, yolo: 89.5 },
    processedAt: new Date().toISOString(),
  },
]

export function isDemoMode(): boolean {
  return import.meta.env.VITE_DEMO_MODE === "true"
}

export async function fetchSpecimens(): Promise<
  Array<{ id: string; title: string; severity: string; previewUrl: string }>
> {
  const demoFallback = [
    { id: "fruit_rot", title: "Fruit Rot (Koleroga)", severity: "Severe", previewUrl: "" },
    { id: "anthracnose", title: "Anthracnose Leaf/Nut", severity: "Moderate", previewUrl: "" },
    { id: "sooty_mold", title: "Sooty Mold Complex", severity: "Mild", previewUrl: "" },
    { id: "nut_cracking", title: "Nut Cracking Disorder", severity: "Moderate", previewUrl: "" },
    { id: "healthy", title: "Healthy Palm Vigor", severity: "Healthy", previewUrl: "" },
    { id: "non_areca", title: "OOD Non-Areca Gate Test", severity: "Gatekeeper", previewUrl: "" },
  ]

  return apiRequest("/specimens", {
    method: "GET",
    mockFallbackData: isDemoMode() ? demoFallback : undefined,
    forceReal: !isDemoMode(),
  })
}

export async function submitAnalysis(
  fileOrUrl: File | string,
  options: { signal?: AbortSignal; blockId?: string; specimenId?: string } = {}
): Promise<InferenceJobSubmitResponse> {
  const fileName = typeof fileOrUrl === "string" ? "sample-image.jpg" : fileOrUrl.name
  const mockJobId = "demo-job-" + Date.now() + "-" + Math.random().toString(36).substring(2, 7)

  let mockSubmitRes: InferenceJobSubmitResponse | undefined = undefined
  if (isDemoMode()) {
    mockJobsStore.set(mockJobId, {
      job_id: mockJobId,
      createdAt: Date.now(),
      fileName,
    })
    mockSubmitRes = {
      job_id: mockJobId,
      status: "queued",
      estimatedTimeSeconds: 3,
    }
  }

  const blockId = options.blockId || "block-a1"

  // Create payload for real HTTP upload
  let body: FormData | string
  if (options.specimenId) {
    body = JSON.stringify({ specimenId: options.specimenId, blockId })
  } else if (typeof fileOrUrl !== "string") {
    const formData = new FormData()
    formData.append("image", fileOrUrl)
    formData.append("blockId", blockId)
    body = formData
  } else if (fileOrUrl.startsWith("specimen:")) {
    body = JSON.stringify({ specimenId: fileOrUrl.slice("specimen:".length), blockId })
  } else if (fileOrUrl.startsWith("blob:") || fileOrUrl.startsWith("data:") || fileOrUrl.startsWith("/")) {
    try {
      const resp = await fetch(fileOrUrl)
      const blob = await resp.blob()
      const formData = new FormData()
      formData.append("image", blob, "uploaded-sample.jpg")
      formData.append("blockId", blockId)
      body = formData
    } catch {
      body = JSON.stringify({ imageUrl: fileOrUrl, blockId })
    }
  } else {
    body = JSON.stringify({ imageUrl: fileOrUrl, blockId })
  }

  return apiRequest<InferenceJobSubmitResponse>("/detect", {
    method: "POST",
    body,
    signal: options.signal,
    mockFallbackData: mockSubmitRes,
    forceReal: !isDemoMode(),
  })
}

export async function getJobStatus(
  jobId: string,
  options: { signal?: AbortSignal } = {}
): Promise<InferenceJobStatusResponse> {
  let mockStatusRes: InferenceJobStatusResponse | undefined = undefined

  if (isDemoMode()) {
    const stored = mockJobsStore.get(jobId)
    const elapsed = stored ? Date.now() - stored.createdAt : 3000

    let status: "queued" | "processing" | "done" | "failed" = "queued"
    let progressPercent = 15

    if (elapsed >= 2500) {
      status = "done"
      progressPercent = 100
    } else if (elapsed >= 800) {
      status = "processing"
      progressPercent = Math.min(85, Math.floor(25 + ((elapsed - 800) / 1700) * 60))
    }

    function simpleHash(str: string): number {
      let hash = 0
      for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
      }
      return Math.abs(hash)
    }

    const selectedDiagnosis = MOCK_DISEASE_PROFILES[
      stored ? simpleHash(stored.job_id) % MOCK_DISEASE_PROFILES.length : 0
    ]

    mockStatusRes = {
      job_id: jobId,
      status,
      progressPercent,
      result: status === "done" ? selectedDiagnosis : undefined,
    }
  }

  return apiRequest<InferenceJobStatusResponse>(`/jobs/${jobId}`, {
    method: "GET",
    signal: options.signal,
    mockFallbackData: mockStatusRes,
    forceReal: !isDemoMode(),
  })
}

export async function cancelJob(jobId: string): Promise<void> {
  mockJobsStore.delete(jobId)
  try {
    await apiRequest<void>(`/jobs/${jobId}/cancel`, {
      method: "POST",
      mockFallbackData: undefined,
      forceReal: !isDemoMode(),
    })
  } catch {
    // Ignore offline cancel errors
  }
}

