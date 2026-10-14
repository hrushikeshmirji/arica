import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react"
import { safeGetJSON, safeSetJSON } from "../utils/safeStorage"
import {
  SAMPLE_DEMO_BLOCKS,
  addPlantationBlockApi,
  deletePlantationBlockApi,
  getSeverityColor,
} from "../services/plantationService"

export interface PlantationBlock {
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
  treatmentStatus?: "none" | "treated" | "recovering" | "cleared"
  lastTreatmentDate?: string
  followUpDate?: string
  treatmentDetails?: string
}

interface PlantationContextType {
  blocks: PlantationBlock[]
  totalTrees: number
  totalAcres: number
  healthyTrees: number
  diseasedTrees: number
  overallHealthScore: number | null // null when 0 blocks exist
  topDiseasedBlocks: PlantationBlock[]
  addBlock: (block: Omit<PlantationBlock, "health" | "color">) => void
  updateBlock: (id: string, updates: Partial<PlantationBlock>) => void
  deleteBlock: (id: string) => void
  loadDemoBlocks: () => void
  clearBlocks: () => void
  markBlockTreated: (blockId: string, details: { treatmentType: string; chemicalUsed: string; followUpDate: string }) => void
}

const STORAGE_KEY = "arecavision_plantation_blocks"

const PlantationContext = createContext<PlantationContextType>({
  blocks: [],
  totalTrees: 0,
  totalAcres: 0,
  healthyTrees: 0,
  diseasedTrees: 0,
  overallHealthScore: null,
  topDiseasedBlocks: [],
  addBlock: () => null,
  updateBlock: () => null,
  deleteBlock: () => null,
  loadDemoBlocks: () => null,
  clearBlocks: () => null,
  markBlockTreated: () => null,
})

export const PlantationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [blocks, setBlocks] = useState<PlantationBlock[]>(() => {
    return safeGetJSON<PlantationBlock[]>(STORAGE_KEY, [], Array.isArray)
  })

  useEffect(() => {
    safeSetJSON(STORAGE_KEY, blocks)
  }, [blocks])

  const totalTrees = blocks.reduce((acc, b) => acc + b.trees, 0)
  const totalAcres = Number(blocks.reduce((acc, b) => acc + b.areaAcres, 0).toFixed(1))
  const diseasedTrees = blocks.reduce((acc, b) => acc + b.diseasedTrees, 0)
  const healthyTrees = totalTrees - diseasedTrees
  const overallHealthScore = blocks.length > 0 && totalTrees > 0 ? Math.round((healthyTrees / totalTrees) * 100) : null

  // Sorted by highest disease count
  const topDiseasedBlocks = useMemo(() => [...blocks].sort((a, b) => b.diseasedTrees - a.diseasedTrees), [blocks])

  const addBlock = useCallback((data: Omit<PlantationBlock, "health" | "color">) => {
    const healthy = Math.max(0, data.trees - data.diseasedTrees)
    const health = data.trees > 0 ? Math.round((healthy / data.trees) * 100) : 100
    const color = getSeverityColor(data.severity)

    const newBlock: PlantationBlock = {
      ...data,
      health,
      color,
    }
    setBlocks((prev) => [...prev, newBlock])
    addPlantationBlockApi(data).catch((err) => {
      console.error("Failed to sync new block to backend:", err)
    })
  }, [])

  const updateBlock = useCallback((id: string, updates: Partial<PlantationBlock>) => {
    setBlocks((prev) =>
      prev.map((b) => {
        if (b.id !== id) return b
        const updated = { ...b, ...updates }
        if (updates.severity) {
          updated.color = getSeverityColor(updates.severity)
        }
        if (updates.trees !== undefined || updates.diseasedTrees !== undefined) {
          const healthy = Math.max(0, updated.trees - updated.diseasedTrees)
          updated.health = updated.trees > 0 ? Math.round((healthy / updated.trees) * 100) : 100
        }
        return updated
      })
    )
  }, [])

  const deleteBlock = useCallback((id: string) => {
    setBlocks((prev) => prev.filter((b) => b.id !== id))
    deletePlantationBlockApi(id).catch((err) => {
      console.error("Failed to sync block deletion to backend:", err)
    })
  }, [])

  const loadDemoBlocks = useCallback(() => {
    setBlocks(SAMPLE_DEMO_BLOCKS)
  }, [])

  const clearBlocks = useCallback(() => {
    setBlocks([])
  }, [])

  const markBlockTreated = useCallback(
    (blockId: string, details: { treatmentType: string; chemicalUsed: string; followUpDate: string }) => {
      const now = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
      setBlocks((prev) =>
        prev.map((b) => {
          const idClean = b.id.toLowerCase().replace(/[^a-z0-9]/g, "")
          const targetClean = blockId.toLowerCase().replace(/[^a-z0-9]/g, "")
          const match = b.id.toLowerCase() === blockId.toLowerCase() || idClean === targetClean || targetClean.includes(idClean) || idClean.includes(targetClean)
          if (!match) return b

          const recoveredDiseased = Math.max(0, Math.round(b.diseasedTrees * 0.4))
          const healthy = Math.max(0, b.trees - recoveredDiseased)
          const newHealth = b.trees > 0 ? Math.round((healthy / b.trees) * 100) : 100

          return {
            ...b,
            diseasedTrees: recoveredDiseased,
            health: newHealth,
            status: "Under Recovery",
            severity: newHealth >= 80 ? ("Mild" as const) : ("Moderate" as const),
            color: newHealth >= 80 ? getSeverityColor("Mild") : getSeverityColor("Moderate"),
            treatmentStatus: "recovering" as const,
            lastTreatmentDate: now,
            followUpDate: details.followUpDate,
            treatmentDetails: `${details.chemicalUsed} (${details.treatmentType})`,
          }
        })
      )
    },
    []
  )

  const contextValue = useMemo(() => ({
    blocks,
    totalTrees,
    totalAcres,
    healthyTrees,
    diseasedTrees,
    overallHealthScore,
    topDiseasedBlocks,
    addBlock,
    updateBlock,
    deleteBlock,
    loadDemoBlocks,
    clearBlocks,
    markBlockTreated,
  }), [blocks, totalTrees, totalAcres, healthyTrees, diseasedTrees, overallHealthScore, topDiseasedBlocks, addBlock, updateBlock, deleteBlock, loadDemoBlocks, clearBlocks, markBlockTreated])

  return (
    <PlantationContext.Provider value={contextValue}>
      {children}
    </PlantationContext.Provider>
  )
}

export const usePlantation = () => useContext(PlantationContext)
