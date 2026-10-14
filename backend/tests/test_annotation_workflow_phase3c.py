"""
Unit tests for ArecaVision AI Phase 3C.1 Human Annotation Workflow.

Verifies:
1. Complete correspondence of the 163 disease images with v2 worklist.
2. Presence and integrity of contact sheets and interactive review gallery.
3. Bidirectional Class-ID translation mapping (preventing tool renumbering corruption).
4. Staging manager validation rules (synthetic box rejection, coordinate checks, class consistency).
5. Dataset isolation: Staging writes exclusively to staging directory, leaving v2 dataset untouched.
6. Training readiness gate preservation (ready_for_training == False).
"""

import os
import sys
import json
import csv
import glob
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

V2_DIR = os.path.join(REPO_ROOT, "backend", "yolo", "dataset_repaired_phase3b_v2")
PHASE3C_DIR = os.path.join(REPO_ROOT, "backend", "yolo", "annotation_workflow_phase3c")

from backend.yolo.annotation_workflow_phase3c.staging_manager import (
    TOOL_TO_CANONICAL,
    CANONICAL_IDS,
    get_staging_status,
    validate_and_stage_labels
)
from backend.yolo.dataset_repaired_phase3b_v2.validate_dataset import validate_repaired_dataset

def test_phase3c_directories_and_configs_exist():
    """Verify all workflow directories and configuration files exist."""
    required_paths = [
        PHASE3C_DIR,
        os.path.join(PHASE3C_DIR, "contact_sheets"),
        os.path.join(PHASE3C_DIR, "staging", "raw_exports"),
        os.path.join(PHASE3C_DIR, "staging", "verified_labels", "train"),
        os.path.join(PHASE3C_DIR, "staging", "verified_labels", "val"),
        os.path.join(PHASE3C_DIR, "staging", "verified_labels", "test"),
        os.path.join(PHASE3C_DIR, "annotation_manifest.json"),
        os.path.join(PHASE3C_DIR, "annotation_manifest.csv"),
        os.path.join(PHASE3C_DIR, "annotation_batches.json"),
        os.path.join(PHASE3C_DIR, "cvat_task_config.yaml"),
        os.path.join(PHASE3C_DIR, "cvat_label_spec.json"),
        os.path.join(PHASE3C_DIR, "label_studio_config.xml"),
        os.path.join(PHASE3C_DIR, "ID_TRANSLATION_MATRIX.md"),
        os.path.join(PHASE3C_DIR, "ANNOTATION_GUIDELINES.md"),
        os.path.join(PHASE3C_DIR, "QC_PROTOCOL.md"),
        os.path.join(PHASE3C_DIR, "verification_report.md"),
        os.path.join(PHASE3C_DIR, "visual_review_gallery.html"),
        os.path.join(PHASE3C_DIR, "staging_manager.py"),
    ]
    for p in required_paths:
        assert os.path.exists(p), f"Missing required workflow path: {p}"

def test_annotation_manifest_matches_v2_worklist():
    """Verify that annotation_manifest.json accounts for all 163 pending disease images."""
    v2_csv_path = os.path.join(V2_DIR, "images_needing_manual_annotation.csv")
    with open(v2_csv_path, "r", encoding="utf-8") as f:
        v2_worklist = list(csv.DictReader(f))
    assert len(v2_worklist) == 163

    manifest_json_path = os.path.join(PHASE3C_DIR, "annotation_manifest.json")
    with open(manifest_json_path, "r", encoding="utf-8") as f:
        p3c_manifest = json.load(f)
    assert len(p3c_manifest) == 163

    v2_files = sorted(r["original_filename"] for r in v2_worklist)
    p3c_files = sorted(r["filename"] for r in p3c_manifest)
    assert v2_files == p3c_files

    # Check split breakdown
    split_counts = {s: len([r for r in p3c_manifest if r["split"] == s]) for s in ["train", "val", "test"]}
    assert split_counts == {"train": 117, "val": 31, "test": 15}

    # Check all images exist on disk in v2
    for r in p3c_manifest:
        img_p = os.path.join(V2_DIR, "images", r["split"], r["filename"])
        assert os.path.isfile(img_p), f"Image file missing on disk: {img_p}"

def test_contact_sheets_and_review_gallery():
    """Verify all 6 batch contact sheets and the review gallery are generated."""
    sheet_files = glob.glob(os.path.join(PHASE3C_DIR, "contact_sheets", "*.png"))
    assert len(sheet_files) == 6, f"Expected 6 contact sheets, got {len(sheet_files)}"
    for sf in sheet_files:
        assert os.path.getsize(sf) > 50000, f"Contact sheet {sf} appears too small (<50KB)"

    gallery_html = os.path.join(PHASE3C_DIR, "visual_review_gallery.html")
    with open(gallery_html, "r", encoding="utf-8") as f:
        html = f.read()
    assert "ArecaVision AI" in html
    assert "PENDING HUMAN LESION ANNOTATION" in html
    assert html.count('class="card"') == 163, "Gallery must contain 163 image cards"

def test_class_id_translation_mapping():
    """Verify that annotation tool class IDs are mapped correctly to canonical IDs."""
    assert TOOL_TO_CANONICAL[0] == 0  # Anthracnose -> Canonical 0
    assert TOOL_TO_CANONICAL[1] == 2  # FruitRot -> Canonical 2
    assert TOOL_TO_CANONICAL[2] == 5  # NutCracking -> Canonical 5
    assert TOOL_TO_CANONICAL[3] == 7  # SootyMold -> Canonical 7

    assert CANONICAL_IDS == {0, 2, 5, 7}

def test_staging_manager_synthetic_and_bound_rejection(tmp_path):
    """Verify staging_manager rejects synthetic boxes, invalid coords, and wrong classes."""
    # Create fake raw export directory
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # 1. Synthetic full-frame box
    with open(raw_dir / "Anthracnose_existing_anthracnose_10.txt", "w") as f:
        f.write("0 0.5 0.5 0.9 0.9\n")

    success, staged, errors = validate_and_stage_labels(raw_dir=str(raw_dir), dry_run=True)
    assert not success
    assert any("Synthetic full-frame placeholder box detected" in e for e in errors)

    # 2. Out of range coordinates
    with open(raw_dir / "Anthracnose_existing_anthracnose_10.txt", "w") as f:
        f.write("0 1.5 0.5 0.2 0.2\n")
    success, staged, errors = validate_and_stage_labels(raw_dir=str(raw_dir), dry_run=True)
    assert not success
    assert any("Out of range normalized coordinates" in e for e in errors)

    # 3. Wrong class assignment (NutCracking ID 2 on Anthracnose image)
    with open(raw_dir / "Anthracnose_existing_anthracnose_10.txt", "w") as f:
        f.write("2 0.3 0.3 0.1 0.1\n")
    success, staged, errors = validate_and_stage_labels(raw_dir=str(raw_dir), dry_run=True)
    assert not success
    assert any("mismatches assigned image class" in e for e in errors)

def test_staging_manager_valid_translation_and_staging(tmp_path):
    """Verify staging_manager translates tool IDs 0..3 to canonical IDs and stages cleanly."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # Anthracnose_existing_anthracnose_10 (Tool ID 0 -> Canonical ID 0)
    with open(raw_dir / "Anthracnose_existing_anthracnose_10.txt", "w") as f:
        f.write("0 0.35 0.40 0.15 0.12\n")

    # FruitRot_existing_fruit_rot_30 (Tool ID 1 -> Canonical ID 2)
    with open(raw_dir / "FruitRot_existing_fruit_rot_30.txt", "w") as f:
        f.write("1 0.45 0.55 0.20 0.18\n")

    success, staged, errors = validate_and_stage_labels(raw_dir=str(raw_dir), dry_run=True)
    assert success, f"Validation failed: {errors}"
    assert len(staged) == 2
    assert any(x[0] == "Anthracnose_existing_anthracnose_10.txt" for x in staged)
    assert any(x[0] == "FruitRot_existing_fruit_rot_30.txt" for x in staged)

def test_v2_dataset_preservation_and_training_gate():
    """Verify that v2 dataset was untouched and training readiness remains gated."""
    v2_report = validate_repaired_dataset(V2_DIR)
    assert v2_report["integrity_passed"] is True
    assert v2_report["ready_for_training"] is False
    assert v2_report["metrics"]["total_disease_pending_annotations"] == 163
    assert v2_report["metrics"]["total_healthy_negative_samples"] == 54
    assert v2_report["metrics"]["exact_cross_split_duplicates"] == 0
    assert v2_report["metrics"]["perceptual_cross_split_leakage"] == 0
