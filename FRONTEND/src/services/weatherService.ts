import { apiRequest } from "./apiClient"
import { WeatherApiResponse } from "../types/api"

export type WeatherState =
  | { status: "UNREQUESTED" }
  | { status: "DENIED"; message: string }
  | { status: "LOADING" }
  | { status: "ERROR"; message: string }
  | { status: "POPULATED"; data: WeatherApiResponse }

const MOCK_WEATHER_DATA: WeatherApiResponse = {
  city: "Madikeri Plantation",
  region: "Kodagu, Karnataka",
  temperature: 24,
  condition: "Light Rain",
  humidity: 91,
  windSpeed: 12,
  rainfall: 18,
  uvIndex: 6,
  sunrise: "06:12 AM",
  sunset: "06:48 PM",
  lastUpdated: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  riskLevel: "High",
  forecast: [
    { day: "Mon", tempMax: 26, tempMin: 21, condition: "Heavy Rain", rainProb: 85 },
    { day: "Tue", tempMax: 25, tempMin: 20, condition: "Thunderstorm", rainProb: 90 },
    { day: "Wed", tempMax: 27, tempMin: 22, condition: "Moderate Rain", rainProb: 60 },
    { day: "Thu", tempMax: 28, tempMin: 22, condition: "Partly Cloudy", rainProb: 35 },
    { day: "Fri", tempMax: 29, tempMin: 23, condition: "Sunny Spells", rainProb: 20 },
  ],
}

/**
 * Weather Service Call: Proxied through Backend Endpoint (/api/v1/weather)
 */
export async function fetchWeatherFromBackend(city?: string, lat?: number, lon?: number): Promise<WeatherApiResponse> {
  const queryParams = new URLSearchParams()
  if (city) queryParams.set("city", city)
  if (lat !== undefined && lon !== undefined) {
    queryParams.set("lat", lat.toString())
    queryParams.set("lon", lon.toString())
  }

  const endpoint = `/weather${queryParams.toString() ? `?${queryParams.toString()}` : ""}`

  return apiRequest<WeatherApiResponse>(endpoint, {
    method: "GET",
    mockFallbackData: {
      ...MOCK_WEATHER_DATA,
      city: city || MOCK_WEATHER_DATA.city,
    },
  })
}

export async function searchWeatherByCity(cityName: string): Promise<WeatherState> {
  if (!cityName.trim()) {
    return { status: "UNREQUESTED" }
  }
  try {
    const data = await fetchWeatherFromBackend(cityName)
    return { status: "POPULATED", data }
  } catch (e) {
    const message = e instanceof Error ? e.message : `Failed to fetch weather for ${cityName}`
    return { status: "ERROR", message }
  }
}

export function getCurrentLocationWeather(): Promise<WeatherState> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      fetchWeatherFromBackend("Madikeri Plantation")
        .then((data) => resolve({ status: "POPULATED", data }))
        .catch(() => resolve({ status: "ERROR", message: "Browser does not support geolocation." }))
      return
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const data = await fetchWeatherFromBackend(undefined, pos.coords.latitude, pos.coords.longitude)
          resolve({ status: "POPULATED", data })
        } catch (e) {
          const message = e instanceof Error ? e.message : "Failed to fetch weather for coordinates."
          resolve({ status: "ERROR", message })
        }
      },
      async (err) => {
        if (err.code === err.PERMISSION_DENIED) {
          resolve({ status: "DENIED", message: "Location permission denied. Search your plantation city above." })
        } else {
          try {
            const defaultData = await fetchWeatherFromBackend("Madikeri Plantation")
            resolve({ status: "POPULATED", data: defaultData })
          } catch {
            resolve({ status: "ERROR", message: "Geolocation position unavailable. Search a city manually above." })
          }
        }
      },
      { timeout: 7000, enableHighAccuracy: true, maximumAge: 60000 }
    )
  })
}

export interface RiskForecastData {
  compositeIndex: number
  overallSeverity: "Healthy" | "Moderate" | "Severe" | "Critical"
  advisoryHeadline: string
  advisoryAction: string
  pathogenMetrics: {
    koleroga: { name: string; riskScore: number; status: string; incubationDays: number }
    anthracnose: { name: string; riskScore: number; status: string; incubationDays: number }
    nutCracking: { name: string; riskScore: number; status: string; incubationDays: number }
  }
  trajectory: Array<{
    day: string
    date: string
    kolerogaRisk: number
    anthracnoseRisk: number
    nutCrackingRisk: number
    rainProbability: number
  }>
  blockVulnerability: Array<{
    blockId: string
    name: string
    trees: number
    healthScore: number
    vulnerabilityScore: number
    primaryThreat: string
    status: string
    severity: string
  }>
  spraySchedule: {
    suitableWindow: string
    recommendedChemical: string
    organicAlternative: string
    withholdingPeriodDays: number
  }
  lastUpdated: string
}

export const MOCK_RISK_FORECAST_DATA: RiskForecastData = {
  compositeIndex: 78,
  overallSeverity: "Severe",
  advisoryHeadline: "High Koleroga & Microclimate Fungal Infection Warning",
  advisoryAction:
    "Relative humidity (>91%) and forecasted monsoonal downpours indicate rapid Phytophthora meadii and Colletotrichum sporulation. Prophylactic fungicide application recommended within 24–48 hours.",
  pathogenMetrics: {
    koleroga: {
      name: "Fruit Rot / Koleroga",
      riskScore: 84,
      status: "Critical",
      incubationDays: 3,
    },
    anthracnose: {
      name: "Anthracnose Lesions",
      riskScore: 58,
      status: "Severe",
      incubationDays: 5,
    },
    nutCracking: {
      name: "Nut Cracking Disorder",
      riskScore: 32,
      status: "Moderate",
      incubationDays: 8,
    },
  },
  trajectory: [
    { day: "Today", date: "Oct 10", kolerogaRisk: 74, anthracnoseRisk: 52, nutCrackingRisk: 28, rainProbability: 85 },
    { day: "Sun", date: "Oct 11", kolerogaRisk: 86, anthracnoseRisk: 61, nutCrackingRisk: 30, rainProbability: 90 },
    { day: "Mon", date: "Oct 12", kolerogaRisk: 89, anthracnoseRisk: 64, nutCrackingRisk: 34, rainProbability: 80 },
    { day: "Tue", date: "Oct 13", kolerogaRisk: 78, anthracnoseRisk: 55, nutCrackingRisk: 31, rainProbability: 60 },
    { day: "Wed", date: "Oct 14", kolerogaRisk: 62, anthracnoseRisk: 48, nutCrackingRisk: 26, rainProbability: 40 },
    { day: "Thu", date: "Oct 15", kolerogaRisk: 48, anthracnoseRisk: 38, nutCrackingRisk: 22, rainProbability: 25 },
    { day: "Fri", date: "Oct 16", kolerogaRisk: 42, anthracnoseRisk: 32, nutCrackingRisk: 20, rainProbability: 20 },
  ],
  blockVulnerability: [
    {
      blockId: "Block A",
      name: "Block A (4.5 Acres)",
      trees: 2310,
      healthScore: 77,
      vulnerabilityScore: 82,
      primaryThreat: "Fruit Rot / Koleroga",
      status: "High Outbreak Risk",
      severity: "Critical",
    },
    {
      blockId: "Block B",
      name: "Block B (5.0 Acres)",
      trees: 2560,
      healthScore: 84,
      vulnerabilityScore: 68,
      primaryThreat: "Anthracnose Lesions",
      status: "Active Monitoring",
      severity: "Severe",
    },
    {
      blockId: "Block C",
      name: "Block C (4.0 Acres)",
      trees: 2048,
      healthScore: 92,
      vulnerabilityScore: 45,
      primaryThreat: "Leaf Spot Complex",
      status: "Moderate Alert",
      severity: "Moderate",
    },
    {
      blockId: "Block D",
      name: "Block D (4.2 Acres)",
      trees: 2120,
      healthScore: 87,
      vulnerabilityScore: 38,
      primaryThreat: "Nut Cracking Disorder",
      status: "Optimal Resistance",
      severity: "Healthy",
    },
  ],
  spraySchedule: {
    suitableWindow: "Within next 24–36 hours (Dry morning hours 06:30 AM – 10:30 AM before showers)",
    recommendedChemical: "1% Bordeaux mixture (1 kg CuSO4 + 1 kg Quicklime in 100 L water) with Rosin soap sticker (100g)",
    organicAlternative: "Trichoderma harzianum or Pseudomonas fluorescens biocontrol spray (20g/L)",
    withholdingPeriodDays: 14,
  },
  lastUpdated: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
}

export async function fetchRiskForecast(city?: string): Promise<RiskForecastData> {
  const query = city ? `?city=${encodeURIComponent(city)}` : ""
  return apiRequest<RiskForecastData>(`/risk/forecast${query}`, {
    method: "GET",
    mockFallbackData: {
      ...MOCK_RISK_FORECAST_DATA,
      lastUpdated: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  })
}
