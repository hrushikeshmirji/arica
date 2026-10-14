import { useState, useEffect } from "react"
import {
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  Droplets,
  Wind,
  Calendar,
  Layers,
  CheckCircle2,
  MapPin,
  Clock,
  Sparkles,
  Calculator,
} from "lucide-react"
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts"
import { useLanguage } from "../contexts/LanguageContext"
import { fetchRiskForecast, RiskForecastData } from "../services/weatherService"
import { THEME_TOKENS } from "../theme/tokens"
import TreatmentCalculatorModal from "../components/TreatmentCalculatorModal"

const PLANTATION_LOCATIONS = [
  "Madikeri Plantation",
  "Shivamogga Belt",
  "Mangaluru Coastal Plot",
  "Sirsi Highland Block",
  "Chikkamagaluru Estate",
]

export default function RiskForecast() {
  const { t } = useLanguage()
  const [selectedLocation, setSelectedLocation] = useState(PLANTATION_LOCATIONS[0])
  const [riskData, setRiskData] = useState<RiskForecastData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCalculator, setShowCalculator] = useState(false)

  const loadRisk = async (location: string) => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchRiskForecast(location)
      setRiskData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load epidemiological risk forecast.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRisk(selectedLocation)
  }, [selectedLocation])

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev) {
      case "Critical":
        return "bg-danger/10 text-danger border-danger/25"
      case "Severe":
        return "bg-warning/10 text-warning border-warning/25"
      case "Moderate":
        return "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/25"
      default:
        return "bg-primary/10 text-primary border-primary/25"
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-foreground">{t("nav.risk", "Epidemiological Risk Forecast")}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("risk.subtitle", "Microclimate infection pressure modeling and 7-day predictive disease trajectories")}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-card border border-border rounded-xl px-3 py-1.5 text-xs text-muted-foreground shadow-sm">
            <MapPin size={14} className="text-primary" />
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="bg-transparent border-none outline-none text-foreground font-semibold cursor-pointer"
            >
              {PLANTATION_LOCATIONS.map((loc) => (
                <option key={loc} value={loc} className="bg-card text-foreground">
                  {loc}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => loadRisk(selectedLocation)}
            disabled={loading}
            className="p-2 rounded-xl bg-card border border-border text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors shadow-sm"
            title="Refresh Forecast"
          >
            <RefreshCw size={14} className={loading ? "animate-spin text-primary" : ""} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-danger/10 border border-danger/25 text-xs text-danger flex items-center gap-2">
          <AlertTriangle size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Composite Overview Card */}
      {riskData && (
        <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
            <div>
              <div className="flex items-center gap-2.5 mb-1.5">
                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${getSeverityBadgeClass(riskData.overallSeverity)}`}>
                  {riskData.overallSeverity} Risk Level
                </span>
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock size={12} /> Updated: {riskData.lastUpdated}
                </span>
              </div>
              <h2 className="text-lg font-bold text-foreground">{riskData.advisoryHeadline}</h2>
              <p className="text-xs text-muted-foreground mt-1 max-w-2xl leading-relaxed">{riskData.advisoryAction}</p>
            </div>

            <div className="flex items-center gap-4 bg-muted/40 p-4 rounded-xl border border-border">
              <div className="text-center">
                <div className="text-3xl font-extrabold text-foreground">{riskData.compositeIndex}%</div>
                <div className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider mt-0.5">Infection Pressure</div>
              </div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                <ShieldAlert size={22} />
              </div>
            </div>
          </div>

          {/* Pathogen Breakdown Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(riskData.pathogenMetrics).map(([key, item]) => (
              <div key={key} className="p-4 rounded-xl bg-background border border-border space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground truncate pr-2">{item.name}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getSeverityBadgeClass(item.status)}`}>
                    {item.status}
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-foreground">{item.riskScore}%</span>
                  <span className="text-[11px] text-muted-foreground">Incubation: ~{item.incubationDays} days</span>
                </div>
                <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      item.riskScore >= 75 ? "bg-danger" : item.riskScore >= 45 ? "bg-warning" : "bg-primary"
                    }`}
                    style={{ width: `${item.riskScore}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7-Day Trajectory Chart */}
      {riskData && (
        <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-bold text-foreground">7-Day Epidemiological Trajectory Projection</h3>
              <p className="text-xs text-muted-foreground">Pathogen sporulation probability correlated with forecasted precipitation</p>
            </div>
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#dc2626]" /> Koleroga</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#b45309]" /> Anthracnose</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" /> Nut Cracking</span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={riskData.trajectory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="kolerogaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#dc2626" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="anthracnoseGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#b45309" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#b45309" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="day" stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={11} domain={[0, 100]} tickLine={false} unit="%" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-card)",
                    borderColor: "var(--color-border)",
                    borderRadius: "0.75rem",
                    fontSize: "12px",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  }}
                />
                <Area type="monotone" dataKey="kolerogaRisk" name="Fruit Rot (Koleroga)" stroke="#dc2626" strokeWidth={2} fillOpacity={1} fill="url(#kolerogaGrad)" />
                <Area type="monotone" dataKey="anthracnoseRisk" name="Anthracnose" stroke="#b45309" strokeWidth={2} fillOpacity={1} fill="url(#anthracnoseGrad)" />
                <Area type="monotone" dataKey="nutCrackingRisk" name="Nut Cracking" stroke="#3b82f6" strokeWidth={1.5} fillOpacity={0} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Spraying Window & Block Vulnerability Grid */}
      {riskData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Prophylactic Advisory Box */}
          <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-foreground font-bold text-sm">
              <Droplets size={16} className="text-primary" />
              <span>Prophylactic Spraying Advisory</span>
            </div>

            <div className="p-4 rounded-xl bg-muted/40 border border-border space-y-2">
              <span className="text-[10px] font-bold text-primary uppercase tracking-wider">Optimal Application Window</span>
              <p className="text-xs font-semibold text-foreground">{riskData.spraySchedule.suitableWindow}</p>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-semibold text-muted-foreground block mb-0.5">Recommended Formulation:</span>
                <span className="text-foreground leading-relaxed">{riskData.spraySchedule.recommendedChemical}</span>
              </div>
              <div>
                <span className="font-semibold text-muted-foreground block mb-0.5">Bio-Control Alternative:</span>
                <span className="text-foreground leading-relaxed">{riskData.spraySchedule.organicAlternative}</span>
              </div>
              <div className="pt-2 border-t border-border flex items-center justify-between text-muted-foreground">
                <span>Withholding Period:</span>
                <span className="font-bold text-foreground">{riskData.spraySchedule.withholdingPeriodDays} Days</span>
              </div>
            </div>

            <button
              onClick={() => setShowCalculator(true)}
              className="w-full py-2.5 px-3 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 flex items-center justify-center gap-2 transition-opacity shadow-sm"
            >
              <Calculator size={14} />
              <span>Calculate Treatment Dosage & Costs (₹)</span>
            </button>
          </div>

          {/* Block Vulnerability Matrix Table */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-foreground font-bold text-sm">
                <Layers size={16} className="text-primary" />
                <span>Plantation Block Vulnerability Matrix</span>
              </div>
              <span className="text-xs text-muted-foreground">{riskData.blockVulnerability.length} Blocks Monitored</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="pb-2.5 font-semibold">Block</th>
                    <th className="pb-2.5 font-semibold">Trees</th>
                    <th className="pb-2.5 font-semibold">Health Score</th>
                    <th className="pb-2.5 font-semibold">Primary Pathogen Threat</th>
                    <th className="pb-2.5 font-semibold text-right">Vulnerability</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {riskData.blockVulnerability.map((b) => (
                    <tr key={b.blockId} className="hover:bg-muted/20 transition-colors">
                      <td className="py-2.5 font-semibold text-foreground">{b.name}</td>
                      <td className="py-2.5 text-muted-foreground">{b.trees.toLocaleString()}</td>
                      <td className="py-2.5">
                        <span className="font-semibold text-foreground">{b.healthScore}%</span>
                      </td>
                      <td className="py-2.5 text-muted-foreground">{b.primaryThreat}</td>
                      <td className="py-2.5 text-right">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getSeverityBadgeClass(b.severity)}`}>
                          {b.vulnerabilityScore}% ({b.severity})
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Commercial Spray Dosage & Cost Calculator Modal */}
      <TreatmentCalculatorModal
        isOpen={showCalculator}
        onClose={() => setShowCalculator(false)}
        initialDisease="koleroga"
        initialPalms={1500}
      />
    </div>
  )
}
