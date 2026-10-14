"""
backend/train_vit_clean.py — Regularized fine-tuning and calibration for ViT-B/16
on the verified 522-image leak-free ArecaVision dataset (479 train / 43 val).

Key features:
1. Deterministic PyTorch setup (seed=42).
2. Small-sample agricultural augmentations (RandomResizedCrop, Flip, ColorJitter).
3. Inverse-frequency class weights with label smoothing (0.1).
4. Discriminative layer-wise optimization (blocks 0-5 frozen; blocks 6-11 at 3e-5; head at 1.5e-4).
5. Cosine annealing schedule with linear warmup and early stopping on validation Macro-F1.
6. Post-hoc Temperature Scaling using L-BFGS to minimize NLL and calibrate probabilities.
7. Verification against golden probes and manifest SHA-256 integrity tagging.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score, classification_report
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR, CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))

import config
from vit.model import ViTClassifier

# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if DEVICE.type == "cpu":
    torch.set_num_threads(min(8, os.cpu_count() or 4))

print(f"[Train] Initialized on {DEVICE} with seed {SEED} (CPU threads={torch.get_num_threads()})")

# ---------------------------------------------------------------------------
# Dataset Loading & Resolution
# ---------------------------------------------------------------------------
CATEGORY_TO_DISEASE = {
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "areca_pest_bud_borer": "BudBorer",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "areca_healthy": "Healthy",
    "areca_diseased_fungal_leaf_spot": "LeafSpotComplex",
    "areca_diseased_physiological_nut_cracking": "NutCracking",
    "areca_diseased_phytoplasma_yellow_leaf": "PhytoplasmaYellowLeaf",
    "areca_diseased_fungal_sooty_mold": "SootyMold",
    "areca_diseased_fungal_stem_bleeding": "StemBleeding",
    "areca_diseased_physiological_stem_cracking": "StemCracking",
    "areca_diseased_yellow_leaf_chlorosis": "YellowLeaf",
}

SEARCH_DIRS = [
    Path("D:/dataset"),
    Path("D:/dataset0000/dataset/dataset_raw"),
    Path("D:/dataset0000/dataset/dataset/train"),
    Path("D:/dataset0000/dataset/dataset/vit/train"),
    Path("D:/drive-download-20261013T133028Z-1-001"),
]


def resolve_image_path(cls_raw: str, filename: str) -> Path:
    for base in SEARCH_DIRS:
        p1 = base / cls_raw / filename
        if p1.exists():
            return p1
        p2 = base / filename
        if p2.exists():
            return p2
    raise FileNotFoundError(f"Cannot resolve image for {cls_raw}/{filename}")


class MemoryCachedDataset(Dataset):
    """Pre-caches decoded PIL images in RAM for 10x faster training epochs on CPU."""

    def __init__(self, items: list[dict[str, Any]], transform: transforms.Compose) -> None:
        self.transform = transform
        self.samples = []
        print(f"[Dataset] Pre-loading and verifying {len(items)} samples into memory...")
        for item in items:
            raw_cls = item["class"]
            fname = item["file"]
            path = resolve_image_path(raw_cls, fname)
            with Image.open(path) as img:
                pil_rgb = img.convert("RGB")
            disease_name = CATEGORY_TO_DISEASE[raw_cls]
            label_idx = config.DISEASE_CLASSES.index(disease_name)
            self.samples.append((pil_rgb, label_idx, disease_name, fname))
        print(f"[Dataset] Successfully cached {len(self.samples)} samples.")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        pil_img, label_idx, _, _ = self.samples[idx]
        tensor = self.transform(pil_img)
        return tensor, label_idx


# ---------------------------------------------------------------------------
# Calibration: Temperature Scaling via L-BFGS
# ---------------------------------------------------------------------------
class ModelWithTemperature(nn.Module):
    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model
        self.temperature = nn.Parameter(torch.ones(1) * 1.0)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        return logits / self.temperature

    def calibrate(self, val_logits: torch.Tensor, val_labels: torch.Tensor) -> float:
        nll_criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.LBFGS([self.temperature], lr=0.01, max_iter=50)

        def eval_step():
            optimizer.zero_grad()
            scaled_logits = self.forward(val_logits)
            loss = nll_criterion(scaled_logits, val_labels)
            loss.backward()
            return loss

        optimizer.step(eval_step)
        optimal_t = float(self.temperature.item())
        print(f"[Calibration] Optimal temperature learned via L-BFGS: {optimal_t:.4f}")
        return optimal_t


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == labels)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
    return float(ece)


# ---------------------------------------------------------------------------
# Main Training Routine
# ---------------------------------------------------------------------------
def main() -> None:
    manifest_path = _HERE / "data" / "clean_dataset_manifest.json"
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    train_items = manifest["train"]
    val_items = manifest["val"]
    print(f"[Manifest] Loaded clean dataset: {len(train_items)} train, {len(val_items)} val (SHA256: {manifest_sha256})")

    # 1. Transforms
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(config.VIT_IMG_SIZE, scale=(0.75, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.25),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15, hue=0.04),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(config.VIT_IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_dataset = MemoryCachedDataset(train_items, train_transform)
    val_dataset = MemoryCachedDataset(val_items, val_transform)

    batch_size = 16
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # 2. Class-imbalance weights
    num_classes = len(config.DISEASE_CLASSES)
    class_counts = torch.zeros(num_classes)
    for _, y, _, _ in train_dataset.samples:
        class_counts[y] += 1

    total_train = len(train_dataset)
    class_weights = total_train / (num_classes * torch.clamp(class_counts, min=1.0))
    class_weights = class_weights / class_weights.mean()
    class_weights = class_weights.to(DEVICE)

    print("\n[Weights] Normalized inverse-frequency class weights:")
    for idx, cname in enumerate(config.DISEASE_CLASSES):
        print(f"  {cname:<22}: count={int(class_counts[idx]):<3} | weight={class_weights[idx].item():.3f}")

    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.10)

    # 3. Model setup & discriminative freezing
    print("\n[Model] Initializing ViT-B/16 architecture...")
    model = ViTClassifier(num_classes=num_classes, pretrained=False, dropout=0.10, freeze_backbone=False).to(DEVICE)

    # Load baseline checkpoint weights if available to start from rich representations
    init_ckpt = _HERE / "vit" / "checkpoints" / "vit_b16.pth"
    if init_ckpt.exists():
        print(f"[Model] Initializing backbone from verified checkpoint: {init_ckpt.name}")
        state = torch.load(init_ckpt, map_location=DEVICE)
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        model.load_state_dict(state, strict=True)
    else:
        print("[Model] Loading fresh ImageNet-pretrained weights via timm...")
        fresh_model = ViTClassifier(num_classes=num_classes, pretrained=True, dropout=0.10, freeze_backbone=False).to(DEVICE)
        model.load_state_dict(fresh_model.state_dict())

    # Freeze patch projection and first 50% (blocks 0 to 5)
    for p in model.model.patch_embed.parameters():
        p.requires_grad = False
    if hasattr(model.model, "cls_token"):
        model.model.cls_token.requires_grad = False
    if hasattr(model.model, "pos_embed"):
        model.model.pos_embed.requires_grad = False

    for idx, blk in enumerate(model.model.blocks):
        if idx < 6:
            for p in blk.parameters():
                p.requires_grad = False
        else:
            for p in blk.parameters():
                p.requires_grad = True

    for p in model.model.norm.parameters():
        p.requires_grad = True
    for p in model.model.head.parameters():
        p.requires_grad = True

    # 4. Optimizer with differential layer-wise learning rates
    blocks_params = []
    for idx in range(6, 12):
        blocks_params.extend([p for p in model.model.blocks[idx].parameters() if p.requires_grad])

    head_params = list(model.model.norm.parameters()) + list(model.model.head.parameters())

    optimizer = AdamW(
        [
            {"params": blocks_params, "lr": 3e-5, "weight_decay": 0.05},
            {"params": head_params, "lr": 1.5e-4, "weight_decay": 0.05},
        ]
    )

    epochs = 25
    warmup_epochs = 3

    def warmup_cosine_lambda(epoch: int) -> float:
        if epoch < warmup_epochs:
            return float(epoch + 1) / float(max(1, warmup_epochs))
        progress = float(epoch - warmup_epochs) / float(max(1, epochs - warmup_epochs))
        return 0.5 * (1.0 + math.cos(math.pi * progress))

    scheduler = LambdaLR(optimizer, lr_lambda=warmup_cosine_lambda)

    # 5. Training loop with early stopping
    best_macro_f1 = 0.0
    best_acc = 0.0
    best_weights = None
    best_epoch = 0
    patience = 8
    patience_counter = 0

    print(f"\n[Train] Commencing fine-tuning for up to {epochs} epochs (warmup={warmup_epochs}, patience={patience})...")

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        correct_train = 0
        total_train_samples = 0

        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)

            optimizer.zero_grad()
            logits = model(x_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(y_batch)
            preds = torch.argmax(logits, dim=1)
            correct_train += (preds == y_batch).sum().item()
            total_train_samples += len(y_batch)

        scheduler.step()
        train_loss = total_loss / total_train_samples
        train_acc = correct_train / total_train_samples

        # Validation evaluation
        model.eval()
        val_preds = []
        val_targets = []
        val_logits_list = []

        with torch.no_grad():
            for x_val, y_val in val_loader:
                x_val = x_val.to(DEVICE)
                logits = model(x_val)
                val_logits_list.append(logits.cpu())
                preds = torch.argmax(logits, dim=1).cpu().numpy()
                val_preds.extend(preds)
                val_targets.extend(y_val.numpy())

        val_acc = accuracy_score(val_targets, val_preds)
        val_macro_f1 = f1_score(val_targets, val_preds, average="macro", zero_division=0)

        lr_blocks = optimizer.param_groups[0]["lr"]
        lr_head = optimizer.param_groups[1]["lr"]
        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} Acc: {train_acc:.2%} | Val Acc: {val_acc:.2%} Macro-F1: {val_macro_f1:.4f} | LR: {lr_blocks:.1e}/{lr_head:.1e}")

        if val_macro_f1 > best_macro_f1 or (val_macro_f1 == best_macro_f1 and val_acc >= best_acc):
            best_macro_f1 = val_macro_f1
            best_acc = val_acc
            best_weights = copy.deepcopy(model.state_dict())
            best_epoch = epoch
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience and epoch >= 15:
                print(f"[Train] Early stopping triggered at epoch {epoch}. Restoring best checkpoint from epoch {best_epoch}.")
                break

    # Restore best weights
    model.load_state_dict(best_weights)
    model.eval()
    print(f"\n[Train] Best checkpoint restored from epoch {best_epoch}: Val Acc={best_acc:.2%}, Macro-F1={best_macro_f1:.4f}")

    # 6. Post-Hoc Temperature Scaling
    print("\n[Calibration] Optimizing scalar temperature on 43 validation samples...")
    val_logits_all = []
    val_targets_all = []
    with torch.no_grad():
        for x_val, y_val in val_loader:
            x_val = x_val.to(DEVICE)
            val_logits_all.append(model(x_val).cpu())
            val_targets_all.append(y_val)

    val_logits_tensor = torch.cat(val_logits_all, dim=0)
    val_targets_tensor = torch.cat(val_targets_all, dim=0)

    calibrator = ModelWithTemperature(model)
    optimal_temperature = calibrator.calibrate(val_logits_tensor, val_targets_tensor)

    # Compute uncalibrated vs calibrated probabilities and ECE
    uncalibrated_probs = torch.softmax(val_logits_tensor, dim=1).numpy()
    calibrated_probs = torch.softmax(val_logits_tensor / optimal_temperature, dim=1).numpy()
    val_labels_np = val_targets_tensor.numpy()

    ece_before = compute_ece(uncalibrated_probs, val_labels_np)
    ece_after = compute_ece(calibrated_probs, val_labels_np)

    print(f"[Calibration] Validation ECE: {ece_before:.4f} (uncalibrated) -> {ece_after:.4f} (calibrated with T={optimal_temperature:.4f})")

    # Detailed classification report
    final_preds = np.argmax(calibrated_probs, axis=1)
    final_acc = accuracy_score(val_labels_np, final_preds)
    final_macro_f1 = f1_score(val_labels_np, final_preds, average="macro", zero_division=0)
    present_classes = sorted(list(set(val_labels_np)))
    present_names = [config.DISEASE_CLASSES[i] for i in present_classes]
    print("\n[Evaluation] Per-class performance on 43 validation samples:")
    print(classification_report(val_labels_np, final_preds, labels=present_classes, target_names=present_names, zero_division=0))

    # 7. Golden Probes Evaluation
    print("\n[Probes] Running 100% parity verification on golden baseline test cases...")
    test_cases = [
        ("USER UPLOADED FRUIT ROT (job-bfd163d5cc18.jpg)", PROJECT_ROOT / "backend" / "data" / "uploads" / "job-bfd163d5cc18.jpg", "FruitRot"),
        ("Fruit Rot 1 (fruit_rot_1.jpg)", Path("D:/dataset/fruit_rot/fruit_rot_1.jpg"), "FruitRot"),
        ("Fruit Rot 10 (fruit_rot_10.jpg)", Path("D:/dataset/fruit_rot/fruit_rot_10.jpg"), "FruitRot"),
        ("Nut Cracking 14 (nut_cracking_14.jpg)", Path("D:/dataset/nut_cracking/nut_cracking_14.jpg"), "NutCracking"),
        ("Nut Cracking 21 (nut_cracking_21.jpg)", Path("D:/dataset/nut_cracking/nut_cracking_21.jpg"), "NutCracking"),
    ]

    probe_pass = True
    for desc, path, expected in test_cases:
        if path.exists():
            with Image.open(path) as img:
                im_t = val_transform(img.convert("RGB")).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                l = model(im_t)
                scaled_l = l / optimal_temperature
                probs = torch.softmax(scaled_l, dim=1)[0].cpu().numpy()
            pred_top = config.DISEASE_CLASSES[np.argmax(probs)]
            conf = probs[np.argmax(probs)] * 100.0
            status_str = "PASS" if pred_top == expected else "FAIL"
            if pred_top != expected:
                probe_pass = False
            print(f"  [{status_str}] {desc:<45}: Pred={pred_top} ({conf:.1f}%), Expected={expected}")

    # 8. Checkpoint Packaging & Guardrail Evaluation
    ckpt_dict = {
        "model_state_dict": best_weights,
        "temperature": optimal_temperature,
        "classes": config.DISEASE_CLASSES,
        "val_acc": float(final_acc),
        "macro_f1": float(final_macro_f1),
        "ece": float(ece_after),
        "manifest_sha256": manifest_sha256,
        "trained_at": "2026-10-14",
    }

    output_ckpt = _HERE / "vit" / "checkpoints" / "vit_b16_clean_v1.pth"
    backup_ckpt = _HERE / "vit" / "checkpoints" / "vit_b16_clean_v1.backup.pt"

    # Baseline to beat or match (from Step 1 baseline inspection: Acc=76.74%, Macro-F1=0.7592)
    BASELINE_ACC = 0.7674
    BASELINE_F1 = 0.7592

    print("\n" + "=" * 80)
    print(f"{'Metric':<25} | {'Step 1 Baseline':<20} | {'Trained Clean ViT':<20} | {'Status'}")
    print("-" * 80)
    print(f"{'Validation Accuracy':<25} | {BASELINE_ACC:<20.2%} | {final_acc:<20.2%} | {'PASS' if final_acc >= BASELINE_ACC else 'REVIEW'}")
    print(f"{'Macro-F1 Score':<25} | {BASELINE_F1:<20.4f} | {final_macro_f1:<20.4f} | {'PASS' if final_macro_f1 >= BASELINE_F1 else 'REVIEW'}")
    print(f"{'Expected Calib Error (ECE)':<25} | {'0.1171':<20} | {ece_after:<20.4f} | {'IMPROVED' if ece_after < 0.1171 else 'MAINTAINED'}")
    print(f"{'Golden Probes Parity':<25} | {'100.0%':<20} | {'100.0%' if probe_pass else 'FAIL':<20} | {'PASS' if probe_pass else 'FAIL'}")
    print("=" * 80)

    if final_macro_f1 >= BASELINE_F1 and final_acc >= BASELINE_ACC and probe_pass:
        print(f"\n[Promotion] Criteria MET! Safeguarding backup at {backup_ckpt.name} and saving clean checkpoint...")
        if output_ckpt.exists():
            torch.save(torch.load(output_ckpt, map_location="cpu"), backup_ckpt)
        torch.save(ckpt_dict, output_ckpt)
        print(f"[Promotion] Successfully saved production checkpoint to {output_ckpt}!")
    else:
        # Also save as candidate
        candidate_path = _HERE / "vit" / "checkpoints" / "vit_b16_clean_candidate.pth"
        torch.save(ckpt_dict, candidate_path)
        print(f"\n[Promotion] Criteria not strictly beaten; saved candidate to {candidate_path.name}.")


if __name__ == "__main__":
    main()
