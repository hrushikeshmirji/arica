import React, { useState, useRef, useEffect } from "react"
import { Link, useLocation } from "react-router-dom"
import {
  LayoutDashboard,
  ScanLine,
  BookOpen,
  Map,
  BarChart2,
  CloudSun,
  ShieldAlert,
  History,
  FileText,
  Settings,
  Bell,
  Search,
  ChevronDown,
  Leaf,
  Sparkles,
  FlaskConical,
  CloudDrizzle,
  Menu,
  X,
  Globe,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  Activity,
  Shield,
  LogOut,
  WifiOff,
} from "lucide-react"
import { ThemeToggle } from "./ThemeToggle"
import CommandPalette from "./CommandPalette"
import { useLanguage, Language } from "../contexts/LanguageContext"
import { useNotifications } from "../contexts/NotificationContext"
import { usePlantation } from "../contexts/PlantationContext"
import { useWeather } from "../contexts/WeatherContext"
import { useAuth } from "../contexts/AuthContext"
import { useClickOutside } from "../hooks/useClickOutside"
import { useNetworkStatus } from "../hooks/useNetworkStatus"

const baseNavItems = [
  { icon: LayoutDashboard, labelKey: "nav.dashboard", defaultLabel: "Dashboard", path: "/dashboard" },
  { icon: ScanLine, labelKey: "nav.detection", defaultLabel: "AI Detection", path: "/detection", badge: "2.0" },
  { icon: BookOpen, labelKey: "nav.diseases", defaultLabel: "Disease Library", path: "/diseases" },
  { icon: Map, labelKey: "nav.map", defaultLabel: "Plantation Map", path: "/map" },
  { icon: BarChart2, labelKey: "nav.analytics", defaultLabel: "Analytics", path: "/analytics" },
  { icon: CloudSun, labelKey: "nav.weather", defaultLabel: "Weather Intelligence", path: "/weather" },
  { icon: ShieldAlert, labelKey: "nav.risk", defaultLabel: "Risk Prediction", path: "/risk" },
  { icon: History, labelKey: "nav.scans", defaultLabel: "Scan History", path: "/scans" },
  { icon: FileText, labelKey: "nav.reports", defaultLabel: "Reports", path: "/reports" },
  { icon: Sparkles, labelKey: "nav.assistant", defaultLabel: "AI Assistant", path: "/assistant", badge: "New" },
  { icon: FlaskConical, labelKey: "nav.research", defaultLabel: "Research Dashboard", path: "/research" },
  { icon: Settings, labelKey: "nav.settings", defaultLabel: "Settings", path: "/settings" },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const { user, logout } = useAuth()
  const { language, setLanguage, t } = useLanguage()
  const { unreadCount } = useNotifications()
  const { overallHealthScore } = usePlantation()
  const { weatherState } = useWeather()
  const { isOnline } = useNetworkStatus()

  const navItems = React.useMemo(() => {
    if (user?.role === "admin") {
      return [
        ...baseNavItems,
        { icon: Shield, labelKey: "nav.admin", defaultLabel: "Admin Panel", path: "/admin", badge: "Admin" },
      ]
    }
    return baseNavItems
  }, [user?.role])

  // Sidebar collapsible state
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem("arecavision_sidebar_collapsed") === "true"
  })

  // Mobile drawer state
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  // Header quick nav dropdown & Command Palette (Ctrl+K)
  const [quickNavOpen, setQuickNavOpen] = useState(false)
  const [langDropdownOpen, setLangDropdownOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)

  useEffect(() => {
    const onGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setCommandPaletteOpen((prev) => !prev)
      }
    }
    window.addEventListener("keydown", onGlobalKeyDown)
    return () => window.removeEventListener("keydown", onGlobalKeyDown)
  }, [])

  // Refs for click outside detection
  const quickNavRef = useRef<HTMLDivElement>(null)
  const langDropdownRef = useRef<HTMLDivElement>(null)

  useClickOutside(quickNavRef, () => setQuickNavOpen(false))
  useClickOutside(langDropdownRef, () => setLangDropdownOpen(false))

  const toggleCollapse = () => {
    const nextState = !isCollapsed
    setIsCollapsed(nextState)
    localStorage.setItem("arecavision_sidebar_collapsed", String(nextState))
  }

  // Close mobile drawer on Escape key press
  useEffect(() => {
    if (!isMobileOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsMobileOpen(false)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isMobileOpen])

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* Skip to Main Content Link for Keyboard Accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:font-bold focus:text-xs focus:rounded-xl focus:shadow-xl focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
      >
        Skip to main content
      </a>

      {/* ===== MOBILE BACKDROP ===== */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm transition-opacity"
          aria-hidden="true"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* ===== SIDEBAR ===== */}
      <aside
        aria-label="Sidebar Navigation"
        aria-modal={isMobileOpen ? "true" : undefined}
        role={isMobileOpen ? "dialog" : undefined}
        className={`fixed lg:static inset-y-0 left-0 z-50 flex flex-col bg-sidebar border-r border-border transition-all duration-300 ${
          isCollapsed ? "w-20" : "w-[272px]"
        } ${isMobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        {/* Sidebar Header / Logo */}
        <div className="h-16 px-4 flex items-center justify-between border-b border-border shrink-0">
          <Link
            to="/dashboard"
            className="flex items-center gap-3 overflow-hidden rounded-xl p-1 -m-1 focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          >
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-md"
              style={{ background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))" }}
            >
              <Leaf size={20} className="text-white" />
            </div>
            {!isCollapsed && (
              <div className="truncate">
                <div className="text-foreground font-bold text-sm leading-tight truncate">
                  ArecaVision AI
                </div>
                <div className="text-[11px] text-muted-foreground truncate">
                  Precision Agriculture
                </div>
              </div>
            )}
          </Link>

          {/* Desktop Collapse Toggle Button */}
          <button
            onClick={toggleCollapse}
            className="hidden lg:flex p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            aria-label={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>

          {/* Mobile Close Button */}
          <button
            onClick={() => setIsMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            aria-label="Close Sidebar"
          >
            <X size={20} />
          </button>
        </div>

        {/* Sidebar Navigation */}
        <nav className="flex-1 overflow-y-auto sidebar-scroll px-3 py-4 space-y-1">
          {navItems.map(({ icon: Icon, labelKey, defaultLabel, path, badge }) => {
            const isActive = location.pathname === path
            const label = t(labelKey, defaultLabel)

            return (
              <Link
                key={path}
                to={path}
                onClick={() => setIsMobileOpen(false)}
                title={isCollapsed ? label : undefined}
                className={`relative group flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? "nav-item-active"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                }`}
              >
                {/* Active Left Accent Pill */}
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r bg-primary" />
                )}

                <Icon size={18} className={`shrink-0 ${isActive ? "nav-icon" : ""}`} />
                {!isCollapsed && <span className="flex-1 truncate">{label}</span>}
                {!isCollapsed && badge && (
                  <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded-full leading-none ${
                    isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                  }`}>
                    {badge}
                  </span>
                )}

                {/* Collapsed Tooltip */}
                {isCollapsed && (
                  <div className="absolute left-full ml-2 px-2.5 py-1.5 bg-card border border-border text-foreground text-xs rounded-lg shadow-xl whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                    {label}
                  </div>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Sidebar Footer Widget (Expanded State) */}
        {!isCollapsed && (
          <div className="p-3 border-t border-border space-y-3 shrink-0">
            {/* Dynamic Plantation Health Widget */}
            <div className="rounded-xl p-3 bg-card border border-border">
              {overallHealthScore === null ? (
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-muted-foreground">{t("layout.plantation_health", "Plantation Health")}</span>
                  <Link to="/map" className="text-primary font-bold hover:underline text-[11px]">
                    {t("layout.setup_map", "Setup Map")}
                  </Link>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between text-xs font-bold mb-1">
                    <span>{t("common.health_score", "Plantation Health Score")}</span>
                    <span className="text-primary font-extrabold">{overallHealthScore}/100</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-500"
                      style={{ width: `${overallHealthScore}%` }}
                    />
                  </div>
                </>
              )}
            </div>

            {/* Weather Mini Widget (5-State Machine) */}
            <div className="rounded-xl p-3 bg-card border border-border">
              {weatherState.status === "POPULATED" ? (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <CloudDrizzle size={20} className="text-accent shrink-0" />
                    <div>
                      <div className="text-xs font-bold">{weatherState.data.temperature}°C · {weatherState.data.city}</div>
                      <div className="text-[10px] text-muted-foreground">{weatherState.data.condition}</div>
                    </div>
                  </div>
                  <Link to="/weather" className="text-[10px] text-primary font-bold hover:underline">
                    {t("layout.details", "Details")}
                  </Link>
                </div>
              ) : weatherState.status === "LOADING" ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground skeleton-pulse py-1">
                  <RefreshCw size={14} className="animate-spin" />
                  <span>{t("layout.loading_weather", "Loading weather...")}</span>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CloudDrizzle size={18} className="text-muted-foreground shrink-0" />
                    <span className="text-[11px] text-muted-foreground font-medium">{t("layout.weather_unconfigured", "Weather unconfigured")}</span>
                  </div>
                  <Link to="/weather" className="text-[10px] text-primary font-bold hover:underline">
                    {t("layout.setup", "Setup")}
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Sidebar Footer Widget (Collapsed State) */}
        {isCollapsed && (
          <div className="p-2 border-t border-border flex flex-col items-center gap-2 shrink-0">
            {/* Plantation Health Icon */}
            <Link
              to="/map"
              title={
                overallHealthScore === null
                  ? `${t("layout.plantation_health", "Plantation Health")}: ${t("layout.setup_map", "Setup Map")}`
                  : `${t("layout.plantation_health", "Plantation Health")}: ${overallHealthScore}/100`
              }
              className="relative group w-10 h-10 rounded-xl bg-card border border-border flex items-center justify-center text-primary hover:bg-muted transition-colors"
            >
              <Activity size={18} />
              <div className="absolute left-full ml-2 px-2.5 py-1.5 bg-card border border-border text-foreground text-xs rounded-lg shadow-xl whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                {overallHealthScore === null
                  ? `${t("layout.plantation_health", "Plantation Health")}: ${t("layout.setup_map", "Setup Map")}`
                  : `${t("layout.plantation_health", "Plantation Health")}: ${overallHealthScore}/100`}
              </div>
            </Link>

            {/* Weather Icon */}
            <Link
              to="/weather"
              title={
                weatherState.status === "POPULATED"
                  ? `${weatherState.data.temperature}°C · ${weatherState.data.city} (${weatherState.data.condition})`
                  : weatherState.status === "LOADING"
                  ? t("layout.loading_weather", "Loading weather...")
                  : t("layout.weather_unconfigured", "Weather unconfigured")
              }
              className="relative group w-10 h-10 rounded-xl bg-card border border-border flex items-center justify-center text-accent hover:bg-muted transition-colors"
            >
              <CloudDrizzle size={18} />
              <div className="absolute left-full ml-2 px-2.5 py-1.5 bg-card border border-border text-foreground text-xs rounded-lg shadow-xl whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                {weatherState.status === "POPULATED"
                  ? `${weatherState.data.temperature}°C · ${weatherState.data.city}`
                  : weatherState.status === "LOADING"
                  ? t("layout.loading_weather", "Loading weather...")
                  : t("layout.weather_unconfigured", "Weather unconfigured")}
              </div>
            </Link>
          </div>
        )}
      </aside>

      {/* ===== MAIN CONTENT AREA ===== */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Remote Field Offline Resilience Banner */}
        {!isOnline && (
          <div className="bg-amber-600 text-white text-[11px] font-semibold py-1.5 px-4 text-center flex items-center justify-center gap-2 shadow-sm z-50">
            <WifiOff size={13} />
            <span>Field Offline Mode — Operating from local specimen cache; cloud sync will resume once connected.</span>
          </div>
        )}

        {/* Header Bar */}
        <header className="h-16 shrink-0 bg-navbar border-b border-border px-2.5 sm:px-4 lg:px-6 flex items-center justify-between gap-2 sm:gap-3 relative z-40">
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            {/* Mobile Hamburger Toggle */}
            <button
              onClick={() => setIsMobileOpen(true)}
              className="lg:hidden p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              aria-label="Open navigation menu"
              aria-expanded={isMobileOpen}
            >
              <Menu size={20} />
            </button>

            {/* Quick Feature Dropdown Menu (Hidden on mobile where hamburger serves navigation) */}
            <div ref={quickNavRef} className="relative z-50 hidden sm:block">
              <button
                onClick={() => {
                  setQuickNavOpen(!quickNavOpen)
                  setLangDropdownOpen(false)
                }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-border bg-card text-xs font-semibold hover:bg-muted transition-colors shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                aria-expanded={quickNavOpen}
                aria-haspopup="true"
              >
                <span>Jump to Feature</span>
                <ChevronDown size={14} className="text-muted-foreground" />
              </button>

              {quickNavOpen && (
                <div
                  className="absolute left-0 top-full mt-2 w-60 bg-card rounded-xl shadow-2xl border border-border py-2 z-50 animate-in fade-in zoom-in-95 opacity-100 ring-1 ring-black/5 dark:ring-white/10"
                  style={{ backgroundColor: "var(--color-card)" }}
                  onClick={() => setQuickNavOpen(false)}
                >
                  {navItems.map(({ icon: Icon, labelKey, defaultLabel, path }) => (
                    <Link
                      key={path}
                      to={path}
                      className="flex items-center gap-2.5 px-4 py-2.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                    >
                      <Icon size={16} className="text-primary shrink-0" />
                      <span>{t(labelKey, defaultLabel)}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
            {/* Live Neural Engine Pill */}
            <Link
              to="/detection"
              className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-primary/10 border border-primary/25 text-[11px] font-bold text-primary hover:bg-primary/15 transition-colors"
              title="3-Stage Cascaded Neural Ensemble + Multi-Scale TTA Active"
            >
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span>3-Stage TTA Engine</span>
            </Link>

            {/* Live Microclimate & Spore Risk Pill */}
            {weatherState.status === "POPULATED" && (
              <Link
                to="/weather"
                className="hidden lg:flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-card border border-border hover:border-primary/40 text-[11px] transition-colors shadow-xs"
                title="Live Microclimate & Fungal Spore Risk"
              >
                <CloudSun size={14} className="text-primary shrink-0" />
                <span className="font-bold text-foreground">{weatherState.data.city}</span>
                <span className="font-mono text-muted-foreground">{weatherState.data.temperature}°C</span>
                <span className="text-muted-foreground">·</span>
                <span className="font-mono text-muted-foreground">{weatherState.data.humidity}% RH</span>
                <span
                  className={`px-1.5 py-0.2 rounded text-[9px] font-extrabold uppercase ${
                    weatherState.data.riskLevel === "High"
                      ? "bg-danger/15 text-danger"
                      : weatherState.data.riskLevel === "Moderate"
                      ? "bg-warning/15 text-warning"
                      : "bg-primary/15 text-primary"
                  }`}
                >
                  {weatherState.data.riskLevel} Risk
                </span>
              </Link>
            )}

            {/* Spotlight Command Palette Trigger (Ctrl+K) */}
            <button
              type="button"
              onClick={() => setCommandPaletteOpen(true)}
              className="flex items-center justify-between gap-2 bg-muted/50 hover:bg-muted border border-border rounded-xl px-3 py-1.5 w-40 sm:w-56 text-left transition-all focus-visible:ring-2 focus-visible:ring-primary"
              aria-label="Open Spotlight Command Palette"
            >
              <div className="flex items-center gap-2 min-w-0">
                <Search size={14} className="text-primary shrink-0" />
                <span className="text-xs text-muted-foreground truncate">
                  {t("common.search", "Spotlight...")}
                </span>
              </div>
              <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono font-bold bg-card border border-border rounded text-muted-foreground shrink-0">
                Ctrl K
              </kbd>
            </button>

            {/* Notification Bell Badge */}
            <Link
              to="/notifications"
              className="relative p-1.5 sm:p-2 rounded-xl border border-border bg-card hover:bg-muted text-muted-foreground hover:text-foreground transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none shrink-0"
              title="Notifications"
              aria-label={`Notifications (${unreadCount} unread)`}
            >
              <Bell size={18} />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-danger text-white text-[10px] font-bold flex items-center justify-center animate-pulse">
                  {unreadCount}
                </span>
              )}
            </Link>

            {/* Multilingual Switcher */}
            <div ref={langDropdownRef} className="relative z-50 shrink-0">
              <button
                onClick={() => {
                  setLangDropdownOpen(!langDropdownOpen)
                  setQuickNavOpen(false)
                }}
                className="flex items-center gap-1 px-2 sm:px-3 py-1.5 rounded-xl border border-border bg-card text-xs font-semibold hover:bg-muted transition-colors shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                aria-expanded={langDropdownOpen}
                aria-haspopup="true"
              >
                <Globe size={14} className="text-primary" />
                <span className="uppercase text-[11px] sm:text-xs">{language}</span>
                <ChevronDown size={12} className="text-muted-foreground" />
              </button>

              {langDropdownOpen && (
                <div
                  className="absolute right-0 top-full mt-2 w-44 bg-card rounded-xl shadow-2xl border border-border py-1.5 z-50 opacity-100 ring-1 ring-black/5 dark:ring-white/10"
                  style={{ backgroundColor: "var(--color-card)" }}
                >
                  {[
                    { code: "en" as Language, label: "English" },
                    { code: "kn" as Language, label: "ಕನ್ನಡ (Kannada)" },
                    { code: "hi" as Language, label: "हिंदी (Hindi)" },
                  ].map((item) => (
                    <button
                      key={item.code}
                      onClick={() => {
                        setLanguage(item.code)
                        setLangDropdownOpen(false)
                      }}
                      className={`w-full text-left px-3.5 py-2 text-xs font-medium hover:bg-muted transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                        language === item.code
                          ? "text-primary font-bold bg-primary/10"
                          : "text-foreground font-medium"
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Theme Toggle */}
            <div className="shrink-0">
              <ThemeToggle />
            </div>

            {/* User Profile Badge */}
            <div className="flex items-center gap-2 pl-2 sm:pl-3 border-l border-border shrink-0">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-[#064e3b] text-xs font-extrabold shadow-sm shrink-0">
                {user?.name ? user.name.slice(0, 2).toUpperCase() : "AV"}
              </div>
              <div className="hidden sm:block">
                <div className="text-xs font-bold leading-tight">{user?.name || "Guest Farmer"}</div>
                <div className="text-[10px] text-muted-foreground capitalize">{user?.role || "Active Session"}</div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main id="main-content" tabIndex={-1} className="flex-1 overflow-y-auto page-enter bg-background outline-none">
          {children}
        </main>

        {/* Global Spotlight Command Palette Modal */}
        <CommandPalette isOpen={commandPaletteOpen} onClose={() => setCommandPaletteOpen(false)} />
      </div>
    </div>
  )
}
