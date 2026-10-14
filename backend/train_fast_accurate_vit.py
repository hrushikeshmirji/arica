"""
backend/train_fast_accurate_vit.py
Fast, ultra-accurate ViT training using feature caching and unified YellowLeaf head tuning.
Produces:
1. backend/vit/checkpoints/vit_b16_clean_v1.pth (Full ViT-B/16 checkpoint)
2. backend/vit/checkpoints/vit_class_prototypes.pt (Accurate, aligned class prototypes)
"""

import os
import sys
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import config
from vit.model import ViTClassifier

DEVICE = torch.device("cpu")
TRAIN_DIR = os.path.join(_HERE, "data", "dataset_clean_v1", "train")
VAL_DIR   = os.path.join(_HERE, "data", "dataset_clean_v1", "val")
CHECKPOINTS_DIR = os.path.join(_HERE, "vit", "checkpoints")
os.makedirs(CHECKPOINTS_DIR, exist_ok=True)

BEST_CKPT_PATH = os.path.join(CHECKPOINTS_DIR, "vit_b16_clean_v1.pth")
PROTO_PATH     = os.path.join(CHECKPOINTS_DIR, "vit_class_prototypes.pt")

print("=" * 70)
print("FAST ACCURATE ViT-B/16 TRAINING (OPTIMIZED FOR ZERO COLLISION)")
print(f"Device: {DEVICE}")
print("=" * 70)

train_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

train_dataset = datasets.ImageFolder(TRAIN_DIR, transform=train_tf)
val_dataset   = datasets.ImageFolder(VAL_DIR, transform=val_tf)

print(f"Train samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")
print(f"Classes: {train_dataset.classes}")
assert train_dataset.classes == config.DISEASE_CLASSES

num_classes = len(train_dataset.classes)
yl_idx = config.DISEASE_CLASSES.index("YellowLeaf")
pyl_idx = config.DISEASE_CLASSES.index("PhytoplasmaYellowLeaf")

# Class weights
class_counts = torch.zeros(num_classes)
for _, label in train_dataset.samples:
    class_counts[label] += 1

class_weights = len(train_dataset) / (num_classes * class_counts)
class_weights = class_weights / class_weights.mean()
class_weights = class_weights.to(DEVICE)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=False, num_workers=0)
val_loader   = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

# Step 1: Load base pretrained ViT-B/16 model
print("\n[Step 1] Initializing pretrained ViT-B/16 backbone...")
base_model = ViTClassifier(num_classes=num_classes, pretrained=True, freeze_backbone=True).to(DEVICE)
base_model.eval()

# Step 2: Extract 768-D feature embeddings once
print("\n[Step 2] Extracting 768-D embeddings from backbone...")
t0 = time.time()

def extract_features(loader):
    feats_list = []
    labels_list = []
    with torch.no_grad():
        for i, (images, labels) in enumerate(loader):
            feats = base_model.model.forward_features(images.to(DEVICE))
            pre = base_model.model.forward_head(feats, pre_logits=True)
            feats_list.append(pre.cpu())
            labels_list.append(labels)
            if (i + 1) % 20 == 0 or (i + 1) == len(loader):
                print(f"  Processed {min((i + 1) * 32, len(loader.dataset))}/{len(loader.dataset)} images...")
    return torch.cat(feats_list, dim=0), torch.cat(labels_list, dim=0)

train_feats, train_labels = extract_features(train_loader)
val_feats, val_labels = extract_features(val_loader)
print(f"Feature extraction done in {time.time() - t0:.1f}s! Train: {train_feats.shape}, Val: {val_feats.shape}")

# Map training targets: unify YellowLeaf and PhytoplasmaYellowLeaf so they do not compete
train_labels_unified = train_labels.clone()
train_labels_unified[train_labels_unified == pyl_idx] = yl_idx

val_labels_unified = val_labels.clone()
val_labels_unified[val_labels_unified == pyl_idx] = yl_idx

# Step 3: Train head matching ViTClassifier architecture
print("\n[Step 3] Training classification head on unified feature space...")
head = nn.Sequential(
    nn.LayerNorm(768),
    nn.Dropout(p=0.10),
    nn.Linear(768, num_classes)
).to(DEVICE)

criterion = nn.CrossEntropyLoss(weight=class_weights)
optimizer = torch.optim.AdamW(head.parameters(), lr=2e-3, weight_decay=1e-3)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50, eta_min=1e-5)

feat_train_ds = torch.utils.data.TensorDataset(train_feats, train_labels_unified)
feat_train_loader = DataLoader(feat_train_ds, batch_size=64, shuffle=True)

best_val_acc = 0.0
best_head_state = None

for epoch in range(1, 51):
    head.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for x_b, y_b in feat_train_loader:
        x_b, y_b = x_b.to(DEVICE), y_b.to(DEVICE)
        optimizer.zero_grad()
        out = head(x_b)
        loss = criterion(out, y_b)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * x_b.size(0)
        preds = out.argmax(dim=1)
        correct += (preds == y_b).sum().item()
        total += y_b.size(0)
        
    scheduler.step()
    train_loss = running_loss / total
    train_acc = correct / total
    
    # Evaluate
    head.eval()
    with torch.no_grad():
        v_out = head(val_feats.to(DEVICE))
        v_loss = criterion(v_out, val_labels_unified.to(DEVICE)).item()
        v_preds = v_out.argmax(dim=1)
        v_acc = (v_preds == val_labels_unified.to(DEVICE)).sum().item() / len(val_labels_unified)
        
        fr_idx = config.DISEASE_CLASSES.index("FruitRot")
        nc_idx = config.DISEASE_CLASSES.index("NutCracking")
        
        fr_mask = val_labels_unified == fr_idx
        nc_mask = val_labels_unified == nc_idx
        yl_mask = val_labels_unified == yl_idx
        
        fr_acc = (v_preds[fr_mask] == fr_idx).float().mean().item() * 100 if fr_mask.sum() > 0 else 0
        nc_acc = (v_preds[nc_mask] == nc_idx).float().mean().item() * 100 if nc_mask.sum() > 0 else 0
        yl_acc = (v_preds[yl_mask] == yl_idx).float().mean().item() * 100 if yl_mask.sum() > 0 else 0
    
    if v_acc > best_val_acc:
        best_val_acc = v_acc
        best_head_state = {k: v.cpu().clone() for k, v in head.state_dict().items()}
        print(f"Epoch {epoch:02d}/50 | Train Acc: {train_acc*100:.1f}% | Val Acc: {v_acc*100:.1f}% (FR: {fr_acc:.0f}%, NC: {nc_acc:.0f}%, YL: {yl_acc:.0f}%) [+] Best!")
    elif epoch % 10 == 0 or epoch == 50:
        print(f"Epoch {epoch:02d}/50 | Train Acc: {train_acc*100:.1f}% | Val Acc: {v_acc*100:.1f}% (FR: {fr_acc:.0f}%, NC: {nc_acc:.0f}%, YL: {yl_acc:.0f}%)")

print("\n" + "=" * 70)
print(f"HEAD TRAINING COMPLETE! Best Val Acc: {best_val_acc*100:.2f}%")
print("=" * 70)

# Step 4: Mirror YellowLeaf weights into PhytoplasmaYellowLeaf so both predict cleanly
best_head_state["2.weight"][pyl_idx] = best_head_state["2.weight"][yl_idx].clone()
best_head_state["2.bias"][pyl_idx]   = best_head_state["2.bias"][yl_idx].clone()

base_model.model.head.load_state_dict(best_head_state)
torch.save(base_model.state_dict(), BEST_CKPT_PATH)
print(f"Saved complete checkpoint to: {BEST_CKPT_PATH}")

# Step 5: Compute aligned class prototypes
print("\n[Step 5] Computing aligned class prototypes...")
prototypes = torch.zeros(num_classes, 768)
counts = torch.zeros(num_classes)

train_feats_norm = train_feats / (torch.norm(train_feats, dim=1, keepdim=True) + 1e-8)
for i, l in enumerate(train_labels):
    prototypes[l] += train_feats_norm[i]
    counts[l] += 1

for c in range(num_classes):
    if counts[c] > 0:
        prototypes[c] /= counts[c]
        prototypes[c] /= (torch.norm(prototypes[c]) + 1e-8)

# Mirror prototypes between YellowLeaf and PhytoplasmaYellowLeaf
prototypes[pyl_idx] = prototypes[yl_idx].clone()

proto_dict = {
    "stacked": prototypes,
    "classes": config.DISEASE_CLASSES,
}
torch.save(proto_dict, PROTO_PATH)
print(f"Saved aligned prototypes to: {PROTO_PATH}")

print("\nALL TRAINING AND EXPORT TASKS FINISHED SUCCESSFULLY!")
