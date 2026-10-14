import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import {
  FileText,
  Download,
  Printer,
  Filter,
  X,
  FileCheck,
  BarChart2,
  TreePine,
  ShieldAlert,
  Loader2,
  AlertCircle,
  Eye,
  Trash2,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Calendar,
  CheckCircle2,
} from "lucide-react"
import { useScanHistory, ScanItem } from "../contexts/ScanHistoryContext"
import { usePlantation } from "../contexts/PlantationContext"
import { useLanguage } from "../contexts/LanguageContext"
import {
  generateReportApi,
  generateSingleScanReport,
  triggerBlobDownload,
} from "../services/reportService"
import { useFocusTrap } from "../hooks/useFocusTrap"
import { getSampleImageForDisease, handleImageError } from "../utils/imageFallback"

export default function Reports() {
  const { t } = useLanguage()
  const { scans, deleteScan } = useScanHistory()
  const { blocks, totalTrees, totalAcres, healthyTrees, diseasedTrees, overallHealthScore } = usePlantation()

  const [selectedBlock, setSelectedBlock] = useState<string>("all")
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const [previewScan, setPreviewScan] = useState<ScanItem | null>(null)
  const [activeReportType, setActiveReportType] = useState<"summary" | "detailed" | "plantation">("summary")

  const reportModalRef = useFocusTrap<HTMLDivElement>(reportModalOpen, () => setReportModalOpen(false))
  const previewModalRef = useFocusTrap<HTMLDivElement>(previewScan !== null, () => setPreviewScan(null))

  // Filter calculations based on block selection
  const selectedBlockObj = blocks.find((b) => b.id === selectedBlock)

  const displayedAcres = selectedBlockObj ? selectedBlockObj.areaAcres : totalAcres
  const displayedTrees = selectedBlockObj ? selectedBlockObj.trees : totalTrees
  const displayedDiseased = selectedBlockObj ? selectedBlockObj.diseasedTrees : diseasedTrees
  const displayedHealthy = selectedBlockObj
    ? Math.max(0, selectedBlockObj.trees - selectedBlockObj.diseasedTrees)
    : healthyTrees
  const displayedHealthScore = selectedBlockObj
    ? selectedBlockObj.health
    : overallHealthScore

  const displayedScans = selectedBlock === "all"
    ? scans
    : scans.filter((s) => s.location.toLowerCase().includes(selectedBlock.toLowerCase()))

  // Report Export Mutation
  const exportMutation = useMutation({
    mutationFn: async (format: "pdf" | "csv") => {
      return generateReportApi(
        {
          type: activeReportType,
          timeframe: new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" }),
          format,
        },
        {
          scans: displayedScans,
          blocks: selectedBlock === "all" ? blocks : blocks.filter((b) => b.id === selectedBlock),
          totalAcres: displayedAcres,
          totalTrees: displayedTrees,
          healthyTrees: displayedHealthy,
          diseasedTrees: displayedDiseased,
          overallHealthScore: displayedHealthScore,
        }
      )
    },
    onSuccess: (exportBlob) => {
      triggerBlobDownload(exportBlob)
    },
  })

  const handleExportScanPdf = (scan: ScanItem) => {
    const reportBlob = generateSingleScanReport(scan, "pdf")
    triggerBlobDownload(reportBlob)
  }

  const handleExportScanCsv = (scan: ScanItem) => {
    const reportBlob = generateSingleScanReport(scan, "csv")
    triggerBlobDownload(reportBlob)
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Export Mutation Error Banner */}
      {exportMutation.isError && (
        <div className="p-3 bg-danger/10 border border-danger/30 rounded-xl flex items-center justify-between text-xs text-danger">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0" />
            <span>
              {(exportMutation.error as Error)?.message ||
                t("reports.export_failed", "Failed to generate report file. Please try again.")}
            </span>
          </div>
          <button
            onClick={() => exportMutation.reset()}
            className="p-1 text-danger hover:bg-danger/20 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            title={t("dash.close", "Close")}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-foreground">{t("nav.reports", "Diagnostic & Field Reports")}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("reports.subtitle", "Generate, view, and export plantation health audits and AI diagnostic reports")}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-card border border-border rounded-xl px-3 py-1.5 text-xs text-muted-foreground shadow-xs">
            <Filter size={14} className="text-primary" />
            <select
              value={selectedBlock}
              onChange={(e) => setSelectedBlock(e.target.value)}
              className="bg-transparent outline-none text-foreground cursor-pointer font-semibold"
            >
              <option value="all" className="bg-card text-foreground">
                {t("reports.all_blocks", "All Blocks")} ({totalAcres} {t("map.acres_unit", "Acres")})
              </option>
              {blocks.map((b) => (
                <option key={b.id} value={b.id} className="bg-card text-foreground">
                  {b.id} ({b.areaAcres} {t("map.acres_unit", "Acres")})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => {
              setActiveReportType("summary")
              setReportModalOpen(true)
            }}
            className="btn-primary text-xs flex items-center gap-2 shadow-sm font-bold"
          >
            <FileText size={15} />
            <span>{t("reports.generate_new", "Generate New Report")}</span>
          </button>
        </div>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-card border border-border shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground font-medium">{t("reports.kpi_area", "Total Area Monitored")}</span>
            <TreePine size={16} className="text-primary" />
          </div>
          <div className="text-2xl font-bold text-foreground">{displayedAcres} {t("map.acres_unit", "Acres")}</div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {displayedTrees.toLocaleString()} {t("map.palms_unit", "Palms")}
            {selectedBlock !== "all" && ` in ${selectedBlock}`}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground font-medium">{t("reports.kpi_health", "Overall Health Index")}</span>
            <BarChart2 size={16} className="text-primary" />
          </div>
          <div className="text-2xl font-bold text-foreground">{displayedHealthScore !== null ? `${displayedHealthScore}%` : "—"}</div>
          <div className="text-[11px] text-primary font-semibold mt-1">
            {displayedHealthy.toLocaleString()} {t("reports.healthy_trees_suffix", "Healthy Trees")}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground font-medium">{t("dash.kpi.diseased_trees", "Diseased Trees")}</span>
            <ShieldAlert size={16} className="text-danger" />
          </div>
          <div className="text-2xl font-bold text-danger">{displayedDiseased.toLocaleString()}</div>
          <div className="text-[11px] text-muted-foreground mt-1">{t("reports.requires_treatment", "Requires Treatment")}</div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground font-medium">{t("reports.saved_reports", "Saved Scan Reports")}</span>
            <FileCheck size={16} className="text-accent" />
          </div>
          <div className="text-2xl font-bold text-foreground">{displayedScans.length}</div>
          <div className="text-[11px] text-muted-foreground mt-1">{t("reports.exportable_audits", "Exportable PDF Audits")}</div>
        </div>
      </div>

      {/* Available Report Templates */}
      <div>
        <h2 className="text-base font-bold text-foreground mb-4">{t("reports.select_template", "Select Report Template")}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              id: "summary" as const,
              title: t("reports.tmpl_exec_title", "Executive Plantation Audit"),
              desc: t("reports.tmpl_exec_desc", "Comprehensive summary of total acreage, overall health score, and block disease rankings."),
              icon: FileText,
              tag: "Overview",
            },
            {
              id: "detailed" as const,
              title: t("reports.tmpl_diag_title", "Disease & Fungus Diagnostic Report"),
              desc: t("reports.tmpl_diag_desc", "Deep dive into Anthracnose & Koleroga outbreak zones, bounding box detections, and explainability maps."),
              icon: ShieldAlert,
              tag: "Clinical",
            },
            {
              id: "plantation" as const,
              title: t("reports.tmpl_yield_title", "Seasonal Yield Projection Report"),
              desc: t("reports.tmpl_yield_desc", "Seasonal harvest yield estimations, acreage productivity, and weather microclimate risk factors."),
              icon: BarChart2,
              tag: "Agronomic",
            },
          ].map((tmpl) => (
            <div
              key={tmpl.id}
              onClick={() => {
                setActiveReportType(tmpl.id)
                setReportModalOpen(true)
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault()
                  setActiveReportType(tmpl.id)
                  setReportModalOpen(true)
                }
              }}
              className="bg-card rounded-2xl border border-border p-5 hover:border-primary/40 hover:shadow-md transition-all cursor-pointer space-y-3 group"
            >
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                  <tmpl.icon size={20} />
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-muted text-muted-foreground uppercase">
                  {tmpl.tag}
                </span>
              </div>
              <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">{tmpl.title}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{tmpl.desc}</p>
              <div className="text-xs font-bold text-primary flex items-center gap-1 pt-1">
                <span>{t("xai.gen_report", "Generate Report")}</span> →
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Saved / Recent Generated Reports Section */}
      <div className="bg-card rounded-2xl border border-border p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-foreground">{t("reports.generated_reports_heading", "Generated Scan Reports")}</h2>
            <p className="text-xs text-muted-foreground">Audited specimen records ready for PDF certificate and CSV generation</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-muted rounded-lg text-muted-foreground">
            {displayedScans.length} {displayedScans.length === 1 ? "Record" : "Records"}
          </span>
        </div>

        {displayedScans.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground space-y-3 border border-dashed border-border rounded-xl bg-muted/20">
            <FileText size={36} className="mx-auto text-primary opacity-60" />
            <div className="text-sm font-bold text-foreground">{t("reports.no_reports_title", "No Generated Reports Yet")}</div>
            <p className="text-xs max-w-sm mx-auto">
              {t("reports.no_reports_desc", 'Perform your first AI diagnosis scan or click "Generate New Report" above to compile diagnostic PDF audits.')}
            </p>
            <button
              onClick={() => {
                setActiveReportType("summary")
                setReportModalOpen(true)
              }}
              className="btn-primary text-xs mx-auto mt-2"
            >
              <FileText size={14} /> {t("reports.generate_plantation_btn", "Generate Plantation Report")}
            </button>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {displayedScans.map((scan) => {
              const thumbnailSrc = getSampleImageForDisease(scan.disease, scan.imageUrl)

              return (
                <div key={scan.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 group">
                  <div className="flex items-center gap-4">
                    {/* Specimen Thumbnail with Fallback Safety */}
                    <div
                      onClick={() => setPreviewScan(scan)}
                      className="w-14 h-14 rounded-xl overflow-hidden bg-muted shrink-0 border border-border relative cursor-pointer hover:ring-2 hover:ring-primary/40 transition-all shadow-xs"
                      title="Click to inspect specimen details"
                    >
                      <img
                        src={thumbnailSrc}
                        alt={scan.disease || "Arecanut specimen"}
                        onError={handleImageError}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <h4
                          onClick={() => setPreviewScan(scan)}
                          className="text-sm font-bold text-foreground hover:text-primary transition-colors cursor-pointer"
                        >
                          {scan.disease} {t("reports.diagnostic_audit_suffix", "Diagnostic Audit")}
                        </h4>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            scan.severity === "Critical" || scan.severity === "Severe"
                              ? "bg-danger/10 text-danger border-danger/20"
                              : scan.severity === "Moderate" || scan.severity === "Uncertain"
                              ? "bg-warning/10 text-warning border-warning/20"
                              : scan.severity === "Healthy"
                              ? "bg-success/10 text-success border-success/20"
                              : "bg-accent/10 text-accent border-accent/20"
                          }`}
                        >
                          {scan.severity}
                        </span>
                      </div>

                      <p className="text-xs text-muted-foreground mt-0.5 flex flex-wrap items-center gap-2">
                        <span>{scan.date}</span>
                        <span>•</span>
                        <span>{scan.location}</span>
                        <span>•</span>
                        <span className="font-semibold text-primary">
                          {t("xai.confidence", "Confidence")}: {scan.confidence}%
                        </span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setPreviewScan(scan)}
                      className="px-2.5 py-1.5 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors flex items-center gap-1"
                      title="Inspect Specimen"
                    >
                      <Eye size={13} />
                      <span className="hidden md:inline">Inspect</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleExportScanCsv(scan)}
                      className="btn-secondary text-xs flex items-center gap-1.5 py-1.5"
                      title="Export CSV record for this specimen"
                    >
                      <Download size={13} />
                      <span>{t("reports.export_csv", "Export CSV")}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleExportScanPdf(scan)}
                      className="btn-primary text-xs flex items-center gap-1.5 shadow-sm py-1.5 font-bold"
                      title="Print or download official PDF certificate for this scan"
                    >
                      <Printer size={13} />
                      <span>{t("reports.export_pdf", "Export PDF")}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteScan(scan.id)}
                      className="p-1.5 text-muted-foreground hover:text-danger hover:bg-danger/10 rounded-lg transition-colors"
                      title="Delete this scan report"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* REPORT GENERATION / PREVIEW MODAL */}
      {reportModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            ref={reportModalRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="reports-modal-title"
            className="bg-card border border-border rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-5 animate-in fade-in zoom-in-95 max-h-[90vh] overflow-y-auto outline-none"
          >
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                  <FileText size={20} />
                </div>
                <div>
                  <h3 id="reports-modal-title" className="text-base font-bold text-foreground">
                    {activeReportType === "detailed"
                      ? t("reports.tmpl_diag_title", "Disease & Fungus Diagnostic Report")
                      : activeReportType === "plantation"
                      ? t("reports.tmpl_yield_title", "Seasonal Yield Projection Report")
                      : t("reports.tmpl_exec_title", "Executive Plantation Audit")}
                  </h3>
                  <p className="text-[11px] text-muted-foreground">
                    {t("reports.field_diag_prefix", "ArecaVision AI Field Diagnostic • Generated on")} {new Date().toLocaleDateString()}
                    {selectedBlock !== "all" && ` • ${selectedBlock}`}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setReportModalOpen(false)}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                aria-label={t("dash.close", "Close")}
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              {/* Summary KPIs */}
              <div className="p-4 rounded-xl bg-muted/30 border border-border grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div>
                  <div className="text-[10px] text-muted-foreground font-semibold uppercase">{t("reports.modal_total_acreage", "Total Acreage")}</div>
                  <div className="text-sm font-extrabold text-foreground">{displayedAcres} {t("map.acres_unit", "Acres")}</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground font-semibold uppercase">{t("reports.modal_palms_monitored", "Palms Monitored")}</div>
                  <div className="text-sm font-extrabold text-foreground">{displayedTrees.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground font-semibold uppercase">{t("map.health_score_prefix", "Health Score")}</div>
                  <div className="text-sm font-extrabold text-primary">{displayedHealthScore !== null ? `${displayedHealthScore}%` : "—"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground font-semibold uppercase">{t("map.kpi_diseased_palms", "Diseased Palms")}</div>
                  <div className="text-sm font-extrabold text-danger">{displayedDiseased.toLocaleString()}</div>
                </div>
              </div>

              {/* Template Specific Section 1: Executive Audit */}
              {activeReportType === "summary" && (
                <div>
                  <h4 className="font-bold text-foreground text-sm mb-2">{t("reports.block_by_block", "Block-by-Block Health Index")}</h4>
                  {blocks.length === 0 ? (
                    <div className="p-4 rounded-lg border border-dashed border-border bg-muted/20 text-center text-xs text-muted-foreground">
                      {t("reports.no_blocks_configured", "No plantation blocks configured yet. Configure blocks on the Plantation Map screen.")}
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {blocks.map((b) => (
                        <div key={b.id} className="p-3 rounded-lg border border-border bg-card flex justify-between items-center">
                          <div>
                            <span className="font-bold text-foreground">{b.id}</span>
                            <span className="text-muted-foreground ml-2">
                              ({b.areaAcres} {t("map.acres_unit", "Acres")} • {b.trees.toLocaleString()} Palms • {b.spacing})
                            </span>
                          </div>
                          <span className="font-bold" style={{ color: b.color }}>
                            {b.status} ({b.health}%)
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Template Specific Section 2: Disease Diagnostic Report */}
              {activeReportType === "detailed" && (
                <div className="space-y-3">
                  <h4 className="font-bold text-foreground text-sm">Active Pathology & Fungicide Protocols</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div className="p-3 rounded-xl border border-border bg-card space-y-1">
                      <div className="font-bold text-foreground flex items-center justify-between">
                        <span>Fruit Rot / Koleroga</span>
                        <span className="text-[10px] px-1.5 py-0.5 bg-danger/10 text-danger rounded-md font-bold">Phytophthora meadii</span>
                      </div>
                      <p className="text-[11px] text-muted-foreground">Spray 1% Bordeaux mixture before monsoon showers; ensure clean drain lines.</p>
                    </div>

                    <div className="p-3 rounded-xl border border-border bg-card space-y-1">
                      <div className="font-bold text-foreground flex items-center justify-between">
                        <span>Anthracnose Lesions</span>
                        <span className="text-[10px] px-1.5 py-0.5 bg-warning/10 text-warning rounded-md font-bold">Colletotrichum</span>
                      </div>
                      <p className="text-[11px] text-muted-foreground">Foliar spray with Copper Oxychloride 50 WP (2.5g/L) or 1% Bordeaux mixture; prune infected fronds.</p>
                    </div>

                    <div className="p-3 rounded-xl border border-border bg-card space-y-1">
                      <div className="font-bold text-foreground flex items-center justify-between">
                        <span>Leaf Spot Complex</span>
                        <span className="text-[10px] px-1.5 py-0.5 bg-sky-500/10 text-sky-600 rounded-md font-bold">Pestalotiopsis</span>
                      </div>
                      <p className="text-[11px] text-muted-foreground">Foliar spray with Copper Oxychloride (0.25%); prune necrotic lower fronds.</p>
                    </div>

                    <div className="p-3 rounded-xl border border-border bg-card space-y-1">
                      <div className="font-bold text-foreground flex items-center justify-between">
                        <span>Yellow Leaf Disease</span>
                        <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/10 text-amber-600 rounded-md font-bold">Phytoplasma</span>
                      </div>
                      <p className="text-[11px] text-muted-foreground">Apply balanced NPK + Magnesium Sulphate (100g) + Zinc Sulphate (50g) to sustain vigor (supportive management only; phytoplasmas have no cure).</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Template Specific Section 3: Seasonal Yield Projection */}
              {activeReportType === "plantation" && (
                <div className="space-y-3">
                  <h4 className="font-bold text-foreground text-sm">Harvest Yield Modeling & Productivity</h4>
                  <div className="grid grid-cols-3 gap-2.5 text-center">
                    <div className="p-3 rounded-xl border border-border bg-card">
                      <div className="text-[10px] text-muted-foreground uppercase font-bold">Projected Chali Yield</div>
                      <div className="text-base font-extrabold text-foreground mt-1">
                        ~{((displayedHealthy * 2.5) / 100).toFixed(1)} Qtl
                      </div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">@ 2.5 kg dried nut/palm</div>
                    </div>

                    <div className="p-3 rounded-xl border border-border bg-card">
                      <div className="text-[10px] text-muted-foreground uppercase font-bold">Yield Loss Prevented</div>
                      <div className="text-base font-extrabold text-primary mt-1">
                        +~{((displayedDiseased * 2.5) / 100).toFixed(1)} Qtl
                      </div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">Via early triage spray</div>
                    </div>

                    <div className="p-3 rounded-xl border border-border bg-card">
                      <div className="text-[10px] text-muted-foreground uppercase font-bold">Harvest Window</div>
                      <div className="text-base font-extrabold text-foreground mt-1">Nov – Feb</div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">Peak maturity phase</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
              <button
                onClick={() => setReportModalOpen(false)}
                className="btn-secondary text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                {t("dash.close", "Close")}
              </button>
              <button
                onClick={() => exportMutation.mutate("csv")}
                disabled={exportMutation.isPending}
                className="btn-secondary text-xs flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                <Download size={14} /> {t("reports.download_csv", "Download CSV")}
              </button>
              <button
                onClick={() => exportMutation.mutate("pdf")}
                disabled={exportMutation.isPending}
                className="btn-primary text-xs flex items-center gap-1.5 shadow-sm font-bold focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                {exportMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Printer size={14} />}
                <span>{t("reports.download_pdf_btn", "Download PDF Report")}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SPECIMEN INSPECTION MODAL */}
      {previewScan && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            ref={previewModalRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="preview-modal-title"
            className="bg-card border border-border rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4 animate-in fade-in zoom-in-95 outline-none"
          >
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={18} className="text-primary" />
                <h3 id="preview-modal-title" className="text-sm font-bold text-foreground">
                  Specimen Diagnostic Summary
                </h3>
              </div>
              <button
                onClick={() => setPreviewScan(null)}
                className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="aspect-[16/10] rounded-xl overflow-hidden bg-muted border border-border relative">
                <img
                  src={getSampleImageForDisease(previewScan.disease, previewScan.imageUrl)}
                  alt={previewScan.disease}
                  onError={handleImageError}
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-2 right-2 px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-black/70 text-white backdrop-blur-md">
                  {previewScan.confidence}% Confidence
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-extrabold text-foreground text-base">{previewScan.disease}</h4>
                  <p className="text-muted-foreground text-[11px]">{previewScan.location} • {previewScan.date}</p>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                    previewScan.severity === "Critical" || previewScan.severity === "Severe"
                      ? "bg-danger/10 text-danger border border-danger/20"
                      : "bg-warning/10 text-warning border border-warning/20"
                  }`}
                >
                  {previewScan.severity}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-muted/30 border border-border space-y-1.5">
                <div className="font-bold text-foreground">Recommended Interventions:</div>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground text-[11px]">
                  {previewScan.recommendedActions && previewScan.recommendedActions.length > 0 ? (
                    previewScan.recommendedActions.map((act, i) => <li key={i}>{act}</li>)
                  ) : (
                    <>
                      <li>Apply 1% Bordeaux mixture foliar spray.</li>
                      <li>Remove and destroy fallen infected arecanuts.</li>
                    </>
                  )}
                </ul>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
              <button
                type="button"
                onClick={() => setPreviewScan(null)}
                className="btn-secondary text-xs"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => handleExportScanPdf(previewScan)}
                className="btn-primary text-xs flex items-center gap-1.5 font-bold shadow-sm"
              >
                <Printer size={13} />
                <span>Export PDF Certificate</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
