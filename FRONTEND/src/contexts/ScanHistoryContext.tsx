import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react"
import { safeGetJSON, safeSetJSON } from "../utils/safeStorage"
import { apiRequest } from "../services/apiClient"

export interface TreatmentRecord {
  isTreated: boolean
  treatedAt: string
  treatmentType: "chemical" | "organic"
  chemicalUsed: string
  dosageNotes?: string
  followUpDate: string
  status: "pending" | "treated" | "recovering" | "cleared"
}

export interface ScanItem {
  id: string
  title: string
  disease: string
  confidence: number
  stage: string
  severity: "Low" | "Moderate" | "High" | "Critical" | "Healthy" | "Mild" | "Severe" | "Non-Arecanut" | "Uncertain"
  date: string
  imageUrl: string
  location: string
  temp: string
  weatherCondition: string
  recommendedActions: string[]
  treatment?: TreatmentRecord
}

interface ScanHistoryContextType {
  scans: ScanItem[]
  isLoading: boolean
  addScan: (scan: Omit<ScanItem, "id" | "date">) => ScanItem
  deleteScan: (id: string) => void
  clearHistory: () => void
  refreshScans: () => Promise<void>
  markTreated: (id: string, details: { treatmentType: "chemical" | "organic"; chemicalUsed: string; notes?: string; followUpDate?: string }) => void
}

const ScanHistoryContext = createContext<ScanHistoryContextType>({
  scans: [],
  isLoading: false,
  addScan: () => ({} as ScanItem),
  deleteScan: () => null,
  clearHistory: () => null,
  refreshScans: async () => {},
  markTreated: () => null,
})

import { getSampleImageForDisease } from "../utils/imageFallback"

const STORAGE_KEY = "arecavision_scan_history"

export const ScanHistoryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [scans, setScans] = useState<ScanItem[]>(() => {
    const raw = safeGetJSON<ScanItem[]>(STORAGE_KEY, [], Array.isArray)
    return raw.map((item) => ({
      ...item,
      imageUrl: getSampleImageForDisease(item.disease, item.imageUrl),
    }))
  })
  const [isLoading, setIsLoading] = useState(false)

  const fetchBackendScans = useCallback(async () => {
    try {
      setIsLoading(true)
      const data = await apiRequest<any[]>("/scans", { method: "GET" })
      if (Array.isArray(data) && data.length > 0) {
        const mapped: ScanItem[] = data.map((item) => ({
          id: item.id || `scan-${Date.now()}`,
          title: `${item.disease || "Arecanut"} Scan`,
          disease: item.disease || "Unknown",
          confidence: typeof item.confidence === "number" ? item.confidence : 90.0,
          stage: item.status || "Completed",
          severity: (item.severity as ScanItem["severity"]) || "Moderate",
          date: item.date || new Date().toLocaleDateString("en-US"),
          imageUrl: getSampleImageForDisease(item.disease, item.imageUrl),
          location: item.block || "Block A-1",
          temp: "24°C",
          weatherCondition: "Humid",
          recommendedActions: ["Maintain field hygiene", "Monitor canopy closely"],
        }))
        setScans(mapped)
      }
    } catch (e) {
      console.warn("Could not fetch scans from backend SQLite, using local cache:", e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBackendScans()
  }, [fetchBackendScans])

  useEffect(() => {
    safeSetJSON(STORAGE_KEY, scans)
  }, [scans])

  const addScan = useCallback((scanData: Omit<ScanItem, "id" | "date">): ScanItem => {
    const newScan: ScanItem = {
      ...scanData,
      id: "scan-" + Date.now(),
      imageUrl: getSampleImageForDisease(scanData.disease, scanData.imageUrl),
      date: new Date().toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }),
    }
    setScans((prev) => [newScan, ...prev])
    return newScan
  }, [])

  const deleteScan = useCallback((id: string) => {
    setScans((prev) => prev.filter((item) => item.id !== id))
    // Call backend delete asynchronously
    apiRequest(`/scans/${id}`, { method: "DELETE" }).catch(() => {})
  }, [])

  const clearHistory = useCallback(() => {
    setScans([])
  }, [])

  const markTreated = useCallback(
    (
      id: string,
      details: {
        treatmentType: "chemical" | "organic"
        chemicalUsed: string
        notes?: string
        followUpDate?: string
      }
    ) => {
      const now = new Date()
      const followUp = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000)
      const defaultFollowUpStr = followUp.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
      const followUpStr = details.followUpDate || defaultFollowUpStr
      const treatedStr = now.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })

      setScans((prev) =>
        prev.map((scan) => {
          if (scan.id !== id) return scan
          return {
            ...scan,
            treatment: {
              isTreated: true,
              treatedAt: treatedStr,
              treatmentType: details.treatmentType,
              chemicalUsed: details.chemicalUsed,
              dosageNotes: details.notes,
              followUpDate: followUpStr,
              status: "recovering" as const,
            },
          }
        })
      )
    },
    []
  )

  const contextValue = useMemo(() => ({
    scans,
    isLoading,
    addScan,
    deleteScan,
    clearHistory,
    refreshScans: fetchBackendScans,
    markTreated,
  }), [scans, isLoading, addScan, deleteScan, clearHistory, fetchBackendScans, markTreated])

  return (
    <ScanHistoryContext.Provider value={contextValue}>
      {children}
    </ScanHistoryContext.Provider>
  )
}


export const useScanHistory = () => useContext(ScanHistoryContext)
