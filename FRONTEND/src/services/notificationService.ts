import { apiRequest } from "./apiClient"
import { NotificationResponse, NotificationItemData } from "../types/api"

export const DEFAULT_NOTIFS: NotificationItemData[] = [
  {
    id: "notif-1",
    type: "critical",
    title: "High Anthracnose Infection Detected",
    msg: "Block C reported 96.4% Anthracnose probability.",
    time: "10 mins ago",
    unread: true,
    blockId: "Block C",
  },
  {
    id: "notif-2",
    type: "warning",
    title: "Monsoon Humidity Alert (>90%)",
    msg: "High risk of Koleroga fruit rot in next 48 hours.",
    time: "25 mins ago",
    unread: true,
    blockId: "Block A",
  },
  {
    id: "notif-3",
    type: "info",
    title: "AI Safety Pipeline Active",
    msg: "EfficientNet-B0 + ViT-B/16 ensemble active with provisional uncertainty gates and zero-box checks.",
    time: "2 hours ago",
    unread: false,
  },
]

/**
 * Note on Mock Error Simulation:
 * Background notification polling uses `bypassErrorSimulation: true` to prevent background 10s interval
 * fetches from triggering noisy error banners when `VITE_MOCK_ERROR_RATE` is enabled during manual testing.
 */
export async function fetchNotifications(options: { bypassErrorSimulation?: boolean } = {}): Promise<NotificationResponse> {
  const unreadCount = DEFAULT_NOTIFS.filter((n) => n.unread).length

  return apiRequest<NotificationResponse>("/notifications", {
    method: "GET",
    bypassErrorSimulation: options.bypassErrorSimulation ?? true,
    mockFallbackData: {
      notifications: DEFAULT_NOTIFS,
      unreadCount,
    },
  })
}

export async function markAllNotificationsReadApi(): Promise<void> {
  return apiRequest<void>("/notifications/read-all", {
    method: "PUT",
    mockFallbackData: undefined,
  })
}

export async function markNotificationReadApi(id: string): Promise<void> {
  return apiRequest<void>(`/notifications/${id}/read`, {
    method: "PUT",
    mockFallbackData: undefined,
  })
}
