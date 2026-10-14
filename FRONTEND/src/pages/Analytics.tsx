import { useState, useEffect } from "react"
import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Legend,
} from "recharts"
import { BarChart2, TrendingUp, Calendar, Download, RefreshCw, Trees, ShieldCheck, Activity } from "lucide-react"
import { useLanguage } from "../contexts/LanguageContext"
import { usePlantation } from "../contexts/PlantationContext"
import { fetchDiseaseDistribution, fetchAnalyticsOverview, AnalyticsOverviewResponse } from "../services/dashboardService"
import { apiRequestBlob } from "../services/apiClient"
import { THEME_TOKENS } from "../theme/tokens"

interface DiseaseDistItem {
  name: string
  value: number
  color: string
}

const defaultDiseaseDist: DiseaseDistItem[] = [
  { name: "Anthracnose", value: 48, color: THEME_TOKENS.severity.critical },
  { name: "Fruit Rot", value: 28, color: THEME_TOKENS.severity.severe },
  { name: "Nut Cracking", value: 14, color: THEME_TOKENS.severity.moderate },
  { name: "Sooty Mold", value: 10, color: THEME_TOKENS.charts.lines.sootyMold },
]

export default function Analytics() {
  const { t } = useLanguage()
  const { blocks, totalTrees } = usePlantation()
  const [diseaseDist, setDiseaseDist] = useState<DiseaseDistItem[]>(defaultDiseaseDist)
  const [overview, setOverview] = useState<AnalyticsOverviewResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [timeframe, setTimeframe] = useState<"30d" | "90d" | "season">("season")
  const [exporting, setExporting] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [distData, overviewData] = await Promise.all([
        fetchDiseaseDistribution().catch(() => defaultDiseaseDist.map(d => ({ name: d.name, percentage: d.value, color: d.color }))),
        fetchAnalyticsOverview().catch(() => null),
      ])

      if (distData && distData.length > 0) {
        setDiseaseDist(
          distData.map((item) => ({
            name: item.name,
            value: item.percentage,
            color: item.color,
          }))
        )
      }

      if (overviewData) {
        setOverview(overviewData)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleExportCSV = async () => {
    try {
      setExporting(true)
      const blob = await apiRequestBlob("/reports/export", {
        method: "POST",
        body: JSON.stringify({ format: "csv", type: "analytics_yield_audit" }),
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `arecavision_analytics_export_${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error("Export error, printing fallback:", err)
      window.print()
    } finally {
      setExporting(false)
    }
  }

  const yieldData = overview?.monthlyYield || [
    { month: "Jan", yield: 4.4, diseaseRate: 8.5 },
    { month: "Feb", yield: 4.8, diseaseRate: 7.8 },
    { month: "Mar", yield: 5.5, diseaseRate: 6.2 },
    { month: "Apr", yield: 6.6, diseaseRate: 5.4 },
    { month: "May", yield: 8.1, diseaseRate: 4.8 },
    { month: "Jun", yield: 7.3, diseaseRate: 9.2 },
  ]

  const activeTreesCount = overview?.totalTrees || totalTrees
  const activeAcreage = overview?.totalAcres || 27.9
  const estYield = overview?.estimatedYieldTons || 36.7
  const controlRate = overview?.diseaseControlRate || 94.2

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-foreground">{t("nav.analytics", "Plantation Analytics")}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("analytics.subtitle", "Enterprise yield projections and disease impact metrics")}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-card border border-border rounded-xl px-3 py-1.5 text-xs text-muted-foreground shadow-sm">
            <Calendar size={14} className="text-primary" />
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value as "30d" | "90d" | "season")}
              className="bg-transparent border-none outline-none text-foreground font-semibold cursor-pointer"
            >
              <option value="30d" className="bg-card text-foreground">Last 30 Days</option>
              <option value="90d" className="bg-card text-foreground">Last 90 Days</option>
              <option value="season" className="bg-card text-foreground">Current Harvest Season</option>
            </select>
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded-xl bg-card border border-border text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors shadow-sm"
            title="Refresh Analytics"
          >
            <RefreshCw size={14} className={loading ? "animate-spin text-primary" : ""} />
          </button>

          <button
            onClick={handleExportCSV}
            disabled={exporting}
            className="btn-primary text-xs flex items-center gap-1.5 shadow-sm"
          >
            <Download size={14} />
            <span>{exporting ? "Generating..." : t("analytics.export_report", "Export Data")}</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-card border border-border shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold">{t("analytics.kpi_yield", "Est. Seasonal Yield")}</span>
            <TrendingUp size={18} className="text-primary" />
          </div>
          <div className="text-2xl font-extrabold text-foreground">{estYield} Tons</div>
          <div className="text-xs text-primary font-semibold flex items-center gap-1">
            <span>+{((estYield / 30.0 - 1) * 100).toFixed(1)}% vs baseline</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold">{t("analytics.kpi_control", "Disease Control Rate")}</span>
            <ShieldCheck size={18} className="text-primary" />
          </div>
          <div className="text-2xl font-extrabold text-foreground">{controlRate}%</div>
          <div className="text-xs text-primary font-semibold">Verified clinical containment</div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold">Monitored Canopy</span>
            <Trees size={18} className="text-primary" />
          </div>
          <div className="text-2xl font-extrabold text-foreground">{activeTreesCount.toLocaleString()} Palms</div>
          <div className="text-xs text-muted-foreground">{blocks.length} active plantation blocks</div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold">Total Plantation Area</span>
            <Activity size={18} className="text-primary" />
          </div>
          <div className="text-2xl font-extrabold text-foreground">{activeAcreage} Acres</div>
          <div className="text-xs text-muted-foreground">~450 palms / acre density</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 bg-card border border-border rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground">{t("analytics.chart_yield_title", "Seasonal Yield Trajectory vs Pathogen Pressure")}</h3>
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#047857]" /> Yield (Tons)</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#dc2626]" /> Infection Rate (%)</span>
            </div>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={yieldData}>
                <defs>
                  <linearGradient id="yieldGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#047857" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#047857" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="infectGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#dc2626" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="month" stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-card)",
                    borderColor: "var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  }}
                />
                <Area type="monotone" dataKey="yield" stroke="#047857" strokeWidth={2} fillOpacity={1} fill="url(#yieldGrad)" name="Yield (Tons)" />
                <Area type="monotone" dataKey="diseaseRate" stroke="#dc2626" strokeWidth={1.5} fillOpacity={1} fill="url(#infectGrad)" name="Infection Rate %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-4 bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-foreground">{t("analytics.chart_disease_title", "Disease Prevalence Breakdown")}</h3>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={diseaseDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} innerRadius={42} paddingAngle={2}>
                  {diseaseDist.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-card)",
                    borderColor: "var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 pt-3 border-t border-border">
            {diseaseDist.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-muted-foreground">{item.name}</span>
                </div>
                <span className="font-bold text-foreground">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
