"""
train_vit_proper.py — Production-Grade Training of ViT-B/16 Disease Classifier
Trains the Stage-3 Vision Transformer classifier on real field data from D:\dataset_raw\dataset_raw.
Uses true ImageNet-21k/1k pretrained backbone, stratified train/val split, multi-augmentation
feature extraction, and AdamW + CosineAnnealing optimization with Label Smoothing.
"""
import glob
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import timm
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from torchvision import transforms

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import config

# Deterministic reproducibility
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

RAW_DIR = r"D:\dataset_raw\dataset_raw"
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

CHECKPOINT_PATH = config.VIT_CHECKPOINT
BACKUP_PATH = os.path.join(config.VIT_MODEL_DIR, "vit_b16_backup.pth")


def extract_features(model, file_list, label_idx, tf, batch_size=16):
    feats, labels = [], []
    model.eval()
    for i in range(0, len(file_list), batch_size):
        batch_files = file_list[i : i + batch_size]
        tensors = []
        for f in batch_files:
            try:
                with Image.open(f) as img:
                    tensors.append(tf(img.convert("RGB")))
            except Exception as e:
                tensors.append(torch.zeros(3, 224, 224))
        batch_t = torch.stack(tensors)
        with torch.no_grad():
            feat = model.forward_features(batch_t)
            pre = model.forward_head(feat, pre_logits=True)
        feats.append(pre.cpu())
        labels.extend([label_idx] * len(batch_files))
    return torch.cat(feats, dim=0), torch.tensor(labels, dtype=torch.long)


def main():
    print("=" * 70)
    print("  PRODUCTION TRAINING: ViT-B/16 ARECANUT DISEASE CLASSIFIER")
    print("=" * 70)

    class_to_idx = {name: i for i, name in enumerate(config.DISEASE_CLASSES)}
    num_classes = len(config.DISEASE_CLASSES)

    train_files_by_class = {}
    val_files_by_class = {}
    val_ratio = 0.20

    total_images = 0
    for cat_folder, disease_name in CATEGORY_TO_DISEASE.items():
        cls_idx = class_to_idx[disease_name]
        folder_path = os.path.join(RAW_DIR, cat_folder)
        files = glob.glob(os.path.join(folder_path, "*.*"))
        # Filter valid images
        valid_files = [
            f for f in files
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp"))
        ]
        random.shuffle(valid_files)
        n_val = max(5, int(len(valid_files) * val_ratio))
        val_files_by_class[cls_idx] = valid_files[:n_val]
        train_files_by_class[cls_idx] = valid_files[n_val:]
        total_images += len(valid_files)
        print(f"  [{disease_name:22s}] Total: {len(valid_files):2d} | Train: {len(valid_files)-n_val:2d} | Val: {n_val:2d}")

    print(f"\nTotal real field images: {total_images}")

    # Standard ImageNet normalization for ViT-B/16
    norm = transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])

    tf_base = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        norm,
    ])

    tf_aug1 = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.ToTensor(),
        norm,
    ])

    tf_aug2 = transforms.Compose([
        transforms.Resize((248, 248)),
        transforms.CenterCrop((224, 224)),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.ToTensor(),
        norm,
    ])

    tf_aug3 = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomRotation(degrees=15),
        transforms.ToTensor(),
        norm,
    ])

    print("\nLoading Pretrained ViT-B/16 (vit_base_patch16_224) via timm...")
    t0 = time.time()
    backbone = timm.create_model("vit_base_patch16_224", pretrained=True)
    backbone.eval()
    print(f"Loaded pretrained backbone in {time.time()-t0:.2f}s.")

    print("\nExtracting feature representations with 4 multi-scale augmentations...")
    t_feat = time.time()
    train_feats, train_labels = [], []
    for cls_idx, files in train_files_by_class.items():
        # Base
        xf0, yf0 = extract_features(backbone, files, cls_idx, tf_base)
        train_feats.append(xf0)
        train_labels.append(yf0)
        # Flip
        xf1, yf1 = extract_features(backbone, files, cls_idx, tf_aug1)
        train_feats.append(xf1)
        train_labels.append(yf1)
        # Crop & Jitter
        xf2, yf2 = extract_features(backbone, files, cls_idx, tf_aug2)
        train_feats.append(xf2)
        train_labels.append(yf2)
        # Rotation
        xf3, yf3 = extract_features(backbone, files, cls_idx, tf_aug3)
        train_feats.append(xf3)
        train_labels.append(yf3)

    X_train = torch.cat(train_feats, dim=0)
    y_train = torch.cat(train_labels, dim=0)

    val_feats, val_labels = [], []
    for cls_idx, files in val_files_by_class.items():
        xf, yf = extract_features(backbone, files, cls_idx, tf_base)
        val_feats.append(xf)
        val_labels.append(yf)

    X_val = torch.cat(val_feats, dim=0)
    y_val = torch.cat(val_labels, dim=0)

    print(f"Extraction completed in {time.time()-t_feat:.1f}s.")
    print(f"  Train feature shape: {X_train.shape} ({X_train.size(0)} samples)")
    print(f"  Val feature shape:   {X_val.shape} ({X_val.size(0)} samples)")

    # Build exact matching head
    in_features = 768
    head = nn.Sequential(
        nn.LayerNorm(in_features),
        nn.Dropout(p=0.20),
        nn.Linear(in_features, num_classes),
    )

    # Class weights to handle class imbalance
    class_counts = torch.bincount(y_train, minlength=num_classes).float()
    total_samples = len(y_train)
    weights = total_samples / (num_classes * torch.clamp(class_counts, min=1.0))
    weights = weights / weights.mean()

    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)
    optimizer = torch.optim.AdamW(head.parameters(), lr=1.5e-3, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80, eta_min=1e-5)

    best_val_acc = 0.0
    best_head_state = None
    best_macro_f1 = 0.0

    print("\nTraining ViT classification head for 80 epochs...")
    batch_size = 32
    n_batches = int(np.ceil(X_train.size(0) / batch_size))

    for epoch in range(1, 81):
        head.train()
        perm = torch.randperm(X_train.size(0))
        X_shuff = X_train[perm]
        y_shuff = y_train[perm]

        total_loss = 0.0
        for b in range(n_batches):
            xb = X_shuff[b * batch_size : (b + 1) * batch_size]
            yb = y_shuff[b * batch_size : (b + 1) * batch_size]

            optimizer.zero_grad()
            out = head(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()

        # Evaluate on Validation
        head.eval()
        with torch.no_grad():
            val_out = head(X_val)
            val_preds = torch.argmax(val_out, dim=1)
            val_acc = accuracy_score(y_val.numpy(), val_preds.numpy())
            val_f1 = f1_score(y_val.numpy(), val_preds.numpy(), average="macro", zero_division=0)

        if epoch % 10 == 0 or val_acc > best_val_acc:
            print(f"  Epoch {epoch:02d}/80 | Loss: {total_loss/n_batches:.4f} | Val Acc: {val_acc:.1%} | Macro F1: {val_f1:.1%}")

        if val_acc > best_val_acc or (val_acc == best_val_acc and val_f1 > best_macro_f1):
            best_val_acc = val_acc
            best_macro_f1 = val_f1
            best_head_state = {k: v.cpu().clone() for k, v in head.state_dict().items()}

    print(f"\nBest Validation Accuracy: {best_val_acc:.1%} | Macro F1: {best_macro_f1:.1%}")

    # Build the full ViTClassifier model with the pretrained backbone + best head
    from vit.model import ViTClassifier
    full_model = ViTClassifier(num_classes=num_classes, pretrained=True, dropout=0.10, freeze_backbone=False)
    # Assign the best head weights
    full_model.model.head.load_state_dict(best_head_state)

    # Save backup of previous checkpoint if it exists
    if os.path.exists(CHECKPOINT_PATH):
        import shutil
        shutil.copy2(CHECKPOINT_PATH, BACKUP_PATH)
        print(f"Backed up previous checkpoint to {BACKUP_PATH}")

    # Save the updated full model state dict
    torch.save(
        {
            "model_state_dict": full_model.state_dict(),
            "val_acc": best_val_acc,
            "macro_f1": best_macro_f1,
            "classes": config.DISEASE_CLASSES,
            "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        CHECKPOINT_PATH,
    )
    print(f"Saved optimized ViT-B/16 checkpoint to: {CHECKPOINT_PATH}")

    # Detailed Evaluation Report
    head.load_state_dict(best_head_state)
    head.eval()
    with torch.no_grad():
        final_preds = torch.argmax(head(X_val), dim=1)

    cm = confusion_matrix(y_val.numpy(), final_preds.numpy(), labels=list(range(num_classes)))
    print("\n" + "=" * 70)
    print("FINAL VALIDATION CONFUSION MATRIX")
    print("=" * 70)
    print(f"{'Class':<22} | " + " | ".join([f"{name[:4]:>4}" for name in config.DISEASE_CLASSES]))
    print("-" * 70)
    for i, name in enumerate(config.DISEASE_CLASSES):
        row = " | ".join([f"{cm[i][j]:4d}" for j in range(num_classes)])
        print(f"{name:<22} | {row}")

    print("\nPer-Class Classification Report:")
    print(classification_report(y_val.numpy(), final_preds.numpy(), target_names=config.DISEASE_CLASSES, digits=3))


if __name__ == "__main__":
    main()
