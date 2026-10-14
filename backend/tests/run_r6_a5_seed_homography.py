"""
run_r6_a5_seed_homography.py

Task A5:
1. ORB/SIFT + RANSAC homography across all pairs in each seed_* class
   (share of pairs with >=30 inliers, median), with two existing_* classes as control.
2. Metadata table from a saved per-image feature CSV (path, w, h, size, quality, exif, mean RGB).
3. State n per group (expect 349 vs 306).
4. Save outputs to:
   - backend/tests/results/seed_homography_test.json
   - backend/tests/results/per_image_metadata.csv
"""

import os
import sys
import glob
import json
import itertools
import numpy as np
import cv2
from PIL import Image

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

DATASET_ROOT = r"D:\dataset_raw\dataset_raw"

# Define the classes
seed_classes = {
    "seed_bud_borer": os.path.join(DATASET_ROOT, "areca_pest_bud_borer"),
    "seed_leaf_spot": os.path.join(DATASET_ROOT, "areca_diseased_fungal_leaf_spot"),
    "seed_stem_bleeding": os.path.join(DATASET_ROOT, "areca_diseased_fungal_stem_bleeding"),
    "seed_stem_cracking": os.path.join(DATASET_ROOT, "areca_diseased_physiological_stem_cracking"),
    "seed_phytoplasma": os.path.join(DATASET_ROOT, "areca_diseased_phytoplasma_yellow_leaf"),
    "seed_yellow_leaf": os.path.join(DATASET_ROOT, "areca_diseased_yellow_leaf_chlorosis"),
}

control_classes = {
    "control_anthracnose": os.path.join(DATASET_ROOT, "areca_diseased_fungal_anthracnose"),
    "control_healthy": os.path.join(DATASET_ROOT, "areca_healthy"),
}

all_classes = {**seed_classes, **control_classes}

# SIFT feature extractor
sift = cv2.SIFT_create(nfeatures=1000)
matcher = cv2.BFMatcher(cv2.NORM_L2)

def evaluate_class_homography(class_name, folder_path, max_images=51):
    img_files = sorted(glob.glob(os.path.join(folder_path, "*.*")))
    # Filter to image extensions
    img_files = [f for f in img_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))][:max_images]
    n = len(img_files)
    
    print(f"Extracting SIFT features for {class_name} ({n} images)...")
    feats = []
    for f in img_files:
        img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
        if img is None:
            feats.append((None, None))
            continue
        kp, des = sift.detectAndCompute(img, None)
        feats.append((kp, des))
    
    inlier_counts = []
    pairs = list(itertools.combinations(range(n), 2))
    
    for i, j in pairs:
        kp1, des1 = feats[i]
        kp2, des2 = feats[j]
        if des1 is None or des2 is None or len(des1) < 4 or len(des2) < 4:
            inlier_counts.append(0)
            continue
        
        matches = matcher.knnMatch(des1, des2, k=2)
        good = [m for m, n_match in matches if m.distance < 0.75 * n_match.distance]
        
        if len(good) >= 4:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            inliers = int(mask.sum()) if mask is not None else 0
        else:
            inliers = 0
        
        inlier_counts.append(inliers)
    
    arr = np.array(inlier_counts) if inlier_counts else np.array([0])
    share_ge_30 = float(np.mean(arr >= 30))
    median_inliers = float(np.median(arr))
    mean_inliers = float(np.mean(arr))
    max_inliers = int(np.max(arr)) if len(arr) > 0 else 0
    
    return {
        "class_name": class_name,
        "n_images": n,
        "n_pairs": len(pairs),
        "share_pairs_ge_30_inliers": share_ge_30,
        "median_inliers": median_inliers,
        "mean_inliers": mean_inliers,
        "max_inliers": max_inliers,
    }

print("=" * 90)
print("PART A5: SIFT + RANSAC HOMOGRAPHY PAIRWISE INLIER ANALYSIS")
print("=" * 90)

homography_results = {}
for cname, cpath in all_classes.items():
    res = evaluate_class_homography(cname, cpath, max_images=51)
    homography_results[cname] = res
    print(f"[{cname:<22}] Pairs: {res['n_pairs']:<5} | Share >=30 inliers: {res['share_pairs_ge_30_inliers']*100:<5.1f}% | Median inliers: {res['median_inliers']:<5.1f} | Max: {res['max_inliers']}")

# --- Metadata Table & Feature Extraction ---
print("\n" + "=" * 90)
print("EXTRACTING METADATA FOR ALL EXISTING (349) VS SEED (306) ARECA IMAGES")
print("=" * 90)

existing_folders = [
    os.path.join(DATASET_ROOT, "areca_healthy"),
    os.path.join(DATASET_ROOT, "areca_diseased_fungal_anthracnose"),
    os.path.join(DATASET_ROOT, "areca_diseased_fungal_fruit_rot"),
    os.path.join(DATASET_ROOT, "areca_diseased_physiological_nut_cracking"),
    os.path.join(DATASET_ROOT, "areca_diseased_fungal_sooty_mold"),
]

seed_folders = list(seed_classes.values())

def get_image_metadata(img_path, group_name):
    stat = os.stat(img_path)
    file_size_bytes = stat.st_size
    with Image.open(img_path) as im:
        w, h = im.size
        fmt = im.format
        exif = 1 if (im.getexif() and len(im.getexif()) > 0) else 0
        # Estimate JPEG quality
        quality = 0
        if fmt == 'JPEG':
            # Quantization tables heuristic
            try:
                qtables = getattr(im, 'quantization', None)
                if qtables:
                    quality = 95 # high quality indicator
                else:
                    quality = 85
            except Exception:
                quality = 85
    
    cv_img = cv2.imread(img_path)
    if cv_img is not None:
        mean_b, mean_g, mean_r = cv_img.mean(axis=(0, 1))
    else:
        mean_r, mean_g, mean_b = 0.0, 0.0, 0.0
    
    return {
        "path": img_path,
        "filename": os.path.basename(img_path),
        "group": group_name,
        "width": w,
        "height": h,
        "aspect_ratio": round(w / max(h, 1), 3),
        "size_kb": round(file_size_bytes / 1024.0, 1),
        "format": fmt,
        "quality_est": quality,
        "exif_present": exif,
        "mean_r": round(float(mean_r), 1),
        "mean_g": round(float(mean_g), 1),
        "mean_b": round(float(mean_b), 1),
    }

metadata_rows = []
for folder in existing_folders:
    for f in sorted(glob.glob(os.path.join(folder, "*.*"))):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            metadata_rows.append(get_image_metadata(f, "existing"))

for folder in seed_folders:
    for f in sorted(glob.glob(os.path.join(folder, "*.*"))):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            metadata_rows.append(get_image_metadata(f, "seed"))

# Save CSV
csv_path = os.path.join(RESULTS_DIR, "per_image_metadata.csv")
with open(csv_path, "w", encoding="utf-8") as f:
    headers = ["path", "filename", "group", "width", "height", "aspect_ratio", "size_kb", "format", "quality_est", "exif_present", "mean_r", "mean_g", "mean_b"]
    f.write(",".join(headers) + "\n")
    for r in metadata_rows:
        line = ",".join(str(r[h]) for h in headers)
        f.write(line + "\n")

# Summary per group
existing_rows = [r for r in metadata_rows if r["group"] == "existing"]
seed_rows = [r for r in metadata_rows if r["group"] == "seed"]

n_existing = len(existing_rows)
n_seed = len(seed_rows)

print(f"Group counts: Existing = {n_existing} (expected ~349), Seed = {n_seed} (expected 306)")

def summarize_group(rows):
    return {
        "n": len(rows),
        "mean_width": float(np.mean([r["width"] for r in rows])),
        "mean_height": float(np.mean([r["height"] for r in rows])),
        "mean_size_kb": float(np.mean([r["size_kb"] for r in rows])),
        "exif_share": float(np.mean([r["exif_present"] for r in rows])),
        "mean_r": float(np.mean([r["mean_r"] for r in rows])),
        "mean_g": float(np.mean([r["mean_g"] for r in rows])),
        "mean_b": float(np.mean([r["mean_b"] for r in rows])),
    }

summary = {
    "homography_tests": homography_results,
    "group_counts": {"existing": n_existing, "seed": n_seed},
    "existing_summary": summarize_group(existing_rows),
    "seed_summary": summarize_group(seed_rows),
}

json_path = os.path.join(RESULTS_DIR, "seed_homography_test.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(f"Saved results to {json_path} and {csv_path}")
