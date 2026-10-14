"""
vit/dataset.py — Dataset, augmentations, MixUp/CutMix for Stage-3 ViT classifier.
"""

from __future__ import annotations

import os
from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import torch
from albumentations.pytorch import ToTensorV2
from torch.utils.data import Dataset, WeightedRandomSampler

_IMG_EXTS = frozenset({".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"})
_MEAN = (0.5, 0.5, 0.5)
_STD  = (0.5, 0.5, 0.5)

# Detect albumentations version once
_ALB_VER = tuple(int(x) for x in A.__version__.split(".")[:2])
_ALB_NEW  = _ALB_VER >= (1, 4)


class ViTDataset(Dataset):
    def __init__(self, data_dir: str | Path, transform=None) -> None:
        self.data_dir  = Path(data_dir)
        self.transform = transform

        if not self.data_dir.is_dir():
            raise FileNotFoundError(f"ViT data directory not found: {self.data_dir}")

        self.classes      = sorted(
            d for d in os.listdir(self.data_dir)
            if (self.data_dir / d).is_dir()
        )
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.image_paths: list[str] = []
        self.labels:      list[int] = []

        for cls in self.classes:
            cls_dir = self.data_dir / cls
            for p in sorted(cls_dir.rglob("*")):
                if p.is_file() and p.suffix.lower() in _IMG_EXTS:
                    self.image_paths.append(str(p))
                    self.labels.append(self.class_to_idx[cls])

        if not self.image_paths:
            raise RuntimeError(f"No images found under {self.data_dir}")

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        path  = self.image_paths[idx]
        label = self.labels[idx]
        bgr   = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            bgr = np.zeros((224, 224, 3), dtype=np.uint8)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        if self.transform:
            rgb = self.transform(image=rgb)["image"]
        return rgb, label

    def make_weighted_sampler(self) -> WeightedRandomSampler:
        counts = np.bincount(self.labels, minlength=len(self.classes)).astype(float)
        w_cls  = 1.0 / np.where(counts > 0, counts, 1.0)
        w_samp = torch.tensor([w_cls[l] for l in self.labels], dtype=torch.float)
        return WeightedRandomSampler(w_samp, num_samples=len(w_samp), replacement=True)


def _make_gauss_dropout(img_size: int):
    """Return GaussNoise + CoarseDropout compatible with installed albumentations."""
    if _ALB_NEW:
        gauss   = A.GaussNoise(std_range=(0.04, 0.22), p=0.3)
        dropout = A.CoarseDropout(
            num_holes_range=(4, 8),
            hole_height_range=(10, 20),
            hole_width_range=(10, 20),
            p=0.3,
        )
    else:
        gauss   = A.GaussNoise(var_limit=(10.0, 50.0), p=0.3)
        dropout = A.CoarseDropout(max_holes=8, max_height=20, max_width=20, p=0.3)
    return gauss, dropout


def get_vit_transforms(img_size: int = 224) -> tuple[A.Compose, A.Compose]:
    _norm = [A.Normalize(mean=_MEAN, std=_STD), ToTensorV2()]
    gauss, dropout = _make_gauss_dropout(img_size)

    if _ALB_NEW:
        crop = A.RandomResizedCrop(size=(img_size, img_size), scale=(0.7, 1.0), p=0.5)
    else:
        crop = A.RandomResizedCrop(height=img_size, width=img_size, scale=(0.7, 1.0), p=0.5)

    train = A.Compose([
        A.Resize(img_size, img_size),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.2),
        A.Rotate(limit=30, border_mode=cv2.BORDER_REFLECT_101, p=0.6),
        A.RandomBrightnessContrast(brightness_limit=0.20, contrast_limit=0.20, p=0.5),
        A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=25, val_shift_limit=15, p=0.4),
        gauss,
        dropout,
        crop,
        *_norm,
    ])
    val = A.Compose([A.Resize(img_size, img_size), *_norm])
    return train, val


# ---------------------------------------------------------------------------
# MixUp / CutMix
# ---------------------------------------------------------------------------

def mixup_data(x, y, alpha=0.2, device="cpu"):
    lam   = np.random.beta(alpha, alpha) if alpha > 0 else 1.0
    idx   = torch.randperm(x.size(0), device=device)
    mixed = lam * x + (1 - lam) * x[idx]
    return mixed, y, y[idx], lam


def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)


def cutmix_data(x, y, alpha=1.0, device="cpu"):
    lam = np.random.beta(alpha, alpha)
    idx = torch.randperm(x.size(0), device=device)
    _, _, H, W = x.shape
    cut_rat = np.sqrt(1.0 - lam)
    cut_w, cut_h = int(W * cut_rat), int(H * cut_rat)
    cx, cy = np.random.randint(W), np.random.randint(H)
    x1 = max(cx - cut_w // 2, 0); x2 = min(cx + cut_w // 2, W)
    y1 = max(cy - cut_h // 2, 0); y2 = min(cy + cut_h // 2, H)
    mixed = x.clone()
    mixed[:, :, y1:y2, x1:x2] = x[idx, :, y1:y2, x1:x2]
    lam = 1 - (x2 - x1) * (y2 - y1) / (W * H)
    return mixed, y, y[idx], lam
