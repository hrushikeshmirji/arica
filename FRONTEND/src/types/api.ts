/**
 * PROVISIONAL CONTRACT - SUBJECT TO RECONCILIATION WITH BACKEND & ML MODEL SERVICES
 * 
 * Note: These TypeScript interfaces define the expected request/response contracts for ArecaVision AI.
 * Any updates to these definitions should be recorded in `docs/SCHEMA_CHANGELOG.md`.
 */

// Generic API Envelope
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
  timestamp: string
}

// Authentication Models
export interface UserTokenPayload {
  id: string
  username: string
  name: string
  email: string
  role: "admin" | "agronomist" | "farmer"
  avatarUrl?: string
}

export interface LoginRequest {
  username?: string
  email: string
  password?: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  name: string
}

export interface AdminUserItem {
  id: string
  username: string
  email: string
  name: string
  role: 'admin' | 'agronomist' | 'farmer'
  createdAt: string
  lastLogin: string | null
  scanCount: number
}

export interface AuthResponse {
  user: UserTokenPayload
  token?: string // Present when using Bearer auth token strategy
  expiresIn?: number
}

export interface RefreshTokenRequest {
  refreshToken?: string
}

// ML Model Inference Models
export interface YoloBoundingBox {
  label: string
  confidence: number
  top: string
  left: string
  width: string
  height: string
  color: string
}

export interface ModelBreakdown {
  cnn: number
  vit: number
  yolo: number
}

export interface TissueMorphometrics {
  healthyPct: number
  chloroticPct: number
  necroticPct: number
  lesionCoveragePct: number
}

export interface DifferentialItem {
  disease: string
  probability: number
}

export interface StageTimingsMs {
  gatekeeperMs: number
  yoloMs: number
  vitTtaMs: number
  xaiRolloutMs: number
  totalMs: number
}

export interface FieldSpecimenItem {
  id: string
  title: string
  severity: string
  previewUrl: string
}

export interface ModelInferenceResponse {
  id: string
  disease: string
  confidence: number
  stage: string
  severity: "Healthy" | "Mild" | "Moderate" | "Severe" | "Critical" | "Non-Arecanut" | "Uncertain"
  description: string
  treatments: string[]
  organicControl: string[]
  yoloBoxes: YoloBoundingBox[]
  saliencyBox?: {
    label: string
    top: string
    left: string
    width: string
    height: string
    color: string
  } | null
  modelBreakdown: ModelBreakdown
  tissueMorphometrics?: TissueMorphometrics
  differentialDiagnosis?: DifferentialItem[]
  stageTimingsMs?: StageTimingsMs
  retakePhoto?: {
    en: string
    kn: string
    hi: string
  }
  consultAgronomist?: {
    en: string
    kn: string
    hi: string
  }
  blockId?: string
  blockName?: string
  processedAt: string
  featureMapUrl?: string
  attentionMapUrl?: string
  gradCamUrl?: string
  gateScore?: number
  isExperimentalClass?: boolean
  isValidatedClass?: boolean
  geminiVerification?: {
    available: boolean
    provider?: string
    verifiedDisease?: string
    confidence?: number
    observations?: string
    recommendedAction?: string
    isArecanut?: boolean
    agreesWithLocalModel?: boolean
  } | null
}

export interface InferenceJobSubmitResponse {
  job_id: string
  status: "queued" | "processing"
  estimatedTimeSeconds: number
}

export interface InferenceJobStatusResponse {
  job_id: string
  status: "queued" | "processing" | "done" | "failed"
  progressPercent: number
  currentStage?: string
  result?: ModelInferenceResponse
  error?: string
}

// Dashboard & Analytics Models
export interface KPIStatsResponse {
  totalTrees: number
  healthyTrees: number
  diseasedTrees: number
  aiAccuracy: number | null
  todayScansCount: number
  pendingAlertsCount: number
  overallHealthScore: number | null
  dataSource?: "recorded" | "demo_preview"
  dataNote?: string | null
}

export interface DiseaseTrendItem {
  date: string
  anthracnose: number
  koleroga?: number
  fruitRot?: number
  nutCracking: number
  sootyMold: number
}

export interface DiseaseDistributionItem {
  name: string
  percentage: number
  color: string
}

// Plantation Map & Block Models
export interface PlantationBlockData {
  id: string
  trees: number
  diseasedTrees: number
  health: number // 0 - 100
  status: string
  severity: "Healthy" | "Mild" | "Moderate" | "Severe" | "Critical"
  color: string
  areaAcres: number
  spacing: string
  soilType: string
}

export interface PlantationSummaryResponse {
  blocks: PlantationBlockData[]
  totalTrees: number
  totalAcres: number
  healthyTrees: number
  diseasedTrees: number
  overallHealthScore: number | null
}

// Notification & Alert Models
// NOTE: NotificationResponse wraps an array of NotificationItemData items along with aggregated unreadCount metadata.
export interface NotificationItemData {
  id: string
  type: "critical" | "warning" | "info"
  title: string
  msg: string
  time: string
  unread: boolean
  blockId?: string
}

export interface NotificationResponse {
  notifications: NotificationItemData[]
  unreadCount: number
}

// Weather Proxy Models (Backend Proxied)
export interface WeatherForecastItem {
  day: string
  tempMax: number
  tempMin: number
  condition: string
  rainProb: number
}

export interface WeatherApiResponse {
  city: string
  region: string
  temperature: number
  condition: string
  humidity: number
  windSpeed: number
  rainfall: number
  uvIndex: number
  sunrise: string
  sunset: string
  lastUpdated: string
  riskLevel: "Low" | "Moderate" | "High"
  forecast: WeatherForecastItem[]
  isLive?: boolean
  dataSource?: string
}

// Export & Report Models
export interface ReportGenerateRequest {
  type: "summary" | "detailed" | "plantation"
  timeframe: string
  format: "pdf" | "csv"
}

export interface ReportExportBlob {
  format: "pdf" | "csv"
  filename: string
  blob: Blob
}

// AI Assistant Models (Query-Cached Conversation)
export interface ChatMessageItem {
  id: string
  sender: "user" | "ai"
  text: string
  timestamp: string
  suggestions?: string[]
}

export interface AssistantChatRequest {
  message: string
  context?: {
    blockId?: string
    scanId?: string
  }
}

export interface AssistantChatResponse {
  reply: string
  suggestedActions?: string[]
  suggestions?: string[]
  timestamp: string
}
