/**
 * ArecaVision AI — Single Source of Truth Design Tokens
 * Used by both DOM CSS variables and Recharts/SVG components.
 */

export const THEME_TOKENS = {
  colors: {
    primary: "#047857",
    primaryHover: "#065f46",
    accent: "#0ea5e9",
    success: "#047857",
    warning: "#b45309",
    danger: "#dc2626",
    error: "#dc2626",
  },

  // 5-Step Severity Scale Tokens (compatible with Recharts SVG stroke/fill)
  severity: {
    healthy: "#047857",
    mild: "#3b82f6",
    moderate: "#b45309",
    severe: "#f97316",
    critical: "#dc2626",
  },

  // Navigation Items Enterprise High-Contrast Token Specifications (No Neon)
  nav: {
    light: {
      activeBg: "#f0fdf4",
      activeText: "#166534",
      activePill: "#166534",
      hoverBg: "#f1f5f9",
      hoverText: "#0f172a",
      defaultText: "#64748b",
    },
    dark: {
      activeBg: "rgba(22, 101, 52, 0.25)",
      activeText: "#4ade80",
      activePill: "#22c55e",
      hoverBg: "#1e293b",
      hoverText: "#f8fafc",
      defaultText: "#94a3b8",
    },
  },

  // Chart & SVG Color Mappings (Recharts props)
  charts: {
    grid: "var(--color-border)",
    tooltipBg: "var(--color-card)",
    tooltipBorder: "var(--color-border)",
    lines: {
      anthracnose: "#dc2626",
      fruitRot: "#f97316",
      nutCracking: "#b45309",
      sootyMold: "#64748b",
      yield: "#047857",
    },
  },
} as const
