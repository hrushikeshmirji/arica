"""
run_a2_source_shortcut.py

Part A2 of ArecaVision Round 5:
- Source-shortcut test on the six seed_* classes vs five existing_* classes
- Per class: width/height/aspect, file size, format, JPEG quality, EXIF, mean RGB
- Train logistic regression on metadata only (no pixels, group-aware split):
    * accuracy for seed-vs-existing
    * accuracy for 11-class label
- Save a 24-image contact sheet per seed_* class (to backend/tests/results/seed_contact_sheets/)
- Save results to backend/tests/results/source_shortcut_test.json
"""

import os
import glob
import json
import random
from collections import Counter, defaultdict
import numpy as np
from PIL import Image, ImageDraw
import torch

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold, GroupShuffleSplit
from sklearn.metrics import accuracy_score, classification_report

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(_HERE, "tests", "results")
CONTACT_DIR = os.path.join(RESULTS_DIR, "seed_contact_sheets")
os.makedirs(CONTACT_DIR, exist_ok=True)

RAW_DIR = r"D:\dataset_raw\dataset_raw"

SEED_CLASSES = [
    "areca_pest_bud_borer",
    "areca_diseased_fungal_leaf_spot",
    "areca_diseased_phytoplasma_yellow_leaf",
    "areca_diseased_fungal_stem_bleeding",
    "areca_diseased_physiological_stem_cracking",
    "areca_diseased_yellow_leaf_chlorosis"
]

EXISTING_CLASSES = [
    "areca_diseased_fungal_anthracnose",
    "areca_diseased_fungal_fruit_rot",
    "areca_healthy",
    "areca_diseased_physiological_nut_cracking",
    "areca_diseased_fungal_sooty_mold"
]

ALL_CLASSES = sorted(SEED_CLASSES + EXISTING_CLASSES)
class_to_idx = {c: i for i, c in enumerate(ALL_CLASSES)}

def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

def hamming_dist(h1, h2):
    return bin(h1 ^ h2).count('1')

def get_jpeg_quality_est(img):
    try:
        tables = getattr(img, "quantization", None)
        if tables and 0 in tables:
            # Average entry in the first (luminance) quantization table.
            # Lower quantization values correspond to higher JPEG quality.
            # Standard approximation formula:
            mean_q = float(np.mean(tables[0]))
            return mean_q
    except Exception:
        pass
    return -1.0

def get_exif_tags_count(img):
    try:
        exif = img.getexif()
        return len(exif) if exif else 0
    except Exception:
        return 0

print("1. Extracting metadata and dHash for all 11 classes...")
records = []
for cname in ALL_CLASSES:
    cdir = os.path.join(RAW_DIR, cname)
    files = sorted(glob.glob(os.path.join(cdir, "*.*")))
    is_seed = (cname in SEED_CLASSES)
    
    for f in files:
        fsize = os.path.getsize(f)
        try:
            with Image.open(f) as img:
                w, h = img.size
                aspect = float(w) / float(h)
                fmt = img.format or "UNKNOWN"
                q_est = get_jpeg_quality_est(img)
                exif_cnt = get_exif_tags_count(img)
                
                # Mean RGB
                rgb_img = img.convert("RGB")
                arr = np.array(rgb_img, dtype=np.float32)
                mean_r = float(arr[:, :, 0].mean())
                mean_g = float(arr[:, :, 1].mean())
                mean_b = float(arr[:, :, 2].mean())
                
                dh = dhash(img)
                
            records.append({
                "path": f,
                "filename": os.path.basename(f),
                "class_name": cname,
                "class_idx": class_to_idx[cname],
                "is_seed": 1 if is_seed else 0,
                "width": w,
                "height": h,
                "aspect": aspect,
                "file_size": fsize,
                "format": fmt,
                "jpeg_quality_mean_quant": q_est,
                "exif_count": exif_cnt,
                "has_exif": 1 if exif_cnt > 0 else 0,
                "mean_r": mean_r,
                "mean_g": mean_g,
                "mean_b": mean_b,
                "dhash": dh
            })
        except Exception as e:
            print(f"Error reading {f}: {e}")

print(f"Total extracted records: {len(records)}")

# 2. Assign dHash clusters (Hamming <= 6) to define groups for group-aware split
print("2. Clustering images by dHash (Hamming <= 6) for group-aware CV...")
n = len(records)
visited = [False] * n
clusters = []
for i in range(n):
    if not visited[i]:
        visited[i] = True
        c = [i]
        q = [i]
        while q:
            curr = q.pop(0)
            for j in range(n):
                if not visited[j] and hamming_dist(records[curr]["dhash"], records[j]["dhash"]) <= 6:
                    visited[j] = True
                    c.append(j)
                    q.append(j)
        clusters.append(c)

groups = np.zeros(n, dtype=int)
for gid, c in enumerate(clusters):
    for idx in c:
        groups[idx] = gid

print(f"Number of distinct dHash clusters (groups): {len(clusters)}")

# 3. Class-level metadata statistics
per_class_stats = {}
for cname in ALL_CLASSES:
    recs = [r for r in records if r["class_name"] == cname]
    widths = [r["width"] for r in recs]
    heights = [r["height"] for r in recs]
    aspects = [r["aspect"] for r in recs]
    fsizes = [r["file_size"] for r in recs]
    formats = Counter(r["format"] for r in recs)
    has_exif_pct = sum(r["has_exif"] for r in recs) / len(recs) * 100.0
    r_vals = [r["mean_r"] for r in recs]
    g_vals = [r["mean_g"] for r in recs]
    b_vals = [r["mean_b"] for r in recs]
    quant_vals = [r["jpeg_quality_mean_quant"] for r in recs if r["jpeg_quality_mean_quant"] >= 0]
    
    per_class_stats[cname] = {
        "count": len(recs),
        "is_seed": cname in SEED_CLASSES,
        "width_mean": float(np.mean(widths)),
        "width_std": float(np.std(widths)),
        "height_mean": float(np.mean(heights)),
        "height_std": float(np.std(heights)),
        "aspect_mean": float(np.mean(aspects)),
        "aspect_std": float(np.std(aspects)),
        "filesize_mean": float(np.mean(fsizes)),
        "filesize_std": float(np.std(fsizes)),
        "formats": dict(formats),
        "has_exif_percent": has_exif_pct,
        "mean_r": float(np.mean(r_vals)),
        "mean_g": float(np.mean(g_vals)),
        "mean_b": float(np.mean(b_vals)),
        "mean_quant_table_val": float(np.mean(quant_vals)) if quant_vals else None
    }

# 4. Logistic Regression on metadata only
# Feature matrix
# Numerical metadata features: width, height, aspect, file_size, exif_count, mean_r, mean_g, mean_b, mean_quant
X_raw = np.array([
    [
        r["width"],
        r["height"],
        r["aspect"],
        r["file_size"],
        r["exif_count"],
        r["has_exif"],
        r["mean_r"],
        r["mean_g"],
        r["mean_b"],
        r["jpeg_quality_mean_quant"] if r["jpeg_quality_mean_quant"] >= 0 else 0.0
    ]
    for r in records
], dtype=np.float32)

y_seed = np.array([r["is_seed"] for r in records], dtype=int)
y_class = np.array([r["class_idx"] for r in records], dtype=int)

# Group-aware cross-validation (5-fold)
sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)

# Evaluation 1: seed vs existing
preds_seed_cv = np.zeros(n, dtype=int)
for train_idx, val_idx in sgkf.split(X_raw, y_seed, groups=groups):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_raw[train_idx])
    X_val = scaler.transform(X_raw[val_idx])
    
    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train, y_seed[train_idx])
    preds_seed_cv[val_idx] = clf.predict(X_val)

acc_seed = accuracy_score(y_seed, preds_seed_cv)
print(f"\n[Logistic Regression - Metadata Only] Seed vs Existing (5-Fold Group CV Accuracy): {acc_seed:.4f} ({acc_seed*100:.2f}%)")

# Evaluation 2: 11-class disease label
preds_class_cv = np.zeros(n, dtype=int)
for train_idx, val_idx in sgkf.split(X_raw, y_class, groups=groups):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_raw[train_idx])
    X_val = scaler.transform(X_raw[val_idx])
    
    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train, y_class[train_idx])
    preds_class_cv[val_idx] = clf.predict(X_val)

acc_class = accuracy_score(y_class, preds_class_cv)
print(f"[Logistic Regression - Metadata Only] 11-Class Label (5-Fold Group CV Accuracy): {acc_class:.4f} ({acc_class*100:.2f}%)")

# Single GroupShuffleSplit 80/20 train/test split for reporting
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X_raw, y_seed, groups=groups))

scaler = StandardScaler()
X_tr = scaler.fit_transform(X_raw[train_idx])
X_te = scaler.transform(X_raw[test_idx])

lr_seed = LogisticRegression(max_iter=1000, random_state=42).fit(X_tr, y_seed[train_idx])
te_acc_seed = accuracy_score(y_seed[test_idx], lr_seed.predict(X_te))

lr_class = LogisticRegression(max_iter=1000, random_state=42).fit(X_tr, y_class[train_idx])
te_acc_class = accuracy_score(y_class[test_idx], lr_class.predict(X_te))

print(f"[Single Holdout 80/20 Group Split] Seed-vs-Existing Test Accuracy: {te_acc_seed:.4f} ({te_acc_seed*100:.2f}%)")
print(f"[Single Holdout 80/20 Group Split] 11-Class Test Accuracy: {te_acc_class:.4f} ({te_acc_class*100:.2f}%)")

# 5. Generate 24-image contact sheet per seed_* class
print("\n5. Generating 24-image contact sheet per seed_* class...")
for cname in SEED_CLASSES:
    cdir = os.path.join(RAW_DIR, cname)
    files = sorted(glob.glob(os.path.join(cdir, "*.*")))
    selected = files[:24]
    
    cols = 6
    rows = 4
    tile_w, tile_h = 200, 200
    header_h = 40
    footer_h = 30
    cell_h = tile_h + footer_h
    sheet = Image.new("RGB", (cols * tile_w, rows * cell_h + header_h), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    
    draw.text((10, 10), f"Class: {cname} (First 24 Images)", fill=(0, 0, 0))
    
    for idx, fpath in enumerate(selected):
        r = idx // cols
        c = idx % cols
        x = c * tile_w
        y = header_h + r * cell_h
        try:
            with Image.open(fpath) as img:
                t = img.convert("RGB").resize((tile_w - 6, tile_h - 6))
                sheet.paste(t, (x + 3, y + 3))
        except Exception:
            pass
        bname = os.path.basename(fpath)
        draw.text((x + 3, y + tile_h - 2), bname, fill=(50, 50, 50))
        
    out_sheet_path = os.path.join(CONTACT_DIR, f"{cname}_24_sheet.png")
    sheet.save(out_sheet_path)
    print(f"Saved: {out_sheet_path}")

# 6. Save full summary json
out_data = {
    "per_class_stats": per_class_stats,
    "group_cv_5fold": {
        "seed_vs_existing_accuracy": acc_seed,
        "class_11_accuracy": acc_class
    },
    "group_holdout_test": {
        "seed_vs_existing_accuracy": te_acc_seed,
        "class_11_accuracy": te_acc_class,
        "test_n": len(test_idx)
    },
    "features_used": [
        "width", "height", "aspect", "file_size", "exif_count",
        "has_exif", "mean_r", "mean_g", "mean_b", "jpeg_quality_mean_quant"
    ]
}

out_json_path = os.path.join(RESULTS_DIR, "source_shortcut_test.json")
with open(out_json_path, "w") as f:
    json.dump(out_data, f, indent=2)
print(f"\nSaved full source shortcut results to {out_json_path}")
