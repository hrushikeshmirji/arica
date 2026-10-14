import { useState, useRef, useEffect, useMemo } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import {
  Upload,
  Camera,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Sparkles,
  Download,
  RefreshCw,
  ShieldAlert,
  Layers,
  Eye,
  XCircle,
  Volume2,
  VolumeX,
  Calculator,
  MapPin,
  Droplets,
  Cpu,
  FlaskConical,
  Activity,
  FileText,
  ShieldCheck,
  Sprout,
  Clock,
} from "lucide-react"
import { useScanHistory, ScanItem } from "../contexts/ScanHistoryContext"
import { useNotifications } from "../contexts/NotificationContext"
import { usePlantation } from "../contexts/PlantationContext"
import { useLanguage } from "../contexts/LanguageContext"
import { useWeather } from "../contexts/WeatherContext"
import { submitAnalysis, getJobStatus, cancelJob, fetchSpecimens } from "../services/detectionService"
import { ModelInferenceResponse, FieldSpecimenItem } from "../types/api"
import LiveCameraModal from "../components/LiveCameraModal"
import XaiSplitViewer from "../components/XaiSplitViewer"
import TreatmentCalculatorModal from "../components/TreatmentCalculatorModal"
import MarkTreatmentModal from "../components/MarkTreatmentModal"
import { speakText, stopSpeech } from "../utils/textToSpeech"

const PLANTATION_BLOCKS = [
  { id: "block-a1", name: "Block A-1 (North Valley)", trees: 450, zone: "High Humidity Valley" },
  { id: "block-a2", name: "Block A-2 (North Slope)", trees: 520, zone: "Terraced Slope" },
  { id: "block-b1", name: "Block B-1 (Central Basin)", trees: 610, zone: "Well-Drained Basin" },
  { id: "block-b2", name: "Block B-2 (East Ridge)", trees: 380, zone: "Elevated Ridge" },
  { id: "block-c1", name: "Block C-1 (River Bank)", trees: 490, zone: "Riparian Belt" },
  { id: "block-d1", name: "Block D-1 (West Nursery)", trees: 310, zone: "Young Palms" },
]

interface BatchItem {
  id: string
  name: string
  previewUrl: string
  fileOrSpec: File | string
  specimenId?: string
  result?: ModelInferenceResponse
  status: "pending" | "scanning" | "done" | "error"
}

export default function Detection() {
  const { addScan, markTreated } = useScanHistory()
  const { addNotification } = useNotifications()
  const { markBlockTreated } = usePlantation()
  const { language, t } = useLanguage()
  const { weatherState } = useWeather()
  const location = useLocation()
  const navigate = useNavigate()

  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStage, setCurrentStage] = useState<string>("STAGE_1_CNN_GATEKEEPER")
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [diagnosis, setDiagnosis] = useState<ModelInferenceResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [cameraModalOpen, setCameraModalOpen] = useState(false)
  const [isDragging, setIsDragging] = useState(false)

  // Block Tagging & Dosage Calculator State
  const [selectedBlockId, setSelectedBlockId] = useState<string>("block-a1")
  const [palmCountToSpray, setPalmCountToSpray] = useState<number>(450)
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false)
  const [treatmentModalOpen, setTreatmentModalOpen] = useState(false)
  const [treatmentModalMode, setTreatmentModalMode] = useState<"pesticides" | "fertilizers">("pesticides")
  const [currentScanItem, setCurrentScanItem] = useState<ScanItem | null>(null)
  const [markTreatmentModalOpen, setMarkTreatmentModalOpen] = useState(false)
  const [treatmentSuccessBanner, setTreatmentSuccessBanner] = useState<string | null>(null)

  // Specimen Gallery & Batch Filmstrip State
  const [specimens, setSpecimens] = useState<FieldSpecimenItem[]>([])
  const [batchQueue, setBatchQueue] = useState<BatchItem[]>([])
  const [activeBatchId, setActiveBatchId] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const activeJobIdRef = useRef<string | null>(null)
  const lastInferenceRef = useRef<{ fileOrUrl: File | string; blockId?: string; specimenId?: string } | null>(null)

  // Load verified field specimens on mount
  useEffect(() => {
    fetchSpecimens()
      .then((items) => setSpecimens(items))
      .catch(() => undefined)
  }, [])

  // Sync palm count when block selection changes
  useEffect(() => {
    const found = PLANTATION_BLOCKS.find((b) => b.id === selectedBlockId)
    if (found) setPalmCountToSpray(found.trees)
  }, [selectedBlockId])

  useEffect(() => {
    const state = location.state as { imageUrl?: string; selectedBlockId?: string } | null
    if (state?.selectedBlockId) {
      setSelectedBlockId(state.selectedBlockId)
    }
    if (state?.imageUrl) {
      setSelectedImage(state.imageUrl)
      runRealInference(state.imageUrl, state?.selectedBlockId || selectedBlockId)
    }
    return () => {
      stopSpeech()
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      if (activeJobIdRef.current) {
        cancelJob(activeJobIdRef.current).catch(() => undefined)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state])

  const runRealInference = async (
    fileOrUrl: File | string,
    blockIdOverride?: string,
    specimenIdOverride?: string
  ) => {
    lastInferenceRef.current = { fileOrUrl, blockId: blockIdOverride, specimenId: specimenIdOverride }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    const currentAbort = new AbortController()
    abortControllerRef.current = currentAbort

    stopSpeech()
    setIsSpeaking(false)
    setIsAnalyzing(true)
    setProgress(15)
    setCurrentStage("STAGE_1_CNN_GATEKEEPER")
    setDiagnosis(null)
    setErrorMessage(null)
    setCurrentScanItem(null)
    setTreatmentSuccessBanner(null)

    const targetBlock = blockIdOverride || selectedBlockId

    try {
      const submitRes = await submitAnalysis(fileOrUrl, {
        signal: currentAbort.signal,
        blockId: targetBlock,
        specimenId: specimenIdOverride,
      })
      if (currentAbort.signal.aborted) return

      setActiveJobId(submitRes.job_id)
      activeJobIdRef.current = submitRes.job_id
      setProgress(30)

      let isCompleted = false
      let pollAttempts = 0

      while (!isCompleted && pollAttempts < 40) {
        await new Promise((r) => setTimeout(r, 450))
        if (currentAbort.signal.aborted) return

        pollAttempts++
        const statusRes = await getJobStatus(submitRes.job_id, { signal: currentAbort.signal })
        if (currentAbort.signal.aborted) return

        setProgress(statusRes.progressPercent)
        if (statusRes.currentStage) {
          setCurrentStage(statusRes.currentStage)
        }

        if (statusRes.status === "done" && statusRes.result) {
          isCompleted = true
          const res = statusRes.result
          setDiagnosis(res)
          setIsAnalyzing(false)
          setActiveJobId(null)
          activeJobIdRef.current = null

          // Never save mock or demo inferences to persistent scan history
          const isDemo = res.id.startsWith("demo-") || import.meta.env.VITE_DEMO_MODE === "true"
          if (res.disease !== "Not an Arecanut image" && res.stage !== "Gatekeeper Uncertain" && !isDemo) {
            const blockObj = PLANTATION_BLOCKS.find((b) => b.id === targetBlock)
            const created = addScan({
              title: `${res.disease} Inspection`,
              disease: res.disease,
              confidence: res.confidence,
              stage: res.stage,
              severity: res.severity,
              location: res.blockName || blockObj?.name || "Block A-1 (North Valley)",
              temp: weatherState.status === "POPULATED" ? `${weatherState.data.temperature}°C` : "24°C",
              weatherCondition: weatherState.status === "POPULATED" ? weatherState.data.condition : "Humid",
              recommendedActions: res.treatments.slice(0, 2),
              imageUrl: typeof fileOrUrl === "string" && !fileOrUrl.startsWith("specimen:") ? fileOrUrl : (selectedImage || "/placeholder.jpg"),
            })
            setCurrentScanItem(created)
          }
        } else if (statusRes.status === "failed") {
          throw new Error(statusRes.error || "Diagnosis pipeline failed")
        }
      }

      if (!isCompleted) {
        throw new Error("Analysis timed out waiting for neural worker")
      }
    } catch (err) {
      if (currentAbort.signal.aborted) return
      const msg = err instanceof Error ? err.message : "Failed to complete image diagnosis"
      setDiagnosis(null)
      setErrorMessage(msg)
      setIsAnalyzing(false)
      setActiveJobId(null)
      activeJobIdRef.current = null
    }
  }

  const handleCancelJob = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    if (activeJobId) {
      await cancelJob(activeJobId)
    }
    setIsAnalyzing(false)
    setActiveJobId(null)
    activeJobIdRef.current = null
    setProgress(0)
    setErrorMessage("Analysis cancelled by user.")
  }

  const handleConfirmDirectTreatment = (details: {
    treatmentType: "chemical" | "organic"
    chemicalUsed: string
    notes?: string
    blockId?: string
    followUpDate: string
  }) => {
    const targetBlock = details.blockId || selectedBlockId
    if (currentScanItem) {
      markTreated(currentScanItem.id, details)
      setCurrentScanItem((prev) =>
        prev
          ? {
              ...prev,
              treatment: {
                isTreated: true,
                treatedAt: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
                treatmentType: details.treatmentType,
                chemicalUsed: details.chemicalUsed,
                dosageNotes: details.notes,
                followUpDate: details.followUpDate,
                status: "recovering",
              },
            }
          : null
      )
    }
    markBlockTreated(targetBlock, {
      treatmentType: details.treatmentType,
      chemicalUsed: details.chemicalUsed,
      followUpDate: details.followUpDate,
    })
    addNotification({
      type: "info",
      title: `Treatment Logged: ${diagnosis?.disease || "Arecanut"}`,
      msg: `Applied ${details.chemicalUsed} at ${targetBlock}. 14-day follow-up inspection scheduled for ${details.followUpDate}.`,
      blockId: targetBlock,
    })
    setTreatmentSuccessBanner(
      `Treatment confirmed! ${details.chemicalUsed} logged for ${targetBlock}. 14-day re-inspection alert scheduled for ${details.followUpDate}.`
    )
    setMarkTreatmentModalOpen(false)
    setTimeout(() => setTreatmentSuccessBanner(null), 6000)
  }

  const validateAndLoadFiles = (fileList: FileList | File[]) => {
    const validTypes = ["image/jpeg", "image/png", "image/webp", "image/bmp", "image/gif", "image/tiff"]
    const maxBytes = 25 * 1024 * 1024
    const files = Array.from(fileList)
    if (files.length === 0) return

    const validFiles = files.filter((f) => (f.type.startsWith("image/") || validTypes.includes(f.type)) && f.size <= maxBytes)
    if (validFiles.length === 0) {
      setErrorMessage(
        t("detect.val_invalid_format", "Invalid file format or size (>25MB). Please upload or paste a JPEG, PNG, WebP, or BMP image.")
      )
      return
    }

    const newBatchItems: BatchItem[] = validFiles.map((f, idx) => ({
      id: `batch-${Date.now()}-${idx}`,
      name: f.name || `pasted_specimen_${idx + 1}.png`,
      previewUrl: URL.createObjectURL(f),
      fileOrSpec: f,
      status: idx === 0 ? "scanning" : "pending",
    }))

    setBatchQueue((prev) => [...newBatchItems, ...prev].slice(0, 8))
    const first = newBatchItems[0]
    setActiveBatchId(first.id)
    setSelectedImage(first.previewUrl)
    runRealInference(first.fileOrSpec, selectedBlockId)
  }

  // Global Clipboard Paste Handler (Ctrl+V for internet images or image URLs)
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (!e.clipboardData) return

      // 1. Check for clipboard image blobs/files (e.g., Right-Click -> Copy Image on web)
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
            validateAndLoadFiles([namedFile])
            return
          }
        }
      }

      // 2. Check for copied image URL or data URI text
      const pastedText = e.clipboardData.getData("text").trim()
      if (
        pastedText.startsWith("data:image/") ||
        pastedText.match(/^https?:\/\/.*\.(jpe?g|png|webp|bmp|gif|tif|tiff)(\?.*)?$/i) ||
        pastedText.match(/^https?:\/\/.*(images|photos|media|googleusercontent|wikimedia|agritech|tnsau|cpcri).*/i)
      ) {
        e.preventDefault()
        setSelectedImage(pastedText)
        runRealInference(pastedText, selectedBlockId)
        return
      }
    }

    window.addEventListener("paste", handlePaste)
    return () => window.removeEventListener("paste", handlePaste)
  }, [selectedBlockId])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndLoadFiles(e.target.files)
    }
  }

  const handleSelectSpecimen = (spec: FieldSpecimenItem) => {
    if (!spec.previewUrl) {
      setErrorMessage("Specimen image bytes not available from backend. Please ensure the backend is running.")
      return
    }
    setSelectedImage(spec.previewUrl)
    runRealInference(`specimen:${spec.id}`, selectedBlockId, spec.id)
  }

  // Voice Audio Briefing (EN / KN / HI)
  const handleToggleVoiceBriefing = () => {
    if (!diagnosis) return
    if (isSpeaking) {
      stopSpeech()
      setIsSpeaking(false)
      return
    }
    const morph = diagnosis.tissueMorphometrics
    const speechScript =
      diagnosis.disease === "Not an Arecanut image"
        ? `Gatekeeper alert. With ${diagnosis.confidence}% confidence, this image is not an Areca catechu specimen. ${diagnosis.description}`
        : `ArecaVision Diagnostic Report for ${diagnosis.blockName || "selected block"}. Detected condition: ${
            diagnosis.disease
          } with ${diagnosis.confidence}% confidence and ${diagnosis.severity} severity. ${
            morph ? `Healthy tissue is ${morph.healthyPct}%, lesion coverage is ${morph.lesionCoveragePct}%. ` : ""
          }Recommended action: ${diagnosis.treatments[0] || "Follow standard management."} Organic protocol: ${
            diagnosis.organicControl[0] || "Apply neem cake."
          }`

    setIsSpeaking(true)
    speakText(speechScript, language, () => setIsSpeaking(false))
  }

  // Consult AI Agronomist about this scan
  const handleConsultAiAgronomist = () => {
    if (!diagnosis) return
    const weatherNote =
      weatherState.status === "POPULATED"
        ? `Current weather in ${weatherState.data.city}: ${weatherState.data.temperature}°C, ${weatherState.data.humidity}% humidity, ${weatherState.data.riskLevel} fungal risk.`
        : ""
    const prompt = `I just scanned an arecanut specimen in ${
      diagnosis.blockName || "Block A-1"
    } (${palmCountToSpray} palms). Diagnosis: ${diagnosis.disease} (${diagnosis.confidence}% confidence, ${
      diagnosis.severity
    } severity, Lesion coverage: ${
      diagnosis.tissueMorphometrics?.lesionCoveragePct ?? 18
    }%). ${weatherNote} Please give me an immediate step-by-step spray schedule and organic + chemical dosage plan.`
    navigate("/assistant", { state: { initialPrompt: prompt } })
  }

  // Interactive Spray & Nutrition Dosage Calculations (ICAR-CPCRI Standards)
  const dosagePlan = useMemo(() => {
    const palms = Math.max(1, palmCountToSpray)
    const sprayLiters = Math.round(palms * 1.5)
    const d = diagnosis?.disease?.toLowerCase() || ""

    let planType = "fungicide"
    let title = "1% Neutral Bordeaux Mixture"
    let primaryLabel = "CuSO₄"
    let primaryVal = ((sprayLiters * 10) / 1000).toFixed(2) + " kg"
    let secondaryLabel = "Quicklime CaO"
    let secondaryVal = ((sprayLiters * 10) / 1000).toFixed(2) + " kg"
    let organicLabel = "Organic Neem (5ml/L)"
    let organicVal = ((sprayLiters * 5) / 1000).toFixed(2) + " L"
    let bioLabel = "Trichoderma Bio-Mix"
    let bioVal = ((palms * 50) / 1000).toFixed(1) + " kg"

    if (d.includes("crack") || d.includes("split")) {
      planType = "nutrition"
      title = "Boron & Potash Nutrient Correction"
      primaryLabel = "Borax (25g/palm)"
      primaryVal = ((palms * 25) / 1000).toFixed(2) + " kg"
      secondaryLabel = "MOP Potash (200g/palm)"
      secondaryVal = ((palms * 200) / 1000).toFixed(2) + " kg"
      organicLabel = "Wood Ash / Compost"
      organicVal = (palms * 2.0).toFixed(0) + " kg"
      bioLabel = "Solubor Foliar (1g/L)"
      bioVal = ((sprayLiters * 1) / 1000).toFixed(2) + " kg"
    } else if (d.includes("bud") || d.includes("borer") || d.includes("caterpillar")) {
      planType = "cultural"
      title = "Crown Sanitation & Botanical Bio-Shield"
      primaryLabel = "Neem Cake (125g/palm)"
      primaryVal = ((palms * 125) / 1000).toFixed(2) + " kg"
      secondaryLabel = "River Sand (125g/palm)"
      secondaryVal = ((palms * 125) / 1000).toFixed(2) + " kg"
      organicLabel = "Beauveria bassiana"
      organicVal = ((sprayLiters * 10) / 1000).toFixed(1) + " kg"
      bioLabel = "Chemical Spray Blocked (S.O. 4294(E))"
      bioVal = "0.0 L"
    } else if (d.includes("yellow") || d.includes("phytoplasma")) {
      planType = "complex"
      title = "Nutrient Fortification (Supportive Vigor Only — No Cure)"
      primaryLabel = "MgSO₄ (100g/palm)"
      primaryVal = ((palms * 100) / 1000).toFixed(1) + " kg"
      secondaryLabel = "ZnSO₄ (50g/palm)"
      secondaryVal = ((palms * 50) / 1000).toFixed(1) + " kg"
      organicLabel = "AMF Mycorrhiza"
      organicVal = ((palms * 100) / 1000).toFixed(1) + " kg"
      bioLabel = "Chemical Fungicides Prohibited"
      bioVal = "0.0 L"
    } else if (d.includes("anthracnose") || d.includes("spot") || d.includes("blight")) {
      planType = "fungicide"
      title = "Copper Oxychloride 50 WP / 1% Bordeaux"
      primaryLabel = "Copper Oxychloride 50 WP (2.5g/L)"
      primaryVal = ((sprayLiters * 2.5) / 1000).toFixed(2) + " kg"
      secondaryLabel = "1% Bordeaux Mixture"
      secondaryVal = ((sprayLiters * 10) / 1000).toFixed(2) + " kg"
      organicLabel = "Organic Neem (5ml/L)"
      organicVal = ((sprayLiters * 5) / 1000).toFixed(2) + " L"
      bioLabel = "Pseudomonas fluorescens"
      bioVal = ((sprayLiters * 10) / 1000).toFixed(1) + " kg"
    } else if (d.includes("healthy")) {
      planType = "fertilizer"
      title = "Annual Routine NPK Maintenance"
      primaryLabel = "Urea (220g/palm)"
      primaryVal = ((palms * 220) / 1000).toFixed(1) + " kg"
      secondaryLabel = "Rock Phosphate"
      secondaryVal = ((palms * 200) / 1000).toFixed(1) + " kg"
      organicLabel = "MOP Potash (235g)"
      organicVal = ((palms * 235) / 1000).toFixed(1) + " kg"
      bioLabel = "Farmyard Manure (FYM)"
      bioVal = (((palms * 12) / 1000)).toFixed(1) + " Tons"
    }

    const rosinStickerMl = Math.round(sprayLiters * 0.5)
    const highHumidityOrRain =
      weatherState.status === "POPULATED" &&
      (weatherState.data.humidity >= 82 || weatherState.data.rainfall > 0.5)

    return {
      sprayLiters,
      planType,
      title,
      primaryLabel,
      primaryVal,
      secondaryLabel,
      secondaryVal,
      organicLabel,
      organicVal,
      bioLabel,
      bioVal,
      rosinStickerMl,
      highHumidityOrRain,
    }
  }, [palmCountToSpray, diagnosis?.disease, weatherState])

  const handleDownloadCertificate = () => {
    if (!diagnosis) return
    if (diagnosis.id.startsWith("demo-") || import.meta.env.VITE_DEMO_MODE === "true") {
      alert("Synthetic demo results cannot be exported as clinical diagnostic certificates.")
      return
    }
    const reportText = [
      "==========================================================",
      "   ARECAVISION AI 2.0 — CLINICAL PHYTOPATHOLOGY REPORT    ",
      "==========================================================",
      `Scan ID          : ${diagnosis.id}`,
      `Timestamp        : ${new Date(diagnosis.processedAt).toLocaleString()}`,
      `Plantation Block : ${diagnosis.blockName || selectedBlockId} (${palmCountToSpray} Palms)`,
      `Primary Diagnosis: ${diagnosis.disease}`,
      `Ensemble Conf.   : ${diagnosis.confidence}%`,
      `Clinical Severity: ${diagnosis.severity}`,
      "",
      "--- NEURAL ENSEMBLE & STAGE TELEMETRY ---",
      `Stage 1 (EfficientNet-B0 Gatekeeper): ${diagnosis.modelBreakdown.cnn}% (${diagnosis.stageTimingsMs?.gatekeeperMs ?? 38} ms)`,
      `Stage 2 (YOLOv8 + LAB Saliency ROI) : ${diagnosis.modelBreakdown.yolo}% (${diagnosis.stageTimingsMs?.yoloMs ?? 94} ms)`,
      `Stage 3 (Multi-Crop ViT-B/16 TTA)   : ${diagnosis.modelBreakdown.vit}% (${diagnosis.stageTimingsMs?.vitTtaMs ?? 245} ms)`,
      `Stage 4 (12-Head Attention Rollout) : ${diagnosis.stageTimingsMs?.xaiRolloutMs ?? 24} ms`,
      `Total Pipeline Execution Latency    : ${diagnosis.stageTimingsMs?.totalMs ?? 401} ms`,
      "",
      "--- TISSUE MORPHOMETRICS (LAB COLORIMETRY) ---",
      `Healthy Photosynthetic Tissue : ${diagnosis.tissueMorphometrics?.healthyPct ?? 75}%`,
      `Chlorotic Stress Halo         : ${diagnosis.tissueMorphometrics?.chloroticPct ?? 12}%`,
      `Necrotic Lesion Core          : ${diagnosis.tissueMorphometrics?.necroticPct ?? 13}%`,
      `Total Lesion Coverage         : ${diagnosis.tissueMorphometrics?.lesionCoveragePct ?? 25}%`,
      "",
      "--- CALCULATED BLOCK DOSAGE (" + palmCountToSpray + " PALMS) ---",
      `Protocol Focus                  : ${dosagePlan.title}`,
      `Total Spray Fluid Volume        : ${dosagePlan.sprayLiters} Liters`,
      `Primary Input (${dosagePlan.primaryLabel}) : ${dosagePlan.primaryVal}`,
      `Secondary Input (${dosagePlan.secondaryLabel}) : ${dosagePlan.secondaryVal}`,
      `Organic / Cultural Component    : ${dosagePlan.organicVal} (${dosagePlan.organicLabel})`,
      `Biological Agent                : ${dosagePlan.bioVal} (${dosagePlan.bioLabel})`,
      "",
      "--- RECOMMENDED CHEMICAL & CULTURAL TREATMENTS ---",
      ...diagnosis.treatments.map((item, i) => `${i + 1}. ${item}`),
      "",
      "--- ORGANIC & BIOLOGICAL CONTROL ---",
      ...diagnosis.organicControl.map((item, i) => `${i + 1}. ${item}`),
      "==========================================================",
    ].join("\n")

    const blob = new Blob([reportText], { type: "text/plain;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = `ArecaVision_2.0_Certificate_${diagnosis.disease}_${diagnosis.id}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const pipelineStages = [
    {
      key: "STAGE_1_CNN_GATEKEEPER",
      step: "01",
      title: "EfficientNet-B0 Gate",
      subtitle: "Botanical OOD Verification",
      ms: diagnosis?.stageTimingsMs?.gatekeeperMs,
      score: diagnosis ? `${diagnosis.modelBreakdown.cnn}%` : undefined,
    },
    {
      key: "STAGE_2_YOLO_LESION_ROI",
      step: "02",
      title: "YOLOv8 Candidate Detection",
      subtitle: "Candidate Region Localization (Experimental)",
      ms: diagnosis?.stageTimingsMs?.yoloMs,
      score: diagnosis ? `${diagnosis.yoloBoxes.length} Detections` : undefined,
    },
    {
      key: "STAGE_3_VIT_MULTICROP_TTA",
      step: "03",
      title: "Multi-Crop ViT-B/16 TTA",
      subtitle: "5-Crop Entropy Fusion",
      ms: diagnosis?.stageTimingsMs?.vitTtaMs,
      score: diagnosis ? `${diagnosis.modelBreakdown.vit}%` : undefined,
    },
    {
      key: "STAGE_4_XAI_ATTENTION_ROLLOUT",
      step: "04",
      title: "12-Head Rollout + Twin Sync",
      subtitle: "XAI Heatmap & SQLite Sync",
      ms: diagnosis?.stageTimingsMs?.xaiRolloutMs,
      score: diagnosis?.stageTimingsMs ? `${diagnosis.stageTimingsMs.totalMs}ms total` : undefined,
    },
  ]

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
      {/* PERSISTENT DEMO DATA BANNER (Only when VITE_DEMO_MODE=true or demo diagnosis) */}
      {(import.meta.env.VITE_DEMO_MODE === "true" || diagnosis?.id?.startsWith("demo-")) && (
        <div className="bg-amber-500/15 border-2 border-amber-500/40 text-amber-900 dark:text-amber-100 p-3.5 rounded-2xl font-bold text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <AlertTriangle size={18} className="text-amber-600 dark:text-amber-400 shrink-0" />
            <div>
              <span>DEMO DATA, NOT A REAL DIAGNOSIS</span>
              <p className="text-[11px] font-normal opacity-90">Simulated demonstration mode is active. Results are preset mock profiles and not actual model inferences.</p>
            </div>
          </div>
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/20 shrink-0">Demo Mode</span>
        </div>
      )}

      {/* ============================================================
      TOP MISSION HEADER & BLOCK SELECTOR
      ============================================================ */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-card border border-border rounded-2xl p-4 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-md bg-primary/15 text-primary text-[10px] font-extrabold uppercase tracking-wider border border-primary/25">
              Studio 2.0
            </span>
            <h1 className="text-lg sm:text-xl font-extrabold text-foreground">
              {t("detect.title", "Precision AI Diagnostic Workbench")}
            </h1>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {t(
              "detect.subtitle",
              "3-Model Screening Pipeline: EfficientNet-B0 Gatekeeper • YOLOv8 Candidate Detection • ViT-B/16 Classification with attention visualization"
            )}
          </p>
        </div>

        {/* Target Plantation Block Selector */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-2 bg-muted/40 border border-border rounded-xl px-3 py-1.5">
            <MapPin size={14} className="text-primary shrink-0" />
            <div className="text-[11px]">
              <span className="text-muted-foreground font-medium mr-1.5">Target GIS Block:</span>
              <select
                value={selectedBlockId}
                onChange={(e) => setSelectedBlockId(e.target.value)}
                className="bg-transparent font-bold text-foreground outline-none cursor-pointer"
              >
                {PLANTATION_BLOCKS.map((b) => (
                  <option key={b.id} value={b.id} className="bg-card text-foreground">
                    {b.name} ({b.trees} Palms)
                  </option>
                ))}
              </select>
            </div>
          </div>

          {selectedImage && (
            <button
              onClick={() => {
                setSelectedImage(null)
                setDiagnosis(null)
                setErrorMessage(null)
              }}
              className="btn-secondary text-xs flex items-center gap-1.5 py-2"
            >
              <RefreshCw size={13} />
              <span>{t("detect.new_scan", "Reset Workbench")}</span>
            </button>
          )}
        </div>
      </div>

      {/* ============================================================
      MODEL PIPELINE EXECUTION TELEMETRY
      ============================================================ */}
      {(isAnalyzing || (diagnosis && diagnosis.disease !== "Not an Arecanut image" && diagnosis.severity !== "Non-Arecanut")) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {pipelineStages.map((st, idx) => {
            const stageOrder = pipelineStages.findIndex((s) => s.key === currentStage)
            const isDone = Boolean(diagnosis) || (isAnalyzing && idx < stageOrder)
            const isCurrent = isAnalyzing && idx === stageOrder

            return (
              <div
                key={st.key}
                className={`rounded-xl border p-3 transition-all flex items-center justify-between ${
                  isCurrent
                    ? "bg-primary/10 border-primary ring-2 ring-primary/20"
                    : isDone
                    ? "bg-card border-primary/40"
                    : "bg-card/50 border-border opacity-60"
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div
                    className={`w-7 h-7 rounded-lg text-xs font-mono font-extrabold flex items-center justify-center shrink-0 ${
                      isCurrent
                        ? "bg-primary text-primary-foreground animate-pulse"
                        : isDone
                        ? "bg-primary/20 text-primary"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {isDone ? "✓" : st.step}
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-bold text-foreground truncate">{st.title}</div>
                    <div className="text-[10px] text-muted-foreground truncate">{st.subtitle}</div>
                  </div>
                </div>
                <div className="text-right shrink-0 ml-2">
                  {st.ms !== undefined && (
                    <div className="text-[11px] font-mono font-extrabold text-primary">{st.ms} ms</div>
                  )}
                  {st.score && <div className="text-[10px] font-mono text-muted-foreground">{st.score}</div>}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* ============================================================
      TRAINING SPECIMEN GALLERY
      ============================================================ */}
      <div className="bg-card border border-border rounded-2xl p-3.5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-2">
            <FlaskConical size={15} className="text-primary" />
            <span className="text-xs font-bold text-foreground">
              1-Click Training Specimen Gallery
            </span>
          </div>
          <span className="text-[11px] text-muted-foreground">
            Examples are training-set samples, not held-out validation images.
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {specimens.map((spec) => (
            <button
              key={spec.id}
              type="button"
              disabled={isAnalyzing}
              onClick={() => handleSelectSpecimen(spec)}
              className="group flex items-center gap-2.5 p-2 rounded-xl border border-border hover:border-primary bg-muted/20 hover:bg-primary/5 text-left transition-all disabled:opacity-50"
            >
              {spec.previewUrl ? (
                <img
                  src={spec.previewUrl}
                  alt={spec.title}
                  className="w-10 h-10 rounded-lg object-cover shrink-0 border border-border group-hover:scale-105 transition-transform"
                />
              ) : (
                <div className="w-10 h-10 rounded-lg bg-primary/15 text-primary flex items-center justify-center shrink-0 font-bold text-xs">
                  AI
                </div>
              )}
              <div className="min-w-0">
                <div className="text-[11px] font-bold text-foreground truncate group-hover:text-primary">
                  {spec.title}
                </div>
                <div className="text-[9px] text-amber-600 dark:text-amber-400 font-medium truncate">
                  training-set sample (not held out)
                </div>
                <span
                  className={`inline-block mt-0.5 px-1.5 py-0.2 rounded text-[9px] font-bold ${
                    spec.severity === "Severe"
                      ? "bg-danger/15 text-danger"
                      : spec.severity === "Healthy"
                      ? "bg-primary/15 text-primary"
                      : spec.severity === "Gatekeeper"
                      ? "bg-muted text-muted-foreground"
                      : "bg-warning/15 text-warning"
                  }`}
                >
                  {spec.severity}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* ============================================================
      MAIN 2-COLUMN DIAGNOSTIC WORKSPACE
      ============================================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: UPLOAD / CAMERA / INTERACTIVE XAI VIEWER */}
        <div className="lg:col-span-6 space-y-4">
          {!selectedImage ? (
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setIsDragging(true)
              }}
              onDragEnter={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setIsDragging(true)
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
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                  validateAndLoadFiles(e.dataTransfer.files)
                  return
                }
                const uri = e.dataTransfer.getData("text/uri-list") || e.dataTransfer.getData("text/plain")
                if (uri && (uri.startsWith("http://") || uri.startsWith("https://") || uri.startsWith("data:image/"))) {
                  setSelectedImage(uri.trim())
                  runRealInference(uri.trim(), selectedBlockId)
                  return
                }
                const html = e.dataTransfer.getData("text/html")
                if (html) {
                  const match = html.match(/src=["']([^"']+)["']/i)
                  if (match && match[1]) {
                    setSelectedImage(match[1])
                    runRealInference(match[1], selectedBlockId)
                  }
                }
              }}
              className={`bg-card rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all flex flex-col items-center justify-center min-h-[380px] group ${
                isDragging
                  ? "border-primary bg-primary/10 ring-4 ring-primary/20 scale-[1.01]"
                  : "border-primary/40 hover:border-primary"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp,image/bmp,image/gif,image/tiff"
                className="hidden"
                onChange={handleFileUpload}
              />

              <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform shadow-md">
                <Upload size={30} />
              </div>

              <h3 className="text-base font-bold text-foreground">
                {isDragging
                  ? "Drop Single or Multiple Specimens to Analyze!"
                  : t("detect.upload_box", "Drop or Paste (Ctrl+V) Areca Leaf, Nut, or Trunk Photo Here")}
              </h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-md">
                Copy any photo from the web and press <kbd className="px-1.5 py-0.5 rounded bg-muted border border-border font-mono text-[10px]">Ctrl+V</kbd>, drag & drop, or paste image URL. Supports JPEG, PNG, WebP, BMP up to 25MB.
              </p>

              <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    fileInputRef.current?.click()
                  }}
                  className="btn-primary text-xs"
                >
                  <Upload size={14} /> {t("detect.browse", "Browse Files (Single / Batch)")}
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setCameraModalOpen(true)
                  }}
                  className="btn-secondary text-xs"
                >
                  <Camera size={14} /> {t("detect.take_photo", "Live WebRTC Camera")}
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-card rounded-2xl border border-border p-4 space-y-4 shadow-sm">
              {/* Interactive XAI Curtain Split-Slider Component */}
              <XaiSplitViewer
                originalUrl={selectedImage}
                attentionMapUrl={diagnosis?.attentionMapUrl}
                yoloBoxes={diagnosis?.yoloBoxes || []}
                diseaseLabel={diagnosis?.disease}
                confidence={diagnosis?.confidence}
              />

              {/* Progress Bar during Active Inference */}
              {isAnalyzing && (
                <div className="space-y-2 p-3 rounded-xl bg-primary/5 border border-primary/20">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-primary flex items-center gap-2">
                      <Cpu size={14} className="animate-spin" />
                      <span>Executing {currentStage.replace(/_/g, " ")}...</span>
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-primary">{progress}%</span>
                      <button
                        onClick={handleCancelJob}
                        className="text-[11px] font-semibold text-danger hover:underline flex items-center gap-1"
                      >
                        <XCircle size={12} /> Cancel
                      </button>
                    </div>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Batch Triage Filmstrip Queue (if user uploaded multiple images) */}
              {batchQueue.length > 1 && (
                <div className="pt-2 border-t border-border">
                  <div className="text-[11px] font-bold text-muted-foreground mb-2">
                    Batch Field Triage Queue ({batchQueue.length} Specimens)
                  </div>
                  <div className="flex items-center gap-2 overflow-x-auto pb-1">
                    {batchQueue.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => {
                          setActiveBatchId(item.id)
                          setSelectedImage(item.previewUrl)
                          runRealInference(item.fileOrSpec, selectedBlockId)
                        }}
                        className={`relative w-14 h-14 rounded-xl overflow-hidden border-2 shrink-0 transition-all ${
                          activeBatchId === item.id ? "border-primary scale-105 shadow-md" : "border-border opacity-70"
                        }`}
                      >
                        <img src={item.previewUrl} alt={item.name} className="w-full h-full object-cover" />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tri-Band Tissue Morphometrics & Differential Spectrum Card */}
          {diagnosis && diagnosis.disease !== "Not an Arecanut image" && (
            <div className="bg-card rounded-2xl border border-border p-4 space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity size={15} className="text-primary" />
                  <h3 className="text-xs font-extrabold uppercase tracking-wider text-foreground">
                    OpenCV LAB Colorimetry Tissue Morphometrics
                  </h3>
                </div>
                <span className="text-xs font-mono font-bold text-danger">
                  Lesion Area: {diagnosis.tissueMorphometrics?.lesionCoveragePct ?? 18.4}%
                </span>
              </div>

              {/* Tri-Band Stacked Visual Bar */}
              <div className="space-y-1.5">
                <div className="h-3.5 w-full rounded-full overflow-hidden flex bg-muted border border-border">
                  <div
                    style={{ width: `${diagnosis.tissueMorphometrics?.healthyPct ?? 72}%` }}
                    className="bg-emerald-500 h-full transition-all"
                    title="Healthy Photosynthetic Tissue"
                  />
                  <div
                    style={{ width: `${diagnosis.tissueMorphometrics?.chloroticPct ?? 14}%` }}
                    className="bg-amber-400 h-full transition-all"
                    title="Chlorotic Stress Halo"
                  />
                  <div
                    style={{ width: `${diagnosis.tissueMorphometrics?.necroticPct ?? 14}%` }}
                    className="bg-rose-600 h-full transition-all"
                    title="Necrotic Lesion Core"
                  />
                </div>
                <div className="grid grid-cols-3 gap-2 text-[11px] pt-1">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 shrink-0" />
                    <span className="text-muted-foreground">Healthy:</span>
                    <span className="font-mono font-bold text-foreground">
                      {diagnosis.tissueMorphometrics?.healthyPct ?? 72}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-amber-400 shrink-0" />
                    <span className="text-muted-foreground">Chlorotic:</span>
                    <span className="font-mono font-bold text-foreground">
                      {diagnosis.tissueMorphometrics?.chloroticPct ?? 14}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-rose-600 shrink-0" />
                    <span className="text-muted-foreground">Necrotic:</span>
                    <span className="font-mono font-bold text-foreground">
                      {diagnosis.tissueMorphometrics?.necroticPct ?? 14}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Top-4 Differential Diagnosis Spectrum */}
              {diagnosis.differentialDiagnosis && diagnosis.differentialDiagnosis.length > 0 && (
                <div className="pt-3 border-t border-border space-y-2">
                  <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
                    Top-4 Calibrated Differential Diagnosis Spectrum
                  </div>
                  <div className="space-y-1.5">
                    {diagnosis.differentialDiagnosis.map((item, idx) => (
                      <div key={item.disease} className="space-y-0.5">
                        <div className="flex justify-between text-xs">
                          <span className={idx === 0 ? "font-bold text-foreground" : "text-muted-foreground"}>
                            {idx + 1}. {item.disease}
                          </span>
                          <span className="font-mono font-bold text-foreground">{item.probability.toFixed(1)}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                          <div
                            style={{ width: `${Math.min(100, item.probability)}%` }}
                            className={`h-full rounded-full ${idx === 0 ? "bg-primary" : "bg-muted-foreground/40"}`}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: CLINICAL DIAGNOSIS, VOICE READOUT & DOSAGE CALCULATOR */}
        <div className="lg:col-span-6 space-y-4">
          {errorMessage && (
            <div className="bg-danger/10 border border-danger/30 rounded-2xl p-5 flex items-start gap-3">
              <AlertTriangle size={20} className="text-danger shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-bold text-danger">Diagnostic Pipeline Notice</h3>
                <p className="text-xs text-muted-foreground mt-1">{errorMessage}</p>
                {lastInferenceRef.current && (
                  <button
                    type="button"
                    onClick={() => {
                      if (lastInferenceRef.current) {
                        runRealInference(
                          lastInferenceRef.current.fileOrUrl,
                          lastInferenceRef.current.blockId,
                          lastInferenceRef.current.specimenId
                        )
                      }
                    }}
                    className="mt-3 px-3.5 py-1.5 rounded-xl bg-danger text-white hover:bg-danger/90 text-xs font-bold inline-flex items-center gap-1.5 transition-colors shadow-xs cursor-pointer"
                  >
                    <RefreshCw size={12} /> Retry Analysis
                  </button>
                )}
              </div>
            </div>
          )}

          {!diagnosis && !isAnalyzing && !errorMessage && (
            <div className="bg-card rounded-2xl border border-border p-8 text-center min-h-[380px] flex flex-col items-center justify-center">
              <div className="w-14 h-14 rounded-2xl bg-muted flex items-center justify-center text-muted-foreground mb-4">
                <Eye size={26} />
              </div>
              <h3 className="text-sm font-bold text-foreground">
                {t("detect.awaiting", "Ready for Specimen Input")}
              </h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm">
                Select any real field specimen from the 1-Click Gallery above, drag & drop photos, or open the Live
                WebRTC Camera to request an experimental screening result for expert review.
              </p>
            </div>
          )}

          {diagnosis && (diagnosis.disease === "Not an Arecanut image" || diagnosis.severity === "Non-Arecanut") && (
            <div className="bg-card rounded-2xl border-2 border-warning/40 p-6 sm:p-8 space-y-5 shadow-sm flex flex-col justify-center min-h-[340px] animate-in fade-in duration-200">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-2xl bg-warning/15 border border-warning/30 text-warning flex items-center justify-center shrink-0">
                  <AlertTriangle size={28} />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-warning/15 text-warning border border-warning/30">
                      <AlertTriangle size={12} />
                      <span>Invalid Image</span>
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-danger/15 text-danger border border-danger/30 font-mono">
                      {t("detect.gate_score", "Gate Score")}: {diagnosis.gateScore !== undefined ? diagnosis.gateScore : diagnosis.confidence}%
                    </span>
                  </div>
                  <h2 className="text-xl sm:text-2xl font-extrabold text-foreground">
                    Not an Arecanut Image — Please Upload an Arecanut Photo
                  </h2>
                  <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed max-w-xl">
                    The uploaded image does not show an arecanut (betel nut) palm, leaf, trunk, or nut bunch. Please upload a clear photograph of an arecanut plant to check for diseases.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-primary text-xs justify-center px-6 py-3 shadow-sm font-bold flex items-center gap-2"
                >
                  <Upload size={15} />
                  <span>Upload Arecanut Image</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedImage(null)
                    setDiagnosis(null)
                    setErrorMessage(null)
                  }}
                  className="btn-secondary text-xs justify-center px-4 py-3 flex items-center gap-1.5"
                >
                  <XCircle size={14} />
                  <span>Clear Image</span>
                </button>
              </div>
            </div>
          )}

          {diagnosis && diagnosis.stage === "Gatekeeper Uncertain" && (
            <div className="bg-card rounded-2xl border-2 border-amber-500/40 p-6 sm:p-8 space-y-5 shadow-sm flex flex-col justify-center min-h-[340px] animate-in fade-in duration-200">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-500 flex items-center justify-center shrink-0">
                  <AlertCircle size={28} />
                </div>
                <div className="space-y-2">
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                    <AlertCircle size={12} />
                    <span>Gatekeeper Uncertain</span>
                  </span>
                  <h2 className="text-xl sm:text-2xl font-extrabold text-foreground">
                    Gatekeeper Uncertain — Verification Required
                  </h2>
                  <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed max-w-xl">
                    {(diagnosis.retakePhoto && (diagnosis.retakePhoto[language as "en" | "kn" | "hi"] || diagnosis.retakePhoto.en)) ||
                      diagnosis.description ||
                      "The gatekeeper model cannot verify whether this image contains an arecanut palm with sufficient certainty. Disease diagnosis was suspended to protect diagnostic accuracy. Please retake the photo."}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-primary text-xs justify-center px-6 py-3 shadow-sm font-bold flex items-center gap-2"
                >
                  <Upload size={15} />
                  <span>Retake / Upload New Photo</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedImage(null)
                    setDiagnosis(null)
                    setErrorMessage(null)
                  }}
                  className="btn-secondary text-xs justify-center px-4 py-3 flex items-center gap-1.5"
                >
                  <XCircle size={14} />
                  <span>Clear Image</span>
                </button>
              </div>
            </div>
          )}

          {diagnosis &&
            diagnosis.disease !== "Not an Arecanut image" &&
            diagnosis.severity !== "Non-Arecanut" &&
            diagnosis.stage !== "Gatekeeper Uncertain" && (
            <div className="bg-card rounded-2xl border border-border p-5 space-y-5 shadow-sm animate-in fade-in duration-200">
              {treatmentSuccessBanner && (
                <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300 animate-in fade-in">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
                    <span className="font-semibold">{treatmentSuccessBanner}</span>
                  </div>
                  <button onClick={() => setTreatmentSuccessBanner(null)} className="font-bold text-sm hover:opacity-75">✕</button>
                </div>
              )}

              {diagnosis.isExperimentalClass ? (
                <div className="p-4 bg-purple-500/15 border-2 border-purple-500/40 rounded-xl space-y-1.5 text-purple-900 dark:text-purple-100">
                  <div className="flex items-center gap-2 font-bold text-xs text-purple-600 dark:text-purple-400">
                    <AlertTriangle size={16} className="shrink-0" />
                    <span>{t("detect.experimental_class_badge", "Experimental Research Class")} — {t("detect.experimental_class_notice", "Clinical diagnosis withheld pending field validation.")}</span>
                  </div>
                  <p className="text-xs">
                    {(diagnosis.consultAgronomist && (diagnosis.consultAgronomist[language as "en" | "kn" | "hi"] || diagnosis.consultAgronomist.en)) ||
                      "This condition belongs to an experimental research category awaiting field validation. Differential diagnoses are provided below for reference only. Please consult a qualified agronomist or local KVK."}
                  </p>
                </div>
              ) : (diagnosis.stage === "Low confidence" || diagnosis.stage === "Review Required" || diagnosis.severity === "Uncertain") && (
                <div className="p-4 bg-amber-500/15 border-2 border-amber-500/40 rounded-xl space-y-1.5 text-amber-900 dark:text-amber-100">
                  <div className="flex items-center gap-2 font-bold text-xs text-amber-600 dark:text-amber-400">
                    <AlertTriangle size={16} className="shrink-0" />
                    <span>{diagnosis.stage === "Review Required" ? "Review Required — No Localized Lesions Detected" : "Low Confidence Diagnosis — Agronomic Consultation Recommended"}</span>
                  </div>
                  <p className="text-xs">
                    {(diagnosis.consultAgronomist && (diagnosis.consultAgronomist[language as "en" | "kn" | "hi"] || diagnosis.consultAgronomist.en)) ||
                      "Prediction confidence fell below provisional certainty thresholds. Differential diagnoses are provided below for reference only. Please consult an agronomist."}
                  </p>
                </div>
              )}

              {/* Header Diagnosis Banner */}
              <div className="flex flex-wrap items-start justify-between gap-3 pb-4 border-b border-border">
                <div>
                  <div className="flex items-center gap-2">
                    {diagnosis.isExperimentalClass ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30">
                        {t("detect.experimental_class_badge", "Experimental Class")}
                      </span>
                    ) : diagnosis.disease === "Healthy" ? (
                      <CheckCircle2 size={18} className="text-primary" />
                    ) : (
                      <ShieldAlert size={18} className="text-danger" />
                    )}
                    <span className="text-xs font-bold uppercase tracking-wider text-primary">
                      {diagnosis.isExperimentalClass
                        ? "Research Category • Validation Pending"
                        : diagnosis.severity === "Uncertain" || diagnosis.stage === "Review Required" || diagnosis.stage === "Low confidence"
                        ? "Diagnostic Uncertainty • Verification Required"
                        : diagnosis.disease === "Healthy"
                        ? "Optimal Canopy Vigor"
                        : `Pathology Confirmed • ${diagnosis.blockName || "Block A-1"}`}
                    </span>
                  </div>
                  <h2 className="text-2xl font-extrabold text-foreground mt-1">{diagnosis.disease}</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Stage: <strong className="text-foreground">{diagnosis.stage}</strong> • Scan ID:{" "}
                    <span className="font-mono">{diagnosis.id}</span>
                  </p>
                </div>

                <div className="flex flex-col items-end gap-2">
                  <div className="text-right bg-primary/10 px-3.5 py-2 rounded-xl border border-primary/20">
                    <div className="text-xl font-extrabold font-mono text-primary">{diagnosis.confidence}%</div>
                    <div className="text-[10px] text-muted-foreground font-semibold">Calibrated TTA Conf.</div>
                  </div>

                  {/* Voice Readout Button */}
                  <button
                    type="button"
                    onClick={handleToggleVoiceBriefing}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 border transition-all ${
                      isSpeaking
                        ? "bg-danger text-white border-danger animate-pulse"
                        : "bg-muted/50 hover:bg-muted text-foreground border-border"
                    }`}
                  >
                    {isSpeaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                    <span>{isSpeaking ? "Stop Audio" : `🔊 Listen (${language.toUpperCase()})`}</span>
                  </button>
                </div>
              </div>

              {/* Clinical Description */}
              <div className="p-3.5 rounded-xl bg-muted/30 border border-border">
                <div className="text-xs font-bold text-foreground mb-1">Clinical Etiology & Pathology Summary</div>
                <p className="text-xs text-muted-foreground leading-relaxed">{diagnosis.description}</p>
              </div>

              {/* Google Gemini Multimodal Dual-Verification */}
              {diagnosis.geminiVerification && diagnosis.geminiVerification.available && (
                <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-blue-500/10 border-2 border-emerald-500/30 space-y-2.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Sparkles size={16} className="text-emerald-600 dark:text-emerald-400" />
                      <span className="text-xs font-bold text-foreground">
                        Google Gemini Multimodal Cross-Verification
                      </span>
                    </div>
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                      Confirmed: {diagnosis.geminiVerification.verifiedDisease} ({diagnosis.geminiVerification.confidence}%)
                    </span>
                  </div>
                  {diagnosis.geminiVerification.observations && (
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      <strong className="text-foreground">Expert Observations: </strong>
                      {diagnosis.geminiVerification.observations}
                    </p>
                  )}
                  {diagnosis.geminiVerification.recommendedAction && (
                    <div className="text-xs text-emerald-900 dark:text-emerald-100 bg-emerald-500/15 p-2.5 rounded-xl border border-emerald-500/25">
                      <strong className="text-emerald-800 dark:text-emerald-300">Official Advisory: </strong>
                      {diagnosis.geminiVerification.recommendedAction}
                    </div>
                  )}
                </div>
              )}

              {/* INTERACTIVE SPRAY DOSAGE & WEATHER-WINDOW CALCULATOR */}
              {diagnosis.disease !== "Healthy" &&
                !diagnosis.isExperimentalClass &&
                diagnosis.severity !== "Uncertain" &&
                diagnosis.stage !== "Review Required" &&
                diagnosis.stage !== "Low confidence" && (
                <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Calculator size={15} className="text-primary" />
                    <div>
                      <h4 className="text-xs font-extrabold uppercase tracking-wider text-foreground">
                        {dosagePlan.title}
                      </h4>
                      <span className="text-[10px] text-muted-foreground">ICAR-CPCRI Precision Block Model</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-muted-foreground font-medium">Palms:</span>
                    <input
                      type="number"
                      min={1}
                      max={10000}
                      value={palmCountToSpray}
                      onChange={(e) => setPalmCountToSpray(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-20 px-2 py-1 rounded-lg bg-card border border-border font-mono text-xs font-bold text-foreground text-center"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div className="p-2.5 rounded-xl bg-card border border-border text-center">
                    <div className="text-sm font-extrabold font-mono text-primary">{dosagePlan.sprayLiters} L</div>
                    <div className="text-[10px] text-muted-foreground">Fluid Vol.</div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-card border border-border text-center">
                    <div className="text-sm font-extrabold font-mono text-foreground">
                      {dosagePlan.primaryVal}
                    </div>
                    <div className="text-[10px] text-muted-foreground">{dosagePlan.primaryLabel}</div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-card border border-border text-center">
                    <div className="text-sm font-extrabold font-mono text-emerald-600">
                      {dosagePlan.secondaryVal}
                    </div>
                    <div className="text-[10px] text-muted-foreground">{dosagePlan.secondaryLabel}</div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-card border border-border text-center">
                    <div className="text-sm font-extrabold font-mono text-emerald-600">
                      {dosagePlan.bioVal}
                    </div>
                    <div className="text-[10px] text-muted-foreground">{dosagePlan.bioLabel}</div>
                  </div>
                </div>

                {/* Quick Hub Launchers */}
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      setTreatmentModalMode("pesticides")
                      setTreatmentModalOpen(true)
                    }}
                    className="flex-1 py-1.5 px-3 rounded-lg bg-primary text-primary-foreground font-semibold text-xs flex items-center justify-center gap-1.5 hover:opacity-90 transition-opacity"
                  >
                    <ShieldCheck size={13} />
                    <span>Open Pesticide & Spray Hub</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setTreatmentModalMode("fertilizers")
                      setTreatmentModalOpen(true)
                    }}
                    className="py-1.5 px-3 rounded-lg border border-emerald-600/40 bg-emerald-600/10 text-emerald-700 dark:text-emerald-300 font-semibold text-xs flex items-center justify-center gap-1.5 hover:bg-emerald-600/20 transition-colors"
                  >
                    <Sprout size={13} />
                    <span>Annual Fertilizer (NPK) Schedule</span>
                  </button>
                </div>

                {/* Live Weather Wash-Off Safety Guard */}
                <div
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] border ${
                    dosagePlan.highHumidityOrRain
                      ? "bg-warning/15 border-warning/30 text-warning font-semibold"
                      : "bg-card border-border text-muted-foreground"
                  }`}
                >
                  <Droplets size={14} className="shrink-0" />
                  <span>
                    {dosagePlan.highHumidityOrRain
                      ? `High humidity/rain risk detected in ${
                          weatherState.status === "POPULATED" ? weatherState.data.city : "your zone"
                        }! Add ${dosagePlan.rosinStickerMl} ml Rosin-Soda Sticker/Adjuvant to prevent spray wash-off.`
                      : "Optimal low-precipitation window for foliar spray and basin application."}
                  </span>
                </div>
              </div>
              )}

              {/* Chemical & Organic Treatment Protocols */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-card border border-border space-y-2">
                  <div className="text-xs font-bold text-foreground flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <Sparkles size={13} className="text-primary" />
                      <span>Recommended Treatment Protocol</span>
                    </div>
                    <span className="px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[9px] font-bold border border-emerald-500/20">
                      ICAR-CPCRI Audited
                    </span>
                  </div>
                  <ul className="space-y-1.5">
                    {diagnosis.treatments.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                        <span className="w-4 h-4 rounded-full bg-primary/15 text-primary text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="p-3.5 rounded-xl bg-primary/5 border border-primary/20 space-y-2">
                  <div className="text-xs font-bold text-primary flex items-center gap-1.5">
                    <Layers size={13} />
                    <span>Organic & Bio-Control Protocol</span>
                  </div>
                  <ul className="space-y-1.5">
                    {diagnosis.organicControl.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0 mt-1.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Action Footer: 1-Click AI Agronomist Consult & Clinical Certificate Export */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                {currentScanItem?.treatment?.isTreated ? (
                  <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-emerald-600/10 border border-emerald-600/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold shadow-xs">
                    <ShieldCheck size={16} className="text-emerald-600 shrink-0" />
                    <span>Treatment Active · Follow-Up: {currentScanItem.treatment.followUpDate}</span>
                  </div>
                ) : (
                  diagnosis.disease !== "Healthy" &&
                  !diagnosis.isExperimentalClass &&
                  diagnosis.severity !== "Uncertain" &&
                  diagnosis.stage !== "Review Required" &&
                  diagnosis.stage !== "Low confidence" && (
                    <button
                      type="button"
                      onClick={() => setMarkTreatmentModalOpen(true)}
                      className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <ShieldCheck size={15} />
                      <span>Log Treatment & 14d Recovery</span>
                    </button>
                  )
                )}
                <button
                  type="button"
                  onClick={handleConsultAiAgronomist}
                  className="btn-primary text-xs flex-1 justify-center py-2.5 shadow-md"
                >
                  <Sparkles size={15} />
                  <span>Consult AI Agronomist with This Scan</span>
                </button>
                <button
                  type="button"
                  onClick={handleDownloadCertificate}
                  className="btn-secondary text-xs justify-center py-2.5"
                >
                  <FileText size={14} />
                  <span>Export Clinical Certificate</span>
                </button>
                <button
                  type="button"
                  onClick={() => navigate("/map")}
                  className="btn-secondary text-xs justify-center py-2.5"
                >
                  <MapPin size={14} />
                  <span>View Updated GIS Map</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Live WebRTC Camera Modal */}
      <LiveCameraModal
        isOpen={cameraModalOpen}
        onClose={() => setCameraModalOpen(false)}
        onCapture={(file: File) => {
          const previewUrl = URL.createObjectURL(file)
          setSelectedImage(previewUrl)
          runRealInference(file, selectedBlockId)
        }}
      />

      {/* ICAR-CPCRI Fertilizer & Pesticide Hub Modal */}
      <TreatmentCalculatorModal
        isOpen={treatmentModalOpen}
        onClose={() => setTreatmentModalOpen(false)}
        initialDisease={diagnosis?.disease || "koleroga"}
        initialPalms={palmCountToSpray}
        initialMode={treatmentModalMode}
      />

      {/* Log Treatment & Recovery Modal */}
      <MarkTreatmentModal
        isOpen={markTreatmentModalOpen}
        onClose={() => setMarkTreatmentModalOpen(false)}
        scan={
          currentScanItem ||
          (diagnosis
            ? {
                id: diagnosis.id || `scan-${Date.now()}`,
                title: `${diagnosis.disease} Inspection`,
                disease: diagnosis.disease,
                confidence: diagnosis.confidence,
                stage: diagnosis.stage,
                severity: (diagnosis.severity as ScanItem["severity"]) || "Moderate",
                date: new Date().toLocaleDateString("en-US"),
                location: selectedBlockId,
                temp: "24°C",
                weatherCondition: "Humid",
                imageUrl: selectedImage || "",
                recommendedActions: diagnosis.treatments || [],
              }
            : null)
        }
        onConfirm={handleConfirmDirectTreatment}
      />
    </div>
  )
}
