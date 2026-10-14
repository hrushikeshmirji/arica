"""
run_r6_a7_vit_real_classes.py

Task A7:
- ViT on the 5 real classes only:
  * original-val and leak-free per-class and total (n, Wilson CI; expect 34/67 and 34/44)
  * precision-vs-coverage for top-1 and margin floors on the leak-free set.
- Save results to backend/tests/results/r6_a7_vit_real_classes.json.
"""

import os
import sys
import glob
import json
import math
import random
from collections import Counter
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from torchvision import transforms

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

import config
from vit.model import ViTClassifier

RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

RAW_DIR = r"D:\dataset_raw\dataset_raw"

# The 5 real classes
REAL_5_CLASSES = {
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "areca_healthy": "Healthy",
    "areca_diseased_physiological_nut_cracking": "NutCracking",
    "areca_diseased_fungal_sooty_mold": "SootyMold",
}

# All 11 classes for training split hash calculation
ALL_11_CLASSES = {
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
real_5_indices = set(class_to_idx[name] for name in REAL_5_CLASSES.values())

val_ratio = 0.2
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

train_files_by_class = {}
val_files_by_class = {}

for cat_folder, disease_name in ALL_11_CLASSES.items():
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

# Collect training hashes across all classes
train_hashes = []
for cls_idx, files in train_files_by_class.items():
    for f in files:
        try:
            with Image.open(f) as img:
                train_hashes.append((dhash(img), f, cls_idx))
        except Exception:
            pass

# Check leakage for the 5 real classes val files
val_orig_real5 = []
val_clean_real5 = []
dropped_real5 = []

for cls_idx in real_5_indices:
    files = val_files_by_class[cls_idx]
    for f in files:
        val_orig_real5.append((f, cls_idx))
        try:
            with Image.open(f) as img:
                vh = dhash(img)
            leaked = False
            for th, tf, t_cls in train_hashes:
                if hamming_dist(vh, th) <= 6:
                    leaked = True
                    dropped_real5.append((f, cls_idx, tf, t_cls, hamming_dist(vh, th)))
                    break
            if not leaked:
                val_clean_real5.append((f, cls_idx))
        except Exception:
            pass

print(f"Original val images (5 real classes) : {len(val_orig_real5)}")
print(f"Dropped leaking images (5 real classes) : {len(dropped_real5)}")
print(f"Leak-free val images (5 real classes) : {len(val_clean_real5)}")

# Load ViT model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ViTClassifier(num_classes=len(config.DISEASE_CLASSES), pretrained=False).to(device)
ckpt_path = os.path.join(_HERE, "vit", "checkpoints", "vit_b16.pth")
ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

tf_base = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])

def evaluate_set(items, restrict_to_real5=True):
    records = []
    for fpath, true_cls in items:
        with Image.open(fpath) as img:
            t = tf_base(img.convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            logits = model(t)
            probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()
        
        if restrict_to_real5:
            # Mask probabilities to the 5 real classes only and renormalize
            mask = np.zeros_like(probs)
            for idx in real_5_indices:
                mask[idx] = probs[idx]
            probs_5 = mask / mask.sum()
            top_indices = np.argsort(probs_5)[::-1]
        else:
            top_indices = np.argsort(probs)[::-1]
        
        top1_idx = int(top_indices[0])
        top2_idx = int(top_indices[1])
        top1_prob = float(probs[top1_idx])
        top2_prob = float(probs[top2_idx])
        margin = float(top1_prob - top2_prob)
        is_correct = bool(top1_idx == true_cls)
        
        records.append({
            "file": fpath,
            "filename": os.path.basename(fpath),
            "true_cls": idx_to_class[true_cls],
            "pred_cls": idx_to_class[top1_idx],
            "top1_prob": top1_prob,
            "top2_prob": top2_prob,
            "margin": margin,
            "is_correct": is_correct
        })
    return records

# Evaluate both standard (11-class logits) and restricted (5-class masked)
records_orig_11 = evaluate_set(val_orig_real5, restrict_to_real5=False)
records_clean_11 = evaluate_set(val_clean_real5, restrict_to_real5=False)

records_orig_5 = evaluate_set(val_orig_real5, restrict_to_real5=True)
records_clean_5 = evaluate_set(val_clean_real5, restrict_to_real5=True)

k_orig_11 = sum(1 for r in records_orig_11 if r["is_correct"])
k_clean_11 = sum(1 for r in records_clean_11 if r["is_correct"])

k_orig_5 = sum(1 for r in records_orig_5 if r["is_correct"])
k_clean_5 = sum(1 for r in records_clean_5 if r["is_correct"])

print("\n" + "=" * 90)
print("EVALUATION COMPARISON:")
print(f"11-Class Model Outputs on 5 Real Classes:")
print(f"  Original Val : {k_orig_11} / {len(records_orig_11)} ({format_wilson(k_orig_11, len(records_orig_11))})")
print(f"  Leak-Free    : {k_clean_11} / {len(records_clean_11)} ({format_wilson(k_clean_11, len(records_clean_11))})")

print(f"\n5-Class Masked Outputs on 5 Real Classes:")
print(f"  Original Val : {k_orig_5} / {len(records_orig_5)} ({format_wilson(k_orig_5, len(records_orig_5))})")
print(f"  Leak-Free    : {k_clean_5} / {len(records_clean_5)} ({format_wilson(k_clean_5, len(records_clean_5))})")

# Let's inspect per-class tables for both
def build_per_class_table(records_orig, records_clean):
    tbl = {}
    for cname in REAL_5_CLASSES.values():
        sub_orig = [r for r in records_orig if r["true_cls"] == cname]
        k_o = sum(1 for r in sub_orig if r["is_correct"])
        n_o = len(sub_orig)
        
        sub_clean = [r for r in records_clean if r["true_cls"] == cname]
        k_c = sum(1 for r in sub_clean if r["is_correct"])
        n_c = len(sub_clean)
        
        tbl[cname] = {
            "original": {"k": k_o, "n": n_o, "str": format_wilson(k_o, n_o)},
            "leak_free": {"k": k_c, "n": n_c, "str": format_wilson(k_c, n_c)},
        }
    return tbl

tbl_11 = build_per_class_table(records_orig_11, records_clean_11)
tbl_5 = build_per_class_table(records_orig_5, records_clean_5)

print("\n" + "=" * 95)
print(f"{'Disease Class':<24} | {'Original Val (11-class)':<34} | {'Leak-Free Val (11-class)':<34}")
print("-" * 95)
for cname, metrics in tbl_11.items():
    print(f"{cname:<24} | {metrics['original']['str']:<34} | {metrics['leak_free']['str']:<34}")
print("-" * 95)
print(f"{'TOTAL (5 Real Classes)':<24} | {format_wilson(k_orig_11, len(records_orig_11)):<34} | {format_wilson(k_clean_11, len(records_clean_11)):<34}")

# Precision-vs-Coverage for top-1 probability and margin floors on the leak-free set
target_clean_records = records_clean_11 # or clean_5
prob_thresholds = [0.0, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90]
margin_thresholds = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]

prob_table = []
for p_th in prob_thresholds:
    retained = [r for r in target_clean_records if r["top1_prob"] >= p_th]
    cov = len(retained) / len(target_clean_records)
    k_ret = sum(1 for r in retained if r["is_correct"])
    prec = (k_ret / len(retained)) if retained else 1.0
    prob_table.append({
        "threshold": p_th,
        "n_retained": len(retained),
        "total": len(target_clean_records),
        "coverage": round(cov, 4),
        "precision": round(prec, 4),
        "wilson_str": format_wilson(k_ret, len(retained)) if retained else "0/0"
    })

margin_table = []
for m_th in margin_thresholds:
    retained = [r for r in target_clean_records if r["margin"] >= m_th]
    cov = len(retained) / len(target_clean_records)
    k_ret = sum(1 for r in retained if r["is_correct"])
    prec = (k_ret / len(retained)) if retained else 1.0
    margin_table.append({
        "threshold": m_th,
        "n_retained": len(retained),
        "total": len(target_clean_records),
        "coverage": round(cov, 4),
        "precision": round(prec, 4),
        "wilson_str": format_wilson(k_ret, len(retained)) if retained else "0/0"
    })

print("\n" + "=" * 80)
print("PRECISION vs COVERAGE: TOP-1 PROBABILITY FLOORS (LEAK-FREE 5 REAL CLASSES)")
print("=" * 80)
print(f"{'Threshold':<12} | {'Retained (n)':<14} | {'Coverage':<12} | {'Precision':<12} | {'Wilson CI'}")
print("-" * 80)
for row in prob_table:
    print(f"{row['threshold']:<12.2f} | {row['n_retained']:<14} | {row['coverage']*100:<11.1f}% | {row['precision']*100:<11.1f}% | {row['wilson_str']}")

print("\n" + "=" * 80)
print("PRECISION vs COVERAGE: MARGIN FLOORS (LEAK-FREE 5 REAL CLASSES)")
print("=" * 80)
print(f"{'Threshold':<12} | {'Retained (n)':<14} | {'Coverage':<12} | {'Precision':<12} | {'Wilson CI'}")
print("-" * 80)
for row in margin_table:
    print(f"{row['threshold']:<12.2f} | {row['n_retained']:<14} | {row['coverage']*100:<11.1f}% | {row['precision']*100:<11.1f}% | {row['wilson_str']}")

final_payload = {
    "n_orig_real5": len(records_orig_11),
    "k_orig_real5": k_orig_11,
    "n_clean_real5": len(records_clean_11),
    "k_clean_real5": k_clean_11,
    "wilson_orig_total": format_wilson(k_orig_11, len(records_orig_11)),
    "wilson_clean_total": format_wilson(k_clean_11, len(records_clean_11)),
    "per_class_table": tbl_11,
    "prob_threshold_table": prob_table,
    "margin_threshold_table": margin_table,
    "raw_records": target_clean_records
}

out_path = os.path.join(RESULTS_DIR, "r6_a7_vit_real_classes.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(final_payload, f, indent=2)

print(f"\nSaved A7 results to {out_path}")
