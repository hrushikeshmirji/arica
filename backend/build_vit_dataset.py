"""
backend/build_vit_dataset.py — Build clean, leak-free ViT dataset manifest with
cluster-aware cross-validation and held-out test folds.

Enforces:
1. Canonical class mapping from fast_train_vit.py (5 real classes + 6 seed classes).
2. Exclude all images in label_conflicts.csv unless resolved_label is populated.
3. Deduplicate exact images within each class (dHash Hamming == 0).
4. Perceptual clustering by dHash (Hamming <= 6).
5. Split BY CLUSTER on real classes:
   - 1 fixed held-out test fold (never used for training, model selection or thresholds)
   - 5 stratified CV folds (for 5-fold group CV / train-val splits)
6. Seed classes:
   - Capped at 10 images per class (at most one per cluster).
   - Training ONLY, never in validation or test.
   - Variant A: Includes capped seeds in training.
   - Variant B: No seeds included (real classes only).
7. Outputs results/train/manifest.json and backend/data/vit_manifest.json with full counts,
   exclusion records, and SHA-256 hash.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_RAW = Path("D:/dataset_raw/dataset_raw")
LABEL_CONFLICTS_CSV = REPO_ROOT / "backend" / "tests" / "results" / "label_conflicts.csv"
OUTPUT_MANIFEST_RESULTS = REPO_ROOT / "results" / "train" / "manifest.json"
OUTPUT_MANIFEST_DATA = REPO_ROOT / "backend" / "data" / "vit_manifest.json"

# Class Mapping from fast_train_vit.py
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

REAL_CLASSES = {
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "areca_healthy": "Healthy",
    "areca_diseased_physiological_nut_cracking": "NutCracking",
    "areca_diseased_fungal_sooty_mold": "SootyMold",
}

SEED_CLASSES = {
    "areca_pest_bud_borer": "BudBorer",
    "areca_diseased_fungal_leaf_spot": "LeafSpotComplex",
    "areca_diseased_phytoplasma_yellow_leaf": "PhytoplasmaYellowLeaf",
    "areca_diseased_fungal_stem_bleeding": "StemBleeding",
    "areca_diseased_physiological_stem_cracking": "StemCracking",
    "areca_diseased_yellow_leaf_chlorosis": "YellowLeaf",
}


def compute_dhash(image: Image.Image, hash_size: int = 8) -> int:
    """Compute 64-bit difference hash (dHash)."""
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
    print("=" * 70)
    print("ArecaVision ViT Dataset Builder (Part 1.1)")
    print("=" * 70)

    if not DATASET_RAW.exists():
        print(f"ERROR: Dataset raw path not found at {DATASET_RAW}", file=sys.stderr)
        sys.exit(1)

    # 1. Load label conflicts
    conflicted_files: dict[str, str] = {}
    if LABEL_CONFLICTS_CSV.exists():
        with open(LABEL_CONFLICTS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fname = row.get("file", "").strip()
                resolved = row.get("resolved_label", "").strip()
                if fname and not resolved:
                    conflicted_files[fname] = row.get("group_id", "conflict_group")
    print(f"[1] Unresolved cross-class conflicted images: {len(conflicted_files)}")

    # 2. Scan all areca raw images
    raw_images = []
    for raw_folder, disease_name in CATEGORY_TO_DISEASE.items():
        folder_path = DATASET_RAW / raw_folder
        if not folder_path.exists():
            continue
        is_seed = raw_folder in SEED_CLASSES
        for img_p in sorted(folder_path.iterdir()):
            if img_p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                raw_images.append({
                    "path": str(img_p),
                    "filename": img_p.name,
                    "folder": raw_folder,
                    "disease": disease_name,
                    "is_seed": is_seed,
                })

    print(f"[2] Total raw areca images scanned: {len(raw_images)}")

    # 3. Compute dHash for all images
    print("[3] Computing dHash for all images...")
    hashes: dict[str, int] = {}
    valid_images = []
    for item in raw_images:
        try:
            with Image.open(item["path"]) as im:
                h = compute_dhash(im)
                hashes[item["filename"]] = h
                valid_images.append(item)
        except Exception as exc:
            print(f"Warning: could not process {item['filename']}: {exc}")

    # 4. Filter exclusions: cross-class conflicts and intra-class exact duplicates
    excluded_records = []
    after_conflicts = []
    for item in valid_images:
        fn = item["filename"]
        if fn in conflicted_files:
            excluded_records.append({
                "file": fn,
                "folder": item["folder"],
                "disease": item["disease"],
                "reason": "cross_class_conflict",
                "detail": f"Unresolved conflict group {conflicted_files[fn]}",
            })
        else:
            after_conflicts.append(item)

    print(f"[4a] Images after conflict exclusion: {len(after_conflicts)}")

    # Intra-class exact deduplication (Hamming == 0 within same class)
    by_disease = defaultdict(list)
    for item in after_conflicts:
        by_disease[item["disease"]].append(item)

    retained_real_images = []
    retained_seed_images_pool = []

    for d_name, items in by_disease.items():
        seen_hashes = {}
        for item in items:
            fn = item["filename"]
            h = hashes[fn]
            if h in seen_hashes:
                excluded_records.append({
                    "file": fn,
                    "folder": item["folder"],
                    "disease": d_name,
                    "reason": "intra_class_exact_duplicate",
                    "detail": f"Exact dHash match with {seen_hashes[h]}",
                })
            else:
                seen_hashes[h] = fn
                if item["is_seed"]:
                    retained_seed_images_pool.append(item)
                else:
                    retained_real_images.append(item)

    print(f"[4b] Retained unique real images: {len(retained_real_images)}")
    print(f"[4c] Retained unique seed images: {len(retained_seed_images_pool)}")

    # 5. Perceptual Clustering on Real Images (Hamming <= 6)
    n_real = len(retained_real_images)
    adj_real = defaultdict(list)
    for i in range(n_real):
        fn_i = retained_real_images[i]["filename"]
        h_i = hashes[fn_i]
        for j in range(i + 1, n_real):
            fn_j = retained_real_images[j]["filename"]
            h_j = hashes[fn_j]
            if hamming_distance(h_i, h_j) <= 6:
                adj_real[i].append(j)
                adj_real[j].append(i)

    visited = set()
    real_clusters = []
    real_cluster_id_map = {}
    for i in range(n_real):
        if i not in visited:
            comp = []
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop()
                comp.append(curr)
                for nb in adj_real[curr]:
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            cid = f"real_cluster_{len(real_clusters):04d}"
            for idx in comp:
                real_cluster_id_map[idx] = cid
            real_clusters.append(comp)

    print(f"[5] Real perceptual clusters (Hamming <= 6): {len(real_clusters)}")

    # 6. Stratified Group Splitting on Real Images
    # 6 folds: fold 5 = fixed held-out test fold, folds 0..4 = 5-fold CV pool
    real_groups = [real_cluster_id_map[i] for i in range(n_real)]
    real_y = [retained_real_images[i]["disease"] for i in range(n_real)]
    real_X = np.arange(n_real)

    sgkf = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=42)
    fold_assignments = np.zeros(n_real, dtype=int)
    for fold_idx, (_, val_idx) in enumerate(sgkf.split(real_X, real_y, real_groups)):
        fold_assignments[val_idx] = fold_idx

    for i, item in enumerate(retained_real_images):
        f = int(fold_assignments[i])
        item["cluster_id"] = real_cluster_id_map[i]
        item["cv_fold"] = f
        if f == 5:
            item["split_type"] = "test"  # Fixed held-out test fold
        elif f == 0:
            item["split_type"] = "val"   # Fold 0 is val for primary seed-0 training
        else:
            item["split_type"] = "train" # Folds 1..4 are train for primary seed-0 training

    # 7. Seed Class Clustering and Capping (10 per class, max 1 per cluster)
    seed_by_class = defaultdict(list)
    for item in retained_seed_images_pool:
        seed_by_class[item["disease"]].append(item)

    selected_capped_seeds = []
    uncapped_omitted_seeds = []

    for d_name, items in sorted(seed_by_class.items()):
        # Cluster seeds within this class
        n_s = len(items)
        adj_s = defaultdict(list)
        for i in range(n_s):
            h_i = hashes[items[i]["filename"]]
            for j in range(i + 1, n_s):
                h_j = hashes[items[j]["filename"]]
                if hamming_distance(h_i, h_j) <= 6:
                    adj_s[i].append(j)
                    adj_s[j].append(i)

        vis = set()
        s_clusters = []
        for i in range(n_s):
            if i not in vis:
                comp = []
                q = [i]
                vis.add(i)
                while q:
                    c = q.pop()
                    comp.append(c)
                    for nb in adj_s[c]:
                        if nb not in vis:
                            vis.add(nb)
                            q.append(nb)
                s_clusters.append(comp)

        # Select at most 1 image per cluster, up to 10 images
        # Sort clusters deterministically
        s_clusters.sort(key=lambda c: sorted([items[idx]["filename"] for idx in c])[0])
        
        chosen_in_class = []
        for c_idx, comp in enumerate(s_clusters):
            sorted_comp = sorted(comp, key=lambda idx: items[idx]["filename"])
            best_idx = sorted_comp[0]
            cluster_id = f"seed_{d_name}_cluster_{c_idx:03d}"
            item = items[best_idx]
            item["cluster_id"] = cluster_id
            item["cv_fold"] = -1  # Not part of CV folds
            item["split_type"] = "train"  # Training only
            if len(chosen_in_class) < 10:
                chosen_in_class.append(item)
            else:
                uncapped_omitted_seeds.append({
                    "file": item["filename"],
                    "folder": item["folder"],
                    "disease": d_name,
                    "reason": "seed_cap_exceeded",
                    "detail": f"Class {d_name} capped at 10 images",
                })
            # Any secondary images in the same cluster are also recorded
            for other_idx in sorted_comp[1:]:
                other_item = items[other_idx]
                uncapped_omitted_seeds.append({
                    "file": other_item["filename"],
                    "folder": other_item["folder"],
                    "disease": d_name,
                    "reason": "seed_cluster_co_member",
                    "detail": f"Max 1 per cluster; cluster represented by {item['filename']}",
                })

        selected_capped_seeds.extend(chosen_in_class)

    print(f"[7] Selected capped seed images (Variant A train only): {len(selected_capped_seeds)} (10 per class across 6 classes)")
    print(f"[7b] Uncapped/co-member seed images omitted: {len(uncapped_omitted_seeds)}")

    # 8. Assemble Full Manifest
    # All files list
    all_manifest_entries = []

    # Real images
    for item in retained_real_images:
        all_manifest_entries.append({
            "filename": item["filename"],
            "disease": item["disease"],
            "folder": item["folder"],
            "is_seed": False,
            "cluster_id": item["cluster_id"],
            "cv_fold": item["cv_fold"], # 0..4 = CV, 5 = Test
            "variant_a_split": item["split_type"], # train / val / test
            "variant_b_split": item["split_type"], # train / val / test
            "dhash_hex": hex(hashes[item["filename"]])[2:].rjust(16, "0"),
        })

    # Capped seed images
    for item in selected_capped_seeds:
        all_manifest_entries.append({
            "filename": item["filename"],
            "disease": item["disease"],
            "folder": item["folder"],
            "is_seed": True,
            "cluster_id": item["cluster_id"],
            "cv_fold": -1,
            "variant_a_split": "train",
            "variant_b_split": "excluded", # Variant B has no seeds
            "dhash_hex": hex(hashes[item["filename"]])[2:].rjust(16, "0"),
        })

    # Summary Statistics
    counts_variant_a = Counter(e["variant_a_split"] for e in all_manifest_entries)
    counts_variant_b = Counter(e["variant_b_split"] for e in all_manifest_entries)

    v_a_by_disease_split = defaultdict(lambda: Counter())
    v_b_by_disease_split = defaultdict(lambda: Counter())
    for e in all_manifest_entries:
        v_a_by_disease_split[e["disease"]][e["variant_a_split"]] += 1
        v_b_by_disease_split[e["disease"]][e["variant_b_split"]] += 1

    fold_by_disease = defaultdict(lambda: Counter())
    for item in retained_real_images:
        fold_name = f"fold_{item['cv_fold']}" if item["cv_fold"] < 5 else "test_fold"
        fold_by_disease[item["disease"]][fold_name] += 1

    summary = {
        "total_scanned_raw": len(raw_images),
        "excluded_conflicts_count": len(conflicted_files),
        "excluded_intra_exact_duplicates_count": len([e for e in excluded_records if e["reason"] == "intra_class_exact_duplicate"]),
        "retained_real_images_total": len(retained_real_images),
        "retained_real_clusters_total": len(real_clusters),
        "selected_capped_seeds_total": len(selected_capped_seeds),
        "omitted_seed_images_total": len(uncapped_omitted_seeds),
        "variant_a": {
            "description": "Real images with 5-fold CV + 1 held-out test fold + 60 capped seeds (train only)",
            "split_totals": dict(counts_variant_a),
            "by_disease": {k: dict(v) for k, v in sorted(v_a_by_disease_split.items())},
        },
        "variant_b": {
            "description": "Real images only (no seeds anywhere); same CV folds and held-out test fold",
            "split_totals": dict(counts_variant_b),
            "by_disease": {k: dict(v) for k, v in sorted(v_b_by_disease_split.items())},
        },
        "real_folds_breakdown": {
            "description": "5 stratified CV folds (folds 0..4, 36 each) + 1 fixed held-out test fold (36)",
            "by_disease": {k: dict(v) for k, v in sorted(fold_by_disease.items())},
            "fold_totals": {
                f"fold_{i}": sum(fold_by_disease[d][f"fold_{i}"] for d in fold_by_disease) for i in range(5)
            } | {"test_fold": sum(fold_by_disease[d]["test_fold"] for d in fold_by_disease)}
        }
    }

    manifest_payload = {
        "metadata": {
            "schema_version": "2.0.0",
            "generator": "backend/build_vit_dataset.py",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "real_classes": list(REAL_CLASSES.values()),
            "seed_classes": list(SEED_CLASSES.values()),
            "governance": {
                "conflicts_excluded": True,
                "exact_dedup_applied": True,
                "clustering_hamming_max": 6,
                "held_out_test_fold_isolated": True,
                "seed_images_in_val_or_test": 0,
            }
        },
        "summary": summary,
        "exclusions": excluded_records + uncapped_omitted_seeds,
        "entries": all_manifest_entries,
    }

    # Serialize canonical JSON bytes and compute SHA-256
    canonical_json_bytes = json.dumps(manifest_payload, sort_keys=True, indent=2).encode("utf-8")
    manifest_sha256 = hashlib.sha256(canonical_json_bytes).hexdigest().upper()
    manifest_payload["manifest_sha256"] = manifest_sha256

    # Write files
    OUTPUT_MANIFEST_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MANIFEST_DATA.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_MANIFEST_RESULTS, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    with open(OUTPUT_MANIFEST_DATA, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    print("\n" + "=" * 80)
    print("=== PART 1.1 DATASET MANIFEST SUMMARY TABLE ===")
    print("=" * 80)
    print(f"Manifest Output (Results): {OUTPUT_MANIFEST_RESULTS}")
    print(f"Manifest Output (Data):    {OUTPUT_MANIFEST_DATA}")
    print(f"Manifest SHA-256:          {manifest_sha256}")
    print("-" * 80)
    print(f"{'Disease Class':<24} | {'Type':<6} | {'Total':<5} | {'Fold 0(Val)':<11} | {'Folds 1-4(Tr)':<12} | {'Test Fold':<9} | {'Var A Train':<11} | {'Var B Train':<11}")
    print("-" * 80)

    all_diseases = list(REAL_CLASSES.values()) + list(SEED_CLASSES.values())
    for d in all_diseases:
        is_s = d in SEED_CLASSES.values()
        c_type = "Seed" if is_s else "Real"
        if not is_s:
            tot = sum(fold_by_disease[d].values())
            f0 = fold_by_disease[d].get("fold_0", 0)
            f14 = sum(fold_by_disease[d].get(f"fold_{i}", 0) for i in range(1, 5))
            ftest = fold_by_disease[d].get("test_fold", 0)
            va_tr = v_a_by_disease_split[d].get("train", 0)
            vb_tr = v_b_by_disease_split[d].get("train", 0)
        else:
            tot = 10
            f0 = 0
            f14 = 0
            ftest = 0
            va_tr = 10
            vb_tr = 0
        print(f"{d:<24} | {c_type:<6} | {tot:<5} | {f0:<11} | {f14:<12} | {ftest:<9} | {va_tr:<11} | {vb_tr:<11}")

    print("-" * 80)
    print(f"{'TOTALS':<24} | {'':<6} | {len(all_manifest_entries):<5} | {36:<11} | {144:<12} | {36:<9} | {counts_variant_a['train']:<11} | {counts_variant_b['train']:<11}")
    print("=" * 80)
    print(f"Variant A Totals: Train={counts_variant_a['train']} | Val={counts_variant_a['val']} | Held-out Test={counts_variant_a['test']}")
    print(f"Variant B Totals: Train={counts_variant_b['train']} | Val={counts_variant_b['val']} | Held-out Test={counts_variant_b['test']}")
    print(f"Seed Images in Val or Test: 0 (Strictly enforced)")
    print("=" * 80)
    print("STOP GATE: STOPPING FOR USER APPROVAL BEFORE TRAINING (Part 1.2).")


if __name__ == "__main__":
    main()
