import os
import sys
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torchvision import datasets, transforms
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import config
from vit.model import ViTClassifier

DEVICE = config.DEVICE
print(f"Using device: {DEVICE}")

DATA_DIR = os.path.join(_HERE, "data", "dataset_clean_v1")
TRAIN_DIR = os.path.join(DATA_DIR, "train")
VAL_DIR = os.path.join(DATA_DIR, "val")
CKPT_DIR = os.path.join(_HERE, "vit", "checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)

TRAIN_FEATS_PATH = os.path.join(CKPT_DIR, "train_feats.pt")
VAL_FEATS_PATH   = os.path.join(CKPT_DIR, "val_feats.pt")
BEST_CKPT_PATH   = os.path.join(CKPT_DIR, "vit_b16_clean_v1.pth")
PROTO_PATH       = os.path.join(CKPT_DIR, "vit_class_prototypes.pt")

val_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

train_dataset = datasets.ImageFolder(TRAIN_DIR, transform=val_tf)
val_dataset   = datasets.ImageFolder(VAL_DIR, transform=val_tf)

print(f"Train samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")
num_classes = len(train_dataset.classes)
assert train_dataset.classes == config.DISEASE_CLASSES

yl_idx = config.DISEASE_CLASSES.index("YellowLeaf")
pyl_idx = config.DISEASE_CLASSES.index("PhytoplasmaYellowLeaf")

# 1. Feature Extraction / Caching
if os.path.exists(TRAIN_FEATS_PATH) and os.path.exists(VAL_FEATS_PATH):
    print(f"\n[Step 1] Loading cached features from {TRAIN_FEATS_PATH} and {VAL_FEATS_PATH}...")
    t_data = torch.load(TRAIN_FEATS_PATH, map_location="cpu")
    train_feats = t_data["feats"]
    train_labels = t_data["labels"]
    
    v_data = torch.load(VAL_FEATS_PATH, map_location="cpu")
    val_feats = v_data["feats"]
    val_labels = v_data["labels"]
else:
    print("\n[Step 1] Initializing pretrained ViT-B/16 backbone for feature extraction...")
    base_model = ViTClassifier(num_classes=num_classes, pretrained=True, freeze_backbone=True).to(DEVICE)
    base_model.eval()

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=False, num_workers=0)
    val_loader   = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

    print(f"Extracting features for {len(train_dataset)} train images...")
    t0 = time.time()
    train_feats = torch.zeros(len(train_dataset), 768)
    train_labels = torch.zeros(len(train_dataset), dtype=torch.long)
    with torch.no_grad():
        idx = 0
        for images, labels in train_loader:
            images = images.to(DEVICE)
            feat = base_model.model.forward_features(images)
            pre = base_model.model.forward_head(feat, pre_logits=True)
            bs = images.size(0)
            train_feats[idx:idx+bs] = pre.cpu()
            train_labels[idx:idx+bs] = labels
            idx += bs
    print(f"Train features extracted in {time.time()-t0:.1f}s")
    torch.save({"feats": train_feats, "labels": train_labels}, TRAIN_FEATS_PATH)

    print(f"Extracting features for {len(val_dataset)} val images...")
    t0 = time.time()
    val_feats = torch.zeros(len(val_dataset), 768)
    val_labels = torch.zeros(len(val_dataset), dtype=torch.long)
    with torch.no_grad():
        idx = 0
        for images, labels in val_loader:
            images = images.to(DEVICE)
            feat = base_model.model.forward_features(images)
            pre = base_model.model.forward_head(feat, pre_logits=True)
            bs = images.size(0)
            val_feats[idx:idx+bs] = pre.cpu()
            val_labels[idx:idx+bs] = labels
            idx += bs
    print(f"Val features extracted in {time.time()-t0:.1f}s")
    torch.save({"feats": val_feats, "labels": val_labels}, VAL_FEATS_PATH)

# 2. Unified Target Representation
train_labels_unified = train_labels.clone()
train_labels_unified[train_labels_unified == pyl_idx] = yl_idx

val_labels_unified = val_labels.clone()
val_labels_unified[val_labels_unified == pyl_idx] = yl_idx

# 3. Compute True Balanced Class Weights on Unified Data
counts = torch.bincount(train_labels_unified, minlength=num_classes).float()
print("\nUnified class counts in training set:")
for idx, c in enumerate(config.DISEASE_CLASSES):
    if idx == pyl_idx: continue
    print(f"  {c:25}: {int(counts[idx].item())} samples")

# Class weights: inverse frequency with square-root smoothing to avoid extreme penalties
weights = torch.zeros(num_classes)
active_indices = [i for i in range(num_classes) if i != pyl_idx]
mean_count = counts[active_indices].mean()

for i in active_indices:
    # Smoothed balance: (mean_count / count) ** 0.65
    weights[i] = (mean_count / (counts[i] + 1e-6)) ** 0.65

weights[pyl_idx] = 0.0
weights = weights / weights[active_indices].mean()
weights = weights.to(DEVICE)

print("\nComputed balanced loss weights:")
for idx in active_indices:
    print(f"  {config.DISEASE_CLASSES[idx]:25}: {weights[idx].item():.3f}")

# 4. Train Linear Head
print("\n[Step 2] Training linear classification head with balanced weights...")
head = nn.Sequential(
    nn.LayerNorm(768),
    nn.Dropout(p=0.10),
    nn.Linear(768, num_classes)
).to(DEVICE)

criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)
optimizer = torch.optim.AdamW(head.parameters(), lr=1.5e-3, weight_decay=1e-3)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=60, eta_min=1e-5)

feat_train_ds = TensorDataset(train_feats, train_labels_unified)
feat_train_loader = DataLoader(feat_train_ds, batch_size=64, shuffle=True)

best_val_acc = 0.0
best_head_state = None

for epoch in range(1, 61):
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
    
    head.eval()
    with torch.no_grad():
        v_out = head(val_feats.to(DEVICE))
        v_loss = criterion(v_out, val_labels_unified.to(DEVICE)).item()
        v_preds = v_out.argmax(dim=1)
        v_acc = (v_preds == val_labels_unified.to(DEVICE)).sum().item() / len(val_labels_unified)
        
        fr_idx = config.DISEASE_CLASSES.index("FruitRot")
        nc_idx = config.DISEASE_CLASSES.index("NutCracking")
        ant_idx = config.DISEASE_CLASSES.index("Anthracnose")
        hea_idx = config.DISEASE_CLASSES.index("Healthy")
        
        ant_acc = (v_preds[val_labels_unified == ant_idx] == ant_idx).float().mean().item() * 100
        fr_acc  = (v_preds[val_labels_unified == fr_idx] == fr_idx).float().mean().item() * 100
        nc_acc  = (v_preds[val_labels_unified == nc_idx] == nc_idx).float().mean().item() * 100
        yl_acc  = (v_preds[val_labels_unified == yl_idx] == yl_idx).float().mean().item() * 100
        hea_acc = (v_preds[val_labels_unified == hea_idx] == hea_idx).float().mean().item() * 100

    if v_acc > best_val_acc:
        best_val_acc = v_acc
        best_head_state = {k: v.cpu().clone() for k, v in head.state_dict().items()}
        print(f"--> Epoch {epoch:02d}/60 | Val Acc: {v_acc*100:.2f}% | Ant: {ant_acc:.0f}%, FR: {fr_acc:.0f}%, NC: {nc_acc:.0f}%, YL: {yl_acc:.0f}%, Hea: {hea_acc:.0f}% [NEW BEST]")
    elif epoch % 10 == 0 or epoch == 60:
        print(f"    Epoch {epoch:02d}/60 | Val Acc: {v_acc*100:.2f}% | Ant: {ant_acc:.0f}%, FR: {fr_acc:.0f}%, NC: {nc_acc:.0f}%, YL: {yl_acc:.0f}%, Hea: {hea_acc:.0f}%")

print("\n" + "=" * 70)
print(f"HEAD TRAINING COMPLETE! Best Val Acc: {best_val_acc*100:.2f}%")
print("=" * 70)

# 5. Mirror weights to PhytoplasmaYellowLeaf so both predict cleanly
best_head_state["2.weight"][pyl_idx] = best_head_state["2.weight"][yl_idx].clone()
best_head_state["2.bias"][pyl_idx]   = best_head_state["2.bias"][yl_idx].clone()

# Save complete model checkpoint
final_model = ViTClassifier(num_classes=num_classes, pretrained=True, freeze_backbone=False).to(DEVICE)
final_model.model.head.load_state_dict(best_head_state)
torch.save(final_model.state_dict(), BEST_CKPT_PATH)
print(f"Saved complete checkpoint to: {BEST_CKPT_PATH}")

# 6. Compute Aligned Class Prototypes (Normalized Mean Embeddings)
print("\n[Step 3] Computing aligned class prototypes...")
prototypes = torch.zeros(num_classes, 768)
counts_proto = torch.zeros(num_classes)

train_feats_norm = train_feats / (torch.norm(train_feats, dim=1, keepdim=True) + 1e-8)
for i, l in enumerate(train_labels):
    prototypes[l] += train_feats_norm[i]
    counts_proto[l] += 1

for c in range(num_classes):
    if counts_proto[c] > 0:
        prototypes[c] /= counts_proto[c]
        prototypes[c] /= (torch.norm(prototypes[c]) + 1e-8)

prototypes[pyl_idx] = prototypes[yl_idx].clone()

proto_dict = {
    "stacked": prototypes,
    "classes": config.DISEASE_CLASSES,
}
torch.save(proto_dict, PROTO_PATH)
print(f"Saved aligned prototypes to: {PROTO_PATH}")

print("\nALL BALANCED TRAINING AND EXPORT TASKS FINISHED SUCCESSFULLY!")
