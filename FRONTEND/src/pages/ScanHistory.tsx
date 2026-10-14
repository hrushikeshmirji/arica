import { useState } from "react"
import { Link } from "react-router-dom"
import {
  ScanLine,
  Search,
  Calendar,
  Trash2,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Filter,
  Plus,
  CloudSun,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  Clock,
  Calculator,
  Sprout,
} from "lucide-react"
import { useScanHistory, ScanItem } from "../contexts/ScanHistoryContext"
import { useNotifications } from "../contexts/NotificationContext"
import { usePlantation } from "../contexts/PlantationContext"
import { useLanguage } from "../contexts/LanguageContext"
import { useFocusTrap } from "../hooks/useFocusTrap"
import { handleImageError } from "../utils/imageFallback"
import MarkTreatmentModal from "../components/MarkTreatmentModal"
import TreatmentCalculatorModal from "../components/TreatmentCalculatorModal"

export default function ScanHistory() {
  const { scans, deleteScan, clearHistory, markTreated } = useScanHistory()
  const { addNotification } = useNotifications()
  const { markBlockTreated } = usePlantation()
  const { t } = useLanguage()

  const [searchTerm, setSearchTerm] = useState("")
  const [selectedDiseaseFilter, setSelectedDiseaseFilter] = useState("All")
  const [treatmentStatusFilter, setTreatmentStatusFilter] = useState<"all" | "treated" | "pending">("all")
  const [currentPage, setCurrentPage] = useState(1)
  const [showClearModal, setShowClearModal] = useState(false)
  const [scanToDelete, setScanToDelete] = useState<string | null>(null)
  const [scanToTreat, setScanToTreat] = useState<ScanItem | null>(null)
  const [calcModalOpen, setCalcModalOpen] = useState(false)
  const [calcModalDisease, setCalcModalDisease] = useState("koleroga")
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null)

  const clearModalRef = useFocusTrap<HTMLDivElement>({
    isOpen: showClearModal,
    onClose: () => setShowClearModal(false),
  })

  const deleteModalRef = useFocusTrap<HTMLDivElement>({
    isOpen: scanToDelete !== null,
    onClose: () => setScanToDelete(null),
  })

  const handleConfirmTreatment = (details: {
    treatmentType: "chemical" | "organic"
    chemicalUsed: string
    notes?: string
    blockId?: string
    followUpDate: string
  }) => {
    if (!scanToTreat) return
    markTreated(scanToTreat.id, details)
    markBlockTreated(details.blockId || scanToTreat.location, {
      treatmentType: details.treatmentType,
      chemicalUsed: details.chemicalUsed,
      followUpDate: details.followUpDate,
    })
    addNotification({
      type: "info",
      title: `Treatment Logged: ${scanToTreat.disease}`,
      msg: `Applied ${details.chemicalUsed} at ${scanToTreat.location}. 14-day follow-up inspection scheduled for ${details.followUpDate}.`,
      blockId: scanToTreat.location,
    })
    setFeedbackMessage(
      `Treatment logged for ${scanToTreat.disease}! 14-day follow-up re-inspection scheduled for ${details.followUpDate}.`
    )
    setTimeout(() => setFeedbackMessage(null), 5000)
    setScanToTreat(null)
  }

  const itemsPerPage = 6

  const filteredScans = scans.filter((scan) => {
    const matchesSearch =
      scan.disease.toLowerCase().includes(searchTerm.toLowerCase()) ||
      scan.location.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter =
      selectedDiseaseFilter === "All" ||
      scan.disease.toLowerCase().includes(selectedDiseaseFilter.toLowerCase())
    const isTreated = !!scan.treatment?.isTreated
    const matchesTreatment =
      treatmentStatusFilter === "all" ||
      (treatmentStatusFilter === "treated" && isTreated) ||
      (treatmentStatusFilter === "pending" && !isTreated && scan.disease !== "Healthy" && scan.disease !== "Non-Arecanut")
    return matchesSearch && matchesFilter && matchesTreatment
  })

  const totalPages = Math.max(1, Math.ceil(filteredScans.length / itemsPerPage))
  const paginatedScans = filteredScans.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-foreground">{t("scans.title", "Scan History")}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("scans.subtitle", "View and manage past plant analysis results")}
          </p>
        </div>

        {scans.length > 0 && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowClearModal(true)}
              className="px-3 py-2 rounded-xl text-xs font-semibold text-danger bg-danger/10 hover:bg-danger/20 transition-colors flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-danger focus-visible:outline-none"
            >
              <Trash2 size={14} /> {t("scans.clear_all", "Clear All History")}
            </button>
            <Link to="/detection" className="btn-primary text-xs flex items-center gap-1.5 shadow-sm">
              <Plus size={14} /> {t("scans.new_scan", "New Scan")}
            </Link>
          </div>
        )}
      </div>

      {feedbackMessage && (
        <div className="p-3 bg-primary/10 border border-primary/30 rounded-xl flex items-center justify-between text-xs text-primary animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span className="font-semibold">{feedbackMessage}</span>
          </div>
          <button onClick={() => setFeedbackMessage(null)} className="text-primary hover:opacity-80 text-sm font-bold">
            ✕
          </button>
        </div>
      )}

      {/* ===== EMPTY STATE ===== */}
      {scans.length === 0 ? (
        <div className="bg-card rounded-2xl border border-border p-12 text-center flex flex-col items-center justify-center min-h-[420px]">
          <div className="w-20 h-20 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-6 shadow-lg shadow-primary/10">
            <ScanLine size={38} />
          </div>

          <h2 className="text-xl font-bold text-foreground mb-2">
            {t("scans.empty_title", "No previous plant analyses found.")}
          </h2>

          <p className="text-sm text-muted-foreground max-w-md mb-8 leading-relaxed">
            {t("scans.empty_desc", "Analyze your first plant to start building your history and tracking plantation health trends.")}
          </p>

          <Link to="/detection" className="btn-primary text-sm px-6 py-3 shadow-lg shadow-primary/20 flex items-center gap-2">
            <ScanLine size={18} />
            <span>{t("scans.analyze_btn", "Analyze Plant")}</span>
          </Link>
        </div>
      ) : (
        /* ===== POPULATED STATE ===== */
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-card p-4 rounded-xl border border-border">
            <div className="flex items-center gap-2 bg-muted/50 border border-border rounded-xl px-3 py-2 w-full sm:w-80">
              <Search size={16} className="text-muted-foreground shrink-0" />
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={t("scans.search_placeholder", "Search scans by plant, disease, or location...")}
                className="bg-transparent border-none outline-none text-xs text-foreground placeholder-muted-foreground flex-1"
              />
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
              <Filter size={16} className="text-muted-foreground" />
              <select
                value={selectedDiseaseFilter}
                onChange={(e) => setSelectedDiseaseFilter(e.target.value)}
                className="bg-card border border-border rounded-xl px-3 py-2 text-xs font-semibold text-foreground outline-none cursor-pointer"
              >
                <option value="All">{t("scans.filter_all", "All Diseases")}</option>
                <option value="Anthracnose">{t("disease.anthracnose", "Anthracnose")}</option>
                <option value="Koleroga">{t("scans.filter_koleroga", "Koleroga / Rot")}</option>
                <option value="Nut Cracking">{t("disease.nut_cracking", "Nut Cracking")}</option>
                <option value="Bud Borer">Bud Borer</option>
                <option value="Yellow Leaf">Yellow Leaf</option>
                <option value="Stem Bleeding">Stem Bleeding</option>
              </select>

              <select
                value={treatmentStatusFilter}
                onChange={(e) => setTreatmentStatusFilter(e.target.value as any)}
                className="bg-card border border-border rounded-xl px-3 py-2 text-xs font-semibold text-foreground outline-none cursor-pointer"
              >
                <option value="all">All Recovery Statuses</option>
                <option value="treated">Treated &amp; Recovering</option>
                <option value="pending">Action Required (Pending)</option>
              </select>
            </div>
          </div>

          {/* Grid View or Filter-Mismatch Empty State */}
          {filteredScans.length === 0 ? (
            <div className="bg-card rounded-2xl border border-border p-12 text-center flex flex-col items-center justify-center min-h-[300px]">
              <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center text-muted-foreground mb-4">
                <Search size={24} />
              </div>
              <h3 className="text-base font-bold text-foreground mb-1">
                {t("scans.no_matching_title", "No scans match your search or filter")}
              </h3>
              <p className="text-xs text-muted-foreground max-w-sm mb-6 leading-relaxed">
                {t("scans.no_matching_desc", "Try adjusting your search query or selecting a different disease filter.")}
              </p>
              <button
                onClick={() => {
                  setSearchTerm("")
                  setSelectedDiseaseFilter("All")
                }}
                className="btn-secondary text-xs px-4 py-2 flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                <RefreshCw size={13} />
                <span>{t("scans.reset_filters", "Reset Filters")}</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {paginatedScans.map((item) => (
                <div key={item.id} className="bg-card rounded-2xl border border-border overflow-hidden shadow-sm card-hover flex flex-col justify-between">
                  <div className="p-4 space-y-3">
                    <div className="relative aspect-[16/10] rounded-xl overflow-hidden bg-muted border border-border">
                      <img
                        src={item.imageUrl}
                        alt={item.title}
                        onError={handleImageError}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute top-2 right-2 px-2 py-1 rounded-full text-[10px] font-extrabold bg-black/60 text-white backdrop-blur-md">
                        {item.confidence}% {t("scans.confidence_suffix", "Confidence")}
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <h3 className="font-bold text-foreground text-sm">{item.title}</h3>
                      <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full border ${
                        item.severity === "Critical" || item.severity === "Severe" || item.severity === "High"
                          ? "bg-danger/10 text-danger border-danger/20"
                          : item.severity === "Moderate" || item.severity === "Uncertain"
                          ? "bg-warning/10 text-warning border-warning/20"
                          : item.severity === "Healthy"
                          ? "bg-success/10 text-success border-success/20"
                          : item.severity === "Non-Arecanut"
                          ? "bg-primary/10 text-primary border-primary/20"
                          : "bg-accent/10 text-accent border-accent/20"
                      }`}>
                        {item.severity}
                      </span>
                    </div>

                    <div className="text-xs text-primary font-bold">{item.disease}</div>

                    {/* Treatment Lifecycle Status Banner */}
                    {item.treatment?.isTreated ? (
                      <div className="p-2.5 rounded-xl bg-emerald-600/10 border border-emerald-600/25 space-y-1">
                        <div className="flex items-center justify-between text-[11px] font-bold text-emerald-700 dark:text-emerald-300">
                          <span className="flex items-center gap-1.5">
                            <CheckCircle2 size={13} className="text-emerald-600 shrink-0" />
                            Treated &amp; Recovering
                          </span>
                          <span className="text-[10px] font-mono text-muted-foreground">{item.treatment.treatedAt}</span>
                        </div>
                        <div className="text-[10px] text-foreground font-semibold truncate">
                          {item.treatment.chemicalUsed}
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] text-primary font-semibold pt-0.5 border-t border-emerald-600/15">
                          <Clock size={11} className="shrink-0" />
                          <span>Follow-up Due: <strong>{item.treatment.followUpDate}</strong></span>
                        </div>
                      </div>
                    ) : item.disease !== "Healthy" && item.disease !== "Non-Arecanut" ? (
                      <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-700 dark:text-amber-400">
                          <AlertTriangle size={13} className="shrink-0" />
                          <span>Treatment Action Pending</span>
                        </div>
                        <button
                          onClick={() => setScanToTreat(item)}
                          className="px-2.5 py-1 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-bold text-[10px] transition-colors shadow-xs"
                        >
                          Log Treatment
                        </button>
                      </div>
                    ) : (
                      <div className="p-2 rounded-xl bg-emerald-600/5 border border-emerald-600/15 flex items-center gap-1.5 text-[11px] text-emerald-700 dark:text-emerald-300 font-medium">
                        <CheckCircle2 size={13} className="text-emerald-600 shrink-0" />
                        <span>Optimal Vigor · Routine Maintenance</span>
                      </div>
                    )}

                    <div className="space-y-1 pt-2 border-t border-border text-[11px] text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <Calendar size={12} /> {item.date}
                      </div>
                      <div className="flex items-center gap-1.5">
                        <CloudSun size={12} /> {item.weatherCondition} ({item.temp}) · {item.location}
                      </div>
                    </div>
                  </div>

                  <div className="px-4 py-3 bg-muted/20 border-t border-border flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {item.disease !== "Healthy" && item.disease !== "Non-Arecanut" && (
                        <button
                          onClick={() => setScanToTreat(item)}
                          className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                        >
                          <ShieldCheck size={13} />
                          <span>{item.treatment?.isTreated ? "Update Treatment" : "Log Treatment"}</span>
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setCalcModalDisease(item.disease)
                          setCalcModalOpen(true)
                        }}
                        className="text-xs font-semibold text-muted-foreground hover:text-foreground flex items-center gap-1"
                        title="Calculate exact pesticide or fertilizer dosages"
                      >
                        <Calculator size={13} />
                        <span>Dosage</span>
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <Link
                        to="/detection"
                        state={{ imageUrl: item.imageUrl }}
                        className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                      >
                        {t("scans.reanalyze", "Re-analyze")} <ExternalLink size={12} />
                      </Link>
                      <button
                        onClick={() => setScanToDelete(item.id)}
                        className="p-1.5 text-muted-foreground hover:text-danger transition-colors rounded-lg"
                        title={t("scans.delete_scan", "Delete Scan")}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {filteredScans.length > 0 && totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-border">
              <span className="text-xs text-muted-foreground">
                {t("scans.showing", "Showing")} {paginatedScans.length} {t("scans.of", "of")} {filteredScans.length} {t("scans.scans_unit", "scans")}
              </span>
              <div className="flex items-center gap-2">
                <button
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  className="p-2 rounded-lg border border-border disabled:opacity-40 hover:bg-muted"
                >
                  <ChevronLeft size={16} />
                </button>
                <span className="text-xs font-semibold text-foreground px-2">
                  {t("scans.page", "Page")} {currentPage} {t("scans.of", "of")} {totalPages}
                </span>
                <button
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  className="p-2 rounded-lg border border-border disabled:opacity-40 hover:bg-muted"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Clear All Confirmation Modal */}
      {showClearModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div
            ref={clearModalRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby="clear-history-title"
            className="bg-card border border-border rounded-2xl p-6 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <div className="w-12 h-12 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
              <AlertTriangle size={24} />
            </div>
            <div className="text-center space-y-1">
              <h2 id="clear-history-title" className="text-base font-bold text-foreground">
                {t("scans.confirm_clear_title", "Clear scan history?")}
              </h2>
              <p className="text-xs text-muted-foreground">
                {t("scans.confirm_clear_desc", "Are you sure you want to delete all scans? This action cannot be undone.")}
              </p>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => setShowClearModal(false)}
                className="flex-1 py-2 px-3 border border-border rounded-xl text-xs font-semibold text-foreground hover:bg-muted transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                {t("scans.confirm_cancel_btn", "Cancel")}
              </button>
              <button
                onClick={() => {
                  clearHistory()
                  setShowClearModal(false)
                  setFeedbackMessage(t("scans.history_cleared", "Scan history successfully cleared."))
                  setTimeout(() => setFeedbackMessage(null), 4000)
                }}
                className="flex-1 py-2 px-3 bg-danger hover:bg-danger/90 text-white rounded-xl text-xs font-bold transition-colors shadow-sm focus-visible:ring-2 focus-visible:ring-danger focus-visible:outline-none"
              >
                {t("scans.confirm_clear_btn", "Yes, Clear All")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Single Scan Confirmation Modal */}
      {scanToDelete !== null && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div
            ref={deleteModalRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-scan-title"
            className="bg-card border border-border rounded-2xl p-6 max-w-sm w-full space-y-4 shadow-2xl"
          >
            <div className="w-12 h-12 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
              <AlertTriangle size={24} />
            </div>
            <div className="text-center space-y-1">
              <h2 id="delete-scan-title" className="text-base font-bold text-foreground">
                {t("scans.delete_scan", "Delete Scan")}
              </h2>
              <p className="text-xs text-muted-foreground">
                {t("scans.confirm_delete_scan", "Are you sure you want to delete this scan?")}
              </p>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => setScanToDelete(null)}
                className="flex-1 py-2 px-3 border border-border rounded-xl text-xs font-semibold text-foreground hover:bg-muted transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                {t("scans.confirm_cancel_btn", "Cancel")}
              </button>
              <button
                onClick={() => {
                  if (scanToDelete) {
                    deleteScan(scanToDelete)
                    setScanToDelete(null)
                    setFeedbackMessage(t("scans.scan_deleted", "Scan item deleted."))
                    setTimeout(() => setFeedbackMessage(null), 4000)
                  }
                }}
                className="flex-1 py-2 px-3 bg-danger hover:bg-danger/90 text-white rounded-xl text-xs font-bold transition-colors shadow-sm focus-visible:ring-2 focus-visible:ring-danger focus-visible:outline-none"
              >
                {t("scans.confirm_clear_btn", "Delete")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mark Treatment Modal */}
      <MarkTreatmentModal
        isOpen={scanToTreat !== null}
        onClose={() => setScanToTreat(null)}
        scan={scanToTreat}
        onConfirm={handleConfirmTreatment}
      />

      {/* Fertilizer & Pesticide Dosage Calculator Modal */}
      <TreatmentCalculatorModal
        isOpen={calcModalOpen}
        onClose={() => setCalcModalOpen(false)}
        initialDisease={calcModalDisease}
      />
    </div>
  )
}
