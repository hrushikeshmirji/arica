"""
pipeline/hybrid_pipeline.py — End-to-end 3-stage hybrid inference pipeline.

Stage 1 : CNN EfficientNet-B0  → Arecanut / Not_Arecanut gate
Stage 2 : YOLOv8               → Diseased region bounding boxes
Stage 3 : ViT-B/16             → Fine-grained disease classification per ROI
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Union

import cv2
import numpy as np
from PIL import Image

_HERE = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _HERE)

import config
from cnn.predict import CNNPredictor
from yolo.detect import YOLODetector
from vit.predict import ViTPredictor

ImageInput = Union[str, Path, Image.Image, np.ndarray]


class HybridPipeline:
    """Three-stage hybrid deep learning inference pipeline.

    Args:
        cnn_weights:  Path to CNN checkpoint (default: config.CNN_CHECKPOINT).
        yolo_weights: Path to YOLO weights   (default: config.YOLO_CHECKPOINT).
        vit_weights:  Path to ViT checkpoint (default: config.VIT_CHECKPOINT).
        yolo_conf:    YOLO confidence threshold.
        yolo_iou:     YOLO IoU threshold for NMS.
    """

    def __init__(
        self,
        cnn_weights:  str | None = None,
        yolo_weights: str | None = None,
        vit_weights:  str | None = None,
        yolo_conf: float = 0.25,
        yolo_iou:  float = 0.45,
    ) -> None:
        print("\n[Pipeline] Initialising …")
        self.cnn  = CNNPredictor(cnn_weights)
        self.yolo = YOLODetector(yolo_weights, conf_threshold=yolo_conf, iou_threshold=yolo_iou)
        self.vit  = ViTPredictor(vit_weights)
        print("[Pipeline] Ready.\n")

    # ------------------------------------------------------------------
    @staticmethod
    def _to_rgb(image: ImageInput) -> np.ndarray:
        if isinstance(image, (str, Path)):
            bgr = cv2.imread(str(image), cv2.IMREAD_COLOR)
            if bgr is None:
                raise FileNotFoundError(f"Cannot read: {image}")
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        if isinstance(image, Image.Image):
            return np.asarray(image.convert("RGB"))
        if isinstance(image, np.ndarray):
            if image.ndim == 2:
                return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            if image.ndim == 3 and image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            if image.ndim == 3 and image.shape[2] == 3:
                return image.copy()
            return image.copy()
        raise TypeError(f"Unsupported type: {type(image)}")

    # ------------------------------------------------------------------
    def predict(self, image_input: ImageInput) -> dict:
        """Run the full pipeline on one image.

        Returns a dict with keys:
            is_arecanut   bool
            message       str
            cnn_label     str
            cnn_conf      float
            annotated_img np.ndarray (RGB) or None
            detections    list[dict]
            inference_ms  float
        """
        t0      = time.perf_counter()
        img_rgb = self._to_rgb(image_input)

        # ── Stage 1: CNN gate ─────────────────────────────────────────
        cnn_label, cnn_conf = self.cnn.predict(img_rgb)

        if cnn_label == "Not_Arecanut":
            return {
                "is_arecanut":   False,
                "message":       "Input is not an Arecanut image.",
                "cnn_label":     cnn_label,
                "cnn_conf":      cnn_conf,
                "annotated_img": None,
                "detections":    [],
                "inference_ms":  (time.perf_counter() - t0) * 1000,
            }

        if cnn_label == "Gatekeeper_Uncertain":
            return {
                "is_arecanut":   False,
                "message":       "Gatekeeper uncertain: cannot verify whether image contains an arecanut palm with sufficient certainty.",
                "cnn_label":     cnn_label,
                "cnn_conf":      cnn_conf,
                "annotated_img": None,
                "detections":    [],
                "inference_ms":  (time.perf_counter() - t0) * 1000,
            }

        # ── Stage 2: YOLO detection ───────────────────────────────────
        yolo_dets, annotated_bgr = self.yolo.detect(img_rgb)
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

        if not yolo_dets:
            cv2.putText(
                annotated_rgb,
                "Arecanut — No disease regions detected",
                (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 0), 2, cv2.LINE_AA,
            )
            return {
                "is_arecanut":   True,
                "message":       "Arecanut confirmed. No diseased regions detected.",
                "cnn_label":     cnn_label,
                "cnn_conf":      cnn_conf,
                "annotated_img": annotated_rgb,
                "detections":    [],
                "inference_ms":  (time.perf_counter() - t0) * 1000,
            }

        # ── Stage 3: ViT per-ROI classification ──────────────────────
        final_dets: list[dict] = []
        for i, det in enumerate(yolo_dets):
            vit_label, vit_conf, attn_map = self.vit.predict(det["crop"])
            x1, y1, x2, y2 = det["box"]

            color = (0, 220, 0) if vit_label == "Healthy" else (220, 30, 30)
            cv2.rectangle(annotated_rgb, (x1, y1), (x2, y2), color, 2)
            tag = f"#{i+1} {vit_label} {vit_conf*100:.1f}%"
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated_rgb, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(annotated_rgb, tag, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            final_dets.append({
                "id":           i + 1,
                "box":          det["box"],
                "yolo_conf":    det["confidence"],
                "yolo_class":   det["class_name"],
                "vit_class":    vit_label,
                "vit_conf":     vit_conf,
                "crop":         det["crop"],
                "attention_map": attn_map,
            })

        n_diseased = sum(1 for d in final_dets if d["vit_class"] != "Healthy")
        msg = (
            f"Arecanut confirmed. {len(final_dets)} region(s) detected, "
            f"{n_diseased} diseased."
        )
        return {
            "is_arecanut":   True,
            "message":       msg,
            "cnn_label":     cnn_label,
            "cnn_conf":      cnn_conf,
            "annotated_img": annotated_rgb,
            "detections":    final_dets,
            "inference_ms":  (time.perf_counter() - t0) * 1000,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid pipeline inference")
    parser.add_argument("--image", required=True)
    args = parser.parse_args()

    pipeline = HybridPipeline()
    result   = pipeline.predict(args.image)

    print("\n" + "=" * 55)
    print("  HYBRID PIPELINE RESULT")
    print("=" * 55)
    print(f"  Message      : {result['message']}")
    print(f"  CNN label    : {result['cnn_label']}  ({result['cnn_conf']:.2%})")
    print(f"  Detections   : {len(result['detections'])}")
    print(f"  Inference    : {result['inference_ms']:.1f} ms")
    for d in result["detections"]:
        print(f"    #{d['id']} box={d['box']}  "
              f"disease={d['vit_class']} ({d['vit_conf']:.2%})")
    print("=" * 55)

    if result["annotated_img"] is not None:
        out = os.path.join(config.OUTPUT_DIR, "pipeline_output.jpg")
        cv2.imwrite(out, cv2.cvtColor(result["annotated_img"], cv2.COLOR_RGB2BGR))
        print(f"  Annotated image → {out}")


if __name__ == "__main__":
    main()
