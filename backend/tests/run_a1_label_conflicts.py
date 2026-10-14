"""
run_a1_label_conflicts.py

Part A1 of ArecaVision Round 5:
- Group cross-class duplicates (Hamming <= 6) across the 11 areca classes in D:\dataset_raw\dataset_raw.
- Write backend/tests/results/label_conflicts.csv (group_id, file, folder label, train/val).
- Generate a contact sheet per group (saved to backend/tests/results/conflicts/).
- Report group count, images in conflict, groups mixing areca_healthy with a disease.
- Determine how many of the 23 ViT errors dropped in the leak-free run have a differently-labelled duplicate in train.
- Do NOT pick labels.
"""

import os
import glob
import random
import csv
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
from torchvision import transforms
from collections import defaultdict

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, _HERE)
os.chdir(_HERE)

import config
from vit.model import ViTClassifier

RAW_DIR = r"D:\dataset_raw\dataset_raw"
RESULTS_DIR = os.path.join(_HERE, "tests", "results")
CONFLICTS_DIR = os.path.join(RESULTS_DIR, "conflicts")
os.makedirs(CONFLICTS_DIR, exist_ok=True)

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

class_to_idx = {name: i for i, name in enumerate(config.DISEASE_CLASSES)}
idx_to_class = {i: name for i, name in enumerate(config.DISEASE_CLASSES)}
val_ratio = 0.2

# Deterministic 80/20 train/val split matching eval_vit_leak_free.py
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

train_files_by_class = {}
val_files_by_class = {}
file_split_map = {}

for cat_folder, disease_name in CATEGORY_TO_DISEASE.items():
    cls_idx = class_to_idx[disease_name]
    files = sorted(glob.glob(os.path.join(RAW_DIR, cat_folder, "*.*")))
    random.shuffle(files)
    n_val = int(len(files) * val_ratio)
    val_files = files[:n_val]
    train_files = files[n_val:]
    val_files_by_class[cls_idx] = val_files
    train_files_by_class[cls_idx] = train_files
    for f in val_files:
        file_split_map[f] = "val"
    for f in train_files:
        file_split_map[f] = "train"

def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

def hamming_dist(h1, h2):
    return bin(h1 ^ h2).count('1')

print("1. Computing dHash for all 11 areca class images...")
all_images = []
for cat, disease in CATEGORY_TO_DISEASE.items():
    files = sorted(glob.glob(os.path.join(RAW_DIR, cat, "*.*")))
    for f in files:
        with Image.open(f) as img:
            h = dhash(img)
        all_images.append({
            "path": f,
            "filename": os.path.basename(f),
            "cat": cat,
            "disease": disease,
            "split": file_split_map[f],
            "hash": h
        })

print(f"Total images hashed: {len(all_images)}")

# Cross-class pairs (Hamming <= 6)
print("2. Finding cross-class duplicates (Hamming <= 6)...")
cross_edges = []
n = len(all_images)
for i in range(n):
    for j in range(i + 1, n):
        if all_images[i]["disease"] != all_images[j]["disease"]:
            dist = hamming_dist(all_images[i]["hash"], all_images[j]["hash"])
            if dist <= 6:
                cross_edges.append((i, j, dist))

print(f"Total cross-class edges: {len(cross_edges)}")

# Connected components of cross-class conflict graph
adj = defaultdict(set)
nodes_in_cross = set()
for u, v, d in cross_edges:
    adj[u].add(v)
    adj[v].add(u)
    nodes_in_cross.add(u)
    nodes_in_cross.add(v)

visited = set()
components = []
for node in sorted(nodes_in_cross):
    if node not in visited:
        comp = []
        q = [node]
        visited.add(node)
        while q:
            curr = q.pop(0)
            comp.append(curr)
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    q.append(neighbor)
        components.append(comp)

print(f"Total conflict groups: {len(components)}")
print(f"Total conflicting images: {len(nodes_in_cross)}")

# Check groups mixing Healthy with a disease
healthy_mix_groups = []
for group_id, comp in enumerate(components, 1):
    diseases = set(all_images[i]["disease"] for i in comp)
    if "Healthy" in diseases and len(diseases) > 1:
        healthy_mix_groups.append((group_id, diseases, comp))

print(f"Groups mixing areca_healthy with disease: {len(healthy_mix_groups)}")

# Write label_conflicts.csv
csv_path = os.path.join(RESULTS_DIR, "label_conflicts.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["group_id", "file", "folder label", "train/val"])
    for group_id, comp in enumerate(components, 1):
        for idx in sorted(comp, key=lambda x: (all_images[x]["disease"], all_images[x]["filename"])):
            item = all_images[idx]
            writer.writerow([
                f"group_{group_id:03d}",
                item["filename"],
                item["cat"],
                item["split"]
            ])

print(f"Saved conflicts table to: {csv_path}")

# Generate contact sheets per group (max 12 images per sheet)
print("3. Generating contact sheet per group...")
for group_id, comp in enumerate(components, 1):
    items = [all_images[i] for i in comp[:12]]
    n_items = len(items)
    cols = min(4, n_items)
    rows = (n_items + cols - 1) // cols
    tile_w, tile_h = 240, 240
    header_h = 50
    footer_h = 45
    cell_h = tile_h + footer_h
    img_sheet = Image.new("RGB", (cols * tile_w, rows * cell_h + header_h), (240, 240, 240))
    draw = ImageDraw.Draw(img_sheet)
    
    # Title
    unique_classes = sorted(list(set(it["disease"] for it in items)))
    draw.text((10, 15), f"Group {group_id:03d} (n={n_items}) | Classes: {', '.join(unique_classes)}", fill=(0, 0, 0))

    for idx, it in enumerate(items):
        r = idx // cols
        c = idx % cols
        x = c * tile_w
        y = header_h + r * cell_h
        try:
            with Image.open(it["path"]) as tile_img:
                tile_resized = tile_img.convert("RGB").resize((tile_w - 10, tile_h - 10))
                img_sheet.paste(tile_resized, (x + 5, y + 5))
        except Exception:
            pass
        # Label text
        label_text = f"{it['filename']}\n{it['disease']} ({it['split']})"
        draw.text((x + 5, y + tile_h - 2), label_text, fill=(20, 20, 20))

    sheet_path = os.path.join(CONFLICTS_DIR, f"group_{group_id:03d}.png")
    img_sheet.save(sheet_path)

print(f"Generated {len(components)} contact sheets in {CONFLICTS_DIR}")

# 4. Analyze the 23 ViT errors dropped in the leak-free run
print("4. Analyzing the 23 ViT errors dropped in the leak-free run...")
train_hashes = []
for cls_idx, files in train_files_by_class.items():
    for f in files:
        with Image.open(f) as img:
            train_hashes.append((dhash(img), f, cls_idx))

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ViTClassifier(num_classes=len(config.DISEASE_CLASSES), pretrained=False).to(device)
ckpt = torch.load("vit/checkpoints/vit_b16.pth", map_location=device, weights_only=False)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

tf_base = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])

dropped_errors = []
dropped_correct = []

for cls_idx, files in val_files_by_class.items():
    for f in files:
        with Image.open(f) as img:
            vh = dhash(img)
            t = tf_base(img.convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            pred_idx = torch.argmax(model(t), dim=1).item()
        
        matches_in_train = []
        for th, tf, t_cls in train_hashes:
            dist = hamming_dist(vh, th)
            if dist <= 6:
                matches_in_train.append((tf, t_cls, dist))
        
        if matches_in_train:
            is_correct = (pred_idx == cls_idx)
            diff_label_matches = [m for m in matches_in_train if m[1] != cls_idx]
            same_label_matches = [m for m in matches_in_train if m[1] == cls_idx]
            info = {
                "val_file": f,
                "filename": os.path.basename(f),
                "true_class": idx_to_class[cls_idx],
                "pred_class": idx_to_class[pred_idx],
                "is_correct": is_correct,
                "diff_label_matches": [(m[0], idx_to_class[m[1]], m[2]) for m in diff_label_matches],
                "same_label_matches": [(m[0], idx_to_class[m[1]], m[2]) for m in same_label_matches],
            }
            if not is_correct:
                dropped_errors.append(info)
            else:
                dropped_correct.append(info)

print(f"Total dropped val images: {len(dropped_errors) + len(dropped_correct)}")
print(f"Total dropped ViT errors: {len(dropped_errors)}")
print(f"Total dropped ViT correct: {len(dropped_correct)}")

diff_count = sum(1 for e in dropped_errors if len(e["diff_label_matches"]) > 0)
same_only_count = sum(1 for e in dropped_errors if len(e["diff_label_matches"]) == 0)

print(f"Dropped ViT errors with a differently-labelled duplicate in train: {diff_count} / {len(dropped_errors)}")
print(f"Dropped ViT errors with ONLY same-label duplicate in train: {same_only_count} / {len(dropped_errors)}")

# Save summary json
summary = {
    "group_count": len(components),
    "images_in_conflict": len(nodes_in_cross),
    "groups_mixing_healthy_with_disease": len(healthy_mix_groups),
    "dropped_vit_errors_count": len(dropped_errors),
    "dropped_vit_errors_with_diff_label_in_train": diff_count,
    "dropped_vit_errors_with_same_label_only_in_train": same_only_count,
    "dropped_errors_details": dropped_errors
}

summary_path = os.path.join(RESULTS_DIR, "label_conflicts_summary.json")
with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)

print(f"Saved summary JSON to {summary_path}")
