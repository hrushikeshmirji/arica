import React, { useState, useRef, useEffect, useCallback } from "react"
import {
  Camera,
  CameraOff,
  X,
  RotateCw,
  Check,
  RefreshCw,
  AlertCircle,
  Sparkles,
  Zap,
  ZapOff,
  Scan,
  Upload,
} from "lucide-react"
import { useLanguage } from "../contexts/LanguageContext"

interface LiveCameraModalProps {
  isOpen: boolean
  onClose: () => void
  onCapture: (file: File) => void
}

export default function LiveCameraModal({
  isOpen,
  onClose,
  onCapture,
}: LiveCameraModalProps) {
  const { t } = useLanguage()
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment")
  const [hasMultipleCameras, setHasMultipleCameras] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null)
  const [videoResolution, setVideoResolution] = useState<{ width: number; height: number } | null>(null)
  const [isFlashing, setIsFlashing] = useState<boolean>(false)
  const [torchSupported, setTorchSupported] = useState<boolean>(false)
  const [torchOn, setTorchOn] = useState<boolean>(false)

  // Clean up media tracks
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop()
        } catch {
          // ignore
        }
      })
      streamRef.current = null
    }
  }, [])

  // Start live camera stream
  const startStream = useCallback(async () => {
    stopStream()
    setIsLoading(true)
    setCameraError(null)
    setCapturedImage(null)
    setCapturedBlob(null)
    setTorchOn(false)

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error(
          t(
            "camera.unsupported",
            "Camera access is not supported by your browser or connection. Please ensure you are using HTTPS or localhost."
          )
        )
      }

      // Check available camera devices
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const videoDevices = devices.filter((d) => d.kind === "videoinput")
        setHasMultipleCameras(videoDevices.length > 1)
      } catch {
        // ignore enumeration errors
      }

      const constraints: MediaStreamConstraints = {
        video: {
          facingMode: { ideal: facingMode },
          width: { ideal: 1920, min: 640 },
          height: { ideal: 1080, min: 480 },
        },
        audio: false,
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {
          // auto-play handling
        })
      }

      // Check torch support
      const videoTrack = stream.getVideoTracks()[0]
      if (videoTrack) {
        const capabilities = (videoTrack.getCapabilities?.() || {}) as { torch?: boolean }
        if (capabilities.torch) {
          setTorchSupported(true)
        }
      }

      setIsLoading(false)
    } catch (err: any) {
      console.error("Camera stream initialization failed:", err)
      stopStream()
      setIsLoading(false)

      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setCameraError(
          t(
            "camera.permission_denied",
            "Camera permission was denied. Please allow camera access in your browser settings to take live photos."
          )
        )
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        setCameraError(
          t(
            "camera.not_found",
            "No camera device was detected on your system. Please plug in a webcam or upload an existing image."
          )
        )
      } else {
        setCameraError(
          err.message ||
            t(
              "camera.generic_error",
              "Unable to start live camera stream. Please try again or upload a photo."
            )
        )
      }
    }
  }, [facingMode, stopStream, t])

  // Toggle Torch/Flash
  const toggleTorch = async () => {
    if (!streamRef.current) return
    const track = streamRef.current.getVideoTracks()[0]
    if (!track) return

    try {
      const newTorchState = !torchOn
      await (track as any).applyConstraints({
        advanced: [{ torch: newTorchState }],
      })
      setTorchOn(newTorchState)
    } catch (err) {
      console.warn("Could not toggle torch:", err)
    }
  }

  // Handle stream dimensions when metadata loads
  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setVideoResolution({
        width: videoRef.current.videoWidth,
        height: videoRef.current.videoHeight,
      })
    }
  }

  // Switch facing mode (Front / Back camera)
  const toggleFacingMode = () => {
    setFacingMode((prev) => (prev === "environment" ? "user" : "environment"))
  }

  // Snap photo from live video feed
  const capturePhoto = () => {
    if (!videoRef.current) return

    setIsFlashing(true)
    setTimeout(() => setIsFlashing(false), 200)

    const video = videoRef.current
    const canvas = canvasRef.current || document.createElement("canvas")
    canvas.width = video.videoWidth || 1280
    canvas.height = video.videoHeight || 720

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // If front camera, flip horizontally for mirror effect
    if (facingMode === "user") {
      ctx.translate(canvas.width, 0)
      ctx.scale(-1, 1)
    }

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const imageUrl = URL.createObjectURL(blob)
          setCapturedImage(imageUrl)
          setCapturedBlob(blob)
          stopStream()
        }
      },
      "image/jpeg",
      0.95
    )
  }

  // Retake photo
  const handleRetake = () => {
    if (capturedImage) {
      URL.revokeObjectURL(capturedImage)
      setCapturedImage(null)
      setCapturedBlob(null)
    }
    startStream()
  }

  // Confirm and submit photo
  const handleConfirm = () => {
    if (capturedBlob) {
      const fileName = `arecavision_camera_${Date.now()}.jpg`
      const file = new File([capturedBlob], fileName, { type: "image/jpeg" })
      onCapture(file)
      handleClose()
    }
  }

  // Close modal and cleanup
  const handleClose = () => {
    stopStream()
    if (capturedImage) {
      URL.revokeObjectURL(capturedImage)
      setCapturedImage(null)
      setCapturedBlob(null)
    }
    onClose()
  }

  // Handle ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        handleClose()
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen])

  // Lifecycle effect when isOpen changes
  useEffect(() => {
    if (isOpen) {
      startStream()
    } else {
      stopStream()
    }
    return () => {
      stopStream()
    }
  }, [isOpen, facingMode])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-card border border-border/80 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border/60 bg-card/90">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <Camera size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-extrabold text-foreground">
                  {capturedImage
                    ? t("camera.preview_title", "Review Photo")
                    : t("camera.live_title", "Live Camera Viewfinder")}
                </h3>
                {!capturedImage && !isLoading && !cameraError && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-500 border border-emerald-500/30 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                    LIVE
                  </span>
                )}
              </div>
              <p className="text-[11px] text-muted-foreground">
                {capturedImage
                  ? t("camera.preview_desc", "Confirm image quality before disease triage")
                  : t("camera.live_desc", "Align Areca nut bunch or palm frond in the center target box")}
              </p>
            </div>
          </div>

          <button
            onClick={handleClose}
            className="w-8 h-8 rounded-full bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground flex items-center justify-center transition-colors"
            title="Close camera"
          >
            <X size={18} />
          </button>
        </div>

        {/* Viewport / Video Display Container */}
        <div className="relative flex-1 bg-black min-h-[320px] sm:min-h-[420px] flex items-center justify-center overflow-hidden">
          {/* Subtle Flash Overlay */}
          {isFlashing && (
            <div className="absolute inset-0 bg-white z-40 animate-out fade-out duration-200" />
          )}

          {/* Offscreen Canvas for Snapshot rendering */}
          <canvas ref={canvasRef} className="hidden" />

          {/* Loading State */}
          {isLoading && !cameraError && (
            <div className="flex flex-col items-center justify-center gap-3 p-8 text-center text-white z-20">
              <div className="w-12 h-12 rounded-full border-3 border-primary/30 border-t-primary animate-spin" />
              <p className="text-xs font-bold">{t("camera.starting_stream", "Connecting to live camera...")}</p>
              <p className="text-[11px] text-white/60 max-w-xs">
                {t("camera.permission_hint", "Please grant camera permissions if prompted by your browser.")}
              </p>
            </div>
          )}

          {/* Error State */}
          {cameraError && (
            <div className="flex flex-col items-center justify-center gap-3 p-8 text-center text-white z-20 max-w-md">
              <div className="w-12 h-12 rounded-full bg-danger/20 text-danger flex items-center justify-center">
                <CameraOff size={24} />
              </div>
              <p className="text-sm font-bold text-danger">{t("camera.error_title", "Camera Unavailable")}</p>
              <p className="text-xs text-white/75 leading-relaxed">{cameraError}</p>
              <div className="flex items-center gap-3 mt-2">
                <button
                  onClick={startStream}
                  className="px-4 py-2 bg-primary text-white text-xs font-bold rounded-xl flex items-center gap-1.5 shadow-sm hover:brightness-110 transition-all"
                >
                  <RefreshCw size={14} />
                  {t("camera.retry", "Try Again")}
                </button>
                <button
                  onClick={handleClose}
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold rounded-xl transition-all"
                >
                  {t("common.cancel", "Cancel")}
                </button>
              </div>
            </div>
          )}

          {/* Live Video Feed */}
          {!capturedImage && (
            <video
              ref={videoRef}
              playsInline
              muted
              autoPlay
              onLoadedMetadata={handleLoadedMetadata}
              className={`w-full h-full object-cover ${
                facingMode === "user" ? "scale-x-[-1]" : ""
              } ${isLoading || cameraError ? "hidden" : "block"}`}
            />
          )}

          {/* Captured Static Preview */}
          {capturedImage && (
            <img
              src={capturedImage}
              alt="Captured Frame"
              className="w-full h-full object-contain bg-black/90"
            />
          )}

          {/* Viewfinder Overlay Targeting Reticle (Live Mode Only) */}
          {!capturedImage && !isLoading && !cameraError && (
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center p-8">
              {/* Target Frame Box */}
              <div className="relative w-64 h-64 sm:w-80 sm:h-80 border-2 border-primary/40 rounded-3xl flex items-center justify-center shadow-[0_0_0_9999px_rgba(0,0,0,0.35)]">
                {/* Corner Brackets */}
                <div className="absolute -top-1 -left-1 w-6 h-6 border-t-3 border-l-3 border-primary rounded-tl-xl" />
                <div className="absolute -top-1 -right-1 w-6 h-6 border-t-3 border-r-3 border-primary rounded-tr-xl" />
                <div className="absolute -bottom-1 -left-1 w-6 h-6 border-b-3 border-l-3 border-primary rounded-bl-xl" />
                <div className="absolute -bottom-1 -right-1 w-6 h-6 border-b-3 border-r-3 border-primary rounded-br-xl" />

                {/* Center Reticle Crosshair */}
                <div className="w-6 h-6 flex items-center justify-center">
                  <div className="w-full h-0.5 bg-primary/60" />
                  <div className="h-full w-0.5 bg-primary/60 absolute" />
                </div>

                <div className="absolute bottom-3 px-3 py-1 bg-black/60 backdrop-blur-md rounded-full text-[10px] font-semibold text-white/90 flex items-center gap-1.5 border border-white/10">
                  <Scan size={12} className="text-primary" />
                  <span>{t("camera.center_palm", "Center Areca palm/nut")}</span>
                </div>
              </div>

              {/* Resolution Tag */}
              {videoResolution && (
                <div className="absolute top-4 right-4 px-2.5 py-1 bg-black/50 backdrop-blur-md rounded-lg text-[10px] font-mono text-white/80 border border-white/10">
                  {videoResolution.width} × {videoResolution.height}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Controls Footer */}
        <div className="px-5 py-4 bg-card border-t border-border/60">
          {!capturedImage ? (
            /* Live Stream Action Controls */
            <div className="flex items-center justify-between gap-4">
              {/* Left Slot: Torch Toggle */}
              <div className="w-24 flex items-center justify-start">
                {torchSupported && (
                  <button
                    onClick={toggleTorch}
                    disabled={isLoading || !!cameraError}
                    className={`p-2.5 rounded-xl border transition-all ${
                      torchOn
                        ? "bg-amber-500/20 text-amber-500 border-amber-500/40"
                        : "bg-muted text-muted-foreground border-border hover:text-foreground"
                    }`}
                    title={torchOn ? "Turn off flashlight" : "Turn on flashlight"}
                  >
                    {torchOn ? <Zap size={18} /> : <ZapOff size={18} />}
                  </button>
                )}
              </div>

              {/* Center Slot: Shutter Snapshot Button */}
              <button
                onClick={capturePhoto}
                disabled={isLoading || !!cameraError}
                className="group relative flex items-center justify-center w-16 h-16 rounded-full border-4 border-primary p-1 bg-primary/10 hover:bg-primary/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 shadow-lg shadow-primary/20"
                title={t("camera.snap", "Capture Photo")}
              >
                <div className="w-full h-full rounded-full bg-primary group-hover:scale-105 transition-transform flex items-center justify-center text-primary-foreground shadow-md">
                  <Camera size={22} />
                </div>
              </button>

              {/* Right Slot: Flip Camera Button */}
              <div className="w-24 flex items-center justify-end">
                {hasMultipleCameras && (
                  <button
                    onClick={toggleFacingMode}
                    disabled={isLoading || !!cameraError}
                    className="p-2.5 rounded-xl border border-border bg-muted hover:bg-muted/80 text-foreground transition-all flex items-center gap-1.5 text-xs font-semibold"
                    title={t("camera.switch", "Flip Camera")}
                  >
                    <RotateCw size={18} />
                  </button>
                )}
              </div>
            </div>
          ) : (
            /* Review / Confirmation Action Controls */
            <div className="flex items-center justify-between gap-3">
              <button
                onClick={handleRetake}
                className="flex-1 px-4 py-2.5 rounded-xl border border-border bg-muted/60 hover:bg-muted text-foreground text-xs font-bold transition-all flex items-center justify-center gap-2"
              >
                <RefreshCw size={15} />
                {t("camera.retake", "Retake Photo")}
              </button>

              <button
                onClick={handleConfirm}
                className="flex-1 px-5 py-2.5 rounded-xl bg-primary hover:brightness-110 text-primary-foreground text-xs font-extrabold transition-all flex items-center justify-center gap-2 shadow-md shadow-primary/20"
              >
                <Sparkles size={15} />
                {t("camera.use_photo", "Use Photo & Run AI")}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
