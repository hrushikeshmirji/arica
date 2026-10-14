"""
train_gate.py — Train Stage-1 EfficientNet-B0 binary gate (Arecanut vs Not_Arecanut)
using D:\dataset_raw\dataset_raw with balanced sampling and validation metrics.
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
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import models, transforms
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

# Seed for reproducibility
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

class GateDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples = samples  # list of (path, label) where 0=Arecanut, 1=Not_Arecanut
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            with Image.open(path) as img:
                img_rgb = img.convert("RGB")
        except Exception:
            img_rgb = Image.new("RGB", (224, 224), color=(0, 0, 0))

        if self.transform:
            tensor = self.transform(img_rgb)
        else:
            tensor = transforms.ToTensor()(img_rgb)
        return tensor, label

def get_data_splits(val_ratio=0.2):
    areca_files = []
    for cat in ARECA_CATS:
        areca_files.extend(glob.glob(os.path.join(RAW_DIR, cat, "*")))
    
    non_areca_files = glob.glob(os.path.join(RAW_DIR, NON_ARECA_CAT, "*"))

    random.shuffle(areca_files)
    random.shuffle(non_areca_files)

    n_areca_val = int(len(areca_files) * val_ratio)
    n_non_val = int(len(non_areca_files) * val_ratio)

    areca_val = areca_files[:n_areca_val]
    areca_train = areca_files[n_areca_val:]

    non_val = non_areca_files[:n_non_val]
    non_train = non_areca_files[n_non_val:]

    train_samples = [(f, 0) for f in areca_train] + [(f, 1) for f in non_train]
    val_samples = [(f, 0) for f in areca_val] + [(f, 1) for f in non_val]

    random.shuffle(train_samples)
    random.shuffle(val_samples)

    print(f"Train set: {len(areca_train)} Arecanut, {len(non_train)} Not_Arecanut (Total: {len(train_samples)})")
    print(f"Val set  : {len(areca_val)} Arecanut, {len(non_val)} Not_Arecanut (Total: {len(val_samples)})")

    return train_samples, val_samples

def build_model(num_classes=2, dropout=0.3):
    weights = models.EfficientNet_B0_Weights.DEFAULT
    model = models.efficientnet_b0(weights=weights)
    in_features = model.classifier[1].in_features

    # Custom head matching cnn.model.CNNClassifier architecture
    model.classifier = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=dropout * 0.5),
        nn.Linear(512, num_classes),
    )
    return model

def train_gate(epochs=6, batch_size=32, lr=1e-3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[Stage-1 Training] Using device: {device}")

    train_samples, val_samples = get_data_splits(val_ratio=0.2)

    # Balanced sampler for training to avoid majority class bias
    train_labels = [s[1] for s in train_samples]
    class_counts = np.bincount(train_labels)
    class_weights = 1.0 / class_counts
    sample_weights = [class_weights[l] for l in train_labels]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_samples), replacement=True)

    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(degrees=20),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_ds = GateDataset(train_samples, transform=train_transform)
    val_ds = GateDataset(val_samples, transform=val_transform)

    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    model = build_model(num_classes=2).to(device)

    # Freeze backbone initially, train head
    for param in model.features.parameters():
        param.requires_grad = False

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    best_areca_recall = 0.0

    print("\nStarting Training (Head Warmup)...")
    for epoch in range(1, epochs + 1):
        if epoch == 3:
            print("[Info] Unfreezing top backbone blocks for fine-tuning...")
            # Unfreeze the last 2 stages of features
            for block in model.features[-3:]:
                for param in block.parameters():
                    param.requires_grad = True
            optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr * 0.2, weight_decay=1e-4)

        t0 = time.time()
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == targets).sum().item()
            total += targets.size(0)

        scheduler.step()
        train_loss = running_loss / total
        train_acc = correct / total

        # Evaluate on validation set
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        y_true = []
        y_pred = []
        y_scores = []

        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * inputs.size(0)
                probs = torch.softmax(outputs, dim=1)
                _, preds = torch.max(outputs, 1)

                val_correct += (preds == targets).sum().item()
                val_total += targets.size(0)
                y_true.extend(targets.cpu().numpy())
                y_pred.extend(preds.cpu().numpy())
                y_scores.extend(probs[:, 0].cpu().numpy())  # Arecanut prob

        val_loss = val_loss / val_total
        val_acc = val_correct / val_total
        dt = time.time() - t0

        # Arecanut recall (class 0 recall)
        cm = confusion_matrix(y_true, y_pred)
        # cm[0][0] = true arecanut predicted arecanut, cm[0][1] = arecanut predicted non-areca
        areca_recall = cm[0][0] / max(1, (cm[0][0] + cm[0][1]))
        non_recall = cm[1][1] / max(1, (cm[1][1] + cm[1][0]))

        print(f"Epoch {epoch}/{epochs} ({dt:.1f}s) | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.2%} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.2%} | "
              f"Areca Recall: {areca_recall:.2%} Non-Areca Recall: {non_recall:.2%}")

        # Save if balanced performance improves
        if (areca_recall >= 0.90 and val_acc > best_val_acc) or (areca_recall > best_areca_recall and val_acc >= 0.90):
            best_val_acc = val_acc
            best_areca_recall = areca_recall
            
            # Backup old checkpoint if exists
            if os.path.exists(CHECKPOINT_PATH) and not os.path.exists(BACKUP_PATH):
                shutil.copy2(CHECKPOINT_PATH, BACKUP_PATH)
                print(f"[Backup] Saved prior checkpoint to {BACKUP_PATH}")

            # Save state dict
            torch.save({"model_state_dict": model.state_dict(), "val_acc": val_acc, "areca_recall": areca_recall}, CHECKPOINT_PATH)
            print(f"  >>> Saved Best Checkpoint! Val Acc: {val_acc:.2%}, Areca Recall: {areca_recall:.2%}")

    print("\n" + "=" * 60)
    print("FINAL STAGE-1 GATE EVALUATION REPORT")
    print("=" * 60)
    
    # Reload best checkpoint to evaluate
    best_ckpt = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=True)
    if "model_state_dict" in best_ckpt:
        model.load_state_dict(best_ckpt["model_state_dict"])
    model.eval()

    y_true, y_pred, y_scores = [], [], []
    with torch.no_grad():
        for inputs, targets in val_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            probs = torch.softmax(outputs, dim=1)
            _, preds = torch.max(outputs, 1)
            y_true.extend(targets.numpy())
            y_pred.extend(preds.cpu().numpy())
            y_scores.extend(probs[:, 0].cpu().numpy())

    cm = confusion_matrix(y_true, y_pred)
    target_names = ["Arecanut", "Not_Arecanut"]
    print("\nConfusion Matrix:")
    print(f"                Predicted Arecanut | Predicted Non-Areca")
    print(f"Actual Arecanut      {cm[0][0]:12d}  |  {cm[0][1]:15d}")
    print(f"Actual Non-Areca     {cm[1][0]:12d}  |  {cm[1][1]:15d}")

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=target_names, digits=4))

if __name__ == "__main__":
    train_gate(epochs=6, batch_size=32, lr=1e-3)
