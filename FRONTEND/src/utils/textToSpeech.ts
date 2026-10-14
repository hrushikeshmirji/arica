let activeUtterance: SpeechSynthesisUtterance | null = null

export function speakText(text: string, language: string, onEnd?: () => void): boolean {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    return false
  }

  // Cancel any ongoing speech
  if (activeUtterance) {
    window.speechSynthesis.cancel()
  }
  window.speechSynthesis.resume()

  const utterance = new SpeechSynthesisUtterance(text)
  activeUtterance = utterance
  
  const localeMap: Record<string, string> = {
    en: "en-IN",
    kn: "kn-IN",
    hi: "hi-IN",
  }
  const targetLang = localeMap[language] || "en-IN"
  utterance.lang = targetLang
  utterance.rate = 0.95 // slightly slower for clearer diction for farmers

  const voices = window.speechSynthesis.getVoices()
  const matchedVoice = voices.find(v => v.lang === targetLang)
  if (matchedVoice) {
    utterance.voice = matchedVoice
  }

  const handleEnd = () => {
    activeUtterance = null
    if (onEnd) onEnd()
  }

  utterance.onend = handleEnd
  utterance.onerror = handleEnd

  window.speechSynthesis.speak(utterance)
  return true
}

export function stopSpeech(): void {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel()
    activeUtterance = null
  }
}

