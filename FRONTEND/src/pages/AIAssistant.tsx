import { useState, useRef, useEffect } from "react"
import { useLocation } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  Send,
  Bot,
  User,
  Loader2,
  AlertCircle,
  RefreshCw,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
} from "lucide-react"
import { useLanguage } from "../contexts/LanguageContext"
import { fetchChatHistory, sendChatMessage } from "../services/assistantService"
import { ChatMessageItem } from "../types/api"
import { useSpeechRecognition } from "../hooks/useSpeechRecognition"
import { speakText, stopSpeech } from "../utils/textToSpeech"

export default function AIAssistant() {
  const location = useLocation()
  const { language, t } = useLanguage()
  const queryClient = useQueryClient()
  const [input, setInput] = useState("")
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const handledPromptRef = useRef<string | null>(null)

  // Voice Input Hook
  const {
    isListening,
    transcript,
    isSupported: isSpeechSupported,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition()

  // Update input when voice transcript updates
  useEffect(() => {
    if (transcript) {
      setInput(transcript)
    }
  }, [transcript])

  // Stop speech when unmounting
  useEffect(() => {
    return () => {
      stopSpeech()
    }
  }, [])

  // Query-Cached Conversation History
  const historyQuery = useQuery({
    queryKey: ["chatHistory"],
    queryFn: fetchChatHistory,
  })

  const messages = historyQuery.data || []

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Chat Mutation updating TanStack Query cache
  const chatMutation = useMutation({
    mutationFn: async (userText: string) => {
      stopSpeech()
      setSpeakingMessageId(null)

      const userMsg: ChatMessageItem = {
        id: "user-" + Date.now(),
        sender: "user",
        text: userText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }

      // Optimistically update query cache
      queryClient.setQueryData<ChatMessageItem[]>(["chatHistory"], (old) => [
        ...(old || []),
        userMsg,
      ])

      const response = await sendChatMessage({ message: userText })
      return { userMsg, response }
    },
    onSuccess: ({ response }) => {
      const aiMsg: ChatMessageItem = {
        id: "ai-" + Date.now(),
        sender: "ai",
        text: response.reply,
        timestamp: response.timestamp,
        suggestions: response.suggestedActions,
      }

      queryClient.setQueryData<ChatMessageItem[]>(["chatHistory"], (old) => [
        ...(old || []),
        aiMsg,
      ])
    },
    onError: (err: Error) => {
      const errorMsg: ChatMessageItem = {
        id: "err-" + Date.now(),
        sender: "ai",
        text: `${t("assistant.error_prefix", "Error processing request:")} ${err.message || t("assistant.error_fallback", "Failed to reach AI assistant")}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }
      queryClient.setQueryData<ChatMessageItem[]>(["chatHistory"], (old) => [
        ...(old || []),
        errorMsg,
      ])
    },
  })

  const handleSend = (textToSend?: string) => {
    const query = (textToSend || input).trim()
    if (!query || chatMutation.isPending) return

    if (isListening) {
      stopListening()
    }
    resetTranscript()

    if (!textToSend) setInput("")
    chatMutation.mutate(query)
  }

  useEffect(() => {
    const state = location.state as { initialPrompt?: string } | null
    if (state?.initialPrompt && handledPromptRef.current !== state.initialPrompt && historyQuery.isSuccess) {
      handledPromptRef.current = state.initialPrompt
      chatMutation.mutate(state.initialPrompt)
    }
  }, [location.state, historyQuery.isSuccess, chatMutation])

  const handleToggleVoiceInput = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  const handleToggleSpeakMessage = (msgId: string, text: string) => {
    if (speakingMessageId === msgId) {
      stopSpeech()
      setSpeakingMessageId(null)
    } else {
      stopSpeech()
      setSpeakingMessageId(msgId)
      speakText(text, language, () => setSpeakingMessageId(null))
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 flex flex-col h-[calc(100vh-5rem)]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-foreground">{t("nav.assistant", "AI Assistant")}</h1>
            <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-extrabold border border-primary/20">
              {t("assistant.badge", "Query-Cached AI Engine")}
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-extrabold border border-emerald-500/20">
              ICAR-CPCRI Audited Guidance
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("assistant.subtitle", "24/7 Multilingual Betel Nut agronomic expert grounded in ICAR-CPCRI & CIBRC standards (unverified off-label chemicals strictly withheld)")}
          </p>
        </div>
      </div>

      {/* Chat Conversation Box */}
      <div className="flex-1 bg-card rounded-2xl border border-border p-4 overflow-y-auto space-y-4 shadow-sm">
        {historyQuery.isLoading ? (
          <div className="flex items-center justify-center h-full text-xs text-muted-foreground gap-2">
            <Loader2 size={18} className="animate-spin text-primary" />
            <span>{t("assistant.hydrating", "Hydrating conversation history...")}</span>
          </div>
        ) : historyQuery.isError ? (
          <div className="p-4 bg-danger/10 border border-danger/30 rounded-xl flex items-center justify-between text-xs text-danger">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} />
              <span>{(historyQuery.error as Error)?.message || t("assistant.load_failed", "Failed to load chat history")}</span>
            </div>
            <button
              onClick={() => historyQuery.refetch()}
              className="px-3 py-1 bg-danger text-white rounded font-bold hover:opacity-90"
            >
              <RefreshCw size={12} className="inline mr-1" /> {t("detect.retry", "Retry")}
            </button>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${msg.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white font-bold text-xs ${
                  msg.sender === "user" ? "bg-accent" : "bg-primary"
                }`}
              >
                {msg.sender === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>

              <div className={`space-y-2 max-w-[80%] ${msg.sender === "user" ? "items-end" : "items-start"}`}>
                <div
                  className={`p-3.5 rounded-2xl text-xs leading-relaxed relative group ${
                    msg.sender === "user"
                      ? "bg-primary text-primary-foreground font-medium rounded-tr-none"
                      : "bg-muted/40 border border-border text-foreground rounded-tl-none"
                  }`}
                >
                  <div>{msg.text}</div>

                  {/* Speaker Button for AI responses */}
                  {msg.sender === "ai" && (
                    <button
                      onClick={() => handleToggleSpeakMessage(msg.id, msg.text)}
                      className={`mt-2 p-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors ${
                        speakingMessageId === msg.id
                          ? "text-danger bg-danger/10 font-bold"
                          : "text-muted-foreground hover:text-primary"
                      }`}
                      title={speakingMessageId === msg.id ? t("assistant.stop_speech", "Stop audio") : t("assistant.speak_response", "Read aloud")}
                    >
                      {speakingMessageId === msg.id ? <VolumeX size={14} /> : <Volume2 size={14} />}
                      <span className="text-[10px]">{speakingMessageId === msg.id ? t("assistant.stop_speech", "Stop Audio") : t("assistant.speak_response", "Listen")}</span>
                    </button>
                  )}
                </div>

                {msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {msg.suggestions.map((sug, i) => (
                      <button
                        key={i}
                        onClick={() => handleSend(sug)}
                        className="px-2.5 py-1 rounded-lg border border-primary/30 bg-primary/10 text-primary text-[11px] font-semibold hover:bg-primary hover:text-white transition-colors"
                      >
                        {sug}
                      </button>
                    ))}
                  </div>
                )}

                <div className="text-[10px] text-muted-foreground px-1">{msg.timestamp}</div>
              </div>
            </div>
          ))
        )}

        {chatMutation.isPending && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground py-2">
            <Loader2 size={16} className="animate-spin text-primary" />
            <span>{t("assistant.analyzing", "AI Assistant is analyzing query...")}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Voice Listening Bar Indicator */}
      {isListening && (
        <div className="p-3 rounded-xl bg-danger/10 border border-danger/30 text-danger text-xs flex items-center justify-between animate-pulse">
          <div className="flex items-center gap-2">
            <Mic size={16} className="animate-bounce" />
            <span className="font-semibold">{t("assistant.listening_status", "Listening... Speak your question in your selected language.")}</span>
          </div>
          <button
            onClick={stopListening}
            className="px-2 py-0.5 rounded bg-danger text-white text-[11px] font-bold"
          >
            {t("assistant.stop_speech", "Stop")}
          </button>
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          handleSend()
        }}
        className="flex items-center gap-2 bg-card border border-border rounded-2xl p-2 shrink-0 shadow-sm"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("assistant.input_placeholder", "Ask AI Assistant about disease treatments, rainfall risk, or plantation care...")}
          className="flex-1 bg-transparent border-none outline-none text-xs text-foreground px-3 placeholder-muted-foreground"
        />

        {/* Microphone Button */}
        {isSpeechSupported && (
          <button
            type="button"
            onClick={handleToggleVoiceInput}
            className={`p-2 rounded-xl text-xs transition-colors ${
              isListening
                ? "bg-danger text-white animate-pulse"
                : "text-muted-foreground hover:text-primary hover:bg-muted/50"
            }`}
            title={isListening ? t("assistant.mic_stop", "Stop listening") : t("assistant.mic_start", "Speak query")}
          >
            {isListening ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
        )}

        <button
          type="submit"
          disabled={!input.trim() || chatMutation.isPending}
          className="btn-primary py-2 px-4 text-xs font-bold disabled:opacity-40 shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none flex items-center gap-1.5"
        >
          <span>{t("assistant.send", "Send")}</span>
          <Send size={14} />
        </button>
      </form>
    </div>
  )
}
