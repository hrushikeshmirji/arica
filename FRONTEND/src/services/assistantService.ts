import { apiRequest } from "./apiClient"
import { AssistantChatRequest, AssistantChatResponse, ChatMessageItem } from "../types/api"

const INITIAL_PROMPTS = [
  "How do I prevent Koleroga fruit rot during the monsoon?",
  "What is the recommended spray for Areca Anthracnose?",
  "How to fix tender nut cracking in betel nut palms?",
  "What soil nutrients are essential for high Areca yield?",
]

const INITIAL_CHAT_HISTORY: ChatMessageItem[] = [
  {
    id: "welcome-1",
    sender: "ai",
    text: "Hello! I am ArecaVision AI Assistant — your expert advisor for Areca Catechu plantation management, disease diagnostics, and yield optimization. How can I help your farm today?",
    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    suggestions: INITIAL_PROMPTS,
  },
]

let sessionChatHistory: ChatMessageItem[] = [...INITIAL_CHAT_HISTORY]

export async function fetchChatHistory(): Promise<ChatMessageItem[]> {
  return apiRequest<ChatMessageItem[]>("/assistant/history", {
    method: "GET",
    mockFallbackData: [...sessionChatHistory],
  })
}

export async function sendChatMessage(req: AssistantChatRequest): Promise<AssistantChatResponse> {
  const msgLower = req.message.toLowerCase()
  let reply = "I am ArecaVision AI, trained on CNN, ViT, and YOLOv8 models. I can assist you with disease diagnostics, weather risk correlation, treatment schedules, and plantation management for Areca catechu."
  let suggestedActions: string[] = ["Check Weather Risk", "View Diagnostics Library", "Schedule Spray"]

  if (msgLower.includes("koleroga") || msgLower.includes("fruit rot")) {
    reply = "Koleroga (Fruit Rot) is caused by Phytophthora meadii during high monsoon humidity (>90%). I recommend applying a 1% Bordeaux mixture to the canopy before heavy rains commence, and ensuring crown sanitation."
    suggestedActions = ["View Bordeaux Guide", "Check Rain Forecast", "Inspect Block A"]
  } else if (msgLower.includes("anthracnose") || msgLower.includes("leaf")) {
    reply = "Anthracnose causes dark lesions on leaves and nut husks. Recommended treatment includes 1% Bordeaux mixture or Copper Oxychloride 50% WP (2.5g/L), along with removing infected plant debris."
    suggestedActions = ["Copper Fungicide Dosage", "View Scan History", "Create Treatment Alert"]
  }

  const mockResponse: AssistantChatResponse = {
    reply,
    suggestedActions,
    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }

  sessionChatHistory.push({
    id: `user-${Date.now()}`,
    sender: "user",
    text: req.message,
    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  })

  sessionChatHistory.push({
    id: `ai-${Date.now()}`,
    sender: "ai",
    text: mockResponse.reply,
    timestamp: mockResponse.timestamp,
    suggestions: mockResponse.suggestedActions,
  })

  return apiRequest<AssistantChatResponse>("/assistant/chat", {
    method: "POST",
    body: JSON.stringify(req),
    mockFallbackData: mockResponse,
  })
}
