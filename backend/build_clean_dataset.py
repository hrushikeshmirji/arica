"""
build_clean_dataset.py — Deduplicate, isolate cross-class conflicts, and generate
a leak-free, cluster-aware train/val manifest for ArecaVision.

Rules enforced:
1. Exact duplicates within each class (Hamming = 0) are deduplicated (canonical kept).
2. Every image in label_conflicts.csv without a resolved_label is excluded.
3. Group-aware splitting based on dHash clusters (Hamming <= 6) ensures zero cross-split leakage.
4. All seed_* images are quarantined to train-only; zero seed images in validation.
5. Saves clean manifest to backend/data/clean_dataset_manifest.json and summary to backend/tests/results/clean_dataset_summary.json.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
DATASET_RAW = Path("D:/dataset_raw/dataset_raw")
LABEL_CONFLICTS_CSV = _HERE / "tests" / "results" / "label_conflicts.csv"
OUTPUT_MANIFEST = _HERE / "data" / "clean_dataset_manifest.json"
OUTPUT_SUMMARY = _HERE / "tests" / "results" / "clean_dataset_summary.json"


def dhash(image: Image.Image, hash_size: int = 8) -> int:
    """Compute difference hash (dHash) as 64-bit integer."""
    gray = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.array(gray, dtype=np.int32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    val = 0
    for b in diff.flatten():
        val = (val << 1) | int(b)
    return val


def hamming_distance(h1: int, h2: int) -> int:
    return bin(h1 ^ h2).count("1")


def main() -> None:
    print(f"Loading raw dataset from {DATASET_RAW}...")
    if not DATASET_RAW.exists():
        print(f"Error: Dataset directory {DATASET_RAW} not found!", file=sys.stderr)
        sys.exit(1)

    # 1. Read unresolved conflicts
    conflicted_files = set()
    if LABEL_CONFLICTS_CSV.exists():
        with open(LABEL_CONFLICTS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                resolved = row.get("resolved_label", "").strip()
                if not resolved:
                    conflicted_files.add(row["file"].strip())
    print(f"Identified {len(conflicted_files)} unresolved cross-class conflicted images.")

    # 2. Gather all areca images
    class_folders = [
        d for d in DATASET_RAW.iterdir()
        if d.is_dir() and d.name.startswith("areca_")
    ]
    print(f"Found {len(class_folders)} areca class folders.")

    raw_images = []
    for c_dir in sorted(class_folders):
        c_name = c_dir.name
        for img_path in sorted(c_dir.iterdir()):
            if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                raw_images.append({
                    "path": str(img_path),
                    "filename": img_path.name,
                    "class": c_name,
                    "is_seed": img_path.name.startswith("seed_") or "seed" in c_name.lower(),
                })

    print(f"Total raw images scanned: {len(raw_images)}")

    # 3. Compute dHash for all images
    print("Computing dHash for all images...")
    hashes = {}
    valid_images = []
    corrupt_images = []

    for img_info in raw_images:
        try:
            with Image.open(img_info["path"]) as im:
                h = dhash(im)
                hashes[img_info["filename"]] = h
                valid_images.append(img_info)
        except Exception as e:
            print(f"Warning: Corrupt image {img_info['filename']}: {e}")
            corrupt_images.append(img_info["filename"])

    # 4. Intra-class deduplication (Hamming == 0) and conflict filtering
    excluded_list = []
    retained_images = []

    # Exclude cross-class conflicts first
    after_conflict = []
    for img_info in valid_images:
        fn = img_info["filename"]
        if fn in conflicted_files:
            excluded_list.append({
                "file": fn,
                "class": img_info["class"],
                "reason": "cross_class_conflict",
            })
        else:
            after_conflict.append(img_info)

    print(f"Images remaining after cross-class conflict filter: {len(after_conflict)}")

    # Intra-class exact duplicates (Hamming == 0 within same class)
    by_class = defaultdict(list)
    for img_info in after_conflict:
        by_class[img_info["class"]].append(img_info)

    intra_dedup_count = 0
    for c_name, c_imgs in by_class.items():
        seen_hashes = {}
        for img_info in c_imgs:
            fn = img_info["filename"]
            h = hashes[fn]
            if h in seen_hashes:
                # duplicate
                intra_dedup_count += 1
                excluded_list.append({
                    "file": fn,
                    "class": c_name,
                    "reason": "intra_class_exact_duplicate",
                    "duplicate_of": seen_hashes[h],
                })
            else:
                seen_hashes[h] = fn
                retained_images.append(img_info)

    print(f"Intra-class exact duplicates dropped: {intra_dedup_count}")
    print(f"Unique images retained: {len(retained_images)}")

    # 5. Group-aware clustering (Hamming <= 6)
    # Build graph of retained images
    n = len(retained_images)
    adj = defaultdict(list)
    for i in range(n):
        fn_i = retained_images[i]["filename"]
        h_i = hashes[fn_i]
        for j in range(i + 1, n):
            fn_j = retained_images[j]["filename"]
            h_j = hashes[fn_j]
            if hamming_distance(h_i, h_j) <= 6:
                adj[i].append(j)
                adj[j].append(i)

    # Connected components
    visited = set()
    clusters = []
    for i in range(n):
        if i not in visited:
            comp = []
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop()
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            clusters.append(comp)

    print(f"Total perceptual clusters (Hamming <= 6): {len(clusters)}")

    # 6. Split assignment:
    # - Seed images: quarantined to train-only
    # - Real images: ~80% train, ~20% val cluster-aware
    train_manifest = []
    val_manifest = []

    # Map cluster index to images
    cluster_records = []
    for c_idx, member_indices in enumerate(clusters):
        members = [retained_images[idx] for idx in member_indices]
        has_seed = any(m["is_seed"] for m in members)
        classes_in_cluster = list({m["class"] for m in members})
        cluster_records.append({
            "cluster_id": f"cluster_{c_idx:04d}",
            "members": members,
            "has_seed": has_seed,
            "classes": classes_in_cluster,
            "size": len(members),
        })

    # Sort clusters deterministically for reproducibility
    cluster_records.sort(key=lambda c: (c["has_seed"], -c["size"], c["cluster_id"]))

    # Group clusters by primary class for balanced splitting among real classes
    real_clusters_by_class = defaultdict(list)
    for cr in cluster_records:
        if cr["has_seed"]:
            # Quarantined to train
            for m in cr["members"]:
                train_manifest.append({
                    "file": m["filename"],
                    "path": m["path"],
                    "class": m["class"],
                    "cluster_id": cr["cluster_id"],
                    "is_seed": True,
                    "quarantine_reason": "seed_class_synthetic_origin",
                })
        else:
            primary_c = cr["classes"][0]
            real_clusters_by_class[primary_c].append(cr)

    # Balanced split for real classes
    rng = np.random.RandomState(42)
    for c_name, c_list in real_clusters_by_class.items():
        # shuffle clusters deterministically
        indices = list(range(len(c_list)))
        rng.shuffle(indices)

        # target ~20% val by count
        total_imgs = sum(c_list[idx]["size"] for idx in indices)
        target_val = max(1, round(total_imgs * 0.20))

        val_count = 0
        for idx in indices:
            cr = c_list[idx]
            if val_count + cr["size"] <= target_val or val_count == 0:
                for m in cr["members"]:
                    val_manifest.append({
                        "file": m["filename"],
                        "path": m["path"],
                        "class": m["class"],
                        "cluster_id": cr["cluster_id"],
                        "is_seed": False,
                    })
                val_count += cr["size"]
            else:
                for m in cr["members"]:
                    train_manifest.append({
                        "file": m["filename"],
                        "path": m["path"],
                        "class": m["class"],
                        "cluster_id": cr["cluster_id"],
                        "is_seed": False,
                    })

    # 7. Verification: Zero cross-split leakage
    print("Verifying cross-split isolation (Hamming <= 6)...")
    train_hashes = [hashes[m["file"]] for m in train_manifest]
    val_hashes = [hashes[m["file"]] for m in val_manifest]

    leakage_count = 0
    for vh in val_hashes:
        for th in train_hashes:
            if hamming_distance(vh, th) <= 6:
                leakage_count += 1
                break

    print(f"Cross-split leakage check: {leakage_count} violations (must be 0).")
    assert leakage_count == 0, "Error: Leakage detected between train and val splits!"

    # 8. Summary generation
    train_by_class = defaultdict(int)
    for m in train_manifest:
        train_by_class[m["class"]] += 1

    val_by_class = defaultdict(int)
    for m in val_manifest:
        val_by_class[m["class"]] += 1

    summary = {
        "total_raw": len(raw_images),
        "excluded_conflicts": len(conflicted_files),
        "excluded_intra_duplicates": intra_dedup_count,
        "total_retained": len(retained_images),
        "train_count": len(train_manifest),
        "val_count": len(val_manifest),
        "seed_in_val_count": sum(1 for m in val_manifest if m["is_seed"]),
        "cross_split_leakage_hamming_le_6": leakage_count,
        "train_by_class": dict(train_by_class),
        "val_by_class": dict(val_by_class),
        "total_clusters": len(clusters),
    }

    manifest_data = {
        "metadata": {
            "version": "1.0.0",
            "generator": "build_clean_dataset.py",
            "date": "2026-10-12",
            "leakage_free": True,
            "seed_quarantined": True,
        },
        "summary": summary,
        "train": train_manifest,
        "val": val_manifest,
        "excluded": excluded_list,
    }

    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Saved manifest to {OUTPUT_MANIFEST}")

    OUTPUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {OUTPUT_SUMMARY}")

    print("\n=== CLEAN DATASET SUMMARY ===")
    print(f"Total raw scanned     : {summary['total_raw']}")
    print(f"Cross-class conflicts : {summary['excluded_conflicts']}")
    print(f"Intra-class duplicates: {summary['excluded_intra_duplicates']}")
    print(f"Retained images       : {summary['total_retained']}")
    print(f"Train images          : {summary['train_count']}")
    print(f"Val images            : {summary['val_count']}")
    print(f"Seed in val           : {summary['seed_in_val_count']} (Quarantine verified)")
    print(f"Leakage violations    : {summary['cross_split_leakage_hamming_le_6']} (Isolation verified)")


if __name__ == "__main__":
    main()
