"""
Unit tests for ArecaVision AI Phase 3B Repaired YOLO Dataset.

Verifies:
1. Workspace directory layout and configuration integrity.
2. Healthy negative background 0-byte label enforcement.
3. Total eradication of synthetic (0.5, 0.5, 0.9, 0.9) boxes in active labels.
4. Quarantine isolation of 115 conflicting duplicate files (54 clusters).
5. Zero cross-split hash duplication between train, val, and test.
6. Programmatic training readiness gate (ready_for_training == False).
7. Comprehensive manifest synchronization.
"""

import os
import glob
import json
import csv
import hashlib
import yaml
import pytest
from collections import defaultdict
from PIL import Image

import sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

REPAIRED_DIR = os.path.join(REPO_ROOT, "backend", "yolo", "dataset_repaired_phase3b")

from backend.yolo.dataset_repaired_phase3b.validate_dataset import (
    validate_repaired_dataset,
    CANONICAL_CLASSES,
    compute_md5
)

def test_repaired_workspace_directories_exist():
    """Verify that all standard YOLO splits and quarantine folders exist."""
    required_dirs = [
        os.path.join(REPAIRED_DIR, "images", "train"),
        os.path.join(REPAIRED_DIR, "images", "val"),
        os.path.join(REPAIRED_DIR, "images", "test"),
        os.path.join(REPAIRED_DIR, "labels", "train"),
        os.path.join(REPAIRED_DIR, "labels", "val"),
        os.path.join(REPAIRED_DIR, "labels", "test"),
        os.path.join(REPAIRED_DIR, "quarantine", "images"),
        os.path.join(REPAIRED_DIR, "quarantine", "labels"),
    ]
    for d in required_dirs:
        assert os.path.isdir(d), f"Required workspace directory missing: {d}"

def test_dataset_yaml_configuration():
    """Verify that dataset.yaml preserves the canonical 11-class schema."""
    yaml_path = os.path.join(REPAIRED_DIR, "dataset.yaml")
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

def test_total_file_conservation():
    """Verify that all 349 original images are accounted for without data loss."""
    train_imgs = glob.glob(os.path.join(REPAIRED_DIR, "images", "train", "*.*"))
    val_imgs = glob.glob(os.path.join(REPAIRED_DIR, "images", "val", "*.*"))
    test_imgs = glob.glob(os.path.join(REPAIRED_DIR, "images", "test", "*.*"))
    quarantine_imgs = glob.glob(os.path.join(REPAIRED_DIR, "quarantine", "images", "*.*"))
    
    assert len(train_imgs) == 169, f"Expected 169 train images, got {len(train_imgs)}"
    assert len(val_imgs) == 44, f"Expected 44 val images, got {len(val_imgs)}"
    assert len(test_imgs) == 21, f"Expected 21 test images, got {len(test_imgs)}"
    assert len(quarantine_imgs) == 115, f"Expected 115 quarantine images, got {len(quarantine_imgs)}"
    
    total_active = len(train_imgs) + len(val_imgs) + len(test_imgs)
    assert total_active == 234, f"Expected 234 active images, got {total_active}"
    assert total_active + len(quarantine_imgs) == 349, (
        f"Total count must equal 349, got {total_active + len(quarantine_imgs)}"
    )

def test_quarantine_isolation_and_no_active_leakage():
    """Verify that conflicting duplicate images are strictly isolated in quarantine."""
    q_dir = os.path.join(REPAIRED_DIR, "quarantine", "images")
    q_imgs = glob.glob(os.path.join(q_dir, "*.*"))
    q_hashes = set(compute_md5(p) for p in q_imgs)
    
    assert len(q_imgs) == 115, f"Expected 115 files in quarantine, found {len(q_imgs)}"
    assert len(q_hashes) == 54, f"Expected 54 unique conflicting hash clusters, found {len(q_hashes)}"
    
    # Assert zero quarantine hash leakage into active splits
    for split in ["train", "val", "test"]:
        split_imgs = glob.glob(os.path.join(REPAIRED_DIR, "images", split, "*.*"))
        for sp in split_imgs:
            sh = compute_md5(sp)
            assert sh not in q_hashes, (
                f"Quarantined duplicate image leaked into active split {split}: {os.path.basename(sp)}"
            )

def test_healthy_negative_zero_byte_labels():
    """Verify that healthy images have 0-byte empty labels for background suppression."""
    manifest_path = os.path.join(REPAIRED_DIR, "dataset_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        records = json.load(f)
        
    healthy_records = [r for r in records if r.get("status") == "verified_healthy_background"]
    assert len(healthy_records) == 62, f"Expected 62 healthy records, found {len(healthy_records)}"
    
    for r in healthy_records:
        split = r["repaired_split"]
        base = os.path.splitext(r["original_filename"])[0]
        lbl_p = os.path.join(REPAIRED_DIR, "labels", split, base + ".txt")
        assert os.path.isfile(lbl_p), f"Missing label file for healthy background image: {lbl_p}"
        assert os.path.getsize(lbl_p) == 0, (
            f"Healthy label file {lbl_p} must be 0 bytes, but was {os.path.getsize(lbl_p)} bytes"
        )

def test_zero_synthetic_full_frame_boxes_in_active_labels():
    """Verify that synthetic (0.5, 0.5, 0.9, 0.9) boxes are completely eliminated."""
    for split in ["train", "val", "test"]:
        label_files = glob.glob(os.path.join(REPAIRED_DIR, "labels", split, "*.txt"))
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

def test_zero_cross_split_duplicates():
    """Verify that active images have no duplicate leakage across train, val, and test."""
    active_hashes = defaultdict(list)
    for split in ["train", "val", "test"]:
        imgs = glob.glob(os.path.join(REPAIRED_DIR, "images", split, "*.*"))
        for p in imgs:
            h = compute_md5(p)
            active_hashes[h].append(split)
            
    cross_split = {h: splits for h, splits in active_hashes.items() if len(splits) > 1}
    assert len(cross_split) == 0, f"Found cross-split duplicates: {cross_split}"
    assert len(active_hashes) == 234, f"Expected 234 unique hashes, got {len(active_hashes)}"

def test_programmatic_validator_and_training_gate():
    """Verify that validate_repaired_dataset() passes integrity but blocks training."""
    report = validate_repaired_dataset(REPAIRED_DIR)
    
    assert report["integrity_passed"] is True, f"Integrity check failed: {report['errors']}"
    assert report["ready_for_training"] is False, (
        "Dataset must NOT be marked ready for training while 172 lesion annotations are pending!"
    )
    assert report["metrics"]["total_disease_pending_annotations"] == 172
    assert report["metrics"]["total_healthy_negative_samples"] == 62
    assert report["metrics"]["quarantined_files"] == 115
    assert report["metrics"]["synthetic_boxes_detected"] == 0
    assert "172 disease images require manual focal lesion" in report["training_readiness_reason"]

def test_all_manifests_exist_and_consistent():
    """Verify that all manifest documents exist and align with dataset counts."""
    # 1. dataset_manifest.json / .csv
    json_path = os.path.join(REPAIRED_DIR, "dataset_manifest.json")
    csv_path = os.path.join(REPAIRED_DIR, "dataset_manifest.csv")
    assert os.path.isfile(json_path) and os.path.isfile(csv_path)
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    assert len(records) == 349
    
    # 2. quarantine_manifest.json / .md
    q_json = os.path.join(REPAIRED_DIR, "quarantine_manifest.json")
    q_md = os.path.join(REPAIRED_DIR, "quarantine_manifest.md")
    assert os.path.isfile(q_json) and os.path.isfile(q_md)
    with open(q_json, "r", encoding="utf-8") as f:
        q_data = json.load(f)
    assert len(q_data) == 54
    assert sum(c["copy_count"] for c in q_data) == 115
    
    # 3. images_needing_manual_annotation.csv / .md
    a_csv = os.path.join(REPAIRED_DIR, "images_needing_manual_annotation.csv")
    a_md = os.path.join(REPAIRED_DIR, "images_needing_manual_annotation.md")
    assert os.path.isfile(a_csv) and os.path.isfile(a_md)
    with open(a_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 172
    
    # 4. healthy_background_manifest.md, class_mapping.md, repair_log.md, validation_report.md
    for doc in ["healthy_background_manifest.md", "class_mapping.md", "repair_log.md", "validation_report.md"]:
        doc_p = os.path.join(REPAIRED_DIR, doc)
        assert os.path.isfile(doc_p), f"Missing required document: {doc}"
        assert os.path.getsize(doc_p) > 100, f"Document {doc} appears empty"
