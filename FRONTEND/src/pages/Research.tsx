import { useState } from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts"
import {
  Sparkles,
  ShieldCheck,
  Cpu,
  Layers,
  CheckCircle2,
  Activity,
  FileCode,
  Flame,
  Info,
  Database,
  Sliders,
} from "lucide-react"
import { useLanguage } from "../contexts/LanguageContext"
import { THEME_TOKENS } from "../theme/tokens"

const modelPerformance = [
  {
    name: "CNN Gatekeeper",
    model: "EfficientNet-B0",
    accuracy: 98.6,
    f1: 98.4,
    role: "Domain Validation & Out-of-Distribution Defense",
  },
  {
    name: "Vision Transformer",
    model: "ViT-B/16",
    accuracy: 63.6,
    f1: 63.8,
    role: "Multi-Class Self-Attention Classifier",
  },
  {
    name: "YOLOv8 Detector",
    model: "YOLOv8n",
    accuracy: 32.2,
    f1: 28.6,
    role: "Candidate Region Detector (YOLOv8 stage: experimental; trained on image-level placeholder boxes; not a validated lesion localizer)",
  },
  {
    name: "Ensemble Pipeline",
    model: "Cascaded 3-Stage",
    accuracy: 73.7,
    f1: 72.1,
    role: "Full End-to-End Triage with Attention Heatmap",
  },
]

const vitClassMetrics = [
  {
    disease: "Sooty Mold (Capnodium spp.)",
    samples: 59,
    precision: "87.5%",
    recall: "83.1%",
    f1: "85.2%",
    status: "Internal split only",
    color: "text-emerald-500",
  },
  {
    disease: "Healthy / Optimal Vigor",
    samples: 73,
    precision: "61.6%",
    recall: "72.6%",
    f1: "66.7%",
    status: "Internal split only",
    color: "text-emerald-500",
  },
  {
    disease: "Fruit Rot / Koleroga (Phytophthora meadii)",
    samples: 79,
    precision: "64.2%",
    recall: "65.8%",
    f1: "65.0%",
    status: "Internal split only",
    color: "text-amber-500",
  },
  {
    disease: "Anthracnose (Colletotrichum gloeosporioides)",
    samples: 72,
    precision: "49.4%",
    recall: "58.3%",
    f1: "53.5%",
    status: "Internal split only",
    color: "text-amber-500",
  },
  {
    disease: "Nut Cracking Disorder",
    samples: 66,
    precision: "63.4%",
    recall: "39.4%",
    f1: "48.6%",
    status: "Internal split only",
    color: "text-amber-500",
  },
]

export default function Research() {
  const { t } = useLanguage()
  const [activeMetric, setActiveMetric] = useState<"accuracy" | "f1">("accuracy")

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-foreground">{t("nav.research", "Research & Benchmark Dashboard")}</h1>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded-full flex items-center gap-1">
              <CheckCircle2 size={11} />
              Exploratory Snapshot; Validation Pending
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("research.subtitle", "Repository-reported experiment metrics; not independent field validation or clinical performance")}
          </p>
        </div>

        <div className="flex items-center gap-2 bg-card border border-border rounded-xl p-1 text-xs">
          <button
            onClick={() => setActiveMetric("accuracy")}
            className={`px-3 py-1 rounded-lg font-semibold transition-colors ${
              activeMetric === "accuracy" ? "bg-primary text-primary-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Accuracy / mAP@50
          </button>
          <button
            onClick={() => setActiveMetric("f1")}
            className={`px-3 py-1 rounded-lg font-semibold transition-colors ${
              activeMetric === "f1" ? "bg-primary text-primary-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Macro F1-Score
          </button>
        </div>
      </div>

      <div role="status" className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs leading-relaxed text-amber-950 dark:text-amber-100">
        <strong>Validation status:</strong> five classes have real-data coverage and six remain experimental seed-origin classes. The separate four-class research candidate scored 25.3% on 91 conflict-filtered local Healthy/Fruit Rot photos and is blocked from ordinary predictions. Figures below are historical internal estimates, not independent deployment accuracy.
      </div>

      {/* Top Architecture Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-card border border-border shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-muted-foreground">Stage 1: Gatekeeper</span>
            <ShieldCheck size={16} className="text-emerald-500" />
          </div>
          <div className="text-2xl font-black text-foreground">98.6%</div>
          <p className="text-[11px] text-muted-foreground">Repository-reported gate result; not independently revalidated</p>
        </div>

        <div className="p-4 rounded-2xl bg-card border border-border shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-muted-foreground">Stage 2: Candidate Region Detector</span>
            <Layers size={16} className="text-sky-500" />
          </div>
          <div className="text-2xl font-black text-foreground">32.2% <span className="text-xs font-normal text-muted-foreground">mAP50</span></div>
          <p className="text-[11px] text-muted-foreground">YOLOv8 stage: experimental; trained on image-level placeholder boxes; not a validated lesion localizer</p>
        </div>

        <div className="p-4 rounded-2xl bg-card border border-border shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-muted-foreground">Stage 3: Vision Transformer</span>
            <Sparkles size={16} className="text-purple-500" />
          </div>
          <div className="text-2xl font-black text-foreground">63.6%</div>
          <p className="text-[11px] text-muted-foreground">Internal split result; real-data coverage is limited to five classes</p>
        </div>

        <div className="p-4 rounded-2xl bg-card border border-border shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-muted-foreground">Ensemble Resolution</span>
            <Activity size={16} className="text-emerald-500" />
          </div>
          <div className="text-2xl font-black text-foreground">73.7%</div>
          <p className="text-[11px] text-muted-foreground">No independent end-to-end field validation is available</p>
        </div>
      </div>

      {/* Main Charts & Metadata Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Architecture Benchmark Comparison Chart */}
        <div className="lg:col-span-8 bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-foreground">
                {t("research.chart_title", "Architecture Benchmark Comparison")}
              </h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Historical measurements on a curated split; label conflicts and source overlap limit interpretation.
              </p>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded-full flex items-center gap-1">
              <CheckCircle2 size={12} />
              Internal split; not external validation
            </span>
          </div>

          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelPerformance} margin={{ top: 10, right: 20, left: -10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.5} />
                <XAxis dataKey="name" stroke="var(--color-muted-foreground)" fontSize={11} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={11} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-card)",
                    borderColor: "var(--color-border)",
                    borderRadius: 12,
                    fontSize: 12,
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  }}
                  formatter={(val: any, name: any) => [`${val}%`, name === "accuracy" ? "Accuracy / mAP" : "Macro F1"]}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                <Bar
                  dataKey="accuracy"
                  name="Accuracy / mAP@50 (%)"
                  fill={THEME_TOKENS.colors.primary}
                  radius={[6, 6, 0, 0]}
                  barSize={32}
                />
                <Bar
                  dataKey="f1"
                  name="Macro F1-Score (%)"
                  fill="#10b981"
                  radius={[6, 6, 0, 0]}
                  barSize={32}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Active Ensemble Metadata Card */}
        <div className="lg:col-span-4 bg-card border border-border rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h3 className="text-sm font-bold text-foreground">
                {t("research.metadata_title", "Active Ensemble Metadata")}
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-full">
                Local checkpoint
              </span>
            </div>

            <div className="space-y-2.5 text-xs mt-3">
              <div className="flex justify-between items-center py-1 border-b border-border/50">
                <span className="text-muted-foreground">{t("research.model_version", "Model Pipeline")}</span>
                <span className="font-bold text-foreground">v2.4 (Cascade Ensemble)</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border/50">
                <span className="text-muted-foreground">{t("research.training_dataset", "Canonical Dataset")}</span>
                <span className="font-bold text-foreground">216 retained real images</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border/50">
                <span className="text-muted-foreground">Active Trained Classes</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400">5 real; 6 experimental</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border/50">
                <span className="text-muted-foreground">Agronomic Ref Classes</span>
                <span className="font-bold text-sky-600 dark:text-sky-400">11 outputs; seed classes unvalidated</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border/50">
                <span className="text-muted-foreground">{t("research.loss_function", "Loss Function")}</span>
                <span className="font-bold text-foreground">CrossEntropy + CIoU/DFL</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border/50">
                <span className="text-muted-foreground">{t("research.optimizer", "Optimizer")}</span>
                <span className="font-bold text-foreground">AdamW (1e-4) + SGD</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border/50">
                <span className="text-muted-foreground">Explainability (XAI)</span>
                <span className="font-bold text-foreground">12-Head ViT Attention Map</span>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-muted-foreground pt-3 border-t border-border/60 leading-relaxed">
            The current backend reports CPU inference, YOLO training interrupted at 3 of 10 planned epochs, and 163 pending annotations. Timing depends on hardware; benchmark figures above are exploratory only.
          </p>
        </div>
      </div>

      {/* Per-Class ViT Validation Table */}
      <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-foreground">
              ViT-B/16 Per-Class Internal Split Summary
            </h3>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              These repository-reported metrics are not an independent external field evaluation.
            </p>
          </div>
          <span className="text-xs font-semibold text-muted-foreground">
            349 Curated Records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="pb-3 font-bold">Pathology / Condition</th>
                <th className="pb-3 font-bold text-center">Dataset Images</th>
                <th className="pb-3 font-bold text-center">Precision</th>
                <th className="pb-3 font-bold text-center">Recall</th>
                <th className="pb-3 font-bold text-center">F1-Score</th>
                <th className="pb-3 font-bold text-right">Validation Assessment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {vitClassMetrics.map((row) => (
                <tr key={row.disease} className="hover:bg-muted/30 transition-colors">
                  <td className="py-3 font-semibold text-foreground">{row.disease}</td>
                  <td className="py-3 text-center text-muted-foreground font-mono">{row.samples}</td>
                  <td className="py-3 text-center font-semibold text-foreground font-mono">{row.precision}</td>
                  <td className="py-3 text-center font-semibold text-foreground font-mono">{row.recall}</td>
                  <td className="py-3 text-center font-bold text-primary font-mono">{row.f1}</td>
                  <td className="py-3 text-right">
                    <span className={`font-semibold ${row.color}`}>{row.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
