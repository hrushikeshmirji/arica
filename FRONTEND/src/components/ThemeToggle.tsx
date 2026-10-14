import { Moon, Sun } from "lucide-react"
import { useTheme } from "../contexts/ThemeProvider"
import { motion, AnimatePresence } from "framer-motion"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const isDark =
    theme === "dark" ||
    (theme === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches)

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="relative p-2.5 rounded-xl hover:bg-muted transition-colors overflow-hidden focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
      aria-label="Toggle theme"
    >
      <AnimatePresence mode="wait" initial={false}>
        {isDark ? (
          <motion.div
            key="moon"
            initial={{ y: -20, opacity: 0, rotate: -90 }}
            animate={{ y: 0, opacity: 1, rotate: 0 }}
            exit={{ y: 20, opacity: 0, rotate: 90 }}
            transition={{ duration: 0.2 }}
          >
            <Moon size={18} className="text-foreground" />
          </motion.div>
        ) : (
          <motion.div
            key="sun"
            initial={{ y: -20, opacity: 0, rotate: -90 }}
            animate={{ y: 0, opacity: 1, rotate: 0 }}
            exit={{ y: 20, opacity: 0, rotate: 90 }}
            transition={{ duration: 0.2 }}
          >
            <Sun size={18} className="text-foreground" />
          </motion.div>
        )}
      </AnimatePresence>
    </button>
  )
}
