"""
backend/train_clean_vit.py — Train clean ViT-B/16 classifier on leak-free dataset_clean_v1.
Stage 1: Linear probe / head training (frozen backbone).
Stage 2: Top-block fine-tuning with class-weighted cross-entropy and cosine annealing.
"""

import os
import sys
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import timm

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

import config
from vit.model import ViTClassifier

DATA_DIR = os.path.join(REPO_ROOT, "backend", "data", "dataset_clean_v1")
TRAIN_DIR = os.path.join(DATA_DIR, "train")
VAL_DIR = os.path.join(DATA_DIR, "val")
CHECKPOINTS_DIR = os.path.join(REPO_ROOT, "backend", "vit", "checkpoints")
os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
BEST_CKPT_PATH = os.path.join(CHECKPOINTS_DIR, "vit_b16_clean_v1.pth")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

# 1. Transforms
train_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomCrop(224),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.5),
    transforms.RandomRotation(degrees=15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

train_dataset = datasets.ImageFolder(TRAIN_DIR, transform=train_transform)
val_dataset = datasets.ImageFolder(VAL_DIR, transform=val_transform)

print(f"Train samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")
print(f"Classes found: {train_dataset.classes}")
assert train_dataset.classes == config.DISEASE_CLASSES, f"Class mismatch: {train_dataset.classes} != {config.DISEASE_CLASSES}"

# 2. Compute class weights for imbalanced CrossEntropyLoss
class_counts = torch.zeros(len(train_dataset.classes))
for _, label in train_dataset.samples:
    class_counts[label] += 1

total_samples = len(train_dataset)
num_classes = len(train_dataset.classes)
class_weights = total_samples / (num_classes * class_counts)
class_weights = class_weights / class_weights.mean() # normalize
class_weights = class_weights.to(DEVICE)
print("\nClass weights:")
for cname, w in zip(train_dataset.classes, class_weights):
    print(f"  {cname:<22}: count={int(class_counts[train_dataset.classes.index(cname)]):<3} | weight={w.item():.2f}")

criterion = nn.CrossEntropyLoss(weight=class_weights)

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=0)
val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=0)

# 3. Initialize Model
print("\nLoading ViT-B/16 with ImageNet pretrained backbone...")
model = ViTClassifier(num_classes=num_classes, pretrained=True, freeze_backbone=True)
model = model.to(DEVICE)

def evaluate(epoch_num=0):
    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0
    per_class_correct = torch.zeros(num_classes)
    per_class_total = torch.zeros(num_classes)
    
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item() * images.size(0)
            
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            
            for p, l in zip(preds, labels):
                per_class_total[l] += 1
                if p == l:
                    per_class_correct[l] += 1
                    
    avg_loss = val_loss / total
    acc = correct / total
    return avg_loss, acc, per_class_correct, per_class_total

# ---------------------------------------------------------------------------
# Stage 1: Warmup Classifier Head (Frozen Backbone) — 10 Epochs
# ---------------------------------------------------------------------------
print("\n" + "="*70)
print("STAGE 1: WARMUP CLASSIFIER HEAD (10 Epochs)")
print("="*70)

head_params = list(model.model.head.parameters())
optimizer_stage1 = torch.optim.AdamW(head_params, lr=1e-3, weight_decay=1e-2)

best_val_acc = 0.0
best_val_loss = float("inf")

for epoch in range(1, 11):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    t0 = time.time()
    
    for images, labels in train_loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        optimizer_stage1.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer_stage1.step()
        
        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
        
    train_loss = running_loss / total
    train_acc = correct / total
    v_loss, v_acc, pc_c, pc_t = evaluate(epoch)
    elapsed = time.time() - t0
    
    print(f"Epoch {epoch:02d}/10 | Train Loss: {train_loss:.4f} Acc: {train_acc*100:.1f}% | Val Loss: {v_loss:.4f} Acc: {v_acc*100:.1f}% | {elapsed:.1f}s")
    
    if v_acc > best_val_acc or (v_acc == best_val_acc and v_loss < best_val_loss):
        best_val_acc = v_acc
        best_val_loss = v_loss
        torch.save(model.state_dict(), BEST_CKPT_PATH)

# ---------------------------------------------------------------------------
# Stage 2: Fine-Tuning Top 2 Blocks + Head — 10 Epochs
# ---------------------------------------------------------------------------
print("\n" + "="*70)
print("STAGE 2: FINE-TUNING TOP TRANSFORMER BLOCKS (10 Epochs)")
print("="*70)

# Unfreeze blocks 10 and 11, plus norm
for name, p in model.model.named_parameters():
    if "blocks.10" in name or "blocks.11" in name or "norm." in name or "head." in name:
        p.requires_grad = True
    else:
        p.requires_grad = False

tunable_params = [p for p in model.parameters() if p.requires_grad]
print(f"Tunable parameters in Stage 2: {sum(p.numel() for p in tunable_params):,}")

optimizer_stage2 = torch.optim.AdamW([
    {"params": [p for n, p in model.model.named_parameters() if ("blocks." in n or "norm." in n) and p.requires_grad], "lr": 5e-5},
    {"params": list(model.model.head.parameters()), "lr": 2e-4}
], weight_decay=1e-2)

scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_stage2, T_max=10, eta_min=1e-6)

for epoch in range(1, 11):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    t0 = time.time()
    
    for images, labels in train_loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        optimizer_stage2.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(tunable_params, max_norm=1.0)
        optimizer_stage2.step()
        
        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
        
    scheduler.step()
    train_loss = running_loss / total
    train_acc = correct / total
    v_loss, v_acc, pc_c, pc_t = evaluate(epoch)
    elapsed = time.time() - t0
    
    fr_idx = train_dataset.classes.index("FruitRot")
    nc_idx = train_dataset.classes.index("NutCracking")
    fr_acc = (pc_c[fr_idx] / pc_t[fr_idx] * 100).item() if pc_t[fr_idx] > 0 else 0
    nc_acc = (pc_c[nc_idx] / pc_t[nc_idx] * 100).item() if pc_t[nc_idx] > 0 else 0
    
    print(f"Epoch {epoch:02d}/10 | Train Loss: {train_loss:.4f} Acc: {train_acc*100:.1f}% | Val Loss: {v_loss:.4f} Acc: {v_acc*100:.1f}% (FR: {fr_acc:.0f}%, NC: {nc_acc:.0f}%) | {elapsed:.1f}s")
    
    if v_acc > best_val_acc or (v_acc == best_val_acc and v_loss < best_val_loss):
        best_val_acc = v_acc
        best_val_loss = v_loss
        torch.save(model.state_dict(), BEST_CKPT_PATH)
        print(f"  [+] Saved new best checkpoint with Val Acc: {best_val_acc*100:.2f}% (Val Loss: {best_val_loss:.4f})")

print("\n" + "="*70)
print(f"TRAINING COMPLETE! Best Validation Accuracy: {best_val_acc*100:.2f}%")
print(f"Saved Checkpoint: {BEST_CKPT_PATH}")
print("="*70)

# Compute and save clean prototypes
print("\nComputing prototypes on clean dataset...")
model.load_state_dict(torch.load(BEST_CKPT_PATH))
model.eval()
prototypes = torch.zeros(num_classes, 768).to(DEVICE)
counts = torch.zeros(num_classes).to(DEVICE)

with torch.no_grad():
    for images, labels in train_loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        feats = model.model.forward_features(images)
        pre = model.model.forward_head(feats, pre_logits=True)
        pre_norm = pre / (torch.norm(pre, dim=1, keepdim=True) + 1e-8)
        for i, l in enumerate(labels):
            prototypes[l] += pre_norm[i]
            counts[l] += 1

for c in range(num_classes):
    if counts[c] > 0:
        prototypes[c] /= counts[c]
        prototypes[c] /= (torch.norm(prototypes[c]) + 1e-8)

proto_path = os.path.join(CHECKPOINTS_DIR, "vit_class_prototypes.pt")
torch.save(prototypes.cpu(), proto_path)
print(f"Saved prototypes to {proto_path}")
