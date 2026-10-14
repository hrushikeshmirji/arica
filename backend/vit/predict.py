"""
vit/predict.py — Inference helper for Stage-3 ViT-B/16 disease classifier.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Union

import cv2
import numpy as np
import torch
from PIL import Image

_HERE = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _HERE)

import config
from vit.dataset import get_vit_transforms
from vit.model import ViTClassifier

ImageInput = Union[str, Path, Image.Image, np.ndarray]


def compute_predictive_reliability(
    probs: torch.Tensor | np.ndarray, num_classes: int = 11
) -> dict[str, Any]:
    """Compute diagnostic reliability metrics: Normalized Shannon Entropy, Top-2 Margin, and High Certainty gating.

    1. Normalized Shannon Entropy:
       entropy = -sum(p * log(p + 1e-12)) / log(num_classes) (ranges from 0.0 certain to 1.0 uniform confusion)
    2. Top-2 Margin:
       margin = top1_prob - top2_prob
    3. is_high_certainty:
       bool(entropy < 0.45 and margin > 0.20)
    """
    if isinstance(probs, torch.Tensor):
        p = probs.detach().cpu().numpy().astype(np.float64)
    else:
        p = np.asarray(probs, dtype=np.float64)

    p = np.squeeze(p)
    p = np.clip(p, 1e-12, 1.0)
    p = p / np.sum(p)

    c = max(int(num_classes), len(p), 2)
    shannon_entropy = float(-np.sum(p * np.log(p)) / np.log(c))
    shannon_entropy = float(np.clip(shannon_entropy, 0.0, 1.0))

    sorted_p = np.sort(p)[::-1]
    top1_prob = float(sorted_p[0])
    top2_prob = float(sorted_p[1]) if len(sorted_p) > 1 else 0.0
    margin = float(top1_prob - top2_prob)

    is_high_certainty = bool(shannon_entropy < 0.45 and margin > 0.20)

    return {
        "predictive_entropy": round(shannon_entropy, 4),
        "top2_margin": round(margin, 4),
        "is_high_certainty": is_high_certainty,
        "top1_prob": round(top1_prob, 4),
        "top2_prob": round(top2_prob, 4),
    }


def predict_vit_with_tta(
    vit_model: torch.nn.Module,
    image_pil: Image.Image | np.ndarray,
    transform,
    temperature: float = 1.0,
    uncertainty_threshold: float = 0.80,
    device: torch.device | str | None = None,
) -> tuple[torch.Tensor, int]:
    """Execute Temperature-Calibrated 3-View Test-Time Augmentation (TTA).

    - Pass 1 (Fast Path): Standard transformed inference (224x224). If max(p_1) >= uncertainty_threshold,
      returns p_1 immediately with tta_views=1 (zero latency overhead on clear images).
    - Pass 2 & 3 (Borderline Field Sample Path): If max(p_1) < uncertainty_threshold:
      * View 2: Horizontal flip of input image (p_2)
      * View 3: 90% central crop resized to 224x224 (p_3)
      Ensemble: p_ensemble = 0.50 * p_1 + 0.25 * p_2 + 0.25 * p_3, returning tta_views=3.
    """
    if device is None:
        try:
            device = next(vit_model.parameters()).device
        except StopIteration:
            device = torch.device("cpu")

    if isinstance(image_pil, np.ndarray):
        rgb = ViTPredictor._to_rgb(image_pil)
    elif isinstance(image_pil, Image.Image):
        rgb = np.asarray(image_pil.convert("RGB"))
    elif isinstance(image_pil, (str, Path)):
        rgb = ViTPredictor._to_rgb(image_pil)
    else:
        raise TypeError(f"Unsupported image type: {type(image_pil)}")

    sq_rgb = ViTPredictor.letterbox_to_square(rgb)
    pil_img = Image.fromarray(sq_rgb)

    def _tf_to_tensor(img: Image.Image) -> torch.Tensor:
        if callable(transform):
            np_arr = np.asarray(img)
            # Try Albumentations named keyword 'image'
            try:
                out = transform(image=np_arr)
                if isinstance(out, dict) and "image" in out:
                    return out["image"]
                if isinstance(out, torch.Tensor):
                    return out
            except Exception:
                pass
            # Try torchvision transform
            try:
                out = transform(img)
                if isinstance(out, torch.Tensor):
                    return out
                if isinstance(out, dict) and "image" in out:
                    return out["image"]
            except Exception:
                pass
            # Try positional numpy
            try:
                out = transform(np_arr)
                if isinstance(out, torch.Tensor):
                    return out
            except Exception:
                pass
        raise ValueError("Provided transform is incompatible with image input.")

    # Pass 1: Standard transformed inference (224x224)
    t1 = _tf_to_tensor(pil_img).unsqueeze(0).to(device)
    temp = max(float(temperature), 0.05)

    with torch.no_grad():
        logits_1 = vit_model(t1)
        p_1 = torch.softmax(logits_1 / temp, dim=-1)[0]

    max_p1 = float(p_1.max().item())
    if max_p1 >= uncertainty_threshold:
        return p_1, 1

    # Pass 2: Horizontal flip
    img_flip = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
    t2 = _tf_to_tensor(img_flip).unsqueeze(0).to(device)

    # Pass 3: 90% central crop resized to 224x224
    w, h = pil_img.size
    cw, ch = max(16, int(w * 0.90)), max(16, int(h * 0.90))
    cx, cy = (w - cw) // 2, (h - ch) // 2
    img_crop = pil_img.crop((cx, cy, cx + cw, cy + ch)).resize((224, 224), Image.Resampling.BILINEAR)
    t3 = _tf_to_tensor(img_crop).unsqueeze(0).to(device)

    with torch.no_grad():
        t_23 = torch.cat([t2, t3], dim=0)
        logits_23 = vit_model(t_23)
        p_23 = torch.softmax(logits_23 / temp, dim=-1)
        p_2 = p_23[0]
        p_3 = p_23[1]

    p_ensemble = 0.50 * p_1 + 0.25 * p_2 + 0.25 * p_3
    p_ensemble = p_ensemble / (p_ensemble.sum() + 1e-12)
    return p_ensemble, 3


def extract_vit_attention_boxes(
    model: ViTClassifier,
    image_input: ImageInput,
    transform,
    orig_width: int,
    orig_height: int,
    threshold: float = 0.65,
    min_area_ratio: float = 0.015,
    device: torch.device | str | None = None,
) -> list[dict[str, Any]]:
    """Derive lesion bounding boxes directly from ViT final encoder block self-attention / spatial feature tokens.

    1. Clean forward hook on the final Transformer encoder block (extract patch token norms on 14x14 grid).
    2. Min-max normalization to [0.0, 1.0], upsample to (orig_width, orig_height) via cv2.INTER_CUBIC, threshold at 0.65.
    3. Connected components via cv2.findContours, discard noise < 1.5% area, rank by mean activation energy.
    4. Wrapped in try...except so inference never crashes.
    """
    try:
        if device is None:
            try:
                device = next(model.parameters()).device
            except StopIteration:
                device = torch.device("cpu")

        rgb = ViTPredictor._to_rgb(image_input)
        sq_img = ViTPredictor.letterbox_to_square(rgb)

        # Trigger forward pass to populate hooks if needed
        with torch.no_grad():
            if callable(transform):
                try:
                    tf_res = transform(image=sq_img)
                    t_in = tf_res["image"].unsqueeze(0).to(device)
                    _ = model(t_in)
                except Exception:
                    pass

        grid = None
        # 1. Extract patch token norms from the final encoder block tokens
        tokens = getattr(model, "get_last_tokens", lambda: None)()
        if tokens is not None and tokens.ndim == 3 and tokens.shape[1] >= 197:
            # Patch tokens: indices 1..196
            patch_tokens = tokens[0, 1:197, :]
            token_norms = torch.norm(patch_tokens, p=2, dim=-1)
            grid_size = int(np.sqrt(token_norms.shape[0]))
            grid = token_norms.reshape(grid_size, grid_size).cpu().numpy()

        # Fallback to CLS attention map if token norms unavailable
        if grid is None:
            attn = getattr(model, "get_attention_maps", lambda: None)()
            if attn is not None and attn.ndim == 4:
                cls_attn = attn[0, :, 0, 1:197].mean(dim=0)
                grid_size = int(np.sqrt(cls_attn.shape[0]))
                grid = cls_attn.reshape(grid_size, grid_size).cpu().numpy()

        if grid is None:
            return []

        # 2. Min-max normalization to [0.0, 1.0]
        g_min, g_max = float(grid.min()), float(grid.max())
        if g_max - g_min > 1e-8:
            grid_norm = (grid - g_min) / (g_max - g_min)
        else:
            grid_norm = np.zeros_like(grid)

        # Upsample to match letterboxed square, then un-pad to original aspect ratio
        h_orig, w_orig = int(orig_height), int(orig_width)
        max_dim = max(h_orig, w_orig)
        upsampled_sq = cv2.resize(grid_norm, (max_dim, max_dim), interpolation=cv2.INTER_CUBIC)

        pad_h = (max_dim - h_orig) // 2
        pad_w = (max_dim - w_orig) // 2
        act_map = upsampled_sq[pad_h : pad_h + h_orig, pad_w : pad_w + w_orig]
        act_map = cv2.resize(act_map, (w_orig, h_orig), interpolation=cv2.INTER_CUBIC)

        # Re-normalize activation map on active frame
        a_min, a_max = float(act_map.min()), float(act_map.max())
        if a_max - a_min > 1e-8:
            act_map = (act_map - a_min) / (a_max - a_min)

        # 3. Threshold at 0.65 and find connected components
        binary_mask = np.uint8(act_map >= float(threshold)) * 255
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = float(w_orig * h_orig * float(min_area_ratio))

        boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area:
                continue
            bx, by, bw, bh = cv2.boundingRect(c)
            x1, y1 = max(0, bx), max(0, by)
            x2, y2 = min(w_orig, bx + bw), min(h_orig, by + bh)
            if (x2 - x1) >= 16 and (y2 - y1) >= 16:
                roi = act_map[y1:y2, x1:x2]
                energy = float(roi.mean()) if roi.size > 0 else 0.0
                boxes.append({
                    "box": [int(x1), int(y1), int(x2), int(y2)],
                    "energy": round(energy, 4),
                    "confidence": round(energy * 100.0, 1),
                    "area_ratio": round(area / float(w_orig * h_orig), 4),
                })

        boxes.sort(key=lambda b: b["energy"], reverse=True)
        return boxes
    except Exception as exc:
        print(f"[ViT Localization] Warning: attention box extraction failed gracefully — {exc}")
        return []


class ViTPredictor:
    """Load a trained ViT-B/16 checkpoint and classify a cropped ROI."""

    def __init__(self, checkpoint_path: str | Path | None = None) -> None:
        self.device  = config.DEVICE
        self.classes = config.DISEASE_CLASSES

        ckpt = Path(checkpoint_path or config.VIT_CHECKPOINT)
        self.model = ViTClassifier(
            num_classes=len(self.classes),
            pretrained=False,
            dropout=config.VIT_DROPOUT,
            freeze_backbone=False,
        ).to(self.device)

        self.temperature = float(getattr(config, "VIT_TEMPERATURE", 1.0))
        if ckpt.is_file():
            state = torch.load(ckpt, map_location=self.device, weights_only=False)
            if isinstance(state, dict):
                if "temperature" in state:
                    try:
                        self.temperature = float(state["temperature"])
                    except Exception:
                        pass
                if "model_state_dict" in state:
                    state = state["model_state_dict"]
            self.model.load_state_dict(state, strict=True)
            print(f"[ViT] Loaded weights from {ckpt} (calibrated temperature={self.temperature:.4f})")
        else:
            print(f"[ViT] Warning: checkpoint not found at {ckpt} — using random weights.")

        self.model.temperature = self.temperature
        self.model.eval()
        _, self._tf = get_vit_transforms(config.VIT_IMG_SIZE)

        # Class prototypes for Out-of-Distribution (OOD) distance verification
        proto_path = Path(config.VIT_MODEL_DIR) / "vit_class_prototypes.pt"
        if proto_path.is_file():
            try:
                proto_obj = torch.load(proto_path, map_location=self.device, weights_only=False)
                if isinstance(proto_obj, dict) and "stacked" in proto_obj:
                    self.prototypes = proto_obj["stacked"].to(self.device)
                elif torch.is_tensor(proto_obj):
                    self.prototypes = proto_obj.to(self.device)
                else:
                    self.prototypes = None
            except Exception as e:
                print(f"[ViT] Could not load prototypes: {e}")
                self.prototypes = None
        else:
            self.prototypes = None

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
    @staticmethod
    def letterbox_to_square(img: np.ndarray, fill_value: int = 114) -> np.ndarray:
        """Pad image to a 1:1 square with neutral fill to preserve aspect ratio and avoid squashing/stretching."""
        h, w = img.shape[:2]
        if h == w:
            return img
        max_dim = max(h, w)
        pad_h = (max_dim - h) // 2
        pad_w = (max_dim - w) // 2
        top = pad_h
        bottom = max_dim - h - pad_h
        left = pad_w
        right = max_dim - w - pad_w
        return cv2.copyMakeBorder(
            img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[fill_value, fill_value, fill_value]
        )

    # ------------------------------------------------------------------
    @staticmethod
    def detect_split_panels(img: np.ndarray) -> list[np.ndarray]:
        """Detect side-by-side or stacked sub-panels commonly found in agricultural web collage images."""
        h, w = img.shape[:2]
        aspect = w / float(max(h, 1))

        # Horizontal side-by-side panels (w/h >= 1.35)
        if aspect >= 1.35:
            start_x = int(w * 0.35)
            end_x = int(w * 0.65)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.ndim == 3 else img
            col_var = np.var(gray, axis=0)
            col_mean = np.mean(gray, axis=0)
            candidates = []
            for x in range(start_x, end_x):
                if col_var[x] < 15.0 or (x > 0 and abs(col_mean[x] - col_mean[x - 1]) > 25.0):
                    candidates.append(x)
            if candidates:
                split_x = int(np.median(candidates))
                p1 = img[:, :max(split_x - 2, int(w * 0.3))]
                p2 = img[:, min(split_x + 2, int(w * 0.7)):]
                return [p1, p2]
            elif aspect >= 1.6:
                p1 = img[:, :int(w * 0.55)]
                p2 = img[:, int(w * 0.45):]
                return [p1, p2]

        # Vertical stacked panels (h/w >= 1.45)
        inv_aspect = h / float(max(w, 1))
        if inv_aspect >= 1.45:
            start_y = int(h * 0.35)
            end_y = int(h * 0.65)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.ndim == 3 else img
            row_var = np.var(gray, axis=1)
            row_mean = np.mean(gray, axis=1)
            candidates = []
            for y in range(start_y, end_y):
                if row_var[y] < 15.0 or (y > 0 and abs(row_mean[y] - row_mean[y - 1]) > 25.0):
                    candidates.append(y)
            if candidates:
                split_y = int(np.median(candidates))
                p1 = img[:max(split_y - 2, int(h * 0.3)), :]
                p2 = img[min(split_y + 2, int(h * 0.7)):, :]
                return [p1, p2]
            elif inv_aspect >= 1.7:
                p1 = img[:int(h * 0.55), :]
                p2 = img[int(h * 0.45):, :]
                return [p1, p2]

        return []

    # ------------------------------------------------------------------
    @staticmethod
    def compute_tissue_morphometrics_and_saliency(rgb: np.ndarray) -> dict:
        """Compute healthy vs chlorotic vs necrotic tissue % and isolate high-saliency lesion ROI."""
        h, w = rgb.shape[:2]
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)

        # Foreground mask (exclude pure white/black sky/background)
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]
        fg_mask = (sat > 18) & (val > 20) & (val < 248)
        fg_pixels = max(int(np.count_nonzero(fg_mask)), 1)

        hue = hsv[:, :, 0]
        l_chan, a_chan, b_chan = lab[:, :, 0], lab[:, :, 1], lab[:, :, 2]

        # Necrotic (dark brown, black, sooty, deep reddish-brown lesions)
        necrotic_mask = fg_mask & (
            ((val < 95) & (sat > 25))
            | ((a_chan > 138) & (l_chan < 145))
        )
        # Chlorotic (yellowing, pale orange-yellow stress halos)
        chlorotic_mask = fg_mask & (~necrotic_mask) & (
            ((hue >= 14) & (hue <= 34) & (sat > 45))
            | ((b_chan > 152) & (a_chan > 124))
        )
        # Healthy tissue (remaining foreground plant tissue)
        healthy_mask = fg_mask & (~necrotic_mask) & (~chlorotic_mask)

        necrotic_pct = round(float(np.count_nonzero(necrotic_mask)) / fg_pixels * 100.0, 1)
        chlorotic_pct = round(float(np.count_nonzero(chlorotic_mask)) / fg_pixels * 100.0, 1)
        healthy_pct = round(max(0.0, 100.0 - necrotic_pct - chlorotic_pct), 1)
        lesion_cov = round(min(100.0, necrotic_pct + chlorotic_pct), 1)

        # Saliency heatmap for lesion localization
        lesion_map = np.zeros((h, w), dtype=np.float32)
        lesion_map[necrotic_mask] = 1.0
        lesion_map[chlorotic_mask] = 0.65
        lesion_blur = cv2.GaussianBlur(lesion_map, (31, 31), 0)

        # Find bounding box around peak lesion cluster if lesion_cov >= 1.5%
        saliency_box = None
        saliency_crop = None
        if lesion_cov >= 1.5 and lesion_blur.max() > 0.10:
            dyn_thresh = max(0.12, min(0.35, float(lesion_blur.max() * 0.40)))
            thresh = np.uint8(lesion_blur > dyn_thresh) * 255
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                valid_cnts = [c for c in contours if cv2.contourArea(c) > (h * w * 0.005)]
                if valid_cnts:
                    largest = max(valid_cnts, key=cv2.contourArea)
                    bx, by, bw, bh = cv2.boundingRect(largest)
                    pad_x, pad_y = int(bw * 0.15), int(bh * 0.15)
                    x1, y1 = max(0, bx - pad_x), max(0, by - pad_y)
                    x2, y2 = min(w, bx + bw + pad_x), min(h, by + bh + pad_y)
                    if (x2 - x1) >= 32 and (y2 - y1) >= 32:
                        saliency_box = [int(x1), int(y1), int(x2), int(y2)]
                        saliency_crop = rgb[y1:y2, x1:x2]

        if saliency_box is None and lesion_cov >= 2.0:
            nz_y, nz_x = np.nonzero(lesion_map > 0)
            if len(nz_y) > 50:
                y1, y2 = max(0, int(nz_y.min())), min(h, int(nz_y.max()))
                x1, x2 = max(0, int(nz_x.min())), min(w, int(nz_x.max()))
                if (x2 - x1) >= 32 and (y2 - y1) >= 32:
                    saliency_box = [x1, y1, x2, y2]
                    saliency_crop = rgb[y1:y2, x1:x2]

        return {
            "healthyPct": healthy_pct,
            "chloroticPct": chlorotic_pct,
            "necroticPct": necrotic_pct,
            "lesionCoveragePct": lesion_cov,
            "saliencyBox": saliency_box,
            "saliencyCrop": saliency_crop,
            "lesionMap": lesion_blur,
        }

    # ------------------------------------------------------------------
    def _calibrate_probs(self, logits: torch.Tensor) -> torch.Tensor:
        """Apply standard temperature-scaled softmax without distorting priors, unifying Yellow Leaf nodes."""
        temp = max(float(self.temperature), 0.05)
        pyl_idx = self.classes.index("PhytoplasmaYellowLeaf") if "PhytoplasmaYellowLeaf" in self.classes else -1
        logits_adj = logits.clone()
        if pyl_idx >= 0:
            # Suppress duplicate node so Yellow Leaf is not double-counted in softmax denominator
            logits_adj[:, pyl_idx] = -1e9
        probs = torch.softmax(logits_adj / temp, dim=1)
        return probs

    # ------------------------------------------------------------------
    @torch.inference_mode()
    def predict(
        self, image: ImageInput
    ) -> tuple[str, float, np.ndarray | None]:
        """Return ``(label, confidence, attention_map_numpy)``."""
        rgb    = self.letterbox_to_square(self._to_rgb(image))
        tensor = self._tf(image=rgb)["image"].unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs  = self._calibrate_probs(logits)[0]
        conf, idx = torch.max(probs, dim=0)
        label = self.classes[idx.item()]

        attn = self.model.get_attention_maps()
        attn_np = attn[0].cpu().numpy() if attn is not None else None  # [heads, N, N]
        return label, float(conf.item()), attn_np

    @torch.inference_mode()
    def predict_tta_ensemble(
        self, image: ImageInput, yolo_crops: list[np.ndarray] | None = None
    ) -> dict:
        """Batched Multi-Crop Test-Time Augmentation (TTA) + Letterboxed Aspect Preservation + Split Panel Fusion."""
        rgb = self._to_rgb(image)
        h, w = rgb.shape[:2]
        morph = self.compute_tissue_morphometrics_and_saliency(rgb)

        # Build multi-scale crop batch: [Full Frame, Center High-Res Crop, Saliency Crop, Split Panels, YOLO Crops]
        crops_with_weights: list[tuple[np.ndarray, float]] = []

        panels = self.detect_split_panels(rgb)
        if panels:
            for pan in panels:
                crops_with_weights.append((self.letterbox_to_square(pan), 0.50))
            crops_with_weights.append((self.letterbox_to_square(rgb), 0.30))
        else:
            crops_with_weights.append((self.letterbox_to_square(rgb), 0.42))
            # High-res center 75% crop
            ch, cw = int(h * 0.75), int(w * 0.75)
            cy1, cx1 = (h - ch) // 2, (w - cw) // 2
            if ch >= 32 and cw >= 32:
                crops_with_weights.append((self.letterbox_to_square(rgb[cy1:cy1 + ch, cx1:cx1 + cw]), 0.28))

        # Saliency crop if present
        if morph["saliencyCrop"] is not None:
            crops_with_weights.append((self.letterbox_to_square(morph["saliencyCrop"]), 0.38))

        # Track where YOLO crops start in the batch so we get their labels in a single forward pass
        yolo_start_idx = len(crops_with_weights)
        valid_yolo_count = 0
        if yolo_crops:
            for y_crop in yolo_crops[:3]:
                if y_crop is not None and y_crop.size > 0:
                    crops_with_weights.append((self.letterbox_to_square(y_crop), 0.42))
                    valid_yolo_count += 1

        tensors = [self._tf(image=c)["image"] for c, _ in crops_with_weights]
        batch = torch.stack(tensors, dim=0).to(self.device)
        logits = self.model(batch)
        probs_batch = self._calibrate_probs(logits)  # [B, C]

        # Capture full-frame attention map from index 0
        attn = self.model.get_attention_maps()
        attn_np = attn[0].cpu().numpy() if attn is not None else None

        # Extract YOLO crop labels from the same batched forward pass (zero extra latency)
        yolo_crop_labels: list[str] = []
        if valid_yolo_count > 0:
            for b_i in range(yolo_start_idx, yolo_start_idx + valid_yolo_count):
                _, c_idx = torch.max(probs_batch[b_i], dim=0)
                yolo_crop_labels.append(self.classes[int(c_idx.item())])

        # Entropy-weighted fusion across all TTA crops
        weights = torch.tensor([w_val for _, w_val in crops_with_weights], device=self.device)
        entropy = -torch.sum(probs_batch * torch.log(probs_batch + 1e-8), dim=1)
        sharpness_weight = torch.exp(-1.4 * entropy) * weights
        sharpness_weight = sharpness_weight / (sharpness_weight.sum() + 1e-8)

        fused_probs = torch.sum(probs_batch * sharpness_weight.unsqueeze(1), dim=0)

        # Morphology-Guided Bayesian Consistency Calibration (gentle boost for pristine foliage)
        healthy_idx = self.classes.index("Healthy") if "Healthy" in self.classes else -1
        if morph["healthyPct"] >= 88.0 and morph["necroticPct"] < 3.0 and healthy_idx >= 0:
            fused_probs[healthy_idx] *= 1.30

        fused_probs = fused_probs / (fused_probs.sum() + 1e-8)

        conf, best_idx = torch.max(fused_probs, dim=0)
        best_label = self.classes[best_idx.item()]
        best_conf = float(conf.item())

        # Metric-Based Out-of-Distribution (OOD) Verification
        max_proto_sim = 1.0
        if self.prototypes is not None:
            try:
                feat_rep = self.model.model.forward_features(batch[0:1])
                pre_rep = self.model.model.forward_head(feat_rep, pre_logits=True)
                pre_norm = pre_rep / torch.norm(pre_rep, dim=1, keepdim=True)
                sims = torch.mm(pre_norm, self.prototypes.T)[0]
                max_proto_sim = float(sims.max().item())
            except Exception:
                max_proto_sim = 1.0

        # Flag as Out-Of-Distribution only if feature representation strongly diverges from all arecanut prototypes (<0.15)
        # AND model prediction has near-zero confidence (<0.20). Do not override valid arecanut scans.
        is_ood = (self.prototypes is not None) and (max_proto_sim < 0.15) and (best_conf < 0.20)

        # Diagnostic reliability metrics
        rel_metrics = compute_predictive_reliability(fused_probs.cpu().numpy(), num_classes=len(self.classes))

        # Weakly-Supervised ViT Attention Rollout for Lesion Localization
        vit_attn_boxes = []
        if not is_ood and best_label != "Healthy":
            vit_attn_boxes = extract_vit_attention_boxes(
                model=self.model,
                image_input=rgb,
                transform=self._tf,
                orig_width=w,
                orig_height=h,
                threshold=0.65,
                min_area_ratio=0.015,
                device=self.device,
            )

        # Top-4 differential diagnosis using true normalized probabilities
        top_vals, top_indices = torch.topk(fused_probs, k=min(4, len(self.classes)))
        differential = [
            {
                "disease": self.classes[int(i.item())],
                "probability": round(float(v.item()) * 100.0, 1),
            }
            for v, i in zip(top_vals, top_indices)
            if float(v.item()) > 0.001
        ]

        return {
            "label": "Not_Arecanut" if is_ood else best_label,
            "confidence": best_conf if not is_ood else round(max(0.88, 1.0 - max_proto_sim), 3),
            "isOOD": is_ood,
            "maxProtoSim": max_proto_sim,
            "attn_map": attn_np,
            "differential": differential,
            "yoloCropLabels": yolo_crop_labels,
            "morphometrics": {
                "healthyPct": morph["healthyPct"],
                "chloroticPct": morph["chloroticPct"],
                "necroticPct": morph["necroticPct"],
                "lesionCoveragePct": morph["lesionCoveragePct"],
            },
            "saliencyBox": morph["saliencyBox"] if not is_ood else None,
            "calibration_temperature": self.temperature,
            "predictive_entropy": rel_metrics["predictive_entropy"],
            "top2_margin": rel_metrics["top2_margin"],
            "tta_views": len(crops_with_weights),
            "is_high_certainty": rel_metrics["is_high_certainty"],
            "vitAttentionBoxes": vit_attn_boxes,
        }

    def extract_attention_boxes(
        self,
        image: ImageInput,
        orig_width: int,
        orig_height: int,
        threshold: float = 0.65,
        min_area_ratio: float = 0.015,
    ) -> list[dict[str, Any]]:
        """Extract weakly-supervised lesion bounding boxes grounded in ViT final encoder block activations."""
        return extract_vit_attention_boxes(
            model=self.model,
            image_input=image,
            transform=self._tf,
            orig_width=orig_width,
            orig_height=orig_height,
            threshold=threshold,
            min_area_ratio=min_area_ratio,
            device=self.device,
        )

    @torch.inference_mode()
    def predict_with_diagnostics(
        self, image: ImageInput, uncertainty_threshold: float = 0.80
    ) -> dict[str, Any]:
        """Run calibrated 3-view TTA, predictive entropy gating, and weakly-supervised lesion localization."""
        rgb = self._to_rgb(image)
        h, w = rgb.shape[:2]
        pil_img = Image.fromarray(rgb)

        probs, tta_views = predict_vit_with_tta(
            vit_model=self.model,
            image_pil=pil_img,
            transform=self._tf,
            temperature=self.temperature,
            uncertainty_threshold=uncertainty_threshold,
            device=self.device,
        )

        probs_np = probs.cpu().numpy()
        rel = compute_predictive_reliability(probs_np, num_classes=len(self.classes))

        conf, best_idx = torch.max(probs, dim=0)
        best_label = self.classes[int(best_idx.item())]
        best_conf = float(conf.item())

        top_vals, top_indices = torch.topk(probs, k=min(4, len(self.classes)))
        differential = [
            {
                "disease": self.classes[int(i.item())],
                "probability": round(float(v.item()) * 100.0, 1),
            }
            for v, i in zip(top_vals, top_indices)
            if float(v.item()) > 0.001
        ]

        attn_boxes = []
        if best_label != "Healthy":
            attn_boxes = self.extract_attention_boxes(rgb, orig_width=w, orig_height=h)

        attn = getattr(self.model, "get_attention_maps", lambda: None)()
        attn_np = attn[0].cpu().numpy() if attn is not None else None

        return {
            "label": best_label,
            "confidence": best_conf,
            "calibration_temperature": self.temperature,
            "predictive_entropy": rel["predictive_entropy"],
            "top2_margin": rel["top2_margin"],
            "tta_views": tta_views,
            "is_high_certainty": rel["is_high_certainty"],
            "vitAttentionBoxes": attn_boxes,
            "differential": differential,
            "attn_map": attn_np,
        }

    @torch.inference_mode()
    def predict_all_probs(self, image: ImageInput) -> dict[str, float]:
        rgb    = self.letterbox_to_square(self._to_rgb(image))
        tensor = self._tf(image=rgb)["image"].unsqueeze(0).to(self.device)
        probs  = self._calibrate_probs(self.model(tensor))[0]
        return {cls: float(probs[i].item()) for i, cls in enumerate(self.classes) if float(probs[i].item()) > 0.0001}

    # ------------------------------------------------------------------
    def get_attention_visualization(
        self, crop_rgb: np.ndarray, attn_map: np.ndarray | None
    ) -> np.ndarray:
        """Overlay Chroma-Guided Multi-Head CLS Attention Rollout heatmap on the crop."""
        h, w = crop_rgb.shape[:2]
        morph = self.compute_tissue_morphometrics_and_saliency(crop_rgb)
        lesion_prior = cv2.resize(morph["lesionMap"], (w, h), interpolation=cv2.INTER_LINEAR)

        if attn_map is not None:
            # attn_map: [heads, N, N]  N = 197 (1 CLS + 196 patches)
            cls_attn  = attn_map[:, 0, 1:]          # [heads, 196]
            # Max-mean head fusion to highlight peak diagnostic heads and suppress sink noise
            mean_attn = 0.5 * cls_attn.mean(axis=0) + 0.5 * cls_attn.max(axis=0)
            grid_size = int(np.sqrt(mean_attn.shape[0]))  # 14
            grid      = mean_attn.reshape(grid_size, grid_size)
            grid      = (grid - grid.min()) / (grid.max() - grid.min() + 1e-8)
            vit_heat  = cv2.resize(grid, (w, h), interpolation=cv2.INTER_CUBIC)
            # Fuse transformer self-attention with LAB lesion chroma saliency
            combined  = 0.58 * vit_heat + 0.42 * lesion_prior
        else:
            combined  = lesion_prior

        combined = cv2.GaussianBlur(combined, (21, 21), 0)
        combined = (combined - combined.min()) / (combined.max() - combined.min() + 1e-8)

        heatmap  = np.uint8(255 * combined)
        colored  = cv2.applyColorMap(heatmap, cv2.COLORMAP_TURBO)
        colored  = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
        return cv2.addWeighted(crop_rgb, 0.52, colored, 0.48, 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="ViT Stage-3 inference")
    parser.add_argument("--image",      required=True)
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()

    predictor = ViTPredictor(args.checkpoint)
    label, conf, attn = predictor.predict(args.image)
    print(f"Disease    : {label}")
    print(f"Confidence : {conf:.2%}")

    if attn is not None:
        img = cv2.cvtColor(cv2.imread(args.image), cv2.COLOR_BGR2RGB)
        vis = predictor.get_attention_visualization(img, attn)
        out = os.path.join(config.OUTPUT_DIR, "vit_attention.jpg")
        cv2.imwrite(out, cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
        print(f"Attention map saved → {out}")


if __name__ == "__main__":
    main()
