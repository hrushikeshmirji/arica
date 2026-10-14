"""
fast_train_vit.py — Fast, high-accuracy calibration of Stage-3 ViT-B/16 classifier
on D:\dataset_raw\dataset_raw arecanut disease classes.
Extracts backbone representations via forward_head(pre_logits=True) to match
exact inference representations, then trains the classification head.
"""
import glob
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
from sklearn.metrics import classification_report, confusion_matrix
from torchvision import transforms

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import config
from vit.model import ViTClassifier

torch.manual_seed(42)
np.random.seed(42)
random.seed(42)

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

def extract_vit_features(model, file_list, label_idx, tf, batch_size=16):
    feats, labels = [], []
    model.eval()

    for i in range(0, len(file_list), batch_size):
        batch_files = file_list[i : i + batch_size]
        tensors = []
        for f in batch_files:
            try:
                with Image.open(f) as img:
                    tensors.append(tf(img.convert("RGB")))
            except Exception:
                tensors.append(torch.zeros(3, 224, 224))

        batch_t = torch.stack(tensors)
        with torch.no_grad():
            feat = model.model.forward_features(batch_t)
            pre_head = model.model.forward_head(feat, pre_logits=True)
        feats.append(pre_head)
        labels.extend([label_idx] * len(batch_files))

    return torch.cat(feats, dim=0), torch.tensor(labels, dtype=torch.long)

def main():
    print("=" * 60)
    print("STAGE 3 ViT-B/16 DISEASE CLASSIFIER CALIBRATION")
    print("=" * 60)

    class_to_idx = {name: i for i, name in enumerate(config.DISEASE_CLASSES)}
    val_ratio = 0.2

    train_files_by_class = {}
    val_files_by_class = {}

    for cat_folder, disease_name in CATEGORY_TO_DISEASE.items():
        cls_idx = class_to_idx[disease_name]
        files = glob.glob(os.path.join(RAW_DIR, cat_folder, "*"))
        random.shuffle(files)
        n_val = int(len(files) * val_ratio)
        val_files_by_class[cls_idx] = files[:n_val]
        train_files_by_class[cls_idx] = files[n_val:]
        print(f"  Class '{disease_name:12s}' (idx {cls_idx:2d}): {len(files)-n_val} train, {n_val} val")

    tf_base = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    tf_aug1 = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    tf_aug2 = transforms.Compose([
        transforms.Resize((240, 240)),
        transforms.CenterCrop((224, 224)),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    print("\nLoading ViT-B/16 architecture...")
    model = ViTClassifier(num_classes=len(config.DISEASE_CLASSES), pretrained=False)
    # Check if a backup checkpoint or legacy checkpoint exists
    source_ckpt = BACKUP_PATH if os.path.exists(BACKUP_PATH) else CHECKPOINT_PATH
    if os.path.exists(source_ckpt):
        state = torch.load(source_ckpt, map_location="cpu", weights_only=False)
        if "model_state_dict" in state:
            state = state["model_state_dict"]
        model.load_state_dict(state, strict=True)
        print(f"[ViT] Loaded backbone weights from {source_ckpt}")

    print("Extracting ViT features with pre_logits=True (Base + 2 Augmentations)...")
    t0 = time.time()
    train_feats, train_lbls = [], []
    for cls_idx, files in train_files_by_class.items():
        # Base
        xf0, yf0 = extract_vit_features(model, files, cls_idx, tf_base)
        train_feats.append(xf0)
        train_lbls.append(yf0)
        # Aug 1 (Flip)
        xf1, yf1 = extract_vit_features(model, files, cls_idx, tf_aug1)
        train_feats.append(xf1)
        train_lbls.append(yf1)
        # Aug 2 (Crop & Jitter)
        xf2, yf2 = extract_vit_features(model, files, cls_idx, tf_aug2)
        train_feats.append(xf2)
        train_lbls.append(yf2)

    X_train = torch.cat(train_feats, dim=0)
    y_train = torch.cat(train_lbls, dim=0)

    val_feats, val_lbls = [], []
    for cls_idx, files in val_files_by_class.items():
        xf, yf = extract_vit_features(model, files, cls_idx, tf_base)
        val_feats.append(xf)
        val_lbls.append(yf)

    X_val = torch.cat(val_feats, dim=0)
    y_val = torch.cat(val_lbls, dim=0)

    print(f"Extracted {X_train.shape[0]} train features and {X_val.shape[0]} val features in {time.time()-t0:.1f}s.")

    # Train Classifier Head: model.model.head
    head = model.model.head

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=60)

    best_val_acc = 0.0
    best_head_state = None

    print("\nTraining ViT Head on extracted features (60 epochs)...")
    batch_size = 32
    n_batches = int(np.ceil(X_train.size(0) / batch_size))

    for epoch in range(1, 61):
        head.train()
        perm = torch.randperm(X_train.size(0))
        X_train_shuff = X_train[perm]
        y_train_shuff = y_train[perm]

        total_loss = 0.0
        for b in range(n_batches):
            xb = X_train_shuff[b*batch_size : (b+1)*batch_size]
            yb = y_train_shuff[b*batch_size : (b+1)*batch_size]

            optimizer.zero_grad()
            out = head(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()

        # Validate
        head.eval()
        with torch.no_grad():
            val_out = head(X_val)
            val_preds = torch.argmax(val_out, dim=1)
            val_acc = (val_preds == y_val).float().mean().item()

        if epoch % 10 == 0 or val_acc > best_val_acc:
            print(f"Epoch {epoch:2d}/60 | Loss: {total_loss/n_batches:.4f} | Val Acc: {val_acc:.2%}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_head_state = {k: v.cpu().clone() for k, v in head.state_dict().items()}

    # Assign best head
    if best_head_state is not None:
        model.model.head.load_state_dict(best_head_state)

    # Save calibrated weights
    torch.save({"model_state_dict": model.state_dict(), "val_acc": best_val_acc}, CHECKPOINT_PATH)
    print(f"\n[Checkpoints] Saved calibrated ViT-B/16 checkpoint to {CHECKPOINT_PATH} with Val Acc: {best_val_acc:.2%}")

    # Final Evaluation Report
    present_indices = sorted(list(train_files_by_class.keys()))
    head.eval()
    with torch.no_grad():
        final_out = head(X_val)
        final_preds = torch.argmax(final_out, dim=1)

    cm = confusion_matrix(y_val.numpy(), final_preds.numpy(), labels=present_indices)
    target_names = [config.DISEASE_CLASSES[i] for i in present_indices]
    print("\n" + "=" * 60)
    print("STAGE 3 FINAL VALIDATION CONFUSION MATRIX")
    print("=" * 60)
    print(f"{'Class':<14} | " + " | ".join([f"{name[:6]:>6}" for name in target_names]))
    print("-" * 60)
    for i, name in enumerate(target_names):
        row_str = " | ".join([f"{cm[i][j]:6d}" for j in range(len(target_names))])
        print(f"{name:<14} | {row_str}")

    print("\nClassification Report on Validation Split:")
    print(classification_report(y_val.numpy(), final_preds.numpy(), labels=present_indices, target_names=target_names, digits=4))

if __name__ == "__main__":
    main()
