"""
backend/train_full_real_vit.py
Trains ViT-B/16 classifier using the comprehensive real-world dataset from D:/dataset0000/dataset/dataset
combined with all disease categories.
"""

import os
import sys
import time
import shutil
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import timm

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import config

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {DEVICE}")

CLASSES = config.DISEASE_CLASSES
print(f"Target 11 Classes: {CLASSES}")

# Source directory mappings
DATASET0000_TRAIN = r"D:\dataset0000\dataset\dataset\train"
DATASET0000_VAL   = r"D:\dataset0000\dataset\dataset\validation"
DATASET_RAW       = r"D:\dataset"

FOLDER_MAP = {
    "FruitRot": os.path.join(DATASET0000_TRAIN, "areca_diseased_fungal_fruit_rot"),
    "NutCracking": os.path.join(DATASET0000_TRAIN, "areca_diseased_physiological_nut_cracking"),
    "Anthracnose": os.path.join(DATASET0000_TRAIN, "areca_diseased_fungal_anthracnose"),
    "SootyMold": os.path.join(DATASET0000_TRAIN, "areca_diseased_fungal_sooty_mold"),
    "YellowLeaf": os.path.join(DATASET0000_TRAIN, "areca_diseased_phytoplasma_yellow_leaf"),
    "PhytoplasmaYellowLeaf": os.path.join(DATASET0000_TRAIN, "areca_diseased_phytoplasma_yellow_leaf"),
    "Healthy": os.path.join(DATASET0000_TRAIN, "areca_healthy"),
    "LeafSpotComplex": os.path.join(DATASET_RAW, "areca_diseased_fungal_leaf_spot"),
    "BudBorer": os.path.join(DATASET_RAW, "areca_pest_bud_borer"),
    "StemBleeding": os.path.join(DATASET_RAW, "areca_diseased_fungal_stem_bleeding"),
    "StemCracking": os.path.join(DATASET_RAW, "areca_diseased_physiological_stem_cracking"),
}

VAL_FOLDER_MAP = {
    "FruitRot": os.path.join(DATASET0000_VAL, "areca_diseased_fungal_fruit_rot"),
    "NutCracking": os.path.join(DATASET0000_VAL, "areca_diseased_physiological_nut_cracking"),
    "Anthracnose": os.path.join(DATASET0000_VAL, "areca_diseased_fungal_anthracnose"),
    "SootyMold": os.path.join(DATASET0000_VAL, "areca_diseased_fungal_sooty_mold"),
    "YellowLeaf": os.path.join(DATASET0000_VAL, "areca_diseased_phytoplasma_yellow_leaf"),
    "PhytoplasmaYellowLeaf": os.path.join(DATASET0000_VAL, "areca_diseased_phytoplasma_yellow_leaf"),
    "Healthy": os.path.join(DATASET0000_VAL, "areca_healthy"),
    "LeafSpotComplex": os.path.join(_HERE, "data", "dataset_clean_v1", "val", "LeafSpotComplex"),
    "BudBorer": os.path.join(_HERE, "data", "dataset_clean_v1", "val", "BudBorer"),
    "StemBleeding": os.path.join(_HERE, "data", "dataset_clean_v1", "val", "StemBleeding"),
    "StemCracking": os.path.join(_HERE, "data", "dataset_clean_v1", "val", "StemCracking"),
}

# Image loading and transform
tf = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

class FeatureDataset(Dataset):
    def __init__(self, features, labels):
        self.features = features
        self.labels = labels
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

def extract_features_from_folders(folder_map, max_per_class=200):
    print("Loading pretrained ViT-B/16 feature extractor...")
    backbone = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=0).to(DEVICE)
    backbone.eval()

    all_features = []
    all_labels = []

    print("\nExtracting features from class folders:")
    for cls_idx, cls_name in enumerate(CLASSES):
        folder = folder_map.get(cls_name)
        if not folder or not os.path.isdir(folder):
            print(f"  [WARN] Missing folder for {cls_name}: {folder}")
            continue
        
        valid_files = [
            f for f in os.listdir(folder)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
        ]
        
        # Limit per class to prevent extreme imbalance
        selected_files = valid_files[:max_per_class]
        print(f"  {cls_name:22}: extracting {len(selected_files)} images (from {len(valid_files)} total)...")
        
        batch_tensors = []
        for fname in selected_files:
            fpath = os.path.join(folder, fname)
            try:
                img = Image.open(fpath).convert("RGB")
                batch_tensors.append(tf(img))
            except Exception:
                continue

            if len(batch_tensors) >= 16:
                batch = torch.stack(batch_tensors, dim=0).to(DEVICE)
                with torch.no_grad():
                    feats = backbone(batch)
                all_features.append(feats.cpu())
                all_labels.extend([cls_idx] * len(batch_tensors))
                batch_tensors = []

        if batch_tensors:
            batch = torch.stack(batch_tensors, dim=0).to(DEVICE)
            with torch.no_grad():
                feats = backbone(batch)
            all_features.append(feats.cpu())
            all_labels.extend([cls_idx] * len(batch_tensors))

    all_features = torch.cat(all_features, dim=0)
    all_labels = torch.tensor(all_labels, dtype=torch.long)
    print(f"\nFeature extraction complete: {all_features.shape[0]} samples, {all_features.shape[1]} dims.")
    return all_features, all_labels

def main():
    t0 = time.time()
    
    # 1. Extract Train Features
    train_features, train_labels = extract_features_from_folders(FOLDER_MAP, max_per_class=180)
    val_features, val_labels     = extract_features_from_folders(VAL_FOLDER_MAP, max_per_class=40)
    
    # 2. Class weights for balance
    class_counts = torch.bincount(train_labels, minlength=len(CLASSES)).float()
    weights = (len(train_labels) / (len(CLASSES) * (class_counts + 1e-5)))
    weights = weights / weights.mean()
    weights = weights.to(DEVICE)
    
    print("\nClass counts and weights:")
    for i, c in enumerate(CLASSES):
        print(f"  {c:22}: count={int(class_counts[i].item()):4d} | weight={weights[i].item():.2f}")

    # 3. Define Classification Head
    head = nn.Sequential(
        nn.Dropout(0.15),
        nn.Linear(768, len(CLASSES))
    ).to(DEVICE)

    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=40)

    train_loader = DataLoader(FeatureDataset(train_features, train_labels), batch_size=32, shuffle=True)
    val_loader   = DataLoader(FeatureDataset(val_features, val_labels), batch_size=32, shuffle=False)

    print("\nTraining classification head (40 epochs)...")
    best_acc = 0.0
    best_state = None

    for epoch in range(1, 41):
        head.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()
            out = head(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y)
        scheduler.step()

        # Validation
        head.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for vx, vy in val_loader:
                vx, vy = vx.to(DEVICE), vy.to(DEVICE)
                preds = head(vx).argmax(dim=1)
                correct += (preds == vy).sum().item()
                total += len(vy)
        val_acc = correct / max(total, 1)

        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in head.state_dict().items()}

        if epoch % 5 == 0 or epoch == 40:
            print(f"Epoch {epoch:2d}/40 | Loss: {total_loss/len(train_labels):.4f} | Val Acc: {val_acc*100:.1f}% (Best: {best_acc*100:.1f}%)")

    # 4. Assemble Full ViT Model and Save Weights
    print("\nAssembling full ViT-B/16 checkpoint...")
    full_model = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=len(CLASSES))
    
    # Load trained head weights into full model
    head_weight = best_state["1.weight"]
    head_bias   = best_state["1.bias"]
    
    with torch.no_grad():
        full_model.head.weight.copy_(head_weight)
        full_model.head.bias.copy_(head_bias)

    # Save checkpoint
    ckpt_path = os.path.join(_HERE, "vit", "checkpoints", "vit_b16_clean_v1.pth")
    torch.save({"model_state_dict": full_model.state_dict(), "classes": CLASSES}, ckpt_path)
    print(f"Saved checkpoint to {ckpt_path}")

    # 5. Compute Class Prototypes for OOD
    print("\nComputing class prototypes...")
    head.eval()
    prototypes = torch.zeros(len(CLASSES), 768)
    for c_i in range(len(CLASSES)):
        mask = (train_labels == c_i)
        if mask.any():
            c_feats = train_features[mask]
            c_proto = c_feats.mean(dim=0)
            c_proto = c_proto / (torch.norm(c_proto) + 1e-8)
            prototypes[c_i] = c_proto
    
    proto_path = os.path.join(_HERE, "vit", "checkpoints", "vit_class_prototypes.pt")
    torch.save(prototypes, proto_path)
    print(f"Saved prototypes to {proto_path}")

    # 6. Test on User Uploads
    print("\n" + "="*70)
    print("TESTING NEW RETRAINED MODEL ON USER IMAGES:")
    print("="*70)
    
    backbone = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=0).to(DEVICE)
    backbone.eval()
    head.load_state_dict({k: v.to(DEVICE) for k, v in best_state.items()})
    head.eval()

    test_imgs = [
        ("Leaf Comparison (YellowLeaf/LeafSpot)", "backend/data/uploads/job-88dd4945ada1.jpg"),
        ("Field Fruit Rot (Koleroga)", "backend/data/uploads/job-bfd163d5cc18.jpg"),
    ]

    for label, ipath in test_imgs:
        full_ipath = os.path.join(os.path.dirname(_HERE), ipath)
        if not os.path.isfile(full_ipath):
            continue
        im = Image.open(full_ipath).convert("RGB")
        tensor = tf(im).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            feat = backbone(tensor)
            logits = head(feat)
            probs = torch.softmax(logits, dim=1)[0]
        
        top3_indices = torch.topk(probs, 3).indices.tolist()
        print(f"\n{label}:")
        for rank, idx in enumerate(top3_indices, 1):
            print(f"  #{rank}: {CLASSES[idx]:22} ({probs[idx]*100:.1f}%)")

    print(f"\nTotal elapsed time: {time.time() - t0:.1f}s")

if __name__ == "__main__":
    main()
