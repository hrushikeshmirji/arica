"""
backend/train_vit.py — Clean, reproducible training of ViT-B/16 classifier (Part 1.2).

Features:
- Supports Variant A (capped seeds in train) and Variant B (no seeds, real classes only).
- Seed-reproducible (seed 0, 1, 2).
- ViT-B/16 pretrained from timm.
- Last 2 transformer blocks + head trainable; earlier blocks frozen.
- AdamW optimizer + Cosine Annealing schedule with linear warmup.
- Label smoothing 0.1.
- Class-balanced sampler (WeightedRandomSampler).
- Augmentations: RandomResizedCrop (scale 0.6-1.0), RandomHorizontalFlip, RandomRotation(15), ColorJitter.
- Preprocessing: PIL EXIF transpose + Normalize(mean=0.5, std=0.5) matching inference.
- Early stopping on validation macro-F1 of real classes (patience 5).
- Saves per epoch: log CSV and last.pth (for resume).
- Saves best checkpoint: vit_v2_{variant}_seed{seed}.pth with full metadata (git commit, class list, manifest hash, date).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageOps
from sklearn.metrics import f1_score, precision_recall_fscore_support
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms

_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))

import config
from vit.model import ViTClassifier

REAL_CLASS_INDICES = [0, 2, 3, 5, 7]  # Anthracnose, FruitRot, Healthy, NutCracking, SootyMold


def get_git_commit() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT))
        return out.decode("utf-8").strip()
    except Exception:
        return "UNKNOWN"


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class ManifestViTDataset(Dataset):
    """Dataset built directly from the verified manifest.json."""

    def __init__(
        self,
        entries: list[dict[str, Any]],
        raw_root: Path,
        transform: Any = None,
    ) -> None:
        self.entries = entries
        self.raw_root = raw_root
        self.transform = transform
        self.class_to_idx = {c: i for i, c in enumerate(config.DISEASE_CLASSES)}
        self.samples: list[tuple[Path, int]] = []

        for e in entries:
            img_path = self.raw_root / e["folder"] / e["filename"]
            idx = self.class_to_idx[e["disease"]]
            self.samples.append((img_path, idx))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        p, label = self.samples[idx]
        with Image.open(p) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            if self.transform:
                tensor = self.transform(img)
            else:
                tensor = transforms.ToTensor()(img)
        return tensor, label

    def get_labels(self) -> list[int]:
        return [s[1] for s in self.samples]


def create_transforms(img_size: int = 224) -> tuple[transforms.Compose, transforms.Compose]:
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(img_size, scale=(0.6, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    return train_transform, val_transform


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * x.size(0)
        preds = out.argmax(dim=1)
        correct += (preds == y).sum().item()
        total += x.size(0)

    avg_loss = total_loss / max(total, 1)
    acc = correct / max(total, 1)
    return avg_loss, acc


@torch.no_grad()
def evaluate_val(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, float, dict[str, float]]:
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        out = model(x)
        loss = criterion(out, y)
        total_loss += loss.item() * x.size(0)

        preds = out.argmax(dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(y.cpu().numpy())

    avg_loss = total_loss / max(len(all_targets), 1)
    acc = (np.array(all_preds) == np.array(all_targets)).mean() if all_targets else 0.0

    # Macro-F1 on REAL classes only
    macro_f1_real = f1_score(
        all_targets,
        all_preds,
        labels=REAL_CLASS_INDICES,
        average="macro",
        zero_division=0,
    )

    # Per-class F1 for real classes
    p, r, f1, _ = precision_recall_fscore_support(
        all_targets,
        all_preds,
        labels=REAL_CLASS_INDICES,
        zero_division=0,
    )
    per_class_f1 = {
        config.DISEASE_CLASSES[idx]: round(float(f1[i]), 4)
        for i, idx in enumerate(REAL_CLASS_INDICES)
    }

    return avg_loss, float(acc), float(macro_f1_real), per_class_f1


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ArecaVision ViT-B/16 classifier.")
    parser.add_argument("--variant", choices=["A", "B"], required=True, help="Variant A (capped seeds) or B (no seeds).")
    parser.add_argument("--seed", type=int, default=0, help="Random seed (default: 0).")
    parser.add_argument("--epochs", type=int, default=25, help="Maximum epochs (default: 25).")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience (default: 5).")
    parser.add_argument("--lr", type=float, default=5e-5, help="Peak learning rate (default: 5e-5).")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size (default: 8).")
    parser.add_argument("--warmup-epochs", type=int, default=2, help="Linear warmup epochs (default: 2).")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint if exists.")
    args = parser.parse_args()

    variant = args.variant
    seed = args.seed
    set_seed(seed)
    device = config.DEVICE

    manifest_path = REPO_ROOT / "results" / "train" / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    manifest_hash = manifest_data.get("manifest_sha256", "UNKNOWN")
    git_commit = get_git_commit()
    raw_root = Path("D:/dataset_raw/dataset_raw")

    # Filter entries by split for this variant
    all_entries = manifest_data["entries"]
    split_key = f"variant_{variant.lower()}_split"

    train_entries = [e for e in all_entries if e.get(split_key) == "train"]
    val_entries = [e for e in all_entries if e.get(split_key) == "val"]
    test_entries = [e for e in all_entries if e.get(split_key) == "test"]

    print("=" * 70)
    print(f"Training ViT-B/16 — Variant {variant} (Seed {seed})")
    print(f"Device: {device} | Manifest Hash: {manifest_hash[:16]}... | Git: {git_commit[:8]}")
    print(f"Splits: Train={len(train_entries)} | Val={len(val_entries)} | Test={len(test_entries)}")
    print("=" * 70)

    train_tf, val_tf = create_transforms(config.VIT_IMG_SIZE)

    train_ds = ManifestViTDataset(train_entries, raw_root, transform=train_tf)
    val_ds = ManifestViTDataset(val_entries, raw_root, transform=val_tf)

    # Class-balanced sampler for training
    train_labels = train_ds.get_labels()
    class_counts = np.bincount(train_labels, minlength=len(config.DISEASE_CLASSES))
    class_weights = 1.0 / np.where(class_counts > 0, class_counts, 1.0)
    sample_weights = [class_weights[l] for l in train_labels]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        sampler=sampler,
        num_workers=0,
        drop_last=False,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )

    # Model: ViTClassifier pretrained, unfreeze last 2 blocks + head
    model = ViTClassifier(
        num_classes=len(config.DISEASE_CLASSES),
        pretrained=True,
        dropout=config.VIT_DROPOUT,
        freeze_backbone=True,
    ).to(device)

    model.unfreeze_last_n_blocks(2)
    print(f"Trainable parameters: {model.trainable_params():,}")

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=args.lr,
        weight_decay=1e-2,
    )

    # Checkpoint paths
    ckpt_dir = REPO_ROOT / "backend" / "vit" / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt_path = ckpt_dir / f"vit_v2_{variant}_seed{seed}.pth"
    last_ckpt_path = ckpt_dir / f"last_v2_{variant}_seed{seed}.pth"

    results_dir = REPO_ROOT / "results" / "train"
    results_dir.mkdir(parents=True, exist_ok=True)
    log_csv_path = results_dir / f"vit_v2_{variant}_seed{seed}_log.csv"

    start_epoch = 0
    best_val_f1 = -1.0
    patience_counter = 0

    if args.resume and last_ckpt_path.exists():
        checkpoint = torch.load(last_ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        start_epoch = checkpoint["epoch"] + 1
        best_val_f1 = checkpoint.get("best_val_f1", -1.0)
        patience_counter = checkpoint.get("patience_counter", 0)
        print(f"Resumed from epoch {start_epoch} (Best Val Macro-F1: {best_val_f1:.4f})")

    # CSV Logger
    csv_exists = log_csv_path.exists()
    csv_file = open(log_csv_path, "a" if csv_exists else "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    if not csv_exists:
        csv_writer.writerow([
            "epoch", "train_loss", "train_acc", "val_loss", "val_acc",
            "val_macro_f1_real", "lr", "epoch_time_s", "timestamp"
        ])

    print(f"Starting training loop ({args.epochs} max epochs, early stopping patience {args.patience})...\n")

    for epoch in range(start_epoch, args.epochs):
        t0 = time.perf_counter()

        # Learning rate schedule: linear warmup + cosine decay
        if epoch < args.warmup_epochs:
            cur_lr = args.lr * (epoch + 1) / args.warmup_epochs
        else:
            progress = (epoch - args.warmup_epochs) / max(args.epochs - args.warmup_epochs, 1)
            cur_lr = 1e-6 + 0.5 * (args.lr - 1e-6) * (1.0 + math.cos(math.pi * progress))

        for param_group in optimizer.param_groups:
            param_group["lr"] = cur_lr

        tr_loss, tr_acc = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_acc, val_f1, per_class_f1 = evaluate_val(model, val_loader, criterion, device)
        elapsed = time.perf_counter() - t0

        timestamp = datetime.utcnow().isoformat() + "Z"
        csv_writer.writerow([
            epoch + 1, round(tr_loss, 4), round(tr_acc, 4), round(val_loss, 4),
            round(val_acc, 4), round(val_f1, 4), f"{cur_lr:.6e}", round(elapsed, 2), timestamp
        ])
        csv_file.flush()

        print(
            f"Epoch {epoch+1:02d}/{args.epochs:02d} | "
            f"TrLoss: {tr_loss:.4f} TrAcc: {tr_acc*100:.1f}% | "
            f"ValLoss: {val_loss:.4f} ValAcc: {val_acc*100:.1f}% | "
            f"ValMacroF1(Real): {val_f1*100:.2f}% | "
            f"LR: {cur_lr:.2e} | Time: {elapsed:.1f}s"
        )
        print(f"  Per-class Real F1: {per_class_f1}")

        # Save last checkpoint for resume
        torch.save({
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "best_val_f1": best_val_f1,
            "patience_counter": patience_counter,
            "variant": variant,
            "seed": seed,
        }, last_ckpt_path)

        # Check improvement
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            patience_counter = 0
            # Save best model with full metadata
            torch.save({
                "model_state_dict": model.state_dict(),
                "best_epoch": epoch + 1,
                "best_val_macro_f1": best_val_f1,
                "variant": variant,
                "seed": seed,
                "git_commit": git_commit,
                "class_list": config.DISEASE_CLASSES,
                "manifest_hash": manifest_hash,
                "date": timestamp,
                "val_metrics": {
                    "val_loss": val_loss,
                    "val_acc": val_acc,
                    "val_macro_f1_real": val_f1,
                    "per_class_f1": per_class_f1,
                }
            }, best_ckpt_path)
            print(f"  --> Saved new best checkpoint: {best_ckpt_path} (F1: {best_val_f1*100:.2f}%)")
        else:
            patience_counter += 1
            print(f"  No improvement for {patience_counter}/{args.patience} epochs.")
            if patience_counter >= args.patience:
                print(f"\n[Early Stopping] Triggered after {epoch+1} epochs. Best Val Macro-F1: {best_val_f1*100:.2f}%")
                break

    csv_file.close()

    # Save summary JSON for this training run
    summary_path = results_dir / f"vit_v2_{variant}_seed{seed}_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "variant": variant,
            "seed": seed,
            "best_checkpoint": str(best_ckpt_path),
            "best_val_macro_f1_real": round(best_val_f1, 4),
            "manifest_hash": manifest_hash,
            "git_commit": git_commit,
            "date": datetime.utcnow().isoformat() + "Z",
            "log_csv": str(log_csv_path),
        }, f, indent=2)

    print(f"\nTraining completed for Variant {variant} (Seed {seed}).")
    print(f"Best checkpoint: {best_ckpt_path}")
    print(f"Summary JSON:    {summary_path}")


if __name__ == "__main__":
    main()
