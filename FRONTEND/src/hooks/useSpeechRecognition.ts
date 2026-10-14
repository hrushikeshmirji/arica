import { useState, useEffect, useRef, useCallback } from "react"
import { useLanguage } from "../contexts/LanguageContext"

interface SpeechRecognitionHook {
  isListening: boolean
  transcript: string
  isSupported: boolean
  startListening: () => void
  stopListening: () => void
  resetTranscript: () => void
}

interface SpeechRecognitionResultItem {
  transcript: string
}

interface SpeechRecognitionResultList {
  length: number
  [index: number]: {
    [index: number]: SpeechRecognitionResultItem
  }
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionErrorEvent {
  error: string
}

interface SpeechRecognitionInstance {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
  abort: () => void
}

export function useSpeechRecognition(): SpeechRecognitionHook {
  const { language } = useLanguage()
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [isSupported, setIsSupported] = useState(false)
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)

  useEffect(() => {
    setIsListening(false)
    const SpeechRecognitionClass =
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).webkitSpeechRecognition

    if (SpeechRecognitionClass) {
      setIsSupported(true)
      const recognition = new SpeechRecognitionClass()
      recognition.continuous = false
      recognition.interimResults = true

      // Map app language to BCP-47 locale tags
      const localeMap: Record<string, string> = {
        en: "en-IN",
        kn: "kn-IN",
        hi: "hi-IN",
      }
      recognition.lang = localeMap[language] || "en-IN"

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let fullTranscript = ""
        for (let i = 0; i < event.results.length; i++) {
          fullTranscript += event.results[i][0].transcript
        }
        setTranscript(fullTranscript)
      }

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.warn("Speech recognition error:", event.error)
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current = recognition
    } else {
      setIsSupported(false)
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onresult = null
        recognitionRef.current.onerror = null
        recognitionRef.current.onend = null
        recognitionRef.current.abort()
      }
    }
  }, [language])

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      try {
        setTranscript("")
        recognitionRef.current.start()
        setIsListening(true)
      } catch (err) {
        console.warn("Speech recognition start failed:", err)
      }
    }
  }, [isListening])

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    }
  }, [isListening])

  const resetTranscript = useCallback(() => {
    setTranscript("")
  }, [])

  return {
    isListening,
    transcript,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  }
}
