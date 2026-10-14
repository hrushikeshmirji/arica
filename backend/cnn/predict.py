"""
cnn/predict.py — Inference helper for Stage-1 EfficientNet-B0 binary gate.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Union

import cv2
import numpy as np
import torch
from PIL import Image

_HERE = str(Path(__file__).resolve().parent.parent)
import sys; sys.path.insert(0, _HERE)

from cnn.dataset import CNN_CLASSES, get_gate_preprocessing
from cnn.model import CNNClassifier
from config import CNN_CHECKPOINT, CNN_IMG_SIZE, DEVICE

ImageInput = Union[str, Path, Image.Image, np.ndarray]

# Calibrated thresholds for field & internet arecanut images vs non-arecanut OOD
GATE_ACCEPT_THRESHOLD = 0.6500
GATE_REJECT_THRESHOLD = 0.4000


class CNNPredictor:
    """Load a trained EfficientNet-B0 checkpoint and classify one image."""

    def __init__(self, checkpoint_path: str | Path | None = None) -> None:
        self.device  = DEVICE
        self.classes = list(CNN_CLASSES)
        ckpt = Path(checkpoint_path or CNN_CHECKPOINT)
        if not ckpt.is_file():
            raise FileNotFoundError(
                f"CNN checkpoint not found: {ckpt}\n"
                "Run  python cnn/train.py  first."
            )
        self.model = CNNClassifier(num_classes=len(self.classes), pretrained=False).to(self.device)
        state = torch.load(ckpt, map_location=self.device, weights_only=False)
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        self.model.load_state_dict(state, strict=True)
        self.model.eval()
        self._tf = get_gate_preprocessing(CNN_IMG_SIZE)

    # ------------------------------------------------------------------
    @staticmethod
    def _to_pil(image: ImageInput) -> Image.Image:
        if isinstance(image, (str, Path)):
            with Image.open(str(image)) as img:
                return img.convert("RGB")
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        if isinstance(image, np.ndarray):
            if image.ndim == 2:
                return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_GRAY2RGB))
            if image.ndim == 3 and image.shape[2] == 4:
                return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_RGBA2RGB))
            if image.ndim == 3 and image.shape[2] == 3:
                return Image.fromarray(image)
        raise TypeError(f"Unsupported image type: {type(image)}")

    @torch.inference_mode()
    def predict(self, image: ImageInput) -> tuple[str, float]:
        """Return ``(label, confidence)`` using shared PIL preprocessing and single score."""
        pil_img = self._to_pil(image)
        w, h = pil_img.size

        # Multi-crop tensors using shared PIL preprocessing
        t_full = self._tf(pil_img)
        cw, ch = int(w * 0.75), int(h * 0.75)
        cx, cy = (w - cw) // 2, (h - ch) // 2
        center_img = pil_img.crop((cx, cy, cx + cw, cy + ch)) if (cw >= 32 and ch >= 32) else pil_img
        t_center = self._tf(center_img)

        batch = torch.stack([t_full, t_center], dim=0).to(self.device)
        probs_batch = self.model.predict_proba(batch)
        full_prob = float(probs_batch[0, 0].item())
        center_prob = float(probs_batch[1, 0].item())
        areca_score = (full_prob + center_prob) / 2.0

        if areca_score >= GATE_ACCEPT_THRESHOLD:
            return "Arecanut", areca_score
        elif areca_score < GATE_REJECT_THRESHOLD:
            gate_score = float(1.0 - areca_score)
            return "Not_Arecanut", gate_score
        else:
            return "Gatekeeper_Uncertain", areca_score

    @torch.inference_mode()
    def predict_all_probs(self, image: ImageInput) -> dict[str, float]:
        """Return a dict mapping each class name to its probability."""
        label, conf = self.predict(image)
        if label == "Not_Arecanut":
            return {"Arecanut": round(1.0 - conf, 4), "Not_Arecanut": round(conf, 4)}
        elif label == "Gatekeeper_Uncertain":
            return {"Arecanut": round(conf, 4), "Not_Arecanut": round(1.0 - conf, 4), "Uncertain": 1.0}
        return {"Arecanut": round(conf, 4), "Not_Arecanut": round(1.0 - conf, 4)}


def main() -> None:
    parser = argparse.ArgumentParser(description="CNN Stage-1 inference")
    parser.add_argument("--image",      required=True, help="Path to image")
    parser.add_argument("--checkpoint", default=None,  help="Optional checkpoint path")
    args = parser.parse_args()
    label, conf = CNNPredictor(args.checkpoint).predict(args.image)
    print(f"Prediction : {label}\nConfidence : {conf:.2%}")


if __name__ == "__main__":
    main()
