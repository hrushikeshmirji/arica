import { Check, ShieldAlert, Info, AlertTriangle, CheckCircle2 } from "lucide-react"
import { useNotifications } from "../contexts/NotificationContext"
import { useLanguage } from "../contexts/LanguageContext"

export default function Notifications() {
  const { notifications, markAllRead, markAsRead } = useNotifications()
  const { t } = useLanguage()

  const hasUnread = notifications.some((n) => n.unread)

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-extrabold text-foreground">{t("nav.notifications", "Notifications")}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{t("notif.subtitle", "Real-time alerts and system logs")}</p>
        </div>

        {notifications.length > 0 && (
          <button
            onClick={markAllRead}
            disabled={!hasUnread}
            className="btn-secondary text-xs flex items-center gap-1.5 disabled:opacity-40 disabled:pointer-events-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          >
            <Check size={14} /> {t("notif.mark_all_read", "Mark All Read")}
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="bg-card rounded-2xl border border-border p-12 text-center flex flex-col items-center justify-center min-h-[360px]">
          <div className="w-16 h-16 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-4 shadow-sm">
            <CheckCircle2 size={32} />
          </div>
          <h2 className="text-lg font-bold text-foreground mb-1.5">
            {t("notif.empty_title", "You're all caught up")}
          </h2>
          <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
            {t("notif.empty_desc", "No active alerts or system notifications at this time.")}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => (
            <div
              key={n.id}
              role="button"
              tabIndex={0}
              onClick={() => markAsRead(n.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault()
                  markAsRead(n.id)
                }
              }}
              className={`p-4 rounded-xl border flex items-start gap-4 transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                n.unread ? "bg-card border-primary/40 shadow-sm" : "bg-card/60 border-border opacity-80"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                  n.type === "critical"
                    ? "bg-danger/10 text-danger"
                    : n.type === "warning"
                    ? "bg-warning/10 text-warning"
                    : "bg-primary/10 text-primary"
                }`}
              >
                {n.type === "critical" ? (
                  <AlertTriangle size={16} />
                ) : n.type === "warning" ? (
                  <ShieldAlert size={16} />
                ) : (
                  <Info size={16} />
                )}
              </div>

              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-foreground">{n.title}</h3>
                  <span className="text-[10px] text-muted-foreground">{n.time}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{n.msg}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
