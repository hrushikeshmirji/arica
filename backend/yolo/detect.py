"""
yolo/detect.py — YOLOv8 disease region detector for Stage-2.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Union

import cv2
import numpy as np
from PIL import Image

_HERE = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _HERE)

import config

ImageInput = Union[str, Path, Image.Image, np.ndarray]

# Colour palette per class index (BGR)
_PALETTE = [
    (0, 0, 255), (0, 165, 255), (0, 255, 0), (255, 0, 0),
    (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0),
    (0, 128, 255), (128, 255, 0), (255, 128, 0),
]


class YOLODetector:
    """Inference helper for the custom YOLOv8 disease region detector."""

    def __init__(
        self,
        checkpoint_path: str | Path | None = None,
        conf_threshold: float = 0.25,
        iou_threshold:  float = 0.45,
    ) -> None:
        from ultralytics import YOLO

        ckpt = Path(checkpoint_path or config.YOLO_CHECKPOINT)
        if not ckpt.is_file():
            print(f"[YOLO] Custom weights not found at {ckpt}. "
                  f"Falling back to pretrained '{config.YOLO_MODEL_NAME}'.")
            ckpt = config.YOLO_MODEL_NAME

        self.model          = YOLO(str(ckpt))
        self.conf_threshold = conf_threshold
        self.iou_threshold  = iou_threshold
        print(f"[YOLO] Model loaded from {ckpt}")

    # ------------------------------------------------------------------
    @staticmethod
    def _load_bgr(image: ImageInput) -> np.ndarray:
        if isinstance(image, (str, Path)):
            bgr = cv2.imread(str(image), cv2.IMREAD_COLOR)
            if bgr is None:
                raise FileNotFoundError(f"Cannot read: {image}")
            return bgr
        if isinstance(image, Image.Image):
            return cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        if isinstance(image, np.ndarray):
            if image.ndim == 2:
                return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            if image.ndim == 3 and image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
            if image.ndim == 3 and image.shape[2] == 3:
                return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            return image.copy()
        raise TypeError(f"Unsupported type: {type(image)}")

    # ------------------------------------------------------------------
    def detect(
        self, image: ImageInput
    ) -> tuple[list[dict], np.ndarray]:
        """Run detection and return detections + annotated BGR image.

        Returns:
            detections: list of dicts with keys
                ``box``        [x1, y1, x2, y2]
                ``confidence`` float
                ``class_id``   int
                ``class_name`` str
                ``crop``       RGB numpy array
            annotated_img: BGR numpy array with drawn boxes
        """
        img_bgr = self._load_bgr(image)
        H, W    = img_bgr.shape[:2]

        results = self.model(
            img_bgr,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False,
        )[0]

        detections: list[dict] = []
        annotated  = img_bgr.copy()

        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(W, x2), min(H, y2)
            if x2 <= x1 or y2 <= y1:
                continue

            conf    = float(box.conf[0].cpu().item())
            cls_id  = int(box.cls[0].cpu().item())
            cls_name = (
                config.DISEASE_CLASSES[cls_id]
                if cls_id < len(config.DISEASE_CLASSES)
                else f"cls_{cls_id}"
            )
            crop_bgr = img_bgr[y1:y2, x1:x2]
            crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)

            detections.append({
                "box":        [x1, y1, x2, y2],
                "confidence": conf,
                "class_id":   cls_id,
                "class_name": cls_name,
                "crop":       crop_rgb,
            })

            color = _PALETTE[cls_id % len(_PALETTE)]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"{cls_name} {conf:.2f}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - lh - 6), (x1 + lw + 2, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 1, y1 - 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        return detections, annotated


def main() -> None:
    parser = argparse.ArgumentParser(description="YOLOv8 Stage-2 inference")
    parser.add_argument("--image",      required=True)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--conf",       type=float, default=0.25)
    args = parser.parse_args()

    detector = YOLODetector(args.checkpoint, conf_threshold=args.conf)
    dets, annotated = detector.detect(args.image)
    print(f"Detected {len(dets)} region(s).")
    for i, d in enumerate(dets):
        print(f"  #{i+1}: {d['class_name']}  conf={d['confidence']:.2f}  box={d['box']}")

    out = os.path.join(config.OUTPUT_DIR, "yolo_output.jpg")
    cv2.imwrite(out, annotated)
    print(f"Annotated image saved → {out}")


if __name__ == "__main__":
    main()
