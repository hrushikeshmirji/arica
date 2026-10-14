import { useState } from "react"
import { usePlantation, PlantationBlock } from "../contexts/PlantationContext"
import { useLanguage } from "../contexts/LanguageContext"
import {
  Map,
  Plus,
  Edit3,
  Trash2,
  TreePine,
  AlertTriangle,
  ShieldCheck,
  Layers,
  Check,
  X,
  Sparkles,
  AlertCircle,
  Calculator,
  RotateCcw,
  Clock,
} from "lucide-react"
import { useFocusTrap } from "../hooks/useFocusTrap"
import TreatmentCalculatorModal from "../components/TreatmentCalculatorModal"

const SPACING_PRESETS = [
  { label: "2.7m × 2.7m (Standard ~512/ac)", value: "2.7m x 2.7m", density: 512 },
  { label: "2.4m × 2.4m (High Density ~680/ac)", value: "2.4m x 2.4m", density: 680 },
  { label: "3.0m × 3.0m (Wide / Intercrop ~440/ac)", value: "3.0m x 3.0m", density: 440 },
]

const SOIL_OPTIONS = [
  "Laterite Red",
  "Sandy Loam",
  "Clay Loam",
  "Coastal Alluvial",
  "Alluvial Loam",
]

export default function PlantationMap() {
  const {
    blocks,
    totalTrees,
    totalAcres,
    healthyTrees,
    diseasedTrees,
    overallHealthScore,
    addBlock,
    updateBlock,
    deleteBlock,
    loadDemoBlocks,
    clearBlocks,
  } = usePlantation()

  const { t } = useLanguage()

  const [selectedBlockId, setSelectedBlockId] = useState<string>(blocks[0]?.id || "")

  // Modal States
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [clearAllModalOpen, setClearAllModalOpen] = useState(false)
  const [treatmentModalOpen, setTreatmentModalOpen] = useState(false)
  const [treatmentBlockPalms, setTreatmentBlockPalms] = useState<number>(450)

  // Target block tracking for direct action invocation
  const [editingBlock, setEditingBlock] = useState<PlantationBlock | null>(null)
  const [blockToDelete, setBlockToDelete] = useState<PlantationBlock | null>(null)

  const addModalRef = useFocusTrap<HTMLFormElement>(addModalOpen, () => setAddModalOpen(false))
  const editModalRef = useFocusTrap<HTMLFormElement>(editModalOpen, () => setEditModalOpen(false))
  const deleteModalRef = useFocusTrap<HTMLDivElement>(deleteModalOpen, () => {
    setDeleteModalOpen(false)
    setBlockToDelete(null)
  })
  const clearAllModalRef = useFocusTrap<HTMLDivElement>(clearAllModalOpen, () => setClearAllModalOpen(false))

  const [addSubmitted, setAddSubmitted] = useState(false)
  const [editSubmitted, setEditSubmitted] = useState(false)

  // Form Fields for Adding / Editing
  const [formName, setFormName] = useState("")
  const [formAcres, setFormAcres] = useState<number>(4.0)
  const [formTrees, setFormTrees] = useState<number>(2048)
  const [formDiseased, setFormDiseased] = useState<number>(0)
  const [formSpacing, setFormSpacing] = useState("2.7m x 2.7m")
  const [formSoil, setFormSoil] = useState("Laterite Red")
  const [formSeverity, setFormSeverity] = useState<PlantationBlock["severity"]>("Healthy")
  const [formStatus, setFormStatus] = useState("Optimal Condition")

  const selectedBlock = blocks.find((b) => b.id === selectedBlockId) || blocks[0]

  // Dynamic density calculation helper
  const getDensityForSpacing = (spacingStr: string): number => {
    if (spacingStr.includes("2.4")) return 680
    if (spacingStr.includes("3.0")) return 440
    return 512
  }

  const suggestedPalms = Math.max(1, Math.round((formAcres || 1) * getDensityForSpacing(formSpacing)))

  const validateAddForm = () => {
    const trimmedName = formName.trim()
    const nameErr = !trimmedName
      ? t("map.val_name_req", "Block name is required")
      : blocks.some((b) => b.id.toLowerCase() === trimmedName.toLowerCase())
      ? t("map.val_name_exists", "A block with this name already exists")
      : null

    const acresErr = !formAcres || formAcres <= 0
      ? t("map.val_acres_min", "Area must be greater than 0 acres")
      : null

    const treesErr = !formTrees || formTrees < 1
      ? t("map.val_trees_min", "Palms count must be at least 1")
      : null

    const diseasedErr = formDiseased < 0
      ? t("map.val_diseased_neg", "Diseased count cannot be negative")
      : formDiseased > formTrees
      ? t("map.val_diseased_max", "Diseased palms cannot exceed total palms")
      : null

    const spacingErr = !formSpacing.trim() ? t("map.val_spacing_req", "Tree spacing is required") : null

    return { nameErr, acresErr, treesErr, diseasedErr, spacingErr, isValid: !nameErr && !acresErr && !treesErr && !diseasedErr && !spacingErr }
  }

  const validateEditForm = () => {
    const trimmedName = formName.trim()
    const nameErr = !trimmedName
      ? t("map.val_name_req", "Block name is required")
      : blocks.some((b) => b.id.toLowerCase() === trimmedName.toLowerCase() && b.id !== editingBlock?.id)
      ? t("map.val_name_exists", "A block with this name already exists")
      : null

    const acresErr = !formAcres || formAcres <= 0
      ? t("map.val_acres_min", "Area must be greater than 0 acres")
      : null

    const treesErr = !formTrees || formTrees < 1
      ? t("map.val_trees_min", "Palms count must be at least 1")
      : null

    const diseasedErr = formDiseased < 0
      ? t("map.val_diseased_neg", "Diseased count cannot be negative")
      : formDiseased > formTrees
      ? t("map.val_diseased_max", "Diseased palms cannot exceed total palms")
      : null

    const spacingErr = !formSpacing.trim() ? t("map.val_spacing_req", "Tree spacing is required") : null

    return { nameErr, acresErr, treesErr, diseasedErr, spacingErr, isValid: !nameErr && !acresErr && !treesErr && !diseasedErr && !spacingErr }
  }

  const handleOpenAddModal = () => {
    // Determine next letter or sequence
    const existingNames = new Set(blocks.map((b) => b.id.trim().toLowerCase()))
    let nextName = "Block A"
    for (let i = 0; i < 26; i++) {
      const candidate = `Block ${String.fromCharCode(65 + i)}`
      if (!existingNames.has(candidate.toLowerCase())) {
        nextName = candidate
        break
      }
    }

    const defaultAcres = 4.0
    const defaultDensity = 512
    setFormName(nextName)
    setFormAcres(defaultAcres)
    setFormTrees(Math.round(defaultAcres * defaultDensity))
    setFormDiseased(0)
    setFormSpacing("2.7m x 2.7m")
    setFormSoil("Laterite Red")
    setFormSeverity("Healthy")
    setFormStatus("Optimal Condition")
    setAddSubmitted(false)
    setAddModalOpen(true)
  }

  const handleOpenEditModal = (b: PlantationBlock) => {
    setEditingBlock(b)
    setFormName(b.id)
    setFormAcres(b.areaAcres)
    setFormTrees(b.trees)
    setFormDiseased(b.diseasedTrees)
    setFormSpacing(b.spacing)
    setFormSoil(b.soilType)
    setFormSeverity(b.severity)
    setFormStatus(b.status)
    setEditSubmitted(false)
    setEditModalOpen(true)
  }

  const handleRequestDelete = (b: PlantationBlock) => {
    setBlockToDelete(b)
    setDeleteModalOpen(true)
  }

  const handleSaveAdd = (e: React.FormEvent) => {
    e.preventDefault()
    setAddSubmitted(true)
    const { isValid } = validateAddForm()
    if (!isValid) return

    addBlock({
      id: formName.trim(),
      areaAcres: formAcres,
      trees: formTrees,
      diseasedTrees: formDiseased,
      spacing: formSpacing.trim(),
      soilType: formSoil,
      severity: formSeverity,
      status: formStatus,
    })
    setSelectedBlockId(formName.trim())
    setAddModalOpen(false)
  }

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingBlock) return
    setEditSubmitted(true)
    const { isValid } = validateEditForm()
    if (!isValid) return

    updateBlock(editingBlock.id, {
      id: formName.trim(),
      areaAcres: formAcres,
      trees: formTrees,
      diseasedTrees: formDiseased,
      spacing: formSpacing.trim(),
      soilType: formSoil,
      severity: formSeverity,
      status: formStatus,
    })

    if (selectedBlockId === editingBlock.id) {
      setSelectedBlockId(formName.trim())
    }
    setEditModalOpen(false)
    setEditingBlock(null)
  }

  const handleConfirmDelete = () => {
    if (!blockToDelete) return
    deleteBlock(blockToDelete.id)
    const remaining = blocks.filter((b) => b.id !== blockToDelete.id)
    if (selectedBlockId === blockToDelete.id) {
      if (remaining.length > 0) {
        setSelectedBlockId(remaining[0].id)
      } else {
        setSelectedBlockId("")
      }
    }
    setBlockToDelete(null)
    setDeleteModalOpen(false)
  }

  const handleConfirmClearAll = () => {
    clearBlocks()
    setSelectedBlockId("")
    setClearAllModalOpen(false)
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Location Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-foreground">{t("map.title", "Plantation Map & Land Size Specification")}</h1>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold border border-emerald-500/20">
              Active Plantation Grid
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("map.subtitle", "Configure land acreage sizes, tree counts, density, and block health tracking")}
          </p>
        </div>


        <div className="flex items-center gap-2">
          {blocks.length === 0 ? (
            <button
              onClick={loadDemoBlocks}
              className="btn-secondary text-xs flex items-center gap-1.5 shadow-sm"
            >
              <Sparkles size={14} className="text-primary" /> {t("map.load_sample", "Load Sample Blocks")}
            </button>
          ) : (
            <button
              onClick={() => setClearAllModalOpen(true)}
              className="px-3 py-2 text-xs font-semibold text-muted-foreground hover:text-danger rounded-xl border border-border hover:border-danger/40 transition-colors flex items-center gap-1.5"
              title="Clear all plantation blocks"
            >
              <RotateCcw size={13} />
              <span>{t("map.clear_all", "Clear All")}</span>
            </button>
          )}

          <button
            onClick={handleOpenAddModal}
            className="btn-primary text-xs flex items-center gap-2 shadow-sm font-bold"
          >
            <Plus size={15} />
            <span>{t("map.add_block", "Add Plantation Block")}</span>
          </button>
        </div>
      </div>

      {/* Top Overview KPI Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-card border border-border shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>{t("map.kpi_total_size", "Total Plantation Size")}</span>
            <TreePine size={16} className="text-primary" />
          </div>
          <div className="text-2xl font-bold text-foreground">
            {blocks.length > 0 ? `${totalAcres} ${t("map.acres_unit", "Acres")}` : t("dash.kpi.unconfigured", "Unconfigured")}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            {blocks.length > 0 ? `${totalTrees.toLocaleString()} ${t("map.palms_unit", "Palms")}` : t("map.add_first_block", "Add first block")}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>{t("map.kpi_avg_density", "Average Density")}</span>
            <Layers size={16} className="text-accent" />
          </div>
          <div className="text-2xl font-bold text-foreground">
            {blocks.length > 0 && totalAcres > 0 ? `${Math.round(totalTrees / totalAcres)} trees/acre` : "—"}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">{t("map.standard_grid", "Standard Grid (2.7m)")}</div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>{t("map.kpi_healthy_palms", "Healthy Palms")}</span>
            <ShieldCheck size={16} className="text-primary" />
          </div>
          <div className="text-2xl font-bold text-primary">
            {blocks.length > 0 ? healthyTrees.toLocaleString() : "—"}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            {overallHealthScore !== null ? `${t("map.health_score_prefix", "Health Score")} ${overallHealthScore}%` : t("map.no_data", "No data")}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>{t("map.kpi_diseased_palms", "Diseased Palms")}</span>
            <AlertTriangle size={16} className="text-danger" />
          </div>
          <div className="text-2xl font-bold text-danger">
            {blocks.length > 0 ? diseasedTrees.toLocaleString() : "0"}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            {t("map.across_prefix", "Across")} {blocks.length} {t("map.blocks_suffix", "Blocks")}
          </div>
        </div>
      </div>

      {/* UNCONFIGURED EMPTY STATE */}
      {blocks.length === 0 ? (
        <div className="bg-card rounded-2xl border-2 border-dashed border-border p-12 text-center max-w-2xl mx-auto my-8 space-y-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto shadow-md">
            <Map size={32} />
          </div>
          <h2 className="text-lg font-bold text-foreground">{t("map.empty_title", "No Plantation Blocks Configured")}</h2>
          <p className="text-xs text-muted-foreground leading-relaxed max-w-md mx-auto">
            {t("map.empty_desc", "Add your plantation blocks, specify land area sizes (in acres), and enter palm tree counts to begin monitoring health indices.")}
          </p>

          <div className="flex items-center justify-center gap-3 pt-2">
            <button onClick={handleOpenAddModal} className="btn-primary text-xs flex items-center gap-2">
              <Plus size={14} /> {t("map.add_block", "Add Plantation Block")}
            </button>
            <button onClick={loadDemoBlocks} className="btn-secondary text-xs flex items-center gap-2">
              <Sparkles size={14} className="text-primary" /> {t("map.load_sample", "Load Sample Blocks")}
            </button>
          </div>
        </div>
      ) : (
        /* POPULATED PLANTATION GRID & SPECIFICATIONS */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Interactive Plantation Grid */}
          <div className="lg:col-span-8 bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-foreground flex items-center gap-2">
                  <Map size={16} className="text-primary" /> {t("map.grid_title", "Interactive Plantation Layout Grid")}
                </span>
                <span className="text-[11px] text-muted-foreground block mt-0.5">
                  Click a block to inspect specifications or use card quick actions
                </span>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-muted rounded-lg text-muted-foreground">
                {blocks.length} {blocks.length === 1 ? "Block" : "Blocks"}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {blocks.map((b) => {
                const isSelected = selectedBlock?.id === b.id
                const blockDensity = b.areaAcres > 0 ? Math.round(b.trees / b.areaAcres) : 0
                const healthPercent = b.health

                return (
                  <div
                    key={b.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedBlockId(b.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault()
                        setSelectedBlockId(b.id)
                      }
                    }}
                    className={`p-4 rounded-2xl border text-left transition-all relative overflow-hidden group cursor-pointer flex flex-col justify-between select-none ${
                      isSelected
                        ? "border-primary shadow-md ring-2 ring-primary/20 bg-primary/5"
                        : "border-border bg-card hover:border-primary/40 hover:bg-muted/20"
                    }`}
                  >
                    <div>
                      {/* Card Header: Identity & Direct Quick Actions */}
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-3.5 h-3.5 rounded-full shrink-0 shadow-xs"
                            style={{ background: b.color }}
                          />
                          <div>
                            <span className="text-sm font-extrabold text-foreground block leading-tight">
                              {b.id}
                            </span>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className="text-[11px] font-bold text-primary">
                                {b.areaAcres} {t("map.acres_unit", "Acres")}
                              </span>
                              {(b.treatmentStatus === "recovering" || b.status === "Under Recovery") && (
                                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 font-bold text-[9px]">
                                  <Clock size={10} /> 14d Recovery
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Card-Level Quick Actions (Edit & Delete) */}
                        <div className="flex items-center gap-1 bg-muted/70 dark:bg-muted/40 p-1 rounded-xl border border-border/50">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleOpenEditModal(b)
                            }}
                            className="p-1 rounded-lg text-muted-foreground hover:text-primary hover:bg-card transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                            title={`${t("map.edit", "Edit")} ${b.id}`}
                            aria-label={`${t("map.edit", "Edit")} ${b.id}`}
                          >
                            <Edit3 size={13} />
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleRequestDelete(b)
                            }}
                            className="p-1 rounded-lg text-muted-foreground hover:text-danger hover:bg-card transition-colors focus-visible:ring-2 focus-visible:ring-danger focus-visible:outline-none"
                            title={`${t("map.delete", "Delete")} ${b.id}`}
                            aria-label={`${t("map.delete", "Delete")} ${b.id}`}
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </div>

                      {/* Palms Count & Density */}
                      <div className="space-y-1 text-xs">
                        <div className="text-foreground font-bold text-sm">
                          {b.trees.toLocaleString()} {t("map.palms_unit", "Palms")}
                        </div>
                        <div className="text-[11px] text-muted-foreground">
                          {blockDensity} trees/acre • {b.spacing}
                        </div>
                        <div className="text-[10px] text-muted-foreground truncate">
                          Soil: {b.soilType}
                        </div>
                      </div>
                    </div>

                    {/* Health Status Bar */}
                    <div className="mt-3 pt-2.5 border-t border-border/60">
                      <div className="flex items-center justify-between text-[11px] mb-1">
                        <span className="font-bold" style={{ color: b.color }}>
                          {t("map.health_prefix", "Health")}: {healthPercent}%
                        </span>
                        <span className="text-muted-foreground">
                          {b.diseasedTrees} {t("map.diseased_suffix", "diseased")}
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{
                            width: `${healthPercent}%`,
                            backgroundColor: b.color,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}

              {/* Inline Dashed "+ Add Plantation Block" Card Tile */}
              <button
                type="button"
                onClick={handleOpenAddModal}
                className="p-5 rounded-2xl border-2 border-dashed border-primary/30 hover:border-primary bg-primary/5 hover:bg-primary/10 text-primary flex flex-col items-center justify-center gap-2.5 min-h-[160px] transition-all group focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none cursor-pointer"
              >
                <div className="w-10 h-10 rounded-full bg-primary/15 group-hover:bg-primary group-hover:text-white flex items-center justify-center transition-all shadow-xs">
                  <Plus size={20} />
                </div>
                <div className="text-center">
                  <span className="text-xs font-extrabold text-foreground group-hover:text-primary transition-colors block">
                    {t("map.add_block", "Add Plantation Block")}
                  </span>
                  <span className="text-[11px] text-muted-foreground mt-0.5 block">
                    Quick setup parcel, acres & palms
                  </span>
                </div>
              </button>
            </div>
          </div>

          {/* Right Column: Block Specifications Panel */}
          {selectedBlock && (
            <div className="lg:col-span-4 bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <h3 className="text-sm font-extrabold text-foreground">
                    {selectedBlock.id} {t("map.spec_suffix", "Specifications")}
                  </h3>
                  <span className="text-[11px] text-muted-foreground font-medium">
                    Detailed acreage & health overview
                  </span>
                </div>
                <span
                  className="px-2.5 py-1 rounded-full text-[11px] font-bold"
                  style={{
                    color: selectedBlock.color,
                    backgroundColor: `${selectedBlock.color}15`,
                  }}
                >
                  {selectedBlock.status}
                </span>
              </div>

              {(selectedBlock.treatmentStatus === "recovering" || selectedBlock.status === "Under Recovery") && (
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-2 animate-in fade-in">
                  <div className="flex items-center justify-between text-xs font-bold text-emerald-800 dark:text-emerald-300">
                    <div className="flex items-center gap-1.5">
                      <ShieldCheck size={15} className="text-emerald-600" />
                      <span>14-Day Post-Treatment Recovery</span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-600 text-white text-[10px] font-bold">
                      Under Care
                    </span>
                  </div>
                  <div className="space-y-1 text-[11px] text-muted-foreground border-t border-emerald-600/15 pt-2">
                    {selectedBlock.treatmentDetails && (
                      <div>Prescription: <strong className="text-foreground">{selectedBlock.treatmentDetails}</strong></div>
                    )}
                    {selectedBlock.lastTreatmentDate && (
                      <div>Logged On: <strong className="text-foreground">{selectedBlock.lastTreatmentDate}</strong></div>
                    )}
                    {selectedBlock.followUpDate && (
                      <div className="text-emerald-700 dark:text-emerald-400 font-semibold flex items-center gap-1 pt-0.5">
                        <Clock size={11} />
                        <span>Follow-up Inspection Due: {selectedBlock.followUpDate}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="space-y-3.5 text-xs">
                <div className="p-3 rounded-xl bg-primary/10 border border-primary/20 flex justify-between items-center">
                  <span className="text-muted-foreground font-medium">{t("map.land_acreage", "Land Acreage Size")}</span>
                  <span className="font-extrabold text-primary text-sm">{selectedBlock.areaAcres} {t("map.acres_unit", "Acres")}</span>
                </div>

                <div className="flex items-center justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">{t("map.condition_status", "Condition Status")}</span>
                  <span className="font-bold" style={{ color: selectedBlock.color }}>
                    {selectedBlock.status}
                  </span>
                </div>

                <div className="flex items-center justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">{t("map.total_palms_monitored", "Total Palms Monitored")}</span>
                  <span className="font-bold text-foreground">{selectedBlock.trees.toLocaleString()}</span>
                </div>

                <div className="flex items-center justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">{t("map.kpi_diseased_palms", "Diseased Palms")}</span>
                  <span className="font-bold text-danger">{selectedBlock.diseasedTrees.toLocaleString()}</span>
                </div>

                <div className="flex items-center justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">{t("map.kpi_healthy_palms", "Healthy Palms")}</span>
                  <span className="font-bold text-primary">{(selectedBlock.trees - selectedBlock.diseasedTrees).toLocaleString()}</span>
                </div>

                <div className="flex items-center justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">{t("map.tree_density", "Tree Density")}</span>
                  <span className="font-bold text-foreground">
                    {selectedBlock.areaAcres > 0 ? Math.round(selectedBlock.trees / selectedBlock.areaAcres) : 0} {t("map.trees_per_acre", "trees / acre")}
                  </span>
                </div>

                <div className="flex items-center justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">{t("map.tree_spacing", "Tree Spacing Grid")}</span>
                  <span className="font-bold text-foreground">{selectedBlock.spacing}</span>
                </div>

                <div className="flex items-center justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">{t("map.soil_profile", "Soil Profile")}</span>
                  <span className="font-bold text-foreground">{selectedBlock.soilType}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("map.health_index", "Health Index")}</span>
                  <span className="font-extrabold text-primary text-sm">{selectedBlock.health}%</span>
                </div>
              </div>

              {/* Dedicated Action Bar in Specifications Panel */}
              <div className="pt-2 border-t border-border space-y-2">
                <button
                  type="button"
                  onClick={() => {
                    setTreatmentBlockPalms(selectedBlock.trees)
                    setTreatmentModalOpen(true)
                  }}
                  className="w-full py-2.5 px-3 rounded-xl bg-primary hover:bg-primary/90 text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                >
                  <Calculator size={14} />
                  <span>Fertilizer & Spray Hub ({selectedBlock.trees.toLocaleString()} Palms)</span>
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleOpenEditModal(selectedBlock)}
                    className="btn-secondary flex-1 text-xs flex items-center justify-center gap-1.5 py-2.5 font-bold"
                  >
                    <Edit3 size={14} />
                    <span>{t("map.edit", "Edit Specifications")}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRequestDelete(selectedBlock)}
                    className="py-2.5 px-3 rounded-xl border border-danger/30 text-danger hover:bg-danger/10 text-xs font-bold flex items-center justify-center gap-1.5 transition-colors focus-visible:ring-2 focus-visible:ring-danger focus-visible:outline-none"
                    title={`Delete ${selectedBlock.id}`}
                  >
                    <Trash2 size={14} />
                    <span>{t("map.delete", "Delete")}</span>
                  </button>
                </div>

                <button
                  type="button"
                  onClick={handleOpenAddModal}
                  className="w-full py-2 px-3 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary text-xs font-bold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Plus size={14} />
                  <span>{t("map.add_block", "Add New Block")}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ADD BLOCK MODAL */}
      {addModalOpen && (() => {
        const errors = validateAddForm()
        return (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <form
              ref={addModalRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby="add-block-title"
              onSubmit={handleSaveAdd}
              noValidate
              className="bg-card border border-border rounded-2xl p-6 max-w-md w-full max-h-[90vh] overflow-y-auto shadow-2xl space-y-4 animate-in fade-in zoom-in-95 outline-none"
            >
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                    <Plus size={18} />
                  </div>
                  <div>
                    <h3 id="add-block-title" className="text-sm font-bold text-foreground">
                      {t("map.add_block", "Add Plantation Block")}
                    </h3>
                    <p className="text-[11px] text-muted-foreground">Configure parcel acreage & palm density</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
                  className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                  aria-label={t("common.cancel", "Cancel")}
                >
                  <X size={18} />
                </button>
              </div>

              {addSubmitted && !errors.isValid && (
                <div role="alert" aria-live="assertive" className="p-2.5 bg-danger/10 border border-danger/30 rounded-xl text-xs text-danger font-semibold flex items-center gap-2">
                  <AlertCircle size={14} className="shrink-0" />
                  <span>{t("map.fix_errors", "Please correct the highlighted errors before saving.")}</span>
                </div>
              )}

              <div className="space-y-3.5 text-xs">
                <div>
                  <label htmlFor="add-form-name" className="block font-semibold text-foreground mb-1">
                    {t("map.label_block_id", "Block Identifier / Name")}
                  </label>
                  <input
                    id="add-form-name"
                    type="text"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder={t("map.placeholder_block_name", "e.g. Block A, North Field")}
                    className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground font-semibold outline-none transition-colors ${
                      addSubmitted && errors.nameErr
                        ? "border-danger ring-1 ring-danger/30"
                        : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                    }`}
                    aria-invalid={addSubmitted && !!errors.nameErr}
                    aria-describedby={addSubmitted && errors.nameErr ? "add-name-error" : undefined}
                  />
                  {addSubmitted && errors.nameErr && (
                    <p id="add-name-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                      <AlertCircle size={12} className="shrink-0" />
                      <span>{errors.nameErr}</span>
                    </p>
                  )}
                </div>

                {/* Acreage Size & Spacing Presets */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="add-form-acres" className="block font-semibold text-foreground mb-1">
                      {t("map.label_land_size", "Land Size (Acres)")}
                    </label>
                    <input
                      id="add-form-acres"
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={formAcres}
                      onChange={(e) => setFormAcres(parseFloat(e.target.value) || 0)}
                      className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground font-semibold outline-none transition-colors ${
                        addSubmitted && errors.acresErr
                          ? "border-danger ring-1 ring-danger/30"
                          : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                      }`}
                      aria-invalid={addSubmitted && !!errors.acresErr}
                      aria-describedby={addSubmitted && errors.acresErr ? "add-acres-error" : undefined}
                    />
                    {addSubmitted && errors.acresErr && (
                      <p id="add-acres-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                        <AlertCircle size={12} className="shrink-0" />
                        <span>{errors.acresErr}</span>
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="add-form-spacing" className="block font-semibold text-foreground mb-1">
                      {t("map.tree_spacing", "Tree Spacing Grid")}
                    </label>
                    <select
                      id="add-form-spacing"
                      value={formSpacing}
                      onChange={(e) => {
                        setFormSpacing(e.target.value)
                        const dens = getDensityForSpacing(e.target.value)
                        setFormTrees(Math.max(1, Math.round(formAcres * dens)))
                      }}
                      className="w-full bg-muted/40 border border-border rounded-lg px-3 py-2 text-foreground font-medium outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    >
                      {SPACING_PRESETS.map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Total Palms with Auto-Calculate Shortcut */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label htmlFor="add-form-trees" className="font-semibold text-foreground">
                      {t("map.label_total_palms", "Total Areca Palms (Trees)")}
                    </label>
                    <button
                      type="button"
                      onClick={() => setFormTrees(suggestedPalms)}
                      className="text-[11px] text-primary hover:text-primary/80 font-bold flex items-center gap-1 transition-colors"
                      title="Apply calculated palms based on acres and spacing"
                    >
                      <Calculator size={12} />
                      <span>Auto-calc (~{suggestedPalms.toLocaleString()})</span>
                    </button>
                  </div>
                  <input
                    id="add-form-trees"
                    type="number"
                    min="1"
                    value={formTrees}
                    onChange={(e) => setFormTrees(parseInt(e.target.value) || 0)}
                    className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground font-semibold outline-none transition-colors ${
                      addSubmitted && errors.treesErr
                        ? "border-danger ring-1 ring-danger/30"
                        : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                    }`}
                    aria-invalid={addSubmitted && !!errors.treesErr}
                    aria-describedby={addSubmitted && errors.treesErr ? "add-trees-error" : undefined}
                  />
                  {addSubmitted && errors.treesErr && (
                    <p id="add-trees-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                      <AlertCircle size={12} className="shrink-0" />
                      <span>{errors.treesErr}</span>
                    </p>
                  )}
                </div>

                {/* Diseased Palms & Soil Profile */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="add-form-diseased" className="block font-semibold text-foreground mb-1">
                      {t("map.label_diseased_count", "Diseased Palms")}
                    </label>
                    <input
                      id="add-form-diseased"
                      type="number"
                      min="0"
                      value={formDiseased}
                      onChange={(e) => {
                        const val = parseInt(e.target.value) || 0
                        setFormDiseased(val)
                        if (val === 0) {
                          setFormSeverity("Healthy")
                          setFormStatus("Optimal Condition")
                        } else if (val < formTrees * 0.1) {
                          setFormSeverity("Mild")
                          setFormStatus("Minor Outbreak")
                        } else {
                          setFormSeverity("Moderate")
                          setFormStatus("Active Monitoring")
                        }
                      }}
                      className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground font-semibold outline-none transition-colors ${
                        (addSubmitted || formDiseased > formTrees) && errors.diseasedErr
                          ? "border-danger ring-1 ring-danger/30"
                          : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                      }`}
                      aria-invalid={(addSubmitted || formDiseased > formTrees) && !!errors.diseasedErr}
                      aria-describedby={errors.diseasedErr ? "add-diseased-error" : undefined}
                    />
                    {(addSubmitted || formDiseased > formTrees) && errors.diseasedErr && (
                      <p id="add-diseased-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                        <AlertCircle size={12} className="shrink-0" />
                        <span>{errors.diseasedErr}</span>
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="add-form-soil" className="block font-semibold text-foreground mb-1">
                      {t("map.soil_profile", "Soil Profile")}
                    </label>
                    <select
                      id="add-form-soil"
                      value={formSoil}
                      onChange={(e) => setFormSoil(e.target.value)}
                      className="w-full bg-muted/40 border border-border rounded-lg px-3 py-2 text-foreground font-medium outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    >
                      {SOIL_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
                  className="btn-secondary text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                >
                  {t("common.cancel", "Cancel")}
                </button>
                <button
                  type="submit"
                  className="btn-primary text-xs flex items-center gap-1.5 shadow-sm font-bold focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                >
                  <Check size={14} /> {t("map.add_block_btn", "Add Block")}
                </button>
              </div>
            </form>
          </div>
        )
      })()}

      {/* EDIT BLOCK MODAL */}
      {editModalOpen && editingBlock && (() => {
        const errors = validateEditForm()
        return (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <form
              ref={editModalRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby="edit-block-title"
              onSubmit={handleSaveEdit}
              noValidate
              className="bg-card border border-border rounded-2xl p-6 max-w-md w-full max-h-[90vh] overflow-y-auto shadow-2xl space-y-4 animate-in fade-in zoom-in-95 outline-none"
            >
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                    <Edit3 size={18} />
                  </div>
                  <div>
                    <h3 id="edit-block-title" className="text-sm font-bold text-foreground">
                      {t("map.edit_prefix", "Edit")} {editingBlock.id} {t("map.spec_suffix", "Specifications")}
                    </h3>
                    <p className="text-[11px] text-muted-foreground">Update parcel dimensions and counts</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setEditModalOpen(false)
                    setEditingBlock(null)
                  }}
                  className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                  aria-label={t("common.cancel", "Cancel")}
                >
                  <X size={18} />
                </button>
              </div>

              {editSubmitted && !errors.isValid && (
                <div role="alert" aria-live="assertive" className="p-2.5 bg-danger/10 border border-danger/30 rounded-xl text-xs text-danger font-semibold flex items-center gap-2">
                  <AlertCircle size={14} className="shrink-0" />
                  <span>{t("map.fix_errors", "Please correct the highlighted errors before saving.")}</span>
                </div>
              )}

              <div className="space-y-3.5 text-xs">
                <div>
                  <label htmlFor="edit-form-name" className="block font-semibold text-foreground mb-1">
                    {t("map.label_block_id", "Block Identifier / Name")}
                  </label>
                  <input
                    id="edit-form-name"
                    type="text"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder={t("map.placeholder_block_name", "e.g. Block A, North Field")}
                    className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground font-semibold outline-none transition-colors ${
                      editSubmitted && errors.nameErr
                        ? "border-danger ring-1 ring-danger/30"
                        : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                    }`}
                    aria-invalid={editSubmitted && !!errors.nameErr}
                    aria-describedby={editSubmitted && errors.nameErr ? "edit-name-error" : undefined}
                  />
                  {editSubmitted && errors.nameErr && (
                    <p id="edit-name-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                      <AlertCircle size={12} className="shrink-0" />
                      <span>{errors.nameErr}</span>
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="edit-form-acres" className="block font-semibold text-foreground mb-1">
                      {t("map.label_block_area", "Block Area Size (Acres)")}
                    </label>
                    <input
                      id="edit-form-acres"
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={formAcres}
                      onChange={(e) => setFormAcres(parseFloat(e.target.value) || 0)}
                      className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground font-semibold outline-none transition-colors ${
                        editSubmitted && errors.acresErr
                          ? "border-danger ring-1 ring-danger/30"
                          : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                      }`}
                      aria-invalid={editSubmitted && !!errors.acresErr}
                      aria-describedby={editSubmitted && errors.acresErr ? "edit-acres-error" : undefined}
                    />
                    {editSubmitted && errors.acresErr && (
                      <p id="edit-acres-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                        <AlertCircle size={12} className="shrink-0" />
                        <span>{errors.acresErr}</span>
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="edit-form-spacing" className="block font-semibold text-foreground mb-1">
                      {t("map.tree_spacing", "Tree Spacing Grid")}
                    </label>
                    <input
                      id="edit-form-spacing"
                      type="text"
                      value={formSpacing}
                      onChange={(e) => setFormSpacing(e.target.value)}
                      className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground outline-none transition-colors ${
                        editSubmitted && errors.spacingErr
                          ? "border-danger ring-1 ring-danger/30"
                          : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                      }`}
                      aria-invalid={editSubmitted && !!errors.spacingErr}
                      aria-describedby={editSubmitted && errors.spacingErr ? "edit-spacing-error" : undefined}
                    />
                    {editSubmitted && errors.spacingErr && (
                      <p id="edit-spacing-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                        <AlertCircle size={12} className="shrink-0" />
                        <span>{errors.spacingErr}</span>
                      </p>
                    )}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label htmlFor="edit-form-trees" className="font-semibold text-foreground">
                      {t("map.label_total_palms", "Total Areca Palms (Trees)")}
                    </label>
                    <button
                      type="button"
                      onClick={() => setFormTrees(suggestedPalms)}
                      className="text-[11px] text-primary hover:text-primary/80 font-bold flex items-center gap-1 transition-colors"
                      title="Apply calculated palms based on acres and spacing"
                    >
                      <Calculator size={12} />
                      <span>Re-calculate (~{suggestedPalms.toLocaleString()})</span>
                    </button>
                  </div>
                  <input
                    id="edit-form-trees"
                    type="number"
                    min="1"
                    value={formTrees}
                    onChange={(e) => setFormTrees(parseInt(e.target.value) || 0)}
                    className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground font-semibold outline-none transition-colors ${
                      editSubmitted && errors.treesErr
                        ? "border-danger ring-1 ring-danger/30"
                        : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                    }`}
                    aria-invalid={editSubmitted && !!errors.treesErr}
                    aria-describedby={editSubmitted && errors.treesErr ? "edit-trees-error" : undefined}
                  />
                  {editSubmitted && errors.treesErr && (
                    <p id="edit-trees-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                      <AlertCircle size={12} className="shrink-0" />
                      <span>{errors.treesErr}</span>
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="edit-form-diseased" className="block font-semibold text-foreground mb-1">
                      {t("map.label_diseased_count", "Diseased Palms")}
                    </label>
                    <input
                      id="edit-form-diseased"
                      type="number"
                      min="0"
                      value={formDiseased}
                      onChange={(e) => setFormDiseased(parseInt(e.target.value) || 0)}
                      className={`w-full bg-muted/40 border rounded-lg px-3 py-2 text-foreground font-semibold outline-none transition-colors ${
                        (editSubmitted || formDiseased > formTrees) && errors.diseasedErr
                          ? "border-danger ring-1 ring-danger/30"
                          : "border-border focus:border-primary focus:ring-2 focus:ring-primary/20"
                      }`}
                      aria-invalid={(editSubmitted || formDiseased > formTrees) && !!errors.diseasedErr}
                      aria-describedby={errors.diseasedErr ? "edit-diseased-error" : undefined}
                    />
                    {(editSubmitted || formDiseased > formTrees) && errors.diseasedErr && (
                      <p id="edit-diseased-error" role="alert" aria-live="polite" className="text-[11px] text-danger font-medium flex items-center gap-1 mt-1">
                        <AlertCircle size={12} className="shrink-0" />
                        <span>{errors.diseasedErr}</span>
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="edit-form-soil" className="block font-semibold text-foreground mb-1">
                      {t("map.soil_profile", "Soil Profile")}
                    </label>
                    <select
                      id="edit-form-soil"
                      value={formSoil}
                      onChange={(e) => setFormSoil(e.target.value)}
                      className="w-full bg-muted/40 border border-border rounded-lg px-3 py-2 text-foreground font-medium outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    >
                      {SOIL_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => {
                    setEditModalOpen(false)
                    setEditingBlock(null)
                  }}
                  className="btn-secondary text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                >
                  {t("common.cancel", "Cancel")}
                </button>
                <button
                  type="submit"
                  className="btn-primary text-xs flex items-center gap-1.5 shadow-sm font-bold focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                >
                  <Check size={14} /> {t("map.save_spec", "Save Specifications")}
                </button>
              </div>
            </form>
          </div>
        )
      })()}

      {/* DELETE BLOCK CONFIRMATION MODAL */}
      {deleteModalOpen && blockToDelete && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div
            ref={deleteModalRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-block-title"
            className="bg-card border border-border rounded-2xl p-6 max-w-sm w-full space-y-4 shadow-2xl animate-in fade-in zoom-in-95 outline-none"
          >
            <div className="w-12 h-12 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
              <AlertTriangle size={24} />
            </div>
            <div className="text-center space-y-2">
              <h2 id="delete-block-title" className="text-base font-extrabold text-foreground">
                {t("map.confirm_delete_block_title", "Delete Plantation Block?")}
              </h2>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {t("map.confirm_delete_block_desc", "Are you sure you want to delete this plantation block? This will permanently remove it from your plantation layout and recalculate all health indices.")}
              </p>
              <div className="p-3 bg-muted/40 rounded-xl border border-border text-xs text-left space-y-1">
                <div className="font-extrabold text-foreground flex items-center justify-between">
                  <span>{blockToDelete.id}</span>
                  <span className="text-[11px] font-bold text-primary">{blockToDelete.areaAcres} Acres</span>
                </div>
                <div className="text-muted-foreground flex justify-between">
                  <span>Monitored Palms:</span>
                  <span className="font-semibold text-foreground">{blockToDelete.trees.toLocaleString()} trees</span>
                </div>
                <div className="text-muted-foreground flex justify-between">
                  <span>Diseased Palms:</span>
                  <span className="font-semibold text-danger">{blockToDelete.diseasedTrees.toLocaleString()} trees</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  setDeleteModalOpen(false)
                  setBlockToDelete(null)
                }}
                className="flex-1 py-2.5 px-3 border border-border rounded-xl text-xs font-semibold text-foreground hover:bg-muted transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                {t("map.confirm_cancel_btn", "Keep Block")}
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                className="flex-1 py-2.5 px-3 bg-danger hover:bg-danger/90 text-white rounded-xl text-xs font-bold transition-colors shadow-sm focus-visible:ring-2 focus-visible:ring-danger focus-visible:outline-none flex items-center justify-center gap-1.5"
              >
                <Trash2 size={13} />
                <span>{t("map.confirm_delete_btn", "Yes, Delete")}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CLEAR ALL CONFIRMATION MODAL */}
      {clearAllModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div
            ref={clearAllModalRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby="clear-all-title"
            className="bg-card border border-border rounded-2xl p-6 max-w-sm w-full space-y-4 shadow-2xl animate-in fade-in zoom-in-95 outline-none"
          >
            <div className="w-12 h-12 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
              <RotateCcw size={24} />
            </div>
            <div className="text-center space-y-2">
              <h2 id="clear-all-title" className="text-base font-extrabold text-foreground">
                Clear All Plantation Blocks?
              </h2>
              <p className="text-xs text-muted-foreground leading-relaxed">
                This will remove all {blocks.length} blocks ({totalAcres} acres, {totalTrees.toLocaleString()} palms). You can add new custom blocks or restore demo data anytime.
              </p>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <button
                type="button"
                onClick={() => setClearAllModalOpen(false)}
                className="flex-1 py-2.5 px-3 border border-border rounded-xl text-xs font-semibold text-foreground hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmClearAll}
                className="flex-1 py-2.5 px-3 bg-danger hover:bg-danger/90 text-white rounded-xl text-xs font-bold transition-colors shadow-sm"
              >
                Yes, Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fertilizer & Pesticide Dosage Hub Modal */}
      <TreatmentCalculatorModal
        isOpen={treatmentModalOpen}
        onClose={() => setTreatmentModalOpen(false)}
        initialPalms={treatmentBlockPalms}
      />
    </div>
  )
}
