import { useState, useRef, useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts"
import {
  TreePine,
  Heart,
  AlertTriangle,
  Cpu,
  ScanLine,
  Bell,
  TrendingUp,
  TrendingDown,
  Camera,
  Image as ImageIcon,
  FolderOpen,
  Upload,
  ChevronRight,
  Check,
  Download,
  Thermometer,
  Droplets,
  Wind,
  CloudRain,
  Sun,
  ShieldAlert,
  Plane,
  X,
  FileText,
  Printer,
  MapPin,
  Search,
  RefreshCw,
  AlertCircle,
  Map,
  Calculator,
} from "lucide-react"
import { useScanHistory } from "../contexts/ScanHistoryContext"
import { useNotifications } from "../contexts/NotificationContext"
import { usePlantation } from "../contexts/PlantationContext"
import { submitAnalysis, getJobStatus } from "../services/detectionService"
import { fetchDiseaseTrends } from "../services/dashboardService"
import { ModelInferenceResponse, DiseaseTrendItem } from "../types/api"
import { useWeather } from "../contexts/WeatherContext"
import { useLanguage } from "../contexts/LanguageContext"
import { useFocusTrap } from "../hooks/useFocusTrap"
import { THEME_TOKENS } from "../theme/tokens"
import LiveCameraModal from "../components/LiveCameraModal"
import TreatmentCalculatorModal from "../components/TreatmentCalculatorModal"
import { fetchRiskForecast, RiskForecastData } from "../services/weatherService"
const trendLegend = [
  { label: "Anthracnose", color: THEME_TOKENS.charts.lines.anthracnose },
  { label: "Fruit Rot", color: THEME_TOKENS.charts.lines.fruitRot },
  { label: "Nut Cracking", color: THEME_TOKENS.charts.lines.nutCracking },
  { label: "Sooty Mold", color: THEME_TOKENS.charts.lines.sootyMold },
]

interface TooltipPayloadItem {
  name: string
  value: number | string
  color?: string
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayloadItem[]
  label?: string
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (active && payload?.length) {
    return (
      <div className="bg-card rounded-lg shadow-lg border border-border px-3 py-2 text-xs">
        <p className="font-semibold text-foreground mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.name} style={{ color: p.color }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { t } = useLanguage()
  const { scans, addScan } = useScanHistory()
  const { notifications, unreadCount, addNotification } = useNotifications()
  const { blocks, totalTrees, healthyTrees, diseasedTrees, topDiseasedBlocks } = usePlantation()

  const [isScanning, setIsScanning] = useState(false)
  const [scanResult, setScanResult] = useState<ModelInferenceResponse | null>(null)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [scanError, setScanError] = useState<string | null>(null)
  const [isCameraModalOpen, setIsCameraModalOpen] = useState<boolean>(false)
  const [isDragging, setIsDragging] = useState<boolean>(false)

  // Report Modal State
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const reportModalRef = useFocusTrap<HTMLDivElement>(reportModalOpen, () => setReportModalOpen(false))

  // Shared weather state from context (single fetch, shared with Layout + Weather page)
  const { weatherState, refreshLocationWeather, searchCity: searchWeatherCity } = useWeather()
  const [weatherSearch, setWeatherSearch] = useState("")

  const fileInputRef = useRef<HTMLInputElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const [riskForecast, setRiskForecast] = useState<RiskForecastData | null>(null)
  const [showCalculator, setShowCalculator] = useState(false)
  const [calculatorDisease, setCalculatorDisease] = useState("koleroga")
  const [isAlertDismissed, setIsAlertDismissed] = useState(false)

  useEffect(() => {
    fetchRiskForecast()
      .then((res) => {
        if (res) setRiskForecast(res)
      })
      .catch(() => undefined)
  }, [])

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const handleEnableLiveLocation = async () => {
    await refreshLocationWeather()
  }

  const handleWeatherSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!weatherSearch.trim()) return
    await searchWeatherCity(weatherSearch.trim())
  }

  // Trigger Image Scan Pipeline
  const handleProcessScan = async (fileOrUrl: File | string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    const currentAbort = new AbortController()
    abortControllerRef.current = currentAbort

    if (typeof fileOrUrl !== "string") {
      const reader = new FileReader()
      reader.onload = (e) => {
        if (typeof e.target?.result === "string") {
          setSelectedImage(e.target.result)
        }
      }
      reader.readAsDataURL(fileOrUrl)
    } else {
      setSelectedImage(fileOrUrl)
    }
    setIsScanning(true)
    setScanResult(null)
    setScanError(null)

    try {
      const submitRes = await submitAnalysis(fileOrUrl, { signal: currentAbort.signal })
      if (currentAbort.signal.aborted) return

      let statusRes = await getJobStatus(submitRes.job_id, { signal: currentAbort.signal })

      while (statusRes.status !== "done" && statusRes.status !== "failed") {
        if (currentAbort.signal.aborted) return
        await new Promise((r) => setTimeout(r, 500))
        if (currentAbort.signal.aborted) return
        statusRes = await getJobStatus(submitRes.job_id, { signal: currentAbort.signal })
      }

      if (currentAbort.signal.aborted) return

      if (statusRes.status === "done" && statusRes.result) {
        const diag: ModelInferenceResponse = statusRes.result
        setScanResult(diag)

        const normalizedConf = diag.confidence <= 1.0 ? Math.round(diag.confidence * 1000) / 10 : Math.round(diag.confidence * 10) / 10

        // Save to Scan History only for valid Arecanut specimens
        if (diag.disease !== "Not an Arecanut image" && diag.severity !== "Non-Arecanut" && diag.stage !== "Gatekeeper Uncertain") {
          addScan({
            title: "Dashboard Quick Analysis",
            disease: diag.disease,
            confidence: normalizedConf,
            stage: diag.stage,
            severity: diag.severity,
            imageUrl: selectedImage || (typeof fileOrUrl === "string" ? fileOrUrl : ""),
            location: weatherState.status === "POPULATED" ? `${weatherState.data.city}, Plantation` : "Local Plantation",
            temp: weatherState.status === "POPULATED" ? `${weatherState.data.temperature}°C` : "—",
            weatherCondition: weatherState.status === "POPULATED" ? weatherState.data.condition : "—",
            recommendedActions: diag.treatments,
          })
        }
      } else if (statusRes.status === "failed") {
        console.error("Scan failed with status 'failed':", statusRes.error)
        const errorMsg = statusRes.error || "The scan could not be completed."
        setScanError(errorMsg)
        addNotification({
          type: "critical",
          title: "Scan Failed",
          msg: errorMsg,
        })
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        return
      }
      console.error("Scan submission/processing failed:", err)
      const errorMsg = err instanceof Error ? err.message : "Something went wrong while submitting the scan."
      setScanError(errorMsg)
      addNotification({
        type: "critical",
        title: "Scan Failed",
        msg: errorMsg,
      })
    } finally {
      if (!currentAbort.signal.aborted) {
        setIsScanning(false)
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleProcessScan(e.target.files[0])
    }
  }

  // Global Clipboard Paste Handler on Dashboard (Ctrl+V for internet images or URLs)
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (!e.clipboardData) return

      // 1. Image file in clipboard
      const items = Array.from(e.clipboardData.items)
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile()
          if (file) {
            e.preventDefault()
            const ext = file.type.split("/")[1] || "png"
            const namedFile = new File([file], `internet_pasted_${Date.now()}.${ext}`, {
              type: file.type || "image/png",
            })
            handleProcessScan(namedFile)
            return
          }
        }
      }

      // 2. Image URL / data URI text
      const pastedText = e.clipboardData.getData("text").trim()
      if (
        pastedText.startsWith("data:image/") ||
        pastedText.match(/^https?:\/\/.*\.(jpe?g|png|webp|bmp|gif|tif|tiff)(\?.*)?$/i) ||
        pastedText.match(/^https?:\/\/.*(images|photos|media|googleusercontent|wikimedia|agritech|tnsau|cpcri).*/i)
      ) {
        e.preventDefault()
        handleProcessScan(pastedText)
        return
      }
    }

    window.addEventListener("paste", handlePaste)
    return () => window.removeEventListener("paste", handlePaste)
  }, [weatherState])

  const validScans = scans.filter(
    (s) => s.disease !== "Not an Arecanut image" && s.severity !== "Non-Arecanut"
  )
  const confidenceValues = validScans
    .map((scan) => Number(scan.confidence))
    .filter((confidence) => Number.isFinite(confidence))
  const avgConfidence = confidenceValues.length > 0
    ? (confidenceValues.reduce((total, confidence) => total + confidence, 0) / confidenceValues.length).toFixed(1)
    : "—"

  const kpiCards = [
    {
      label: t("dash.kpi.total_trees", "Total Trees"),
      value: (totalTrees > 0 ? totalTrees : 12540).toLocaleString(),
      change: "—",
      positive: true,
      sub: t("dash.kpi.sub_monitored", "monitored"),
      icon: TreePine,
      iconBg: "bg-primary/10",
      iconColor: "text-primary",
      onClick: () => navigate("/map"),
    },
    {
      label: t("dash.kpi.healthy_trees", "Healthy Trees"),
      value: (healthyTrees > 0 ? healthyTrees : 10312).toLocaleString(),
      change: "—",
      positive: true,
      sub: t("dash.kpi.sub_healthy", "healthy"),
      icon: Heart,
      iconBg: "bg-primary/10",
      iconColor: "text-primary",
      onClick: () => navigate("/map"),
    },
    {
      label: t("dash.kpi.diseased_trees", "Diseased Trees"),
      value: (diseasedTrees > 0 ? diseasedTrees : 2228).toLocaleString(),
      change: "—",
      positive: false,
      sub: t("dash.kpi.sub_under_care", "under care"),
      icon: AlertTriangle,
      iconBg: "bg-danger/10",
      iconColor: "text-danger",
      onClick: () => navigate("/diseases"),
    },
    {
      label: t("dash.kpi.ai_accuracy", "Average Scan Confidence"),
      value: avgConfidence === "—" ? avgConfidence : `${avgConfidence}%`,
      change: "—",
      positive: false,
      sub: t("dash.kpi.sub_ensemble", "scan confidence; not accuracy"),
      icon: Cpu,
      iconBg: "bg-accent/10",
      iconColor: "text-accent",
      onClick: () => navigate("/research"),
    },
    {
      label: t("dash.kpi.total_scans", "Total Scans"),
      value: String(validScans.length),
      change: "—",
      positive: true,
      sub: t("dash.kpi.sub_processed", "available records"),
      icon: ScanLine,
      iconBg: "bg-primary/10",
      iconColor: "text-primary",
      onClick: () => navigate("/scans"),
    },
    {
      label: t("dash.kpi.pending_alerts", "Pending Alerts"),
      value: String(unreadCount),
      change: unreadCount > 0 ? t("dash.kpi.action_required", "Action Required") : t("dash.kpi.all_clear", "All Clear"),
      positive: unreadCount === 0,
      sub: "",
      icon: Bell,
      iconBg: unreadCount > 0 ? "bg-danger/10" : "bg-primary/10",
      iconColor: unreadCount > 0 ? "text-danger" : "text-primary",
      onClick: () => navigate("/notifications"),
    },
  ]

  const [trendData, setTrendData] = useState<DiseaseTrendItem[]>([])

  useEffect(() => {
    let isMounted = true
    if (scans.length > 0) {
      fetchDiseaseTrends()
        .then((data) => {
          if (isMounted) setTrendData(data)
        })
        .catch((err) => {
          console.error("Failed to load disease trends:", err)
        })
    } else {
      setTrendData([])
    }
    return () => {
      isMounted = false
    }
  }, [scans.length])

  return (
    <div className="p-6 space-y-6">
      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*"
        className="hidden"
      />

      {blocks.length === 0 && (
        <div role="status" className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-900 dark:text-amber-200">
          Demo preview values are shown because no plantation blocks are configured. Scan confidence is not model accuracy.
        </div>
      )}

      {/* ============================================================
      DYNAMIC ENVIRONMENTAL & PATHOGEN THREAT ADVISORY BANNER
      ============================================================ */}
      {!isAlertDismissed && (riskForecast?.compositeIndex ?? 0) >= 30 && (
        <div className="mb-5 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-700 shrink-0 mt-0.5">
              <AlertTriangle size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[11px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-800 border border-amber-500/30">
                  {riskForecast?.overallSeverity || "Moderate"} Pathogen Risk Detected
                </span>
                <span className="text-xs text-muted-foreground font-medium">
                  Microclimate Infection Index: <strong>{riskForecast?.compositeIndex}%</strong>
                </span>
              </div>
              <h3 className="font-bold text-sm text-foreground mt-1">
                {riskForecast?.advisoryHeadline || "Elevated Spore Germination Microclimate Detected"}
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5 max-w-3xl leading-relaxed">
                {riskForecast?.advisoryAction || "Prophylactic spraying of 1% Bordeaux mixture recommended within the upcoming dry window."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
            <button
              onClick={() => {
                setCalculatorDisease("koleroga")
                setShowCalculator(true)
              }}
              className="px-3.5 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 flex items-center gap-1.5 transition-opacity shadow-sm"
            >
              <Calculator size={14} />
              <span>Calculate Spray Dosage</span>
            </button>
            <button
              onClick={() => navigate("/risk")}
              className="px-3 py-1.5 rounded-xl border border-border bg-card text-foreground text-xs font-bold hover:bg-muted/40 transition-colors"
            >
              7-Day Forecast
            </button>
            <button
              onClick={() => setIsAlertDismissed(true)}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
              title="Dismiss Alert"
            >
              <X size={15} />
            </button>
          </div>
        </div>
      )}

      {/* ============================================================
      KPI GRID
      ============================================================ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpiCards.map(({ label, value, change, positive, sub, icon: Icon, iconBg, iconColor, onClick }) => (
          <div
            key={label}
            role="button"
            tabIndex={0}
            aria-label={`${label}: ${value}, ${change !== "—" ? change : ""} ${sub}`}
            onClick={onClick}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                onClick()
              }
            }}
            className="bg-card rounded-xl border border-border shadow-sm p-4 card-hover cursor-pointer focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none transition-all"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className={`w-10 h-10 rounded-xl ${iconBg} flex items-center justify-center shrink-0`}>
                  <Icon size={18} className={iconColor} />
                </div>
                <span className="text-xs text-muted-foreground font-medium truncate">{label}</span>
              </div>
              <ChevronRight size={15} className="text-muted-foreground/50 shrink-0 ml-1" />
            </div>

            <div className="text-xl sm:text-2xl font-bold text-foreground mb-1 break-words tracking-tight">{value}</div>

            <div className="flex items-center gap-1 flex-wrap">
              {change !== "—" ? (
                positive ? (
                  <TrendingUp size={13} className="text-primary shrink-0" />
                ) : (
                  <TrendingDown size={13} className="text-danger shrink-0" />
                )
              ) : null}
              <span className={`text-xs font-medium ${positive ? "text-primary" : "text-danger"}`}>
                {change}
              </span>
              <span className="text-xs text-muted-foreground">{sub}</span>
            </div>
          </div>
        ))}
      </div>

      {/* ============================================================
      QUICK SCAN & FIELD DIAGNOSTIC SHORTCUT
      ============================================================ */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-foreground">
            {t("dash.title", "Quick Diagnostic Scan")} <span className="text-muted-foreground font-normal text-sm">– Field Shortcut</span>
          </h2>
          <button
            onClick={() => navigate("/detection", { state: selectedImage ? { imageUrl: selectedImage } : undefined })}
            className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
          >
            <span>Open Full Diagnostic Studio</span>
            <ChevronRight size={14} />
          </button>
        </div>

        {scanError && (
          <div className="mb-4 p-3 bg-danger/10 border border-danger/30 rounded-xl flex items-center justify-between text-xs text-danger">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="shrink-0" />
              <span>{scanError}</span>
            </div>
            <button
              onClick={() => setScanError(null)}
              className="p-1 hover:bg-danger/20 rounded text-danger transition-colors"
              title={t("dash.close", "Close")}
            >
              <X size={14} />
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* ---------- LEFT: Quick Upload Zone ---------- */}
          <div className="lg:col-span-4 space-y-3">
            {/* Drag & Drop Upload Zone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isScanning) setIsDragging(true)
              }}
              onDragEnter={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isScanning) setIsDragging(true)
              }}
              onDragLeave={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setIsDragging(false)
              }}
              onDrop={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setIsDragging(false)
                if (isScanning) return
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                  const file = e.dataTransfer.files[0]
                  handleProcessScan(file)
                  return
                }
                const uri = e.dataTransfer.getData("text/uri-list") || e.dataTransfer.getData("text/plain")
                if (uri && (uri.startsWith("http://") || uri.startsWith("https://") || uri.startsWith("data:image/"))) {
                  handleProcessScan(uri.trim())
                  return
                }
                const html = e.dataTransfer.getData("text/html")
                if (html) {
                  const match = html.match(/src=["']([^"']+)["']/i)
                  if (match && match[1]) {
                    handleProcessScan(match[1])
                  }
                }
              }}
              className={`bg-card rounded-2xl border-2 border-dashed p-6 text-center transition-all cursor-pointer relative group ${
                isDragging
                  ? "border-primary bg-primary/10 ring-4 ring-primary/20 scale-[1.02]"
                  : "border-primary/30 hover:border-primary"
              }`}
            >
              <div
                className={`w-13 h-13 mx-auto mb-2.5 rounded-full flex items-center justify-center transition-transform ${
                  isDragging ? "bg-primary text-white scale-110" : "bg-primary/10 text-primary group-hover:scale-110"
                }`}
              >
                <Upload size={22} />
              </div>
              <p className="text-xs font-bold text-foreground">
                {isDragging ? t("detect.drop_here", "Drop photo here to analyze") : t("dash.upload_photo", "Upload or Paste (Ctrl+V) Plant Photo")}
              </p>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                {isDragging ? t("detect.release_drop", "Release to start multi-model diagnosis") : t("dash.drag_drop", "Paste copied image (Ctrl+V), drag & drop, or click to browse")}
              </p>
            </div>

            {/* Quick Action Buttons */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setIsCameraModalOpen(true)}
                className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-border bg-card text-xs text-muted-foreground font-medium hover:border-primary hover:text-primary transition-all"
              >
                <Camera size={14} />
                <span>{t("dash.camera_capture", "Live Camera")}</span>
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-border bg-card text-xs text-muted-foreground font-medium hover:border-primary hover:text-primary transition-all"
              >
                <ImageIcon size={14} />
                <span>{t("dash.image_gallery", "Gallery")}</span>
              </button>
            </div>

            {/* Recent Scan History Thumbnails */}
            <div className="pt-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-foreground">{t("dash.recent_scans", "Recent Scans")}</span>
                {scans.length > 0 && (
                  <Link to="/scans" className="text-[11px] text-primary font-medium hover:underline">
                    {t("dash.view_all", "View All")} ({scans.length})
                  </Link>
                )}
              </div>

              {scans.length === 0 ? (
                <div className="text-[11px] text-muted-foreground text-center py-3 px-2 border border-dashed border-border rounded-xl bg-muted/20">
                  {t("dash.no_recent_scans", "No recent scans. Upload a photo above to run analysis.")}
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  {scans.slice(0, 3).map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleProcessScan(item.imageUrl)}
                      className="relative aspect-[4/3] rounded-lg overflow-hidden bg-muted group cursor-pointer border border-border hover:border-primary transition-all"
                      title={`${item.disease} (${item.confidence}%)`}
                    >
                      {item.imageUrl ? (
                        <img
                          src={item.imageUrl}
                          alt={item.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-muted text-muted-foreground text-xs">
                          No Image
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* ---------- RIGHT: Quick Diagnostic Result Summary ---------- */}
          {isScanning ? (
            <div className="lg:col-span-8 bg-card rounded-xl border border-border flex flex-col items-center justify-center p-8 min-h-[240px]">
              <div className="flex flex-col items-center text-center space-y-2 animate-in fade-in duration-300">
                <div className="w-10 h-10 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
                <p className="text-xs font-bold text-foreground">Running Multi-Model Inference...</p>
                <p className="text-[11px] text-muted-foreground">Evaluating binary gatekeeper (CNN), disease locator (YOLO), and classifier (ViT)</p>
              </div>
            </div>
          ) : scanResult ? (
            scanResult.disease === "Not an Arecanut image" || scanResult.severity === "Non-Arecanut" ? (
              <div className="lg:col-span-8 bg-card rounded-2xl border-2 border-warning/40 p-6 shadow-sm flex flex-col justify-center min-h-[240px] animate-in fade-in zoom-in-95 duration-200">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                  {selectedImage ? (
                    <div className="relative w-20 h-20 rounded-xl overflow-hidden bg-muted shrink-0 border-2 border-warning/50">
                      <img src={selectedImage} alt="Invalid upload" className="w-full h-full object-cover opacity-75" />
                      <div className="absolute inset-0 bg-warning/25 flex items-center justify-center">
                        <AlertTriangle size={24} className="text-warning drop-shadow" />
                      </div>
                    </div>
                  ) : (
                    <div className="w-14 h-14 rounded-2xl bg-warning/15 border border-warning/30 text-warning flex items-center justify-center shrink-0">
                      <AlertTriangle size={28} />
                    </div>
                  )}

                  <div className="space-y-1.5 flex-1">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-warning/15 border border-warning/30 text-warning text-[11px] font-bold">
                      <AlertTriangle size={12} />
                      <span>Invalid Image</span>
                    </span>
                    <h3 className="text-lg sm:text-xl font-extrabold text-foreground">
                      Not an Arecanut Image — Please Upload an Arecanut Photo
                    </h3>
                    <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed max-w-xl">
                      The uploaded image does not contain an arecanut (betel nut) palm, leaf, trunk, or nut cluster. Please upload a clear photograph of an arecanut plant to run disease detection.
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3 mt-5 pt-4 border-t border-border">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="btn-primary text-xs flex items-center justify-center gap-2 px-5 py-2.5 shadow-sm font-bold"
                  >
                    <Upload size={15} />
                    <span>Upload Arecanut Image</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setScanResult(null)
                      setSelectedImage(null)
                    }}
                    className="btn-secondary text-xs flex items-center justify-center gap-1.5 px-4 py-2.5"
                  >
                    <X size={14} />
                    <span>Clear Image</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="lg:col-span-8 bg-card rounded-xl border border-border p-5 shadow-sm space-y-4 animate-in fade-in zoom-in-95 duration-300">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-3 border-b border-border">
                  <div className="flex items-center gap-3">
                    {selectedImage ? (
                      <div className="w-16 h-16 rounded-xl overflow-hidden bg-muted shrink-0 border border-border">
                        <img src={selectedImage} alt="Scanned plant" className="w-full h-full object-cover" />
                      </div>
                    ) : null}
                    <div>
                      <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Quick Scan Result</div>
                      <div className="text-lg font-extrabold text-foreground flex items-center gap-2 mt-0.5">
                        <span>{scanResult.disease}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          scanResult.severity === "Healthy"
                            ? "bg-success/10 text-success border-success/20"
                            : scanResult.severity === "Mild"
                            ? "bg-accent/10 text-accent border-accent/20"
                            : scanResult.severity === "Moderate" || scanResult.severity === "Uncertain"
                            ? "bg-warning/10 text-warning border-warning/20"
                            : "bg-danger/10 text-danger border-danger/20"
                        }`}>
                          {scanResult.severity}
                        </span>
                      </div>
                      <div className="text-[11px] text-muted-foreground mt-0.5">
                        {scanResult.stage}
                      </div>
                    </div>
                  </div>

                  <div className="text-right sm:border-l sm:border-border sm:pl-4">
                    <div className="text-[10px] text-muted-foreground font-semibold">AI Confidence</div>
                    <div className="text-2xl font-black text-primary">{scanResult.confidence}%</div>
                  </div>
                </div>

                {/* Multi-Model Breakdown Badges */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded-lg bg-muted/30 border border-border">
                    <div className="text-[10px] text-muted-foreground">CNN Gate</div>
                    <div className="font-bold text-foreground text-xs mt-0.5">
                      {scanResult.modelBreakdown?.cnn !== undefined ? `${scanResult.modelBreakdown.cnn}%` : "100%"}
                    </div>
                  </div>
                  <div className="p-2 rounded-lg bg-muted/30 border border-border">
                    <div className="text-[10px] text-muted-foreground">YOLOv8 Localizer</div>
                    <div className="font-bold text-foreground text-xs mt-0.5">
                      {scanResult.modelBreakdown?.yolo !== undefined ? `${scanResult.modelBreakdown.yolo}%` : "0%"}
                    </div>
                  </div>
                  <div className="p-2 rounded-lg bg-muted/30 border border-border">
                    <div className="text-[10px] text-muted-foreground">ViT Classifier</div>
                    <div className="font-bold text-foreground text-xs mt-0.5">
                      {scanResult.modelBreakdown?.vit !== undefined ? `${scanResult.modelBreakdown.vit}%` : `${scanResult.confidence}%`}
                    </div>
                  </div>
                </div>

                {/* Top Recommended Treatment */}
                {scanResult.treatments && scanResult.treatments.length > 0 && (
                  <div className="p-3 rounded-lg bg-muted/20 border border-border text-xs text-muted-foreground flex items-start gap-2">
                    <Check size={14} className="text-primary shrink-0 mt-0.5" />
                    <span className="leading-relaxed">
                      <strong className="text-foreground">Primary Treatment: </strong>
                      {scanResult.treatments[0]}
                    </span>
                  </div>
                )}

                {/* Action Buttons: Navigate to Full Detection Studio */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full sm:w-auto btn-secondary text-xs flex items-center justify-center gap-1.5"
                  >
                    <Upload size={13} />
                    <span>Scan Another Photo</span>
                  </button>

                  <button
                    onClick={() => navigate("/detection", { state: { imageUrl: selectedImage } })}
                    className="w-full sm:w-auto btn-primary text-xs flex items-center justify-center gap-1.5 shadow-sm font-bold"
                  >
                    <span>Open Full XAI Laboratory & Prescriptions</span>
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )
          ) : (
            <div className="lg:col-span-8 bg-card rounded-xl border-2 border-border border-dashed flex flex-col items-center justify-center p-8 min-h-[240px]">
              <div className="flex flex-col items-center text-center max-w-md space-y-3">
                <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                  <ScanLine size={24} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-foreground">Quick Diagnostic Shortcut</h3>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                    Upload a plant photo from your device for instant CNN + YOLO + ViT inference, or open the full laboratory for deep explainability maps.
                  </p>
                </div>
                <div className="flex items-center gap-2.5 pt-1">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="btn-primary text-xs flex items-center gap-1.5 shadow-sm"
                  >
                    <Upload size={13} />
                    <span>Upload & Scan</span>
                  </button>
                  <button
                    onClick={() => navigate("/detection")}
                    className="btn-secondary text-xs flex items-center gap-1.5"
                  >
                    <span>Full Diagnostic Studio</span>
                    <ChevronRight size={13} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ============================================================
      INTELLIGENCE & RECENT ALERTS ROW
      ============================================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Weather Intelligence (5-State Machine) */}
        <div className="lg:col-span-4 bg-card rounded-xl border border-border shadow-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-bold text-foreground">{t("weather.title", "Weather Intelligence")}</div>
            {weatherState.status === "POPULATED" && (
              weatherState.data.isLive !== false ? (
                <div className="flex items-center gap-1.5" title={weatherState.data.dataSource || "Live Microclimate Feed"}>
                  <div className="w-2 h-2 rounded-full bg-primary pulse-live" />
                  <span className="text-[11px] text-primary font-semibold">{t("weather.live", "Live")}</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400" title={weatherState.data.dataSource || "Simulated Baseline"}>
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  <span className="text-[10px] font-semibold">Simulated Baseline</span>
                </div>
              )
            )}
          </div>


          {/* STATE 1: UNREQUESTED */}
          {weatherState.status === "UNREQUESTED" && (
            <div className="space-y-3 text-center py-4">
              <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto">
                <MapPin size={20} />
              </div>
              <div>
                <div className="text-xs font-bold text-foreground">{t("dash.location_required", "Location Access Required")}</div>
                <p className="text-[11px] text-muted-foreground mt-1 leading-snug">
                  {t("dash.location_required_desc", "Enable live location access or search your city to view real-time microclimate analytics.")}
                </p>
              </div>

              <button
                onClick={handleEnableLiveLocation}
                className="w-full btn-primary text-xs justify-center py-2 shadow-sm"
              >
                <MapPin size={14} />
                <span>{t("dash.enable_live_btn", "Enable Live Location")}</span>
              </button>

              <form onSubmit={handleWeatherSearch} className="flex items-center gap-1.5 pt-1">
                <input
                  type="text"
                  value={weatherSearch}
                  onChange={(e) => setWeatherSearch(e.target.value)}
                  placeholder={t("dash.or_enter_city", "Or enter city name...")}
                  className="flex-1 bg-muted/40 border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground outline-none"
                />
                <button
                  type="submit"
                  aria-label={t("dash.search_weather_aria", "Search weather by city")}
                  className="p-1.5 rounded-lg bg-card border border-border text-muted-foreground hover:text-foreground"
                >
                  <Search size={14} />
                </button>
              </form>
            </div>
          )}

          {/* STATE 2: DENIED */}
          {weatherState.status === "DENIED" && (
            <div className="space-y-3 text-center py-4">
              <div className="w-10 h-10 rounded-full bg-warning/10 text-warning flex items-center justify-center mx-auto">
                <AlertCircle size={20} />
              </div>
              <div>
                <div className="text-xs font-bold text-foreground">{t("dash.location_denied", "Location Access Denied")}</div>
                <p className="text-[11px] text-muted-foreground mt-1 leading-snug">
                  {weatherState.message} {t("dash.location_denied_desc", "Search a city manually below to load weather data.")}
                </p>
              </div>

              <form onSubmit={handleWeatherSearch} className="flex items-center gap-1.5 pt-1">
                <input
                  type="text"
                  value={weatherSearch}
                  onChange={(e) => setWeatherSearch(e.target.value)}
                  placeholder={t("dash.enter_city_name", "Enter city name...")}
                  className="flex-1 bg-muted/40 border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground outline-none"
                />
                <button type="submit" className="p-1.5 rounded-lg btn-primary text-xs">
                  {t("dash.search_btn", "Search")}
                </button>
              </form>
            </div>
          )}

          {/* STATE 3: LOADING */}
          {weatherState.status === "LOADING" && (
            <div className="space-y-3 py-6 text-center">
              <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin mx-auto" />
              <div className="text-xs text-muted-foreground skeleton-pulse py-1 rounded">{t("dash.fetching_weather", "Fetching microclimate data...")}</div>
            </div>
          )}

          {/* STATE 4: ERROR */}
          {weatherState.status === "ERROR" && (
            <div className="space-y-3 text-center py-4">
              <div className="w-10 h-10 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
                <AlertTriangle size={20} />
              </div>
              <div>
                <div className="text-xs font-bold text-foreground">{t("dash.weather_error", "Weather Service Error")}</div>
                <p className="text-[11px] text-muted-foreground mt-1 leading-snug">{weatherState.message}</p>
              </div>
              <button
                onClick={handleEnableLiveLocation}
                className="btn-secondary text-xs mx-auto flex items-center gap-1.5"
              >
                <RefreshCw size={12} /> {t("dash.retry_conn", "Retry Connection")}
              </button>
            </div>
          )}

          {/* STATE 5: POPULATED */}
          {weatherState.status === "POPULATED" && (
            <div className="space-y-3 animate-in fade-in duration-300">
              <div className="text-xs text-muted-foreground font-medium">
                {weatherState.data.city}, {weatherState.data.region}
              </div>

              <div className="grid grid-cols-3 gap-2">
                {[
                  { icon: Thermometer, label: t("dash.temp_short", "Temp"), val: `${weatherState.data.temperature}°C` },
                  { icon: Droplets, label: t("weather.humidity", "Humidity"), val: `${weatherState.data.humidity}%` },
                  { icon: CloudRain, label: t("dash.rain_short", "Rain"), val: `${weatherState.data.rainfall} mm` },
                  { icon: Wind, label: t("dash.wind_short", "Wind"), val: `${weatherState.data.windSpeed} km/h` },
                  { icon: Sun, label: t("weather.uv", "UV Index"), val: `${weatherState.data.uvIndex}` },
                  { icon: ShieldAlert, label: t("dash.risk_badge", "Risk"), val: weatherState.data.riskLevel, isRisk: true },
                ].map(({ icon: WIcon, label, val, isRisk }) => (
                  <div key={label} className="text-center p-2 rounded-lg bg-muted/30 border border-border">
                    <WIcon size={14} className="mx-auto text-primary mb-1" />
                    <div className={`text-xs font-bold ${isRisk ? "text-danger" : "text-foreground"}`}>
                      {val}
                    </div>
                    <div className="text-[9px] text-muted-foreground">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* AI Risk Forecast */}
        <div className="lg:col-span-4 bg-card rounded-xl border border-border shadow-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-bold text-foreground">
              {t("weather.forecast_title", "AI Risk Forecast")} <span className="text-xs font-normal text-muted-foreground">{t("dash.five_days", "(5 Days)")}</span>
            </div>
            {weatherState.status === "POPULATED" && (
              <span className="px-2 py-0.5 text-[10px] font-bold bg-danger/10 text-danger rounded-full border border-danger/20">
                {weatherState.data.riskLevel} {t("dash.risk_badge", "Risk")}
              </span>
            )}
          </div>

          {weatherState.status !== "POPULATED" ? (
            <div className="text-xs text-muted-foreground text-center py-6 border border-dashed border-border rounded-xl bg-muted/20">
              {t("dash.risk_forecast_empty", "Live weather data required for risk forecasting — enable location or search city above.")}
            </div>
          ) : (
            <>
              <p className="text-xs text-muted-foreground mb-3">
                {t("dash.humidity_risk_prefix", "Humidity metrics")} ({weatherState.data.humidity}%) {t("dash.humidity_risk_suffix", "indicate fungal infection potential for")} <span className="font-bold text-danger">{t("dash.anthracnose_koleroga", "Anthracnose & Koleroga")}</span>.
              </p>
              <div>
                <div className="text-[11px] font-semibold text-muted-foreground mb-1.5">{t("dash.risk_drivers", "Risk Drivers")}</div>
                <ul className="space-y-1">
                  <li className="text-xs text-muted-foreground flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary" /> {t("dash.rh_tracking", "Relative humidity tracking")} ({weatherState.data.humidity}%)
                  </li>
                  <li className="text-xs text-muted-foreground flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-warning" /> {t("dash.precip_index", "Precipitation index")} ({weatherState.data.rainfall} mm)
                  </li>
                </ul>
              </div>
            </>
          )}
        </div>

        {/* Recent Alerts */}
        <div className="lg:col-span-4 bg-card rounded-xl border border-border shadow-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-bold text-foreground">{t("dash.recent_alerts", "Recent Alerts")}</div>
            {notifications.length > 0 && (
              <Link to="/notifications" className="text-xs text-primary font-medium hover:underline">
                {t("dash.view_all", "View All")}
              </Link>
            )}
          </div>

          {notifications.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-6 border border-dashed border-border rounded-xl bg-muted/20">
              {t("dash.no_alerts", "No active alerts for your plantation. All systems optimal.")}
            </div>
          ) : (
            <div className="space-y-2.5">
              {notifications.slice(0, 3).map((item) => (
                <Link
                  key={item.id}
                  to="/notifications"
                  className="flex items-start gap-2.5 group cursor-pointer"
                >
                  <div
                    className={`w-2.5 h-2.5 rounded-full mt-1 shrink-0 ${
                      item.type === "critical"
                        ? "bg-danger"
                        : item.type === "warning"
                        ? "bg-warning"
                        : "bg-primary"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-foreground font-medium leading-snug group-hover:text-primary transition-colors">
                      {item.title}
                    </p>
                    <p className="text-[10px] text-muted-foreground">{item.time}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ============================================================
      BOTTOM ROW: Charts
      ============================================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Disease Trend Chart */}
        <div className="lg:col-span-3 bg-card rounded-xl border border-border shadow-sm p-5">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-bold text-foreground">
              {t("dash.disease_trend", "Disease Trend")} <span className="text-muted-foreground font-normal">{t("dash.this_month", "(This Month)")}</span>
            </h3>
            {trendData.length > 0 && (
              <div className="flex items-center gap-3">
                {trendLegend.map(({ label, color }) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                    <span className="text-[11px] text-muted-foreground">{label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {trendData.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center border border-dashed border-border rounded-xl bg-muted/10 min-h-[220px]">
              <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-3 shadow-sm">
                <TrendingUp size={22} />
              </div>
              <p className="text-xs font-bold text-foreground mb-1">
                {t("dash.no_trends", "No historical scan trends available.")}
              </p>
              <p className="text-[11px] text-muted-foreground max-w-sm mb-4 leading-relaxed">
                {t("dash.empty_trend_desc", "Analyze plant imagery to start tracking temporal disease progression and recovery curves.")}
              </p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-primary text-xs px-3.5 py-1.5 flex items-center gap-1.5 shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                <Upload size={13} />
                <span>{t("dash.scan_plant_cta", "Scan a Plant")}</span>
              </button>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="date" stroke="var(--color-muted-foreground)" fontSize={11} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={11} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="anthracnose" stroke={THEME_TOKENS.charts.lines.anthracnose} strokeWidth={2.5} name="Anthracnose" />
                <Line type="monotone" dataKey="fruitRot" stroke={THEME_TOKENS.charts.lines.fruitRot} strokeWidth={2} name="Fruit Rot" />
                <Line type="monotone" dataKey="nutCracking" stroke={THEME_TOKENS.charts.lines.nutCracking} strokeWidth={2} name="Nut Cracking" />
                <Line type="monotone" dataKey="sootyMold" stroke={THEME_TOKENS.charts.lines.sootyMold} strokeWidth={2} name="Sooty Mold" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top Diseased Areas */}
        <div className="lg:col-span-2 bg-card rounded-xl border border-border shadow-sm p-5">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-bold text-foreground">{t("dash.top_diseased_areas", "Top Diseased Areas")}</h3>
            {blocks.length > 0 && (
              <Link to="/map" className="text-xs text-primary font-medium hover:underline">
                {t("dash.view_map", "View Map")}
              </Link>
            )}
          </div>

          {topDiseasedBlocks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 px-4 text-center border border-dashed border-border rounded-xl bg-muted/10 min-h-[220px]">
              <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-3 shadow-sm">
                <TreePine size={22} />
              </div>
              <p className="text-xs font-bold text-foreground mb-1">
                {t("dash.no_blocks", "No plantation blocks configured.")}
              </p>
              <p className="text-[11px] text-muted-foreground max-w-xs mb-4 leading-relaxed">
                {t("dash.empty_blocks_desc", "Configure plantation sectors, acreage, and palm counts to track hotspot zones.")}
              </p>
              <Link
                to="/map"
                className="btn-primary text-xs px-3.5 py-1.5 flex items-center gap-1.5 shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                <Map size={13} />
                <span>{t("dash.setup_map_cta", "Setup Plantation Map")}</span>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {topDiseasedBlocks.map(({ id, diseasedTrees, status, color }) => {
                const maxTrees = 1000
                const pct = Math.min(100, Math.round((diseasedTrees / maxTrees) * 100))

                return (
                  <div key={id}>
                    <div className="flex items-center justify-between mb-1.5">
                      <div>
                        <span className="text-xs font-bold text-foreground">{id}</span>
                        <span className="text-[11px] text-muted-foreground ml-2">{diseasedTrees} {t("dash.diseased_trees_suffix", "Diseased Trees")}</span>
                      </div>
                      <span className="text-[11px] font-bold" style={{ color }}>
                        {status}
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, background: color }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* ============================================================
      REPORT GENERATION MODAL
      ============================================================ */}
      {reportModalOpen && scanResult && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            ref={reportModalRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="report-modal-title"
            className="bg-card border border-border rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-5 animate-in fade-in zoom-in-95 outline-none"
          >
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <FileText size={20} className="text-primary" />
                <h3 id="report-modal-title" className="text-base font-bold text-foreground">
                  {t("dash.report_modal_title", "AI Diagnostic Report")}
                </h3>
              </div>
              <button
                onClick={() => setReportModalOpen(false)}
                className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                aria-label={t("dash.close", "Close")}
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-muted/40 border border-border flex justify-between items-center">
                <div>
                  <div className="text-[10px] text-muted-foreground font-semibold uppercase">{t("dash.condition", "Condition")}</div>
                  <div className="text-sm font-extrabold text-danger">{scanResult.disease}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-muted-foreground font-semibold uppercase">{t("xai.confidence", "Confidence")}</div>
                  <div className="text-sm font-extrabold text-primary">{scanResult.confidence}%</div>
                </div>
              </div>

              <div>
                <span className="font-bold text-foreground">{t("dash.diag_summary", "Diagnostic Summary:")}</span>
                <p className="text-muted-foreground mt-0.5 leading-relaxed">{scanResult.description}</p>
              </div>

              <div>
                <span className="font-bold text-foreground">{t("dash.rec_treatment_plan", "Recommended Treatment Plan:")}</span>
                <ul className="mt-1 space-y-1">
                  {scanResult.treatments.map((t, i) => (
                    <li key={i} className="flex items-center gap-2 text-muted-foreground">
                      <Check size={12} className="text-primary shrink-0" />
                      <span>{t}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
              <button
                onClick={() => setReportModalOpen(false)}
                className="btn-secondary text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                {t("dash.close", "Close")}
              </button>
              <button
                onClick={() => {
                  window.print()
                }}
                className="btn-primary text-xs flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                <Printer size={14} /> {t("dash.print_export_pdf", "Print / Export PDF")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Live WebRTC Camera Stream Modal */}
      <LiveCameraModal
        isOpen={isCameraModalOpen}
        onClose={() => setIsCameraModalOpen(false)}
        onCapture={(file) => handleProcessScan(file)}
      />

      {/* Commercial Spray Dosage & Cost Calculator Modal */}
      <TreatmentCalculatorModal
        isOpen={showCalculator}
        onClose={() => setShowCalculator(false)}
        initialDisease={calculatorDisease}
        initialPalms={totalTrees || 1500}
      />
    </div>
  )
}
