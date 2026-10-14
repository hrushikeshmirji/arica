import React, { useState, useRef, useCallback, useEffect } from "react"
import { Layers, Columns, Scan, Eye, Sliders } from "lucide-react"
import { YoloBoundingBox } from "../types/api"

interface XaiSplitViewerProps {
  originalUrl: string
  attentionMapUrl?: string
  yoloBoxes?: YoloBoundingBox[]
  diseaseLabel?: string
  confidence?: number
}

type ViewMode = "split" | "attention" | "yolo" | "original"

export default function XaiSplitViewer({
  originalUrl,
  attentionMapUrl,
  yoloBoxes = [],
  diseaseLabel,
  confidence,
}: XaiSplitViewerProps) {
  const [mode, setMode] = useState<ViewMode>(() => {
    if (attentionMapUrl) return "split"
    if (yoloBoxes.length > 0) return "yolo"
    return "original"
  })

  useEffect(() => {
    if (attentionMapUrl) {
      setMode("split")
    } else if (yoloBoxes.length > 0) {
      setMode("yolo")
    } else {
      setMode("original")
    }
  }, [attentionMapUrl, yoloBoxes.length])
  const [splitPos, setSplitPos] = useState<number>(52)
  const [showBoxesInSplit, setShowBoxesInSplit] = useState<boolean>(true)
  const [heatmapOpacity, setHeatmapOpacity] = useState<number>(0.85)
  const containerRef = useRef<HTMLDivElement>(null)
  const isDraggingRef = useRef<boolean>(false)

  const updateSplitFromClientX = useCallback((clientX: number) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const rel = ((clientX - rect.left) / Math.max(rect.width, 1)) * 100
    setSplitPos(Math.max(4, Math.min(96, rel)))
  }, [])

  const handlePointerDown = (e: React.PointerEvent) => {
    if (mode !== "split") return
    isDraggingRef.current = true
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
    updateSplitFromClientX(e.clientX)
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDraggingRef.current || mode !== "split") return
    updateSplitFromClientX(e.clientX)
  }

  const handlePointerUp = () => {
    isDraggingRef.current = false
  }

  return (
    <div className="space-y-3">
      {/* Mode Control Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 bg-muted/30 p-2 rounded-xl border border-border">
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => setMode("split")}
            disabled={!attentionMapUrl}
            className={`px-2.5 py-1.5 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all ${
              mode === "split"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-card disabled:opacity-40"
            }`}
          >
            <Columns size={13} />
            <span>XAI Curtain Split</span>
          </button>

          <button
            type="button"
            onClick={() => setMode("attention")}
            disabled={!attentionMapUrl}
            className={`px-2.5 py-1.5 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all ${
              mode === "attention"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-card disabled:opacity-40"
            }`}
          >
            <Layers size={13} />
            <span>ViT Rollout Map</span>
          </button>

          <button
            type="button"
            onClick={() => setMode("yolo")}
            className={`px-2.5 py-1.5 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all ${
              mode === "yolo"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-card"
            }`}
          >
            <Scan size={13} />
            <span>Detections ({yoloBoxes.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setMode("original")}
            className={`px-2.5 py-1.5 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all ${
              mode === "original"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-card"
            }`}
          >
            <Eye size={13} />
            <span>Raw Specimen</span>
          </button>
        </div>

        {/* Contextual Controls */}
        <div className="flex items-center gap-3">
          {(mode === "split" || mode === "attention") && (
            <label className="flex items-center gap-1.5 text-[11px] text-muted-foreground cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showBoxesInSplit}
                onChange={(e) => setShowBoxesInSplit(e.target.checked)}
                className="rounded accent-primary"
              />
              <span>Overlay Boxes</span>
            </label>
          )}

          {mode === "attention" && (
            <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <Sliders size={12} className="text-primary" />
              <input
                type="range"
                min={0.2}
                max={1}
                step={0.05}
                value={heatmapOpacity}
                onChange={(e) => setHeatmapOpacity(parseFloat(e.target.value))}
                className="w-20 accent-primary"
              />
            </div>
          )}
        </div>
      </div>

      {/* Interactive Viewport */}
      <div
        ref={containerRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        className={`relative w-full h-80 sm:h-96 rounded-2xl overflow-hidden bg-black/95 border border-border shadow-inner select-none ${
          mode === "split" ? "cursor-ew-resize" : ""
        }`}
      >
        {/* Base Layer: Original Specimen Image */}
        <img
          src={originalUrl}
          alt="Areca Specimen"
          draggable={false}
          className="w-full h-full object-contain pointer-events-none"
        />

        {/* Split Mode Layer: Clipped Attention Rollout Heatmap on the Right Side */}
        {mode === "split" && attentionMapUrl && (
          <>
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                clipPath: `inset(0 0 0 ${splitPos}%)`,
              }}
            >
              <img
                src={attentionMapUrl}
                alt="ViT 12-Head Attention Rollout"
                draggable={false}
                className="w-full h-full object-contain"
              />
            </div>

            {/* Draggable Vertical Curtain Divider Line & Handle */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-white/90 shadow-[0_0_12px_rgba(16,185,129,0.9)] pointer-events-none z-20"
              style={{ left: `${splitPos}%` }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-primary text-primary-foreground border-2 border-white shadow-lg flex items-center justify-center">
                <Columns size={14} />
              </div>
            </div>

            {/* Corner Badges */}
            <div className="absolute top-3 left-3 px-2.5 py-1 rounded-md bg-black/70 backdrop-blur-md text-white text-[10px] font-bold tracking-wider uppercase border border-white/15 pointer-events-none z-10">
              Raw Specimen
            </div>
            <div className="absolute top-3 right-3 px-2.5 py-1 rounded-md bg-primary/90 backdrop-blur-md text-primary-foreground text-[10px] font-bold tracking-wider uppercase border border-white/20 pointer-events-none z-10">
              ViT-B/16 Self-Attention Rollout
            </div>
          </>
        )}

        {/* Full Attention Rollout Mode OR YOLO fallback when no boxes */}
        {((mode === "attention") || (mode === "yolo" && yoloBoxes.length === 0)) && attentionMapUrl && (
          <img
            src={attentionMapUrl}
            alt="ViT Attention Rollout"
            draggable={false}
            style={{ opacity: mode === "yolo" ? 0.85 : heatmapOpacity }}
            className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity"
          />
        )}

        {/* When YOLO mode has no detections */}
        {mode === "yolo" && yoloBoxes.length === 0 && (
          <div className="absolute top-4 inset-x-0 flex justify-center pointer-events-none z-20">
            <div className="px-3.5 py-1.5 rounded-lg bg-black/85 backdrop-blur-md text-amber-300 text-xs font-semibold border border-amber-500/30 shadow-lg">
              {attentionMapUrl ? "No localized lesion; showing ViT attention map" : "No localized lesion candidates detected"}
            </div>
          </div>
        )}

        {/* Bounding Boxes Layer (YOLOv8 Candidate Detection) */}
        {(mode === "yolo" || ((mode === "split" || mode === "attention") && showBoxesInSplit)) &&
          yoloBoxes.map((box, idx) => (
            <div
              key={`${box.label}-${idx}`}
              style={{
                top: box.top,
                left: box.left,
                width: box.width,
                height: box.height,
                borderColor: box.color || "#10b981",
              }}
              className="absolute border-2 rounded-lg pointer-events-none transition-all shadow-[0_0_15px_rgba(0,0,0,0.4)] z-10"
            >
              <span
                style={{ backgroundColor: box.color || "#10b981" }}
                className="absolute -top-6 left-0 px-2 py-0.5 rounded text-[10px] font-extrabold text-white whitespace-nowrap shadow-md"
              >
                {box.label}
              </span>
            </div>
          ))}

        {/* Bottom Telemetry Legend Bar */}
        <div className="absolute bottom-2.5 inset-x-3 flex items-center justify-between px-3 py-1.5 rounded-xl bg-black/70 backdrop-blur-md border border-white/10 text-[11px] text-white/90 pointer-events-none z-20">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="font-semibold">
              {mode === "split"
                ? "Drag curtain slider left/right to compare specimen morphology with neural attention"
                : mode === "attention"
                ? "Chroma-Guided 12-Head CLS Attention Rollout"
                : mode === "yolo"
                ? yoloBoxes.length > 0
                  ? `${yoloBoxes.length} Candidate Region(s) Localized`
                  : attentionMapUrl
                  ? "No localized lesion; showing ViT attention map"
                  : "No localized lesion candidates detected"
                : "Raw Unprocessed RGB Input"}
            </span>
          </div>
          {diseaseLabel && (
            <span className="hidden sm:inline font-mono font-bold text-primary">
              {diseaseLabel} {confidence ? `(${confidence.toFixed(1)}%)` : ""}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
