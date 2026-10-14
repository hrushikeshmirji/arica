"""
backend/scripts/audit_and_clean_manifest.py — Clean, deduplicate, and curate the master dataset from D:/dataset.
Resolves cross-disease duplicate collisions, removes HTML/corrupted files, and generates a clean manifest.
"""

import os
import sys
import json
import hashlib
from collections import defaultdict
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))
import config

TARGET_CLASSES = config.DISEASE_CLASSES

# Mapping of raw folders to canonical classes
FOLDER_CLASS_MAP = {
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "fruit_rot": "FruitRot",
    
    "areca_diseased_physiological_nut_cracking": "NutCracking",
    "nut_cracking": "NutCracking",
    
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "anthracnose": "Anthracnose",
    
    "areca_diseased_fungal_sooty_mold": "SootyMold",
    "sooty_mold": "SootyMold",
    
    "areca_healthy": "Healthy",
    "healthy": "Healthy",
    
    "areca_diseased_phytoplasma_yellow_leaf": "PhytoplasmaYellowLeaf",
    "areca_diseased_yellow_leaf_chlorosis": "YellowLeaf",
    
    "areca_diseased_fungal_stem_bleeding": "StemBleeding",
    "areca_diseased_physiological_stem_cracking": "StemCracking",
    "areca_pest_bud_borer": "BudBorer",
    "areca_diseased_fungal_leaf_spot": "LeafSpotComplex",
}

DATASET_ROOT = "D:/dataset"
DRIVE_ROOT = "D:/drive-download-20261013T133028Z-1-001"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

print("="*70)
print("AUDITING AND CURATING DATASET FROM D:/dataset AND GOOGLE DRIVE DOWNLOAD")
print("="*70)

# 1. Collect all candidates
raw_candidates = defaultdict(lambda: defaultdict(list))
corrupted_files = []

for root_dir in [DATASET_ROOT, DRIVE_ROOT]:
    if not os.path.exists(root_dir):
        continue
    for fld in os.listdir(root_dir):
        if fld in FOLDER_CLASS_MAP:
            target_cls = FOLDER_CLASS_MAP[fld]
            folder_path = os.path.join(root_dir, fld)
            for fname in os.listdir(folder_path):
                fpath = os.path.join(folder_path, fname)
                if os.path.isfile(fpath):
                    # Validate image
                    try:
                        with Image.open(fpath) as im:
                            w, h = im.size
                            fmt = im.format
                            if w < 64 or h < 64:
                                corrupted_files.append((fpath, f"Too small: ({w}, {h})"))
                                continue
                        # Hash
                        h_val = sha256_file(fpath)
                        raw_candidates[h_val][target_cls].append((fpath, fname, fld, (w, h), fmt))
                    except Exception as e:
                        corrupted_files.append((fpath, str(e)))

print(f"Total corrupted/invalid non-image files rejected: {len(corrupted_files)}")
print(f"Total unique valid images across all folders: {len(raw_candidates)}")

# 2. Resolve collisions
curated_dataset = defaultdict(list)
disambiguated_log = []
discarded_ambiguous = []

for h_val, class_occurrences in raw_candidates.items():
    assigned_class = None
    all_classes = list(class_occurrences.keys())
    
    if len(all_classes) == 1:
        # Clean single-class image!
        assigned_class = all_classes[0]
        sample = class_occurrences[assigned_class][0]
        curated_dataset[assigned_class].append({
            "sha256": h_val,
            "filepath": sample[0],
            "filename": sample[1],
            "source_folder": sample[2],
            "size": sample[3],
            "format": sample[4]
        })
    else:
        # Cross-class collision!
        # Rule 1: FruitRot vs NutCracking
        # All 32 collisions originated as 'existing_fruit_rot_*' or were verified fruit rot bunches
        if set(all_classes) == {"FruitRot", "NutCracking"}:
            assigned_class = "FruitRot"
            disambiguated_log.append({
                "sha256": h_val,
                "classes_found": all_classes,
                "resolved_to": "FruitRot",
                "reason": "Image originally from FruitRot; depicts rotting fallen nuts/bunches; purged from NutCracking"
            })
            sample = class_occurrences["FruitRot"][0]
            curated_dataset["FruitRot"].append({
                "sha256": h_val,
                "filepath": sample[0],
                "filename": sample[1],
                "source_folder": sample[2],
                "size": sample[3],
                "format": sample[4]
            })
        elif "Healthy" in all_classes:
            # If an image appears in both a disease and Healthy, it CANNOT be Healthy.
            # Discard to avoid noise or contamination
            discarded_ambiguous.append({
                "sha256": h_val,
                "classes_found": all_classes,
                "action": "DISCARDED",
                "reason": "Contradiction between Healthy and Diseased"
            })
        elif set(all_classes) == {"Anthracnose", "SootyMold"}:
            # Ambiguous foliar lesion vs mold; discard to maintain pristine separation
            discarded_ambiguous.append({
                "sha256": h_val,
                "classes_found": all_classes,
                "action": "DISCARDED",
                "reason": "Ambiguous foliar collision between Anthracnose and SootyMold"
            })
        else:
            discarded_ambiguous.append({
                "sha256": h_val,
                "classes_found": all_classes,
                "action": "DISCARDED",
                "reason": f"Multi-class contradiction: {all_classes}"
            })

print("\n--- CURATION RESULTS ---")
print(f"Total cleanly curated images: {sum(len(v) for v in curated_dataset.values())}")
print(f"Total disambiguated collisions (FruitRot recovered): {len(disambiguated_log)}")
print(f"Total ambiguous collisions safely discarded: {len(discarded_ambiguous)}")

print("\nPer-Class Clean Image Counts:")
for cls in TARGET_CLASSES:
    print(f"  {cls:<22}: {len(curated_dataset[cls])} clean images")

# Also include the user's real Fruit Rot photo in FruitRot!
USER_UPLOAD = os.path.join(REPO_ROOT, "backend", "data", "uploads", "job-bfd163d5cc18.jpg")
if os.path.exists(USER_UPLOAD):
    u_h = sha256_file(USER_UPLOAD)
    curated_dataset["FruitRot"].append({
        "sha256": u_h,
        "filepath": USER_UPLOAD,
        "filename": "user_real_fruit_rot_sample.jpg",
        "source_folder": "user_uploads",
        "size": (374, 534),
        "format": "JPEG"
    })
    print(f"  [+] Added user's real field Fruit Rot image (job-bfd163d5cc18.jpg) to FruitRot class!")

# Save manifest
manifest_path = os.path.join(REPO_ROOT, "backend", "data", "curated_clean_dataset_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump({
        "class_counts": {cls: len(curated_dataset[cls]) for cls in TARGET_CLASSES},
        "curated_dataset": curated_dataset,
        "disambiguated_log": disambiguated_log,
        "discarded_ambiguous": discarded_ambiguous,
        "corrupted_files_count": len(corrupted_files)
    }, f, indent=2)

print(f"\nSaved curated manifest to: {manifest_path}")
