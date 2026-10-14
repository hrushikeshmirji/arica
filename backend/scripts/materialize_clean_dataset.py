"""
backend/scripts/materialize_clean_dataset.py — Materialize the clean, curated dataset into train/val splits.
Standardizes images into clean RGB JPEGs with zero cross-contamination.
"""

import os
import sys
import json
import shutil
import random
from PIL import Image, ImageOps

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MANIFEST_PATH = os.path.join(REPO_ROOT, "backend", "data", "curated_clean_dataset_manifest.json")
OUTPUT_DIR = os.path.join(REPO_ROOT, "backend", "data", "dataset_clean_v1")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

curated = manifest["curated_dataset"]

train_dir = os.path.join(OUTPUT_DIR, "train")
val_dir = os.path.join(OUTPUT_DIR, "val")

# Clean existing target
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(train_dir, exist_ok=True)
os.makedirs(val_dir, exist_ok=True)

# Deterministic random seed
rng = random.Random(42)

summary = {}

for cls, items in curated.items():
    cls_train_dir = os.path.join(train_dir, cls)
    cls_val_dir = os.path.join(val_dir, cls)
    os.makedirs(cls_train_dir, exist_ok=True)
    os.makedirs(cls_val_dir, exist_ok=True)
    
    # Shuffle deterministically
    shuffled = list(items)
    rng.shuffle(shuffled)
    
    # 80/20 split (min 2 in val)
    n_val = max(2, int(len(shuffled) * 0.20))
    val_items = shuffled[:n_val]
    train_items = shuffled[n_val:]
    
    # Process train
    for i, item in enumerate(train_items):
        src_path = item["filepath"]
        dst_name = f"{cls}_train_{i+1:03d}.jpg"
        dst_path = os.path.join(cls_train_dir, dst_name)
        try:
            with Image.open(src_path) as im:
                im = ImageOps.exif_transpose(im)
                if im.mode != "RGB":
                    im = im.convert("RGB")
                # Resize if excessively large to keep training fast while preserving pathology
                im.thumbnail((640, 640), Image.Resampling.LANCZOS)
                im.save(dst_path, "JPEG", quality=95)
        except Exception as e:
            print(f"Error copying {src_path}: {e}")

    # Process val
    for i, item in enumerate(val_items):
        src_path = item["filepath"]
        dst_name = f"{cls}_val_{i+1:03d}.jpg"
        dst_path = os.path.join(cls_val_dir, dst_name)
        try:
            with Image.open(src_path) as im:
                im = ImageOps.exif_transpose(im)
                if im.mode != "RGB":
                    im = im.convert("RGB")
                im.thumbnail((640, 640), Image.Resampling.LANCZOS)
                im.save(dst_path, "JPEG", quality=95)
        except Exception as e:
            print(f"Error copying {src_path}: {e}")

    summary[cls] = {"train": len(train_items), "val": len(val_items), "total": len(items)}
    print(f"Class {cls:<22}: Train={len(train_items):<3} | Val={len(val_items):<3} | Total={len(items)}")

print("\n" + "="*70)
print(f"TOTAL CLEAN DATASET MATERIALIZED AT: {OUTPUT_DIR}")
print(f"  Total Train: {sum(s['train'] for s in summary.values())}")
print(f"  Total Val:   {sum(s['val'] for s in summary.values())}")
print("="*70)
