import { useState, useEffect } from "react"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { Leaf, Lock, Mail, ArrowRight, Loader2, AlertCircle, User } from "lucide-react"
import { useAuth } from "../contexts/AuthContext"
import { useLanguage } from "../contexts/LanguageContext"
import { motion, AnimatePresence } from "framer-motion"

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, login, register } = useAuth()
  const { t } = useLanguage()

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || "/dashboard"

  useEffect(() => {
    if (user) {
      navigate(from, { replace: true })
    }
  }, [user, navigate, from])

  const [activeTab, setActiveTab] = useState<"login" | "register">(() => {
    return (location.state as { tab?: string })?.tab === "register" ? "register" : "login"
  })

  // Login State
  const [loginEmail, setLoginEmail] = useState("")
  const [loginPassword, setLoginPassword] = useState("")

  // Register State
  const [regName, setRegName] = useState("")
  const [regUsername, setRegUsername] = useState("")
  const [regEmail, setRegEmail] = useState("")
  const [regPassword, setRegPassword] = useState("")
  const [regConfirmPassword, setRegConfirmPassword] = useState("")

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!loginEmail.trim() || !loginPassword) return

    setLoading(true)
    setError(null)
    setSuccessMsg(null)

    try {
      await login({ email: loginEmail, password: loginPassword })
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : t("login.failed_fallback", "Failed to authenticate."))
    } finally {
      setLoading(false)
    }
  }

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!regName || !regUsername || !regEmail || !regPassword || !regConfirmPassword) return
    if (regPassword !== regConfirmPassword) {
      setError("Passwords do not match.")
      return
    }

    setLoading(true)
    setError(null)
    setSuccessMsg(null)

    try {
      await register({
        name: regName,
        username: regUsername,
        email: regEmail,
        password: regPassword,
      })
      setSuccessMsg("Account created successfully! Redirecting...")
      setTimeout(() => {
        navigate("/dashboard")
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/10 text-foreground flex items-center justify-center p-6 relative overflow-hidden">
      {/* Abstract Background Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-secondary/20 blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10 backdrop-blur-xl bg-card/80 border border-border rounded-3xl p-8 shadow-2xl"
      >
        <div className="text-center space-y-4 mb-8">
          <Link to="/" className="inline-flex items-center justify-center gap-2 mb-2 focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded-xl">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground flex items-center justify-center shadow-lg">
              <Leaf size={24} />
            </div>
          </Link>
          <h1 className="text-2xl font-extrabold text-foreground tracking-tight">ArecaVision AI</h1>
        </div>

        <div className="flex p-1 mb-8 bg-muted/50 rounded-xl">
          <button
            onClick={() => { setActiveTab("login"); setError(null); setSuccessMsg(null); }}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${activeTab === "login" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
          >
            Sign In
          </button>
          <button
            onClick={() => { setActiveTab("register"); setError(null); setSuccessMsg(null); }}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${activeTab === "register" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
          >
            Create Account
          </button>
        </div>

        <AnimatePresence mode="wait">
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 p-3 bg-danger/10 border border-danger/30 rounded-xl flex items-center gap-2 text-danger text-xs"
            >
              <AlertCircle size={16} className="shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}
          {successMsg && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center gap-2 text-emerald-500 text-xs"
            >
              <AlertCircle size={16} className="shrink-0" />
              <span>{successMsg}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {activeTab === "login" ? (
          <motion.form
            key="login"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            onSubmit={handleLoginSubmit}
            className="space-y-4"
          >
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Email / Username</label>
              <div className="flex items-center gap-2.5 bg-background/50 border border-border rounded-xl px-3 py-2.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                <Mail size={16} className="text-muted-foreground shrink-0" />
                <input
                  type="text"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="Enter your email or username"
                  className="bg-transparent border-none outline-none text-sm text-foreground placeholder-muted-foreground flex-1"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Password</label>
              <div className="flex items-center gap-2.5 bg-background/50 border border-border rounded-xl px-3 py-2.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                <Lock size={16} className="text-muted-foreground shrink-0" />
                <input
                  type="password"
                  required
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  className="bg-transparent border-none outline-none text-sm text-foreground placeholder-muted-foreground flex-1"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 mt-4 justify-center text-sm font-bold shadow-lg shadow-primary/25 disabled:opacity-50"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <span>Sign In</span>}
            </button>
          </motion.form>
        ) : (
          <motion.form
            key="register"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            onSubmit={handleRegisterSubmit}
            className="space-y-4"
          >
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Full Name</label>
              <div className="flex items-center gap-2.5 bg-background/50 border border-border rounded-xl px-3 py-2.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                <User size={16} className="text-muted-foreground shrink-0" />
                <input
                  type="text"
                  required
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  placeholder="John Doe"
                  className="bg-transparent border-none outline-none text-sm text-foreground placeholder-muted-foreground flex-1"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Username</label>
              <div className="flex items-center gap-2.5 bg-background/50 border border-border rounded-xl px-3 py-2.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                <User size={16} className="text-muted-foreground shrink-0" />
                <input
                  type="text"
                  required
                  value={regUsername}
                  onChange={(e) => setRegUsername(e.target.value)}
                  placeholder="johndoe123"
                  className="bg-transparent border-none outline-none text-sm text-foreground placeholder-muted-foreground flex-1"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Email</label>
              <div className="flex items-center gap-2.5 bg-background/50 border border-border rounded-xl px-3 py-2.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                <Mail size={16} className="text-muted-foreground shrink-0" />
                <input
                  type="email"
                  required
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  placeholder="john@example.com"
                  className="bg-transparent border-none outline-none text-sm text-foreground placeholder-muted-foreground flex-1"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Password</label>
              <div className="flex items-center gap-2.5 bg-background/50 border border-border rounded-xl px-3 py-2.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                <Lock size={16} className="text-muted-foreground shrink-0" />
                <input
                  type="password"
                  required
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="••••••••"
                  className="bg-transparent border-none outline-none text-sm text-foreground placeholder-muted-foreground flex-1"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Confirm Password</label>
              <div className="flex items-center gap-2.5 bg-background/50 border border-border rounded-xl px-3 py-2.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                <Lock size={16} className="text-muted-foreground shrink-0" />
                <input
                  type="password"
                  required
                  value={regConfirmPassword}
                  onChange={(e) => setRegConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="bg-transparent border-none outline-none text-sm text-foreground placeholder-muted-foreground flex-1"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 mt-4 justify-center text-sm font-bold shadow-lg shadow-primary/25 disabled:opacity-50"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <span>Create Account</span>}
            </button>
          </motion.form>
        )}
      </motion.div>
    </div>
  )
}
