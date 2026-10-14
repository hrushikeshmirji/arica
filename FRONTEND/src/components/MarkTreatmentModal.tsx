import React, { useState, useEffect, useMemo } from "react"
import {
  X,
  ShieldCheck,
  Calendar,
  Sprout,
  CheckCircle2,
  Clock,
  Droplets,
  AlertCircle,
  FileText,
  User,
  Layers,
} from "lucide-react"
import { ScanItem } from "../contexts/ScanHistoryContext"

export interface MarkTreatmentModalProps {
  isOpen: boolean
  onClose: () => void
  scan: ScanItem | null
  onConfirm: (details: {
    treatmentType: "chemical" | "organic"
    chemicalUsed: string
    notes?: string
    blockId?: string
    followUpDate: string
  }) => void
}

import {
  getRecommendationsForDisease,
  getActionableTreatments,
  getOrganicControl,
  getBlockedTreatments,
} from "../data/recommendationRegistry"

function getRecommendationForDisease(disease: string) {
  const records = getRecommendationsForDisease(disease)
  if (!records.length) {
    return {
      chemical: "Consult local Krishi Vigyan Kendra (KVK) officer (chemical unverified for this class)",
      organic: "Maintain orchard hygiene and apply enriched organic compost",
      isChemicalBlocked: true,
      blockedReason: "No approved CIBRC label claim for this crop condition",
    }
  }

  const verifiedChemical = records.find(
    (r) => r.verificationStatus === "VERIFIED_OFFICIAL" && r.actionableChemicalAllowed
  )
  const organicRec = records.find(
    (r) => r.category === "BIO_CONTROL" || r.category === "CULTURAL_SANITATION" || r.category === "MECHANICAL_BARRIER"
  )
  const blocked = records.filter(
    (r) => r.verificationStatus === "BLOCKED_UNVERIFIED" || r.verificationStatus === "OUTDATED_REVIEW_REQUIRED"
  )

  return {
    chemical: verifiedChemical
      ? `${verifiedChemical.title} (${verifiedChemical.dosagePerLiter || verifiedChemical.dosagePerPalm || "Standard ICAR-CPCRI dose"})`
      : "Chemical treatment withheld (unverified/restricted under CIBRC / S.O. 4294(E)). Use cultural/organic control.",
    organic: organicRec
      ? `${organicRec.title}: ${organicRec.guidanceText.slice(0, 95)}...`
      : "Maintain plantation sanitation, adequate aeration, and balanced compost",
    isChemicalBlocked: !verifiedChemical,
    blockedReason: blocked.length > 0 ? blocked[0].guidanceText.slice(0, 120) : undefined,
  }
}


export default function MarkTreatmentModal({
  isOpen,
  onClose,
  scan,
  onConfirm,
}: MarkTreatmentModalProps) {
  const [treatmentType, setTreatmentType] = useState<"chemical" | "organic">("chemical")
  const [chemicalUsed, setChemicalUsed] = useState("")
  const [notes, setNotes] = useState("")
  const [applicator, setApplicator] = useState("Manual Climber / Sprayer")

  const rec = useMemo(() => {
    return scan ? getRecommendationForDisease(scan.disease) : { chemical: "", organic: "" }
  }, [scan])

  useEffect(() => {
    if (scan) {
      setChemicalUsed(treatmentType === "chemical" ? rec.chemical : rec.organic)
    }
  }, [scan, treatmentType, rec])

  if (!isOpen || !scan) return null

  // 14 days follow-up calculation
  const now = new Date()
  const followUpDateObj = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000)
  const followUpFormatted = followUpDateObj.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
  const todayFormatted = now.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onConfirm({
      treatmentType,
      chemicalUsed: chemicalUsed || (treatmentType === "chemical" ? rec.chemical : rec.organic),
      notes: notes ? `${notes} (Applicator: ${applicator})` : `Applicator: ${applicator}`,
      blockId: scan.location,
      followUpDate: followUpFormatted,
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/60 backdrop-blur-sm overflow-y-auto animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg bg-card border border-border rounded-2xl shadow-2xl overflow-hidden my-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border bg-muted/20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center text-primary">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h3 className="font-bold text-sm sm:text-base text-foreground">
                Log Treatment & Recovery Schedule
              </h3>
              <p className="text-xs text-muted-foreground">
                ICAR-CPCRI 14-Day Re-Inspection Protocol
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {/* Target Specimen Summary Box */}
          <div className="p-3.5 rounded-xl bg-muted/30 border border-border flex items-center justify-between gap-3">
            <div>
              <div className="text-[11px] text-muted-foreground font-semibold uppercase tracking-wider">
                Diagnosed Target
              </div>
              <div className="font-bold text-foreground text-sm mt-0.5">{scan.disease}</div>
              <div className="text-[11px] text-muted-foreground">
                Location: <strong className="text-foreground">{scan.location}</strong> · Scanned on {scan.date}
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20 shrink-0">
              {scan.severity}
            </span>
          </div>

          {/* Treatment Formulation Type */}
          <div>
            <label className="block text-xs font-bold text-foreground mb-1.5">
              Applied Treatment Formulation
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setTreatmentType("chemical")}
                className={`py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  treatmentType === "chemical"
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-background text-muted-foreground border-border hover:bg-muted/40"
                }`}
              >
                <ShieldCheck size={14} />
                <span>Chemical Fungicide / Spray</span>
              </button>
              <button
                type="button"
                onClick={() => setTreatmentType("organic")}
                className={`py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  treatmentType === "organic"
                    ? "bg-emerald-700 text-white border-emerald-700"
                    : "bg-background text-muted-foreground border-border hover:bg-muted/40"
                }`}
              >
                <Sprout size={14} />
                <span>Certified Bio-Organic</span>
              </button>
            </div>
          </div>

          {/* Chemical/Bio Active Name */}
          <div>
            <label className="block text-xs font-bold text-foreground mb-1">
              Active Chemical / Bio-Formulation Used:
            </label>
            <input
              type="text"
              required
              value={chemicalUsed}
              onChange={(e) => setChemicalUsed(e.target.value)}
              placeholder="e.g. 1% Bordeaux Mixture + Rosin sticker"
              className="w-full px-3 py-2 rounded-xl bg-background border border-border text-foreground font-semibold text-xs focus:ring-2 focus:ring-primary/40 focus:outline-none"
            />
          </div>

          {/* 14-Day Calendar Follow-up Banner */}
          <div className="p-3.5 rounded-xl border border-primary/30 bg-primary/5 space-y-2">
            <div className="flex items-center gap-2 font-bold text-primary text-xs">
              <Calendar size={15} />
              <span>14-Day Epidemiological Recovery Window</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
              <div className="p-2 rounded-lg bg-card border border-border">
                <span className="text-muted-foreground block text-[10px]">Treatment Logged Date:</span>
                <span className="font-bold text-foreground">{todayFormatted}</span>
              </div>
              <div className="p-2 rounded-lg bg-card border border-primary/40 text-primary">
                <span className="text-muted-foreground block text-[10px]">Next Re-Inspection Due:</span>
                <span className="font-extrabold font-mono text-xs">{followUpFormatted}</span>
              </div>
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed pt-1">
              An automated high-priority reminder will be placed in your notification feed on{" "}
              <strong>{followUpFormatted}</strong> to verify lesion arrest and remission.
            </p>
          </div>

          {/* Applicator Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground mb-1">
                Applicator / Climber:
              </label>
              <input
                type="text"
                value={applicator}
                onChange={(e) => setApplicator(e.target.value)}
                placeholder="Name or team"
                className="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-foreground text-xs focus:ring-1 focus:ring-primary/40 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground mb-1">
                Field Observation Notes:
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. 100% canopy drenched"
                className="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-foreground text-xs focus:ring-1 focus:ring-primary/40 focus:outline-none"
              />
            </div>
          </div>

          {/* GIS Sync Notice */}
          <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 bg-muted/20 p-2 rounded-lg border border-border">
            <CheckCircle2 size={13} className="text-emerald-600 shrink-0" />
            <span>
              GIS Block <strong>{scan.location}</strong> will be upgraded to <strong>"Under Recovery"</strong>.
            </span>
          </div>

          {/* Footer Buttons */}
          <div className="pt-2 flex items-center justify-end gap-2 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-xl border border-border bg-card text-foreground font-semibold hover:bg-muted/40 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-primary text-primary-foreground font-bold hover:opacity-90 flex items-center gap-1.5 shadow-sm transition-opacity"
            >
              <CheckCircle2 size={14} />
              <span>Confirm & Schedule Follow-Up</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
