"""
Unit tests for ArecaVision AI Phase 3B.2 Repaired YOLO Dataset (v2 Workspace).

Verifies:
1. Workspace directory layout and 11-class YAML configuration.
2. 100% total file conservation (217 active + 132 quarantined = 349).
3. Complete eradication of both exact-hash and perceptual-hash cross-split leakage.
4. Quarantine isolation of all 132 duplicate and near-duplicate conflict files (62 clusters).
5. Strict 0-byte negative background label enforcement (54 healthy images).
6. Total absence of synthetic (0.5, 0.5, 0.9, 0.9) boxes in active labels.
7. Programmatic training readiness gate (ready_for_training == False pending 163 manual annotations).
8. Full synchronization across all manifests.
"""

import os
import sys
import glob
import json
import csv
import yaml
import pytest
from collections import defaultdict
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

REPAIRED_V2_DIR = os.path.join(REPO_ROOT, "backend", "yolo", "dataset_repaired_phase3b_v2")

from backend.yolo.dataset_repaired_phase3b_v2.validate_dataset import (
    validate_repaired_dataset,
    CANONICAL_CLASSES,
    compute_md5,
    compute_dhash,
    hamming_distance
)

def test_v2_workspace_directories_exist():
    """Verify that all standard YOLO splits and quarantine folders exist in v2."""
    required_dirs = [
        os.path.join(REPAIRED_V2_DIR, "images", "train"),
        os.path.join(REPAIRED_V2_DIR, "images", "val"),
        os.path.join(REPAIRED_V2_DIR, "images", "test"),
        os.path.join(REPAIRED_V2_DIR, "labels", "train"),
        os.path.join(REPAIRED_V2_DIR, "labels", "val"),
        os.path.join(REPAIRED_V2_DIR, "labels", "test"),
        os.path.join(REPAIRED_V2_DIR, "quarantine", "images"),
        os.path.join(REPAIRED_V2_DIR, "quarantine", "labels"),
    ]
    for d in required_dirs:
        assert os.path.isdir(d), f"Required v2 workspace directory missing: {d}"

def test_v2_dataset_yaml_configuration():
    """Verify that dataset.yaml in v2 preserves the canonical 11-class schema."""
    yaml_path = os.path.join(REPAIRED_V2_DIR, "dataset.yaml")
    assert os.path.isfile(yaml_path), f"dataset.yaml missing at {yaml_path}"
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
        
    assert cfg.get("nc") == 11, f"Expected nc=11, got {cfg.get('nc')}"
    names = cfg.get("names", {})
    assert len(names) == 11, f"Expected 11 class names, got {len(names)}"
    
    for idx, cname in CANONICAL_CLASSES.items():
        assert names.get(idx) == cname or names.get(str(idx)) == cname, (
            f"Class {idx} mismatch: expected {cname}, got {names.get(idx)}"
        )

def test_v2_total_file_conservation():
    """Verify that all 349 original images are accounted for in v2 without data loss."""
    train_imgs = glob.glob(os.path.join(REPAIRED_V2_DIR, "images", "train", "*.*"))
    val_imgs = glob.glob(os.path.join(REPAIRED_V2_DIR, "images", "val", "*.*"))
    test_imgs = glob.glob(os.path.join(REPAIRED_V2_DIR, "images", "test", "*.*"))
    quarantine_imgs = glob.glob(os.path.join(REPAIRED_V2_DIR, "quarantine", "images", "*.*"))
    
    assert len(train_imgs) == 157, f"Expected 157 train images in v2, got {len(train_imgs)}"
    assert len(val_imgs) == 40, f"Expected 40 val images in v2, got {len(val_imgs)}"
    assert len(test_imgs) == 20, f"Expected 20 test images in v2, got {len(test_imgs)}"
    assert len(quarantine_imgs) == 132, f"Expected 132 quarantine images in v2, got {len(quarantine_imgs)}"
    
    total_active = len(train_imgs) + len(val_imgs) + len(test_imgs)
    assert total_active == 217, f"Expected 217 active images in v2, got {total_active}"
    assert total_active + len(quarantine_imgs) == 349, (
        f"Total count must equal 349, got {total_active + len(quarantine_imgs)}"
    )

def test_v2_quarantine_isolation_and_no_active_leakage():
    """Verify that all 132 duplicate/conflict images are strictly isolated in quarantine."""
    q_dir = os.path.join(REPAIRED_V2_DIR, "quarantine", "images")
    q_imgs = glob.glob(os.path.join(q_dir, "*.*"))
    q_hashes = set(compute_md5(p) for p in q_imgs)
    
    assert len(q_imgs) == 132, f"Expected 132 files in v2 quarantine, found {len(q_imgs)}"
    
    # Assert zero quarantine hash leakage into active splits
    for split in ["train", "val", "test"]:
        split_imgs = glob.glob(os.path.join(REPAIRED_V2_DIR, "images", split, "*.*"))
        for sp in split_imgs:
            sh = compute_md5(sp)
            assert sh not in q_hashes, (
                f"Quarantined duplicate image leaked into active split {split}: {os.path.basename(sp)}"
            )

def test_v2_healthy_negative_zero_byte_labels():
    """Verify that 54 active healthy images have 0-byte empty labels."""
    manifest_path = os.path.join(REPAIRED_V2_DIR, "dataset_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        records = json.load(f)
        
    healthy_records = [r for r in records if r.get("status") == "verified_healthy_background"]
    assert len(healthy_records) == 54, f"Expected 54 active healthy records, found {len(healthy_records)}"
    
    for r in healthy_records:
        split = r["repaired_split"]
        base = os.path.splitext(r["original_filename"])[0]
        lbl_p = os.path.join(REPAIRED_V2_DIR, "labels", split, base + ".txt")
        assert os.path.isfile(lbl_p), f"Missing label file for healthy background image: {lbl_p}"
        assert os.path.getsize(lbl_p) == 0, (
            f"Healthy label file {lbl_p} must be 0 bytes, but was {os.path.getsize(lbl_p)} bytes"
        )

def test_v2_zero_synthetic_boxes_in_active_labels():
    """Verify that synthetic (0.5, 0.5, 0.9, 0.9) boxes are completely absent in v2."""
    for split in ["train", "val", "test"]:
        label_files = glob.glob(os.path.join(REPAIRED_V2_DIR, "labels", split, "*.txt"))
        for lp in label_files:
            if os.path.getsize(lp) > 0:
                with open(lp, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) == 5:
                            coords = [float(x) for x in parts[1:]]
                            assert coords != [0.5, 0.5, 0.9, 0.9], (
                                f"Synthetic placeholder box detected in {lp}: {line}"
                            )

def test_v2_zero_exact_and_perceptual_cross_split_leakage():
    """Verify that active images in v2 have 0 exact and 0 perceptual cross-split duplicates."""
    active_exact_hashes = defaultdict(list)
    active_dhashes = []
    
    for split in ["train", "val", "test"]:
        imgs = glob.glob(os.path.join(REPAIRED_V2_DIR, "images", split, "*.*"))
        for p in imgs:
            fname = os.path.basename(p)
            h = compute_md5(p)
            active_exact_hashes[h].append(split)
            with Image.open(p) as im:
                dh = compute_dhash(im)
            active_dhashes.append({"split": split, "file": fname, "dhash": dh})
            
    # Exact cross-split
    exact_cross = {h: splits for h, splits in active_exact_hashes.items() if len(set(splits)) > 1}
    assert len(exact_cross) == 0, f"Found exact cross-split duplicates in v2: {exact_cross}"
    
    # Perceptual cross-split (Hamming dist <= 2)
    perceptual_cross = []
    for i in range(len(active_dhashes)):
        for j in range(i + 1, len(active_dhashes)):
            i1 = active_dhashes[i]
            i2 = active_dhashes[j]
            if i1["split"] != i2["split"]:
                dist = hamming_distance(i1["dhash"], i2["dhash"])
                if dist <= 2:
                    perceptual_cross.append((i1["split"], i1["file"], i2["split"], i2["file"], dist))
                    
    assert len(perceptual_cross) == 0, f"Found perceptual cross-split near-duplicates in v2: {perceptual_cross}"

def test_v2_programmatic_validator_and_training_gate():
    """Verify that validate_repaired_dataset() passes integrity but strictly gates training."""
    report = validate_repaired_dataset(REPAIRED_V2_DIR)
    
    assert report["integrity_passed"] is True, f"v2 integrity check failed: {report['errors']}"
    assert report["ready_for_training"] is False, (
        "Dataset must NOT be marked ready for training while 163 lesion annotations are pending!"
    )
    assert report["metrics"]["total_disease_pending_annotations"] == 163
    assert report["metrics"]["total_healthy_negative_samples"] == 54
    assert report["metrics"]["quarantined_files"] == 132
    assert report["metrics"]["exact_cross_split_duplicates"] == 0
    assert report["metrics"]["perceptual_cross_split_leakage"] == 0
    assert report["metrics"]["synthetic_boxes_detected"] == 0
    assert "163 disease images require manual focal lesion" in report["training_readiness_reason"]

def test_v2_manifests_exist_and_synchronized():
    """Verify that all manifest documents exist and align with v2 counts."""
    # 1. dataset_manifest.json / .csv
    json_path = os.path.join(REPAIRED_V2_DIR, "dataset_manifest.json")
    csv_path = os.path.join(REPAIRED_V2_DIR, "dataset_manifest.csv")
    assert os.path.isfile(json_path) and os.path.isfile(csv_path)
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    assert len(records) == 349
    
    # 2. quarantine_manifest.json / .md
    q_json = os.path.join(REPAIRED_V2_DIR, "quarantine_manifest.json")
    q_md = os.path.join(REPAIRED_V2_DIR, "quarantine_manifest.md")
    assert os.path.isfile(q_json) and os.path.isfile(q_md)
    with open(q_json, "r", encoding="utf-8") as f:
        q_data = json.load(f)
    assert len(q_data) == 62  # 54 exact MD5 + 8 perceptual near-duplicate clusters
    assert sum(c["copy_count"] for c in q_data) == 132
    
    # 3. images_needing_manual_annotation.csv / .md
    a_csv = os.path.join(REPAIRED_V2_DIR, "images_needing_manual_annotation.csv")
    a_md = os.path.join(REPAIRED_V2_DIR, "images_needing_manual_annotation.md")
    assert os.path.isfile(a_csv) and os.path.isfile(a_md)
    with open(a_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 163
    
    # 4. healthy_background_manifest.md, class_mapping.md, repair_log.md, validation_report.md
    for doc in ["healthy_background_manifest.md", "class_mapping.md", "repair_log.md", "validation_report.md"]:
        doc_p = os.path.join(REPAIRED_V2_DIR, doc)
        assert os.path.isfile(doc_p), f"Missing required document: {doc}"
        assert os.path.getsize(doc_p) > 100, f"Document {doc} appears empty"
