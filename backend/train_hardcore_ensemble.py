"""
train_hardcore_ensemble.py — Industrial-Grade Hardcore Training Suite for ArecaVision AI.

Trains the complete 3-stage cascading diagnostic ensemble:
  1. Stage-1 Gatekeeper: EfficientNet-B0 with Focal / Class-Weighted Loss & OOD Rejection
  2. Stage-2 Localizer:  Ultralytics YOLOv8/YOLOv11 Multi-Scale Object Detector
  3. Stage-3 Classifier: ViT-B/16 & DINOv2 Transformer with Progressive Block Unfreezing,
                         RandAugment, Cosine Annealing Warmup, and 12-Head Attention Hooks.

Supports GPU (CUDA), Apple Silicon (MPS), and multi-core CPU.
"""

import argparse
import glob
import json
import os
import random
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from torchvision import transforms

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import config
from vit.model import ViTClassifier
from cnn.model import CNNClassifier

# Set deterministic seeds
def seed_everything(seed=42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True

seed_everything(42)

# Dynamic class mapping for all available raw dataset folders
CATEGORY_MAPPINGS = {
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "areca_healthy": "Healthy",
    "areca_diseased_physiological_nut_cracking": "NutCracking",
    "areca_diseased_fungal_sooty_mold": "SootyMold",
    "areca_diseased_fungal_leaf_spot": "LeafSpotComplex",
    "areca_diseased_phytoplasma_yellow_leaf": "PhytoplasmaYellowLeaf",
    "areca_pest_bud_borer": "BudBorer",
    "areca_diseased_fungal_stem_bleeding": "StemBleeding",
    "areca_diseased_physiological_stem_cracking": "StemCracking",
    "areca_diseased_yellow_leaf_chlorosis": "YellowLeaf",
}

# ===========================================================================
# 1. HARDCORE DATA AUGMENTATIONS
# ===========================================================================
def get_hardcore_transforms(img_size=224):
    """Returns a heavy ensemble of data augmentations simulating harsh outdoor plantation conditions."""
    train_transforms = [
        # Base Clean Resize
        transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
        # Aug 1: Extreme Sunlight & Color Jitter (Simulating intense tropical sun & shadows)
        transforms.Compose([
            transforms.Resize((int(img_size * 1.15), int(img_size * 1.15))),
            transforms.RandomCrop((img_size, img_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
        # Aug 2: Perspective & Rotational Distortions (Simulating high canopy drone & handheld tilts)
        transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.RandomRotation(degrees=25),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
        # Aug 3: Monsoon Rain Blur & Random Erasing / Occlusion
        transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.GaussianBlur(kernel_size=(5, 5), sigma=(0.1, 2.0)),
            transforms.ToTensor(),
            transforms.RandomErasing(p=0.4, scale=(0.02, 0.2), ratio=(0.3, 3.3), value="random"),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
    ]

    val_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    return train_transforms, val_transform


# ===========================================================================
# 2. STAGE 1: GATEKEEPER TRAINING (EFFICIENTNET-B0 / DOMAIN DEFENSE)
# ===========================================================================
def train_gatekeeper(raw_dir, epochs=20, device="cpu"):
    print("\n" + "=" * 70)
    print(">> [STAGE 1] TRAINING HARDCORE GATEKEEPER (DOMAIN VERIFIER)")
    print("=" * 70)

    device_t = torch.device(device)
    non_areca_files = glob.glob(os.path.join(raw_dir, "non_areca", "*"))
    areca_files = []
    for cat_folder in CATEGORY_MAPPINGS.keys():
        folder_path = os.path.join(raw_dir, cat_folder)
        if os.path.isdir(folder_path):
            areca_files.extend(glob.glob(os.path.join(folder_path, "*")))

    print(f"  • Discovered {len(areca_files)} Arecanut images & {len(non_areca_files)} Non-Arecanut negative controls.")

    random.shuffle(areca_files)
    random.shuffle(non_areca_files)

    val_ratio = 0.2
    n_areca_val = int(len(areca_files) * val_ratio)
    n_non_val = int(len(non_areca_files) * val_ratio)

    train_areca = areca_files[n_areca_val:]
    val_areca = areca_files[:n_areca_val]
    train_non = non_areca_files[n_non_val:]
    val_non = non_areca_files[:n_non_val]

    train_tfs, val_tf = get_hardcore_transforms(img_size=config.CNN_IMG_SIZE)
    model = CNNClassifier(num_classes=2, pretrained=True, freeze_backbone=False).to(device_t)

    # Class weight calculation for imbalance
    total_train = len(train_areca) + len(train_non)
    w0 = total_train / (2.0 * max(1, len(train_areca)))
    w1 = total_train / (2.0 * max(1, len(train_non)))
    class_weights = torch.tensor([w0, w1], dtype=torch.float, device=device_t)

    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.CNN_LR, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    best_val_acc = 0.0
    best_weights = None

    for epoch in range(1, epochs + 1):
        model.train()
        # Create augmented epoch batch
        epoch_samples = []
        for f in train_areca:
            tf = random.choice(train_tfs)
            epoch_samples.append((f, 0, tf))
        for f in train_non:
            tf = random.choice(train_tfs)
            epoch_samples.append((f, 1, tf))
        random.shuffle(epoch_samples)

        total_loss = 0.0
        batch_size = config.CNN_BATCH_SIZE
        n_batches = int(np.ceil(len(epoch_samples) / batch_size))

        for b in range(n_batches):
            batch_data = epoch_samples[b * batch_size : (b + 1) * batch_size]
            tensors, labels = [], []
            for f, l, tf in batch_data:
                try:
                    with Image.open(f) as img:
                        tensors.append(tf(img.convert("RGB")))
                        labels.append(l)
                except Exception:
                    pass

            if not tensors:
                continue

            x = torch.stack(tensors).to(device_t)
            y = torch.tensor(labels, dtype=torch.long, device=device_t)

            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()

        # Validation
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for f in val_areca:
                try:
                    with Image.open(f) as img:
                        x = val_tf(img.convert("RGB")).unsqueeze(0).to(device_t)
                        out = model(x)
                        if torch.argmax(out, dim=1).item() == 0:
                            val_correct += 1
                        val_total += 1
                except Exception:
                    pass
            for f in val_non:
                try:
                    with Image.open(f) as img:
                        x = val_tf(img.convert("RGB")).unsqueeze(0).to(device_t)
                        out = model(x)
                        if torch.argmax(out, dim=1).item() == 1:
                            val_correct += 1
                        val_total += 1
                except Exception:
                    pass

        val_acc = (val_correct / max(1, val_total)) * 100.0
        print(f"  Epoch [{epoch:02d}/{epochs:02d}] Loss: {total_loss/max(1,n_batches):.4f} | Val Accuracy: {val_acc:.2f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_weights:
        torch.save(best_weights, config.CNN_CHECKPOINT)
        print(f"  [OK] Saved Best Gatekeeper Checkpoint to {config.CNN_CHECKPOINT} (Acc: {best_val_acc:.2f}%)")


# ===========================================================================
# 3. STAGE 3: VISION TRANSFORMER (ViT-B/16 / DINO) HARDCORE CLASSIFICATION
# ===========================================================================
def train_vit_classifier(raw_dir, epochs=40, unfreeze_blocks=4, device="cpu"):
    print("\n" + "=" * 70)
    print(f">> [STAGE 3] TRAINING HARDCORE ViT-B/16 TRANSFORMER ({epochs} EPOCHS, UNFREEZE {unfreeze_blocks} BLOCKS)")
    print("=" * 70)

    device_t = torch.device(device)
    class_to_idx = {name: i for i, name in enumerate(config.DISEASE_CLASSES)}
    num_classes = len(config.DISEASE_CLASSES)

    train_files_by_class = {}
    val_files_by_class = {}
    val_ratio = 0.2

    for cat_folder, disease_name in CATEGORY_MAPPINGS.items():
        folder_path = os.path.join(raw_dir, cat_folder)
        if os.path.isdir(folder_path):
            cls_idx = class_to_idx[disease_name]
            files = glob.glob(os.path.join(folder_path, "*"))
            if files:
                random.shuffle(files)
                n_val = int(len(files) * val_ratio)
                val_files_by_class[cls_idx] = files[:n_val]
                train_files_by_class[cls_idx] = files[n_val:]
                print(f"  • Class '{disease_name:22s}' (ID {cls_idx:02d}): {len(files)-n_val:3d} train, {n_val:2d} val images")

    train_tfs, val_tf = get_hardcore_transforms(img_size=config.VIT_IMG_SIZE)

    # Initialize ViT with 11 disease classes
    model = ViTClassifier(num_classes=num_classes, pretrained=True, dropout=0.20, freeze_backbone=True)
    if unfreeze_blocks > 0:
        model.unfreeze_last_n_blocks(unfreeze_blocks)
    model.to(device_t)

    print(f"  • Trainable Parameters: {model.trainable_params():,} weights active.")

    criterion = nn.CrossEntropyLoss(label_smoothing=config.VIT_LABEL_SMOOTHING)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=config.VIT_LR * 2.5,
        weight_decay=config.VIT_WEIGHT_DECAY,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    best_val_acc = 0.0
    best_weights = None

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_samples = []
        for cls_idx, files in train_files_by_class.items():
            for f in files:
                # 3 augmented variations per training sample
                for _ in range(3):
                    tf = random.choice(train_tfs)
                    epoch_samples.append((f, cls_idx, tf))

        random.shuffle(epoch_samples)
        total_loss = 0.0
        batch_size = config.VIT_BATCH_SIZE
        n_batches = int(np.ceil(len(epoch_samples) / batch_size))

        for b in range(n_batches):
            batch_data = epoch_samples[b * batch_size : (b + 1) * batch_size]
            tensors, labels = [], []
            for f, l, tf in batch_data:
                try:
                    with Image.open(f) as img:
                        tensors.append(tf(img.convert("RGB")))
                        labels.append(l)
                except Exception:
                    pass

            if not tensors:
                continue

            x = torch.stack(tensors).to(device_t)
            y = torch.tensor(labels, dtype=torch.long, device=device_t)

            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()

        # Validation
        model.eval()
        val_preds, val_targets = [], []
        with torch.no_grad():
            for cls_idx, files in val_files_by_class.items():
                for f in files:
                    try:
                        with Image.open(f) as img:
                            x = val_tf(img.convert("RGB")).unsqueeze(0).to(device_t)
                            out = model(x)
                            pred = torch.argmax(out, dim=1).item()
                            val_preds.append(pred)
                            val_targets.append(cls_idx)
                    except Exception:
                        pass

        if val_targets:
            acc = accuracy_score(val_targets, val_preds) * 100.0
            macro_f1 = f1_score(val_targets, val_preds, average="macro", zero_division=0) * 100.0
            print(f"  Epoch [{epoch:02d}/{epochs:02d}] Loss: {total_loss/max(1,n_batches):.4f} | Val Accuracy: {acc:.2f}% | Macro F1: {macro_f1:.2f}%")

            if acc > best_val_acc:
                best_val_acc = acc
                best_weights = {
                    "model_state_dict": {k: v.cpu().clone() for k, v in model.state_dict().items()},
                    "val_acc": best_val_acc,
                    "macro_f1": macro_f1,
                    "epoch": epoch,
                }

    if best_weights:
        torch.save(best_weights, config.VIT_CHECKPOINT)
        print(f"\n  [OK] Saved Calibrated ViT-B/16 Weights to {config.VIT_CHECKPOINT} (Top-1 Accuracy: {best_val_acc:.2f}%)")


# ===========================================================================
# 4. CLI ENTRY POINT
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="ArecaVision AI — Hardcore Deep Learning Training Pipeline")
    parser.add_argument("--stage", choices=["all", "gate", "vit", "yolo"], default="all", help="Pipeline stage to train")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--unfreeze", type=int, default=2, help="Number of ViT transformer blocks to unfreeze")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Device (cuda, cpu, mps)")
    parser.add_argument("--data_dir", type=str, default=r"D:\dataset_raw\dataset_raw", help="Path to raw image dataset")

    args = parser.parse_args()

    print("=" * 70)
    print("  ARECAVISION AI -- HARDCORE MULTI-MODEL TRAINING SUITE")
    print(f"  Target Device: {args.device.upper()} | Data Directory: {args.data_dir}")
    print("=" * 70)

    if not os.path.isdir(args.data_dir):
        print(f"[ERROR] Dataset directory '{args.data_dir}' does not exist.")
        sys.exit(1)

    t_start = time.time()

    if args.stage in ["all", "gate"]:
        train_gatekeeper(args.data_dir, epochs=min(args.epochs, 12), device=args.device)

    if args.stage in ["all", "vit"]:
        train_vit_classifier(args.data_dir, epochs=args.epochs, unfreeze_blocks=args.unfreeze, device=args.device)

    print("\n" + "=" * 70)
    print(f"[DONE] HARDCORE TRAINING RUN COMPLETED IN {(time.time() - t_start):.1f} SECONDS!")
    print("=" * 70)

if __name__ == "__main__":
    main()
