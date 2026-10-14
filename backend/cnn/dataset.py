"""
cnn/dataset.py — Dataset and augmentation pipeline for Stage-1 binary gate.

Expected layout:
    dataset/cnn/<split>/Arecanut/*
    dataset/cnn/<split>/Not_Arecanut/*

Class order is fixed: index 0 = Arecanut, index 1 = Not_Arecanut.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import albumentations as A
import cv2
import numpy as np
import torch
from albumentations.pytorch import ToTensorV2
from torch.utils.data import Dataset, WeightedRandomSampler

CNN_CLASSES: tuple[str, str] = ("Arecanut", "Not_Arecanut")
_IMG_EXTS = frozenset({".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"})
_MEAN = (0.485, 0.456, 0.406)
_STD  = (0.229, 0.224, 0.225)

# Albumentations ≥1.4 renamed some params — detect version once
import albumentations as _A_ver
_ALB_NEW = tuple(int(x) for x in _A_ver.__version__.split(".")[:2]) >= (1, 4)


class CNNDataset(Dataset):
    """Binary image dataset for EfficientNet-B0.

    Args:
        data_dir: Path to one split directory (e.g. ``cnn/train``).
        transform: Albumentations pipeline returning an ``image`` tensor.
        classes: Ordered class names — do not change after training.
    """

    def __init__(
        self,
        data_dir: str | Path,
        transform: Callable | None = None,
        classes: Iterable[str] = CNN_CLASSES,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.classes = tuple(classes)
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}

        if not self.data_dir.is_dir():
            raise FileNotFoundError(f"Split directory not found: {self.data_dir}")

        self.samples: list[tuple[Path, int]] = []
        for cls, idx in self.class_to_idx.items():
            cls_dir = self.data_dir / cls
            if not cls_dir.is_dir():
                raise FileNotFoundError(f"Class folder missing: {cls_dir}")
            for p in sorted(cls_dir.rglob("*")):
                if p.is_file() and p.suffix.lower() in _IMG_EXTS:
                    self.samples.append((p, idx))

        if not self.samples:
            raise RuntimeError(f"No images found under {self.data_dir}")

        self.image_paths = [str(p) for p, _ in self.samples]
        self.labels      = [lbl for _, lbl in self.samples]

    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        path, label = self.samples[index]
        bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if bgr is None:
            # Skip corrupt file — return a neighbour sample instead
            alt = (index + 1) % len(self.samples)
            path, label = self.samples[alt]
            bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if bgr is None:
                bgr = np.zeros((224, 224, 3), dtype=np.uint8)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        if self.transform is not None:
            rgb = self.transform(image=rgb)["image"]
        else:
            rgb = torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).float() / 255.0
        return rgb, label

    # ------------------------------------------------------------------
    def make_weighted_sampler(self) -> WeightedRandomSampler:
        """Return a sampler that up-samples the minority class."""
        counts = np.bincount(self.labels, minlength=len(self.classes)).astype(float)
        weights_per_class = 1.0 / np.where(counts > 0, counts, 1.0)
        sample_weights = torch.tensor(
            [weights_per_class[lbl] for lbl in self.labels], dtype=torch.float
        )
        return WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------

def get_cnn_transforms(img_size: int = 224) -> tuple[A.Compose, A.Compose]:
    """Return (train_transform, eval_transform) with ImageNet normalisation."""
    _norm = [A.Normalize(mean=_MEAN, std=_STD), ToTensorV2()]

    # GaussNoise: old API uses var_limit, new API uses std_range
    if _ALB_NEW:
        gauss = A.GaussNoise(std_range=(0.04, 0.22), p=0.3)
        dropout = A.CoarseDropout(num_holes_range=(4, 8), hole_height_range=(8, 16),
                                  hole_width_range=(8, 16), p=0.3)
    else:
        gauss = A.GaussNoise(var_limit=(10.0, 50.0), p=0.3)
        dropout = A.CoarseDropout(max_holes=8, max_height=16, max_width=16, p=0.3)

    train = A.Compose([
        A.Resize(img_size, img_size),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.2),
        A.Rotate(limit=30, border_mode=cv2.BORDER_REFLECT_101, p=0.6),
        A.RandomBrightnessContrast(brightness_limit=0.25, contrast_limit=0.25, p=0.5),
        A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10, p=0.4),
        gauss,
        dropout,
        *_norm,
    ])
    val = A.Compose([A.Resize(img_size, img_size), *_norm])
    return train, val


def get_gate_preprocessing(img_size: int = 224):
    """Canonical shared preprocessing for Stage-1 Gatekeeper: PIL resize + ImageNet normalisation."""
    from torchvision import transforms
    return transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
