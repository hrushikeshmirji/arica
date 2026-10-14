import { useState, useMemo } from "react"
import { useNavigate } from "react-router-dom"
import { Search, ShieldAlert, Sparkles, CheckCircle2, Camera, Droplets, Bug, AlertTriangle, Calculator, Sprout } from "lucide-react"
import { useLanguage } from "../contexts/LanguageContext"
import { handleImageError } from "../utils/imageFallback"
import TreatmentCalculatorModal from "../components/TreatmentCalculatorModal"

type FilterCategory = "all" | "fungal" | "pest_disorder" | "healthy"

interface DiseaseItem {
  id: string
  name: string
  kannadaName: string
  category: "fungal" | "pest_disorder" | "healthy"
  shortDesc: string
  symptoms: string[]
  treatment: string
  severity: "Critical" | "Severe" | "Moderate" | "Mild" | "Healthy"
  isActiveVision: boolean
  modelBackbone: string
  image: string
}

export default function Diseases() {
  const { t, language } = useLanguage()
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [filterCategory, setFilterCategory] = useState<FilterCategory>("all")
  const [treatmentModalOpen, setTreatmentModalOpen] = useState(false)
  const [treatmentModalDisease, setTreatmentModalDisease] = useState("koleroga")
  const [treatmentModalMode, setTreatmentModalMode] = useState<"pesticides" | "fertilizers">("pesticides")

  const diseaseCatalog: DiseaseItem[] = useMemo(() => [
    {
      id: "koleroga",
      name: t("diseases.koleroga.name", "Fruit Rot / Koleroga (Phytophthora meadii)"),
      kannadaName: "ಕೊಳೆರೋಗ / ಮಹಾಲಿ",
      category: "fungal",
      shortDesc: t("diseases.koleroga.desc", "Devastating water-borne oomycete disease active during monsoon seasons causing mass nut dropping."),
      symptoms: [
        t("diseases.koleroga.symptom1", "Water-soaked dark lesions on nut surface"),
        t("diseases.koleroga.symptom2", "Foul smelling soft rot and felty fungal growth"),
        t("diseases.koleroga.symptom3", "Mass premature nut shedding across bunches"),
      ],
      treatment: t("diseases.koleroga.treatment", "Spray 1% Bordeaux mixture before monsoon onset covering fruit bunches. Repeat after 40-45 days if rainfall persists."),
      severity: "Critical",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_koleroga.jpg",
    },
    {
      id: "anthracnose",
      name: t("diseases.anthracnose.name", "Anthracnose (Colletotrichum gloeosporioides)"),
      kannadaName: "ಹಿಂಗಾರ ಒಣಗುವ ರೋಗ (ಆಂಥ್ರಾಕ್ನೋಸ್)",
      category: "fungal",
      shortDesc: t("diseases.anthracnose.desc", "Fungal infection causing leaf blight, dieback, and dark sunken lesions on developing nuts."),
      symptoms: [
        t("diseases.anthracnose.symptom1", "Dark sunken circular spots on husk"),
        t("diseases.anthracnose.symptom2", "Leaf dieback and dark blighted frond tips"),
        t("diseases.anthracnose.symptom3", "Premature nut shedding and stalk rot"),
      ],
      treatment: t("diseases.anthracnose.treatment", "Spray 1% Bordeaux mixture or Copper Oxychloride 50% WP (2.5g/L). Prune infected fronds and improve aeration."),
      severity: "Severe",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_anthracnose.jpg",
    },
    {
      id: "bud_borer",
      name: t("diseases.bud_borer.name", "Bud Borer Pest Infestation"),
      kannadaName: "ಸುಳಿ ಹುಳು ಬಾಧೆ",
      category: "pest_disorder",
      shortDesc: t("diseases.bud_borer.desc", "Larval pest infestation boring into tender spindle and crown tissues, causing shoot rot and wilting."),
      symptoms: [
        t("diseases.bud_borer.symptom1", "Bore holes and frass accumulation at crown"),
        t("diseases.bud_borer.symptom2", "Spindle leaf wilting and central shoot decay"),
        t("diseases.bud_borer.symptom3", "Stunted vegetative growth and crown deformation"),
      ],
      treatment: t("diseases.bud_borer.treatment", "Clean dead debris from leaf axils and dust with neem cake and sand (1:1). Chlorpyrifos crown spray is restricted under S.O. 4294(E)."),
      severity: "Critical",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_bud_borer.jpg",
    },
    {
      id: "leaf_spot",
      name: t("diseases.leaf_spot.name", "Leaf Spot Complex"),
      kannadaName: "ಎಲೆ ಚುಕ್ಕೆ ರೋಗ",
      category: "fungal",
      shortDesc: t("diseases.leaf_spot.desc", "Complex fungal pathology causing necrotic circular and irregular spots, reducing photosynthetic vigor."),
      symptoms: [
        t("diseases.leaf_spot.symptom1", "Circular to irregular necrotic brown leaf spots"),
        t("diseases.leaf_spot.symptom2", "Yellow halos surrounding necrotic lesions"),
        t("diseases.leaf_spot.symptom3", "Premature drying of lower canopy fronds"),
      ],
      treatment: t("diseases.leaf_spot.treatment", "Remove severely spotted lower fronds, thin overhanging shade trees, and improve crown aeration. Unverified chemical triazoles withheld."),
      severity: "Moderate",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_leaf_spot.jpg",
    },
    {
      id: "nut_cracking",
      name: t("diseases.nut_cracking.name", "Nut Cracking Disorder"),
      kannadaName: "ಕಾಯಿ ಒಡೆಯುವಿಕೆ / ಬಿರುಕು",
      category: "pest_disorder",
      shortDesc: t("diseases.nut_cracking.desc", "Physiological disorder resulting from sudden moisture fluctuation or boron deficiency."),
      symptoms: [
        t("diseases.nut_cracking.symptom1", "Splitting and cracking of tender nut husk"),
        t("diseases.nut_cracking.symptom2", "Exposure of inner kernel tissue to atmosphere"),
        t("diseases.nut_cracking.symptom3", "Secondary microbial colonization on exposed tissue"),
      ],
      treatment: t("diseases.nut_cracking.treatment", "Apply Borax (15-20g per palm annually) and maintain uniform, regulated irrigation."),
      severity: "Moderate",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_nut_cracking.jpg",
    },
    {
      id: "phytoplasma",
      name: t("diseases.phytoplasma.name", "Phytoplasma Yellow Leaf Disease"),
      kannadaName: "ಹಳದಿ ಎಲೆ ರೋಗ (ಫೈಟೋಪ್ಲಾಸ್ಮಾ)",
      category: "pest_disorder",
      shortDesc: t("diseases.phytoplasma.desc", "Systemic phytoplasma pathogen causing intense yellowing of inner whorl leaflets and crown decline."),
      symptoms: [
        t("diseases.phytoplasma.symptom1", "Progressive yellowing of inner whorl leaflets"),
        t("diseases.phytoplasma.symptom2", "Marginal brown necrosis and leaflet stunting"),
        t("diseases.phytoplasma.symptom3", "Black kernel rot inside developing nuts"),
      ],
      treatment: t("diseases.phytoplasma.treatment", "Supportive nutrition only (NOT A CURE): Apply balanced NPK + Magnesium Sulphate (100g) + Zinc Sulphate (50g) to sustain vigor. Chemical fungicides are prohibited; rogue severely diseased palms."),
      severity: "Severe",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_phytoplasma.jpg",
    },
    {
      id: "sooty_mold",
      name: t("diseases.sooty_mold.name", "Sooty Mold (Capnodium spp.)"),
      kannadaName: "ಕಾಡಿಗೆ ರೋಗ / ಕಪ್ಪು ಬೂಜು",
      category: "fungal",
      shortDesc: t("diseases.sooty_mold.desc", "Superficial black fungal coating thriving on honeydew excreted by sap-sucking scale insects."),
      symptoms: [
        t("diseases.sooty_mold.symptom1", "Velvety black soot coating covering frond surface"),
        t("diseases.sooty_mold.symptom2", "Blockage of sunlight and reduced photosynthesis"),
        t("diseases.sooty_mold.symptom3", "Presence of scale insects and mealybug colonies"),
      ],
      treatment: t("diseases.sooty_mold.treatment", "Spray 2% boiled starch paste to peel off black mold. Manage sucking insect vectors with Fish Oil Rosin Soap (FORS) or neem oil."),
      severity: "Mild",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_sooty_mold.jpg",
    },
    {
      id: "stem_bleeding",
      name: t("diseases.stem_bleeding.name", "Stem Bleeding (Thielaviopsis paradoxa)"),
      kannadaName: "ಕಾಂಡ ಸೋರುವಿಕೆ ರೋಗ",
      category: "fungal",
      shortDesc: t("diseases.stem_bleeding.desc", "Fungal infection causing exudation of dark reddish-brown gummy fluid from trunk fissures."),
      symptoms: [
        t("diseases.stem_bleeding.symptom1", "Dark reddish-brown exudation oozing from trunk"),
        t("diseases.stem_bleeding.symptom2", "Internal fibrous tissue rotting beneath bark"),
        t("diseases.stem_bleeding.symptom3", "Tapering of trunk and yellowing of lower canopy"),
      ],
      treatment: t("diseases.stem_bleeding.treatment", "Chisel affected decaying bark cleanly to healthy wood and burn shavings. Chemical wound dressings are under agronomic review; obsolete coal tar and banned Tridemorph are prohibited. Consult KVK."),
      severity: "Severe",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_stem_bleeding.jpg",
    },
    {
      id: "stem_cracking",
      name: t("diseases.stem_cracking.name", "Stem Cracking Disorder"),
      kannadaName: "ಕಾಂಡ ಸೀಳುವಿಕೆ / ಲಂಬ ಬಿರುಕು",
      category: "pest_disorder",
      shortDesc: t("diseases.stem_cracking.desc", "Longitudinal splits on palm trunk caused by intense sun scorch, drought stress, or sap surges."),
      symptoms: [
        t("diseases.stem_cracking.symptom1", "Vertical fissures and cracking on sun-facing trunk"),
        t("diseases.stem_cracking.symptom2", "Bark peeling and trunk structural weakening"),
        t("diseases.stem_cracking.symptom3", "Secondary entry point for boring pests and pathogens"),
      ],
      treatment: t("diseases.stem_cracking.treatment", "Whitewash trunk up to 2.5m with slaked lime wash. Plant protective border shade trees."),
      severity: "Moderate",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_stem_cracking.jpg",
    },
    {
      id: "yellow_leaf",
      name: t("diseases.yellow_leaf.name", "Yellow Leaf Disease (General Chlorosis)"),
      kannadaName: "ಸಾಮಾನ್ಯ ಹಳದಿ ಎಲೆ ಕೊರತೆ",
      category: "pest_disorder",
      shortDesc: t("diseases.yellow_leaf.desc", "Progressive foliar chlorosis and canopy yellowing caused by waterlogging or micronutrient stress."),
      symptoms: [
        t("diseases.yellow_leaf.symptom1", "Uniform yellowing starting from lower older fronds"),
        t("diseases.yellow_leaf.symptom2", "Reduction in nut bunch size and kernel weight"),
        t("diseases.yellow_leaf.symptom3", "Root tip decay in poorly drained soils"),
      ],
      treatment: t("diseases.yellow_leaf.treatment", "Improve drainage with 0.75m inter-row trenches; apply Dolomite lime (500g/palm in alternate years if pH < 5.5) and Zinc Sulphate (50g/palm). Fungicides withheld."),
      severity: "Moderate",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Self-Attention Classifier",
      image: "/samples/sample_yellow_leaf.jpg",
    },
    {
      id: "healthy",
      name: t("diseases.healthy.name", "Healthy Palm / Optimal Vigor"),
      kannadaName: "ಆರೋಗ್ಯಕರ ಮರ",
      category: "healthy",
      shortDesc: t("diseases.healthy.desc", "Canopy and nuts show optimal vigor, healthy green pigmentation, and no pathological symptoms."),
      symptoms: [
        t("diseases.healthy.symptom1", "Vibrant green, fully expanded fronds"),
        t("diseases.healthy.symptom2", "Uniform, well-developed nut bunches"),
        t("diseases.healthy.symptom3", "Intact trunk and active root absorption"),
      ],
      treatment: t("diseases.healthy.treatment", "Continue balanced seasonal NPK nutrition and maintain regular irrigation scheduling."),
      severity: "Healthy",
      isActiveVision: true,
      modelBackbone: "ViT-B/16 Baseline Feature Classifier",
      image: "/samples/sample_healthy.jpg",
    },
  ], [t])

  const counts = useMemo(() => ({
    all: diseaseCatalog.length,
    fungal: diseaseCatalog.filter((d) => d.category === "fungal").length,
    pest_disorder: diseaseCatalog.filter((d) => d.category === "pest_disorder").length,
    healthy: diseaseCatalog.filter((d) => d.category === "healthy").length,
  }), [diseaseCatalog])

  const filtered = useMemo(() => {
    return diseaseCatalog.filter((d) => {
      const q = search.toLowerCase().trim()
      const matchesSearch =
        !q ||
        d.name.toLowerCase().includes(q) ||
        d.kannadaName.toLowerCase().includes(q) ||
        d.shortDesc.toLowerCase().includes(q) ||
        d.symptoms.some((s) => s.toLowerCase().includes(q))
      if (!matchesSearch) return false

      if (filterCategory === "fungal") return d.category === "fungal"
      if (filterCategory === "pest_disorder") return d.category === "pest_disorder"
      if (filterCategory === "healthy") return d.category === "healthy"
      return true
    })
  }, [diseaseCatalog, search, filterCategory])

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* ─── HEADER & FILTER BAR ───────────────────────────────────── */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-extrabold text-foreground tracking-tight">
              {t("nav.diseases", "Disease Library")}
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-primary/10 text-primary border border-primary/20">
              11 Diseases Active
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {t("diseases.subtitle", "Pathological reference and treatment protocols for Areca Catechu")}
            {language === "kn" && " • ಅಡಿಕೆ ಬೆಳೆ ರೋಗ ಕೈಪಿಡಿ"}
          </p>

          <div className="flex flex-wrap items-center gap-2 mt-2.5">
            <button
              onClick={() => {
                setTreatmentModalDisease("koleroga")
                setTreatmentModalMode("pesticides")
                setTreatmentModalOpen(true)
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 transition-opacity shadow-xs"
            >
              <Calculator size={13} />
              <span>Pesticide & Spray Hub</span>
            </button>
            <button
              onClick={() => {
                setTreatmentModalDisease("maintenance")
                setTreatmentModalMode("fertilizers")
                setTreatmentModalOpen(true)
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-600/40 bg-emerald-600/10 text-emerald-700 dark:text-emerald-300 text-xs font-bold hover:bg-emerald-600/20 transition-colors shadow-xs"
            >
              <Sprout size={13} />
              <span>Annual Fertilizer (NPK) Schedule</span>
            </button>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          {/* Dynamic Filter Pills */}
          <div className="flex items-center bg-card border border-border rounded-xl p-1 text-xs shadow-xs overflow-x-auto">
            <button
              onClick={() => setFilterCategory("all")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors shrink-0 ${
                filterCategory === "all"
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All ({counts.all})
            </button>
            <button
              onClick={() => setFilterCategory("fungal")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 shrink-0 ${
                filterCategory === "fungal"
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Droplets size={12} className={filterCategory === "fungal" ? "text-primary-foreground" : "text-amber-500"} />
              Fungal ({counts.fungal})
            </button>
            <button
              onClick={() => setFilterCategory("pest_disorder")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 shrink-0 ${
                filterCategory === "pest_disorder"
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Bug size={12} className={filterCategory === "pest_disorder" ? "text-primary-foreground" : "text-rose-500"} />
              Pests & Disorders ({counts.pest_disorder})
            </button>
            <button
              onClick={() => setFilterCategory("healthy")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 shrink-0 ${
                filterCategory === "healthy"
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <CheckCircle2 size={12} className={filterCategory === "healthy" ? "text-primary-foreground" : "text-emerald-500"} />
              Healthy ({counts.healthy})
            </button>
          </div>

          {/* Search Box */}
          <div className="flex items-center gap-2 bg-card border border-border rounded-xl px-3 py-2 w-full sm:w-64 shadow-xs">
            <Search size={15} className="text-muted-foreground shrink-0" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("diseases.search_placeholder", language === "kn" ? "ರೋಗ ಹುಡುಕಿ..." : "Search disease catalog...")}
              className="bg-transparent border-none outline-none text-xs text-foreground placeholder-muted-foreground flex-1"
            />
          </div>
        </div>
      </div>

      {/* ─── DISEASE CARDS GRID ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filtered.length === 0 ? (
          <div className="col-span-1 md:col-span-2 text-center py-16 bg-card border border-border rounded-2xl">
            <Search size={36} className="text-muted-foreground mx-auto mb-3" />
            <p className="text-sm font-semibold text-foreground">{t("diseases.no_match_title", "No diseases match your search")}</p>
            <p className="text-xs text-muted-foreground mt-1">{t("diseases.no_match_desc", "Try a different search term or clear the filter.")}</p>
            <button
              onClick={() => {
                setSearch("")
                setFilterCategory("all")
              }}
              className="mt-3 px-4 py-1.5 bg-primary text-primary-foreground text-xs font-bold rounded-xl shadow-xs hover:bg-primaryHover transition-colors"
            >
              {t("scans.reset_filters", "Reset Filters")}
            </button>
          </div>
        ) : (
          filtered.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-card border border-border shadow-xs hover:shadow-md transition-all flex flex-col justify-between group"
            >
              <div className="space-y-4">
                {/* Photo & Titles */}
                <div className="flex items-start gap-4">
                  <div className="relative shrink-0 overflow-hidden rounded-xl border border-border">
                    <img
                      src={item.image}
                      alt={item.name}
                      onError={handleImageError}
                      className="w-24 h-24 sm:w-28 sm:h-28 object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute top-1 left-1 bg-black/60 backdrop-blur-xs text-[9px] text-white font-bold px-1.5 py-0.5 rounded">
                      Field Photo
                    </div>
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Badges */}
                    <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          item.severity === "Critical"
                            ? "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20"
                            : item.severity === "Severe"
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"
                            : item.severity === "Moderate"
                            ? "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20"
                            : item.severity === "Mild"
                            ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20"
                            : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                        }`}
                      >
                        {item.severity} Risk
                      </span>

                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 flex items-center gap-1">
                        <Sparkles size={10} />
                        Vision AI Active
                      </span>
                    </div>

                    {/* Disease Names */}
                    <h3 className="text-sm font-extrabold text-foreground leading-snug group-hover:text-primary transition-colors">
                      {item.name}
                    </h3>
                    {language === "kn" && item.kannadaName && (
                      <div className="text-xs font-semibold text-primary mt-0.5">
                        {item.kannadaName}
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                      {item.shortDesc}
                    </p>
                  </div>
                </div>

                {/* Diagnostic Symptoms */}
                <div>
                  <div className="text-xs font-bold text-foreground mb-1.5 flex items-center gap-1.5">
                    <ShieldAlert size={13} className="text-amber-500" />
                    <span>{t("diseases.diagnostic_symptoms", "Key Diagnostic Symptoms:")}</span>
                  </div>
                  <div className="space-y-1">
                    {item.symptoms.map((s, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-muted-foreground">
                        <span className="text-primary font-bold leading-tight mt-0.5">•</span>
                        <span>{s}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Treatment & Action Footers */}
              <div className="mt-4 pt-3.5 border-t border-border space-y-3">
                <div className="text-xs bg-muted/40 p-2.5 rounded-xl border border-border/60">
                  <span className="font-bold text-foreground block mb-0.5">
                    {t("diseases.protocol_label", "Treatment Protocol:")}
                  </span>
                  <span className="text-muted-foreground leading-relaxed">{item.treatment}</span>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pt-1">
                  <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                    <CheckCircle2 size={12} className="text-primary shrink-0" />
                    <span>Pipeline: <strong className="text-foreground/80">{item.modelBackbone}</strong></span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => {
                        setTreatmentModalDisease(item.id)
                        setTreatmentModalMode("pesticides")
                        setTreatmentModalOpen(true)
                      }}
                      className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-primary/30 bg-primary/5 text-primary text-xs font-semibold hover:bg-primary/15 transition-colors"
                      title="Calculate exact chemical pesticide, bio-organic & fertilizer dosage"
                    >
                      <Calculator size={13} />
                      <span>Dosage & Fertilizers</span>
                    </button>

                    <button
                      onClick={() => navigate("/detection", { state: { imageUrl: item.image } })}
                      className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primaryHover transition-colors shadow-xs"
                    >
                      <Camera size={13} />
                      <span>Scan Sample in AI Doctor</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* ICAR-CPCRI Fertilizer & Pesticide Hub Modal */}
      <TreatmentCalculatorModal
        isOpen={treatmentModalOpen}
        onClose={() => setTreatmentModalOpen(false)}
        initialDisease={treatmentModalDisease}
        initialPalms={500}
        initialMode={treatmentModalMode}
      />
    </div>
  )
}
