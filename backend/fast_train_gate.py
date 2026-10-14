"""
fast_train_gate.py — Fast, robust feature-cached training for Stage-1 EfficientNet-B0
Precomputes backbone embeddings, then trains the classification head with class weighting
to eliminate negative bias and guarantee high Arecanut recall and high Non-Arecanut rejection.
"""
import os
import sys
import glob
import random
import time
import shutil
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix

torch.manual_seed(42)
np.random.seed(42)
random.seed(42)

RAW_DIR = r"D:\dataset_raw\dataset_raw"
ARECA_CATS = [
    "areca_diseased_fungal_anthracnose",
    "areca_diseased_fungal_fruit_rot",
    "areca_diseased_fungal_sooty_mold",
    "areca_diseased_physiological_nut_cracking",
    "areca_healthy"
]
NON_ARECA_CAT = "non_areca"

CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cnn", "checkpoints")
CHECKPOINT_PATH = os.path.join(CHECKPOINT_DIR, "cnn_efficientnet_b0.pth")
BACKUP_PATH = os.path.join(CHECKPOINT_DIR, "cnn_efficientnet_b0_backup.pth")

from cnn.model import CNNClassifier

def build_efficientnet_b0():
    return CNNClassifier(num_classes=2, pretrained=True, dropout=0.30)

def extract_features(model, file_list, label_val, tf, batch_size=32):
    features_list = []
    labels_list = []

    model.eval()
    backbone = nn.Sequential(model.backbone.features, model.backbone.avgpool)

    # Process in batches
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
            feat = backbone(batch_t)
            feat = torch.flatten(feat, 1)  # [B, 1280]
        features_list.append(feat)
        labels_list.extend([label_val] * len(batch_files))

    all_features = torch.cat(features_list, dim=0)
    all_labels = torch.tensor(labels_list, dtype=torch.long)
    return all_features, all_labels

def main():
    print("=" * 60)
    print("STAGE 1 GATEKEEPER TRAINING (EFFICIENTNET-B0)")
    print("=" * 60)

    # 1. Collect file paths
    areca_files = []
    for cat in ARECA_CATS:
        areca_files.extend(glob.glob(os.path.join(RAW_DIR, cat, "*")))
    
    non_areca_files = glob.glob(os.path.join(RAW_DIR, NON_ARECA_CAT, "*"))

    random.shuffle(areca_files)
    random.shuffle(non_areca_files)

    # Balance: 349 areca, 600 representative non-areca (plus holdout)
    selected_non_areca = non_areca_files[:700]

    val_ratio = 0.2
    n_areca_val = int(len(areca_files) * val_ratio)
    n_non_val = int(len(selected_non_areca) * val_ratio)

    areca_train = areca_files[n_areca_val:]
    areca_val = areca_files[:n_areca_val]

    non_train = selected_non_areca[n_non_val:]
    non_val = selected_non_areca[:n_non_val]

    print(f"Arecanut files    : {len(areca_train)} train, {len(areca_val)} val")
    print(f"Non-Arecanut files: {len(non_train)} train, {len(non_val)} val")

    from cnn.dataset import get_gate_preprocessing
    tf = get_gate_preprocessing(224)

    print("\nLoading pretrained EfficientNet-B0 backbone...")
    model = build_efficientnet_b0()

    print("Extracting feature embeddings for training split...")
    t0 = time.time()
    feat_areca_tr, lbl_areca_tr = extract_features(model, areca_train, 0, tf)
    feat_non_tr, lbl_non_tr = extract_features(model, non_train, 1, tf)

    # Combine and shuffle
    X_train = torch.cat([feat_areca_tr, feat_non_tr], dim=0)
    y_train = torch.cat([lbl_areca_tr, lbl_non_tr], dim=0)
    perm = torch.randperm(X_train.size(0))
    X_train, y_train = X_train[perm], y_train[perm]

    print(f"Extracting validation embeddings (elapsed: {time.time()-t0:.1f}s)...")
    feat_areca_val, lbl_areca_val = extract_features(model, areca_val, 0, tf)
    feat_non_val, lbl_non_val = extract_features(model, non_val, 1, tf)

    X_val = torch.cat([feat_areca_val, feat_non_val], dim=0)
    y_val = torch.cat([lbl_areca_val, lbl_non_val], dim=0)

    print(f"Extracted {X_train.shape[0]} train features and {X_val.shape[0]} val features.")

    # Train Classifier Head
    head = model.backbone.classifier
    
    # Class weights to balance Arecanut (0) vs Non-Arecanut (1)
    counts = np.bincount(y_train.numpy())
    class_weights = torch.tensor([1.0 / counts[0], 1.0 / counts[1]], dtype=torch.float)
    class_weights = class_weights / class_weights.sum()
    print(f"Class counts: {counts}, Normalized weights: {class_weights.tolist()}")

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=40)

    best_areca_recall = 0.0
    best_acc = 0.0
    best_head_state = None

    print("\nTraining Gatekeeper Head (40 epochs)...")
    batch_size = 32
    n_batches = int(np.ceil(X_train.size(0) / batch_size))

    for epoch in range(1, 41):
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

        # Validation
        head.eval()
        with torch.no_grad():
            val_out = head(X_val)
            val_preds = torch.argmax(val_out, dim=1)
            val_acc = (val_preds == y_val).float().mean().item()

            cm = confusion_matrix(y_val.numpy(), val_preds.numpy())
            areca_rec = cm[0][0] / (cm[0][0] + cm[0][1])
            non_rec = cm[1][1] / (cm[1][1] + cm[1][0])

        if epoch % 5 == 0 or epoch == 40 or areca_rec >= 0.95:
            print(f"Epoch {epoch:2d}/40 | Loss: {total_loss/n_batches:.4f} | Val Acc: {val_acc:.2%} | Areca Recall: {areca_rec:.2%} | Non-Areca Recall: {non_rec:.2%}")

        if (areca_rec >= 0.94 and val_acc >= best_acc) or (areca_rec > best_areca_recall and val_acc >= 0.90):
            best_areca_recall = areca_rec
            best_acc = val_acc
            best_head_state = {k: v.cpu().clone() for k, v in head.state_dict().items()}

    # Assign best head back to model
    if best_head_state is not None:
        model.backbone.classifier.load_state_dict(best_head_state)

    # Backup prior checkpoint if exists
    if os.path.exists(CHECKPOINT_PATH) and not os.path.exists(BACKUP_PATH):
        shutil.copy2(CHECKPOINT_PATH, BACKUP_PATH)
        print(f"\n[Backup] Backed up previous checkpoint to {BACKUP_PATH}")

    # Save full state dict
    torch.save({"model_state_dict": model.state_dict(), "val_acc": float(best_acc), "areca_recall": float(best_areca_recall)}, CHECKPOINT_PATH)
    print(f"[Checkpoints] Saved calibrated Stage-1 model to {CHECKPOINT_PATH}")

    # Final Evaluation Report
    head.eval()
    with torch.no_grad():
        final_out = head(X_val)
        final_preds = torch.argmax(final_out, dim=1)

    cm = confusion_matrix(y_val.numpy(), final_preds.numpy())
    print("\n" + "=" * 60)
    print("STAGE 1 FINAL VALIDATION CONFUSION MATRIX")
    print("=" * 60)
    print(f"                 Predicted Arecanut | Predicted Non-Areca")
    print(f"Actual Arecanut       {cm[0][0]:12d}  |  {cm[0][1]:15d}")
    print(f"Actual Non-Areca      {cm[1][0]:12d}  |  {cm[1][1]:15d}")
    print("\nClassification Report:")
    print(classification_report(y_val.numpy(), final_preds.numpy(), target_names=["Arecanut", "Not_Arecanut"], digits=4))

if __name__ == "__main__":
    main()
