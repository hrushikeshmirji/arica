import os
import glob
import json
import math
import random
from collections import Counter
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from sklearn.metrics import classification_report

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, _HERE)
os.chdir(_HERE)
RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

import config
from vit.model import ViTClassifier

random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

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

class_to_idx = {name: i for i, name in enumerate(config.DISEASE_CLASSES)}
val_ratio = 0.2

train_files_by_class = {}
val_files_by_class = {}

for cat_folder, disease_name in CATEGORY_TO_DISEASE.items():
    cls_idx = class_to_idx[disease_name]
    files = sorted(glob.glob(os.path.join(RAW_DIR, cat_folder, "*.*")))
    random.shuffle(files)
    n_val = int(len(files) * val_ratio)
    val_files_by_class[cls_idx] = files[:n_val]
    train_files_by_class[cls_idx] = files[n_val:]

def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

def hamming_dist(h1, h2):
    return bin(h1 ^ h2).count('1')

def wilson_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0, 0.0
    z = 1.959963984540054
    p_hat = k / n
    denominator = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denominator
    margin = (z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denominator
    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)
    return p_hat, lower, upper

def format_wilson(k, n):
    p, l, u = wilson_interval(k, n)
    return f"{k:3d}/{n:3d} ({p:6.2%}) [{l:6.2%}, {u:6.2%}]"

# Collect all training hashes
train_hashes = []
for cls_idx, files in train_files_by_class.items():
    for f in files:
        try:
            with Image.open(f) as img:
                train_hashes.append((dhash(img), f, cls_idx))
        except Exception:
            pass

# Check leakage in val files
val_leak_free_by_class = {}
dropped_files = []

for cls_idx, files in val_files_by_class.items():
    clean_files = []
    for f in files:
        try:
            with Image.open(f) as img:
                vh = dhash(img)
            # check distance to any training hash
            leaked = False
            for th, tf, t_cls in train_hashes:
                if hamming_dist(vh, th) <= 6:
                    leaked = True
                    dropped_files.append({
                        "val_file": f,
                        "val_class": config.DISEASE_CLASSES[cls_idx],
                        "train_file": tf,
                        "train_class": config.DISEASE_CLASSES[t_cls],
                        "dist": hamming_dist(vh, th)
                    })
                    break
            if not leaked:
                clean_files.append(f)
        except Exception:
            pass
    val_leak_free_by_class[cls_idx] = clean_files

total_orig_val = sum(len(f) for f in val_files_by_class.values())
total_clean_val = sum(len(f) for f in val_leak_free_by_class.values())

print(f"Original Validation Images: {total_orig_val}")
print(f"Dropped Leaking Images (Hamming <= 6 to train): {len(dropped_files)}")
print(f"Leak-Free Validation Images: {total_clean_val}")

# Evaluate model on both sets
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

def evaluate_files(files_by_class):
    y_true = []
    y_pred = []
    for cls_idx, files in files_by_class.items():
        for f in files:
            try:
                with Image.open(f) as img:
                    t = tf_base(img.convert("RGB")).unsqueeze(0).to(device)
                with torch.no_grad():
                    pred = torch.argmax(model(t), dim=1).item()
                y_true.append(cls_idx)
                y_pred.append(pred)
            except Exception:
                pass
    return np.array(y_true), np.array(y_pred)

y_true_orig, y_pred_orig = evaluate_files(val_files_by_class)
y_true_clean, y_pred_clean = evaluate_files(val_leak_free_by_class)

print("\n" + "=" * 95)
print("1.5 ViT ACCURACY COMPARISON: ORIGINAL VAL vs LEAK-FREE VAL (95% WILSON INTERVALS)")
print("=" * 95)
header = f"{'Disease Class':<24} | {'Original Val Recall (n=' + str(total_orig_val) + ')':<34} | {'Leak-Free Val Recall (n=' + str(total_clean_val) + ')':<34}"
print(header)
print("-" * len(header))

comparison_table = {}
for cls_idx, c_name in enumerate(config.DISEASE_CLASSES):
    # orig
    mask_orig = (y_true_orig == cls_idx)
    n_orig = int(mask_orig.sum())
    k_orig = int((y_pred_orig[mask_orig] == cls_idx).sum())
    str_orig = format_wilson(k_orig, n_orig)

    # clean
    mask_clean = (y_true_clean == cls_idx)
    n_clean = int(mask_clean.sum())
    k_clean = int((y_pred_clean[mask_clean] == cls_idx).sum())
    str_clean = format_wilson(k_clean, n_clean)

    print(f"{c_name:<24} | {str_orig:<34} | {str_clean:<34}")
    comparison_table[c_name] = {
        "original": {"k": k_orig, "n": n_orig, "str": str_orig},
        "leak_free": {"k": k_clean, "n": n_clean, "str": str_clean}
    }

# Overall accuracy
k_all_orig = int((y_true_orig == y_pred_orig).sum())
n_all_orig = len(y_true_orig)
k_all_clean = int((y_true_clean == y_pred_clean).sum())
n_all_clean = len(y_true_clean)

str_all_orig = format_wilson(k_all_orig, n_all_orig)
str_all_clean = format_wilson(k_all_clean, n_all_clean)
print("-" * len(header))
print(f"{'OVERALL ACCURACY':<24} | {str_all_orig:<34} | {str_all_clean:<34}")

out_results = {
    "total_original": total_orig_val,
    "dropped_leak_count": len(dropped_files),
    "total_leak_free": total_clean_val,
    "dropped_details": dropped_files,
    "overall_original": {"k": k_all_orig, "n": n_all_orig, "str": str_all_orig},
    "overall_leak_free": {"k": k_all_clean, "n": n_all_clean, "str": str_all_clean},
    "per_class": comparison_table
}

json_path = os.path.join(RESULTS_DIR, "vit_leak_free_eval.json")
with open(json_path, "w") as f:
    json.dump(out_results, f, indent=2)
print(f"\nSaved results to {json_path}")
