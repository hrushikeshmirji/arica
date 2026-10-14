import React, { useState, useEffect, useRef, useMemo } from "react"
import { useNavigate } from "react-router-dom"
import {
  Search,
  ScanLine,
  LayoutDashboard,
  Map,
  CloudSun,
  Sparkles,
  BookOpen,
  FlaskConical,
  FileText,
  History,
  ShieldAlert,
  ArrowRight,
  Command,
  X,
  Sprout,
  Calculator,
} from "lucide-react"

interface CommandItem {
  id: string
  title: string
  subtitle: string
  category: "Operations" | "Plantation Blocks" | "Pathology Library" | "Intelligence"
  path: string
  state?: Record<string, unknown>
  icon: React.ElementType
  badge?: string
}

const COMMAND_ITEMS: CommandItem[] = [
  {
    id: "cmd-detect",
    title: "AI Diagnostic Studio 2.0",
    subtitle: "Run the 3-model screening pipeline, inspect attention maps & review guidance",
    category: "Operations",
    path: "/detection",
    icon: ScanLine,
    badge: "Primary",
  },
  {
    id: "cmd-fertilizers",
    title: "ICAR-CPCRI Fertilizer & Pesticide Hub",
    subtitle: "Precise chemical dosages, Bordeaux preparation & annual NPK split schedule",
    category: "Operations",
    path: "/diseases",
    icon: Sprout,
    badge: "Agronomy",
  },
  {
    id: "cmd-dashboard",
    title: "Executive Command Dashboard",
    subtitle: "Plantation health KPIs, live microclimate & field triage shortcut",
    category: "Operations",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    id: "cmd-assistant",
    title: "Consult AI Agronomist",
    subtitle: "Interactive treatment protocols, Bordeaux mixing & soil nutrition Q&A",
    category: "Operations",
    path: "/assistant",
    icon: Sparkles,
    badge: "AI",
  },
  {
    id: "cmd-map",
    title: "GIS Plantation Digital Twin",
    subtitle: "Interactive block-level epidemiology, tree counts & risk zones",
    category: "Plantation Blocks",
    path: "/map",
    icon: Map,
  },
  {
    id: "cmd-block-a1",
    title: "Scan Block A-1 (North Valley — 450 Palms)",
    subtitle: "Launch Diagnostic Studio pre-tagged to Block A-1 (Critical Koleroga Zone)",
    category: "Plantation Blocks",
    path: "/detection",
    state: { selectedBlockId: "block-a1" },
    icon: ScanLine,
    badge: "Critical",
  },
  {
    id: "cmd-block-c1",
    title: "Scan Block C-1 (River Bank — 490 Palms)",
    subtitle: "Launch Diagnostic Studio pre-tagged to Block C-1 (Yellow Leaf Zone)",
    category: "Plantation Blocks",
    path: "/detection",
    state: { selectedBlockId: "block-c1" },
    icon: ScanLine,
    badge: "Alert",
  },
  {
    id: "cmd-weather",
    title: "Live Weather & Fungal Spore Risk",
    subtitle: "Real-time Open-Meteo telemetry, humidity thresholds & spray windows",
    category: "Intelligence",
    path: "/weather",
    icon: CloudSun,
  },
  {
    id: "cmd-risk",
    title: "Epidemiological Risk Prediction",
    subtitle: "7-day pathogen outbreak modeling for Koleroga & Anthracnose",
    category: "Intelligence",
    path: "/risk",
    icon: ShieldAlert,
  },
  {
    id: "cmd-diseases",
    title: "Clinical Disease Taxonomy Library (11 Profiles)",
    subtitle: "Scientific etiology, chemical & organic management protocols",
    category: "Pathology Library",
    path: "/diseases",
    icon: BookOpen,
  },
  {
    id: "cmd-research",
    title: "Empirical ML Research Benchmarks",
    subtitle: "EfficientNet-B0 Gatekeeper, YOLOv8n & ViT-B/16 validation metrics",
    category: "Intelligence",
    path: "/research",
    icon: FlaskConical,
  },
  {
    id: "cmd-scans",
    title: "SQLite Persistent Scan History",
    subtitle: "Audit historical diagnoses, severity levels & block records",
    category: "Operations",
    path: "/scans",
    icon: History,
  },
  {
    id: "cmd-reports",
    title: "Clinical PDF & CSV Report Exporter",
    subtitle: "Generate formal plantation pathology certificates",
    category: "Operations",
    path: "/reports",
    icon: FileText,
  },
]

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const navigate = useNavigate()
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return COMMAND_ITEMS
    return COMMAND_ITEMS.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        item.subtitle.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q)
    )
  }, [query])

  useEffect(() => {
    if (isOpen) {
      setQuery("")
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 20)
    }
  }, [isOpen])

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        if (isOpen) onClose()
      }
      if (!isOpen) return

      if (e.key === "Escape") {
        e.preventDefault()
        onClose()
      } else if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedIndex((prev) => (filtered.length > 0 ? (prev + 1) % filtered.length : 0))
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedIndex((prev) => (filtered.length > 0 ? (prev - 1 + filtered.length) % filtered.length : 0))
      } else if (e.key === "Enter" && filtered[selectedIndex]) {
        e.preventDefault()
        const target = filtered[selectedIndex]
        navigate(target.path, target.state ? { state: target.state } : undefined)
        onClose()
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, filtered, selectedIndex, navigate, onClose])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[12vh] px-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Header */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-border bg-muted/20">
          <Search size={18} className="text-primary shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Jump to Plantation Block, Diagnostic Studio, Disease Profile, or Tool..."
            className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
          />
          <div className="hidden sm:flex items-center gap-1 text-[10px] font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded border border-border">
            <span>ESC</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Close command palette"
          >
            <X size={16} />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-[60vh] overflow-y-auto p-2 space-y-1">
          {filtered.length === 0 ? (
            <div className="py-10 text-center text-xs text-muted-foreground">
              No matching commands, blocks, or disease profiles found for "{query}".
            </div>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon
              const active = idx === selectedIndex
              return (
                <button
                  key={item.id}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  onClick={() => {
                    navigate(item.path, item.state ? { state: item.state } : undefined)
                    onClose()
                  }}
                  className={`w-full flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl text-left transition-all ${
                    active ? "bg-primary/12 border border-primary/30 text-foreground" : "hover:bg-muted/50 border border-transparent text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        active ? "bg-primary text-primary-foreground shadow-sm" : "bg-muted text-muted-foreground"
                      }`}
                    >
                      <Icon size={17} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold truncate">{item.title}</span>
                        {item.badge && (
                          <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded bg-primary/15 text-primary border border-primary/25">
                            {item.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-muted-foreground truncate mt-0.5">{item.subtitle}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="hidden md:inline text-[10px] text-muted-foreground font-medium px-2 py-0.5 rounded bg-muted/60">
                      {item.category}
                    </span>
                    <ArrowRight size={14} className={active ? "text-primary translate-x-0.5 transition-transform" : "text-muted-foreground/40"} />
                  </div>
                </button>
              )
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-border bg-muted/30 flex items-center justify-between text-[11px] text-muted-foreground">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <Command size={12} className="text-primary" /> <strong>ArecaVision OS 2.0</strong> Spotlight
            </span>
            <span className="hidden sm:inline">•</span>
            <span className="hidden sm:inline">Use ↑↓ arrows and Enter to navigate</span>
          </div>
          <span className="font-mono text-[10px] text-primary">SQLite + 3-Stage TTA Active</span>
        </div>
      </div>
    </div>
  )
}
