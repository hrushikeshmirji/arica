import { apiRequest } from "./apiClient"
import { KPIStatsResponse, DiseaseTrendItem, DiseaseDistributionItem } from "../types/api"

export async function fetchKPIStats(): Promise<KPIStatsResponse> {
  const mockStats: KPIStatsResponse = {
    totalTrees: 12540,
    healthyTrees: 10312,
    diseasedTrees: 2228,
    aiAccuracy: null,
    todayScansCount: 57,
    pendingAlertsCount: 2,
    overallHealthScore: 82,
  }

  return apiRequest<KPIStatsResponse>("/dashboard/kpi", {
    method: "GET",
    mockFallbackData: mockStats,
  })
}

export async function fetchDiseaseTrends(): Promise<DiseaseTrendItem[]> {
  const mockTrends: DiseaseTrendItem[] = [
    { date: "1 May", anthracnose: 42, koleroga: 12, fruitRot: 12, nutCracking: 8, sootyMold: 5 },
    { date: "7 May", anthracnose: 58, koleroga: 18, fruitRot: 18, nutCracking: 10, sootyMold: 6 },
    { date: "14 May", anthracnose: 75, koleroga: 35, fruitRot: 35, nutCracking: 12, sootyMold: 8 },
    { date: "21 May", anthracnose: 92, koleroga: 62, fruitRot: 62, nutCracking: 14, sootyMold: 11 },
    { date: "28 May", anthracnose: 110, koleroga: 88, fruitRot: 88, nutCracking: 15, sootyMold: 14 },
  ]

  return apiRequest<DiseaseTrendItem[]>("/dashboard/trends", {
    method: "GET",
    mockFallbackData: mockTrends,
  })
}

export async function fetchDiseaseDistribution(): Promise<DiseaseDistributionItem[]> {
  const mockDist: DiseaseDistributionItem[] = [
    { name: "Anthracnose", percentage: 52, color: "var(--severity-severe)" },
    { name: "Fruit Rot / Koleroga", percentage: 28, color: "var(--severity-critical)" },
    { name: "Nut Cracking", percentage: 12, color: "var(--severity-moderate)" },
    { name: "Sooty Mold", percentage: 8, color: "var(--severity-mild)" },
  ]

  return apiRequest<DiseaseDistributionItem[]>("/dashboard/distribution", {
    method: "GET",
    mockFallbackData: mockDist,
  })
}

export interface AnalyticsOverviewResponse {
  totalTrees: number
  totalAcres: number
  estimatedYieldTons: number
  diseaseControlRate: number
  activeBlocksCount: number
  totalScansRecorded: number
  monthlyYield: Array<{
    month: string
    yield: number
    diseaseRate: number
  }>
}

export async function fetchAnalyticsOverview(): Promise<AnalyticsOverviewResponse> {
  const mockFallback: AnalyticsOverviewResponse = {
    totalTrees: 12540,
    totalAcres: 27.9,
    estimatedYieldTons: 36.7,
    diseaseControlRate: 94.2,
    activeBlocksCount: 8,
    totalScansRecorded: 12,
    monthlyYield: [
      { month: "Jan", yield: 4.4, diseaseRate: 8.5 },
      { month: "Feb", yield: 4.8, diseaseRate: 7.8 },
      { month: "Mar", yield: 5.5, diseaseRate: 6.2 },
      { month: "Apr", yield: 6.6, diseaseRate: 5.4 },
      { month: "May", yield: 8.1, diseaseRate: 4.8 },
      { month: "Jun", yield: 7.3, diseaseRate: 9.2 },
    ],
  }

  return apiRequest<AnalyticsOverviewResponse>("/analytics/overview", {
    method: "GET",
    mockFallbackData: mockFallback,
  })
}

