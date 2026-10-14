import { apiRequest } from "./apiClient"
import { PlantationSummaryResponse, PlantationBlockData } from "../types/api"

export const SAMPLE_DEMO_BLOCKS: PlantationBlockData[] = [
  { id: "Block A", trees: 2310, diseasedTrees: 531, health: 77, status: "Severe Anthracnose", severity: "Severe", color: "var(--severity-severe)", areaAcres: 4.5, spacing: "2.7m x 2.7m", soilType: "Laterite Red" },
  { id: "Block B", trees: 2560, diseasedTrees: 412, health: 84, status: "Moderate Koleroga", severity: "Moderate", color: "var(--severity-moderate)", areaAcres: 5.0, spacing: "2.7m x 2.7m", soilType: "Clay Loam" },
  { id: "Block C", trees: 2890, diseasedTrees: 680, health: 76, status: "High Anthracnose", severity: "Critical", color: "var(--severity-critical)", areaAcres: 5.6, spacing: "2.7m x 2.7m", soilType: "Red Sandy Loam" },
  { id: "Block D", trees: 2120, diseasedTrees: 280, health: 87, status: "Mild Nut Cracking", severity: "Mild", color: "var(--severity-mild)", areaAcres: 4.2, spacing: "2.7m x 2.7m", soilType: "Alluvial" },
  { id: "Block E", trees: 2660, diseasedTrees: 325, health: 88, status: "Optimal Condition", severity: "Healthy", color: "var(--severity-healthy)", areaAcres: 5.2, spacing: "2.7m x 2.7m", soilType: "Laterite Red" },
]

export async function fetchPlantationSummary(): Promise<PlantationSummaryResponse> {
  const blocks = SAMPLE_DEMO_BLOCKS
  const totalTrees = blocks.reduce((acc, b) => acc + b.trees, 0)
  const totalAcres = Number(blocks.reduce((acc, b) => acc + b.areaAcres, 0).toFixed(1))
  const diseasedTrees = blocks.reduce((acc, b) => acc + b.diseasedTrees, 0)
  const healthyTrees = totalTrees - diseasedTrees
  const overallHealthScore = blocks.length > 0 && totalTrees > 0 ? Math.round((healthyTrees / totalTrees) * 100) : null

  const mockSummary: PlantationSummaryResponse = {
    blocks,
    totalTrees,
    totalAcres,
    healthyTrees,
    diseasedTrees,
    overallHealthScore,
  }

  return apiRequest<PlantationSummaryResponse>("/plantation/summary", {
    method: "GET",
    mockFallbackData: mockSummary,
  })
}

export function getSeverityColor(sev: PlantationBlockData["severity"]): string {
  switch (sev) {
    case "Healthy": return "var(--severity-healthy)"
    case "Mild": return "var(--severity-mild)"
    case "Moderate": return "var(--severity-moderate)"
    case "Severe": return "var(--severity-severe)"
    case "Critical": return "var(--severity-critical)"
    default: return "var(--severity-healthy)"
  }
}

export async function addPlantationBlockApi(
  data: Omit<PlantationBlockData, "health" | "color">
): Promise<PlantationBlockData> {
  const healthy = Math.max(0, data.trees - data.diseasedTrees)
  const health = data.trees > 0 ? Math.round((healthy / data.trees) * 100) : 100

  const newBlock: PlantationBlockData = {
    ...data,
    health,
    color: getSeverityColor(data.severity),
  }

  return apiRequest<PlantationBlockData>("/plantation/blocks", {
    method: "POST",
    body: JSON.stringify(data),
    mockFallbackData: newBlock,
  })
}

export async function deletePlantationBlockApi(id: string): Promise<void> {
  return apiRequest<void>(`/plantation/blocks/${id}`, {
    method: "DELETE",
    mockFallbackData: undefined,
  })
}
