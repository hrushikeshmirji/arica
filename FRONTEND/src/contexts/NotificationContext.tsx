import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react"
import { safeGetJSON, safeSetJSON } from "../utils/safeStorage"
import { DEFAULT_NOTIFS, markAllNotificationsReadApi, markNotificationReadApi } from "../services/notificationService"

export interface NotificationItem {
  id: string
  type: "critical" | "warning" | "info"
  title: string
  msg: string
  time: string
  unread: boolean
  blockId?: string
}

interface NotificationContextType {
  notifications: NotificationItem[]
  unreadCount: number
  markAllRead: () => void
  markAsRead: (id: string) => void
  addNotification: (item: Omit<NotificationItem, "id" | "time" | "unread">) => void
}

const STORAGE_KEY = "arecavision_notifications"

const NotificationContext = createContext<NotificationContextType>({
  notifications: DEFAULT_NOTIFS,
  unreadCount: 2,
  markAllRead: () => null,
  markAsRead: () => null,
  addNotification: () => null,
})

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>(() => {
    const loaded = safeGetJSON<NotificationItem[]>(STORAGE_KEY, DEFAULT_NOTIFS, Array.isArray)
    // Filter out temporary network disconnect artifacts and duplicate unread items
    const seen = new Set<string>()
    const cleaned = loaded.filter((n) => {
      if (n.title === "Scan Failed" && (n.msg?.includes("Failed to fetch") || n.msg?.includes("Network Error") || n.msg?.includes("connect to backend"))) {
        return false
      }
      if (n.unread) {
        const key = `${n.title}::${n.msg}`
        if (seen.has(key)) return false
        seen.add(key)
      }
      return true
    })
    return cleaned.length > 0 ? cleaned : DEFAULT_NOTIFS
  })

  useEffect(() => {
    safeSetJSON(STORAGE_KEY, notifications)
  }, [notifications])

  const unreadCount = notifications.filter((n) => n.unread).length

  const markAllRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })))
    markAllNotificationsReadApi().catch((err) => {
      console.error("Failed to sync mark all read to backend:", err)
    })
  }, [])

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, unread: false } : n))
    )
    markNotificationReadApi(id).catch((err) => {
      console.error("Failed to sync mark notification read to backend:", err)
    })
  }, [])

  const addNotification = useCallback((item: Omit<NotificationItem, "id" | "time" | "unread">) => {
    setNotifications((prev) => {
      // Deduplicate: If an unread notification with identical title and message exists, don't create a duplicate
      const duplicateIndex = prev.findIndex(
        (n) => n.unread && n.title === item.title && n.msg === item.msg
      )
      if (duplicateIndex !== -1) {
        // Already present as unread; update timestamp to 'Just now' and preserve single card
        const updated = [...prev]
        updated[duplicateIndex] = { ...updated[duplicateIndex], time: "Just now" }
        return updated
      }

      const newItem: NotificationItem = {
        ...item,
        id: "notif-" + Date.now() + "-" + Math.random().toString(36).substring(2, 7),
        time: "Just now",
        unread: true,
      }
      return [newItem, ...prev]
    })
  }, [])


  const contextValue = useMemo(() => ({
    notifications,
    unreadCount,
    markAllRead,
    markAsRead,
    addNotification
  }), [notifications, unreadCount, markAllRead, markAsRead, addNotification])

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
    </NotificationContext.Provider>
  )
}

export const useNotifications = () => useContext(NotificationContext)
