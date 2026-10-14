"""
train_disease_classifier.py — Calibrate and fine-tune Stage-3 ViT-B/16 classifier
on D:\dataset_raw\dataset_raw disease classes (Anthracnose, FruitRot, SootyMold, NutCracking, Healthy).
Maintains exact 11-class compatibility with config.DISEASE_CLASSES and attention hooks.
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
from torchvision import transforms
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import config
from vit.model import ViTClassifier

# Seed
torch.manual_seed(42)
np.random.seed(42)
random.seed(42)

RAW_DIR = r"D:\dataset_raw\dataset_raw"
CATEGORY_TO_DISEASE = {
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "areca_healthy": "Healthy",
    "areca_diseased_physiological_nut_cracking": "NutCracking",
    "areca_diseased_fungal_sooty_mold": "SootyMold",
}

CHECKPOINT_PATH = config.VIT_CHECKPOINT
BACKUP_PATH = os.path.join(config.VIT_MODEL_DIR, "vit_b16_backup.pth")

class DiseaseDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples = samples  # list of (path, class_idx)
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

def get_splits(val_ratio=0.2):
    class_to_idx = {name: i for i, name in enumerate(config.DISEASE_CLASSES)}
    train_samples, val_samples = [], []

    for cat_folder, disease_name in CATEGORY_TO_DISEASE.items():
        cls_idx = class_to_idx[disease_name]
        files = glob.glob(os.path.join(RAW_DIR, cat_folder, "*"))
        random.shuffle(files)
        n_val = int(len(files) * val_ratio)
        val_f = files[:n_val]
        train_f = files[n_val:]
        train_samples.extend([(f, cls_idx) for f in train_f])
        val_samples.extend([(f, cls_idx) for f in val_f])
        print(f"Class '{disease_name:12s}' (idx {cls_idx:2d}): {len(train_f)} train, {len(val_f)} val")

    random.shuffle(train_samples)
    random.shuffle(val_samples)
    print(f"\nTotal: {len(train_samples)} train, {len(val_samples)} val")
    return train_samples, val_samples

def train_disease_classifier(epochs=35, lr=5e-4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[Stage-3 Disease Classifier] Using device: {device}")

    train_samples, val_samples = get_splits(val_ratio=0.2)

    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    train_ds = DiseaseDataset(train_samples, transform=train_tf)
    val_ds = DiseaseDataset(val_samples, transform=val_tf)

    train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=16, shuffle=False)

    # Load ViT model
    model = ViTClassifier(num_classes=len(config.DISEASE_CLASSES), pretrained=False, freeze_backbone=True).to(device)
    if os.path.exists(CHECKPOINT_PATH):
        state = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=True)
        if "model_state_dict" in state:
            state = state["model_state_dict"]
        model.load_state_dict(state, strict=True)
        print(f"[ViT] Loaded existing weights from {CHECKPOINT_PATH}")

    # Unfreeze head and last transformer block for fine-tuning
    model.unfreeze_last_n_blocks(1)
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[ViT] Trainable parameters (Block 11 + Head): {trainable_params:,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0

    print("\nStarting Fine-tuning...")
    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            train_correct += (preds == targets).sum().item()
            train_total += targets.size(0)

        scheduler.step()
        train_acc = train_correct / train_total

        # Validate
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        y_true, y_pred = [], []

        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * inputs.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == targets).sum().item()
                val_total += targets.size(0)
                y_true.extend(targets.cpu().numpy())
                y_pred.extend(preds.cpu().numpy())

        val_acc = val_correct / val_total
        dt = time.time() - t0

        if epoch % 5 == 0 or val_acc > best_val_acc:
            print(f"Epoch {epoch:2d}/{epochs} ({dt:.1f}s) | Train Loss: {train_loss/train_total:.4f} Acc: {train_acc:.2%} | Val Acc: {val_acc:.2%}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            # Backup
            if os.path.exists(CHECKPOINT_PATH) and not os.path.exists(BACKUP_PATH):
                shutil.copy2(CHECKPOINT_PATH, BACKUP_PATH)
                print(f"[Backup] Saved original checkpoint to {BACKUP_PATH}")

            torch.save({"model_state_dict": model.state_dict(), "val_acc": val_acc}, CHECKPOINT_PATH)
            print(f"  >>> Checkpoint Saved with Val Acc: {val_acc:.2%}")

    print("\n" + "=" * 60)
    print("FINAL STAGE-3 ViT EVALUATION REPORT")
    print("=" * 60)

    # Evaluate best saved model
    best_ckpt = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=True)
    if "model_state_dict" in best_ckpt:
        model.load_state_dict(best_ckpt["model_state_dict"])
    model.eval()

    y_true, y_pred = [], []
    with torch.no_grad():
        for inputs, targets in val_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            y_true.extend(targets.cpu().numpy())
            y_pred.extend(preds.cpu().numpy())

    present_classes = sorted(list(set(y_true)))
    target_names = [config.DISEASE_CLASSES[i] for i in present_classes]
    print("\nClassification Report on Validation Split:")
    print(classification_report(y_true, y_pred, labels=present_classes, target_names=target_names, digits=4))

if __name__ == "__main__":
    train_disease_classifier(epochs=30, lr=3e-4)
