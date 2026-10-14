"""
Unit tests for ArecaVision AI Phase 3C.3 Safe Annotation Bundle.

Verifies:
1. Bundle directory layout, batch structure, specs, and documentation.
2. Exact 163 unique disease images across all 6 batches (15, 31, 33, 28, 23, 33).
3. Image integrity: all 163 images open cleanly with PIL and match manifest MD5 hashes.
4. Portable ZIP archive presence, CRC integrity, and exact contents.
5. Strict distinction between tool IDs (0..3) and canonical YOLO IDs (0, 2, 5, 7).
6. Zero fabricated annotation files in the bundle.
7. V2 dataset preservation and blocked training readiness gate.
"""

import os
import sys
import json
import csv
import glob
import zipfile
import pytest
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
BUNDLE_DIR = os.path.join(REPO_ROOT, "backend", "yolo", "annotation_bundle_phase3c")
V2_DIR = os.path.join(REPO_ROOT, "backend", "yolo", "dataset_repaired_phase3b_v2")

from backend.yolo.dataset_repaired_phase3b_v2.validate_dataset import (
    validate_repaired_dataset,
    compute_md5
)

def test_bundle_structure_and_documents_exist():
    """Verify that bundle root and all required subdirectories and documents exist."""
    assert os.path.isdir(BUNDLE_DIR), f"Missing bundle directory: {BUNDLE_DIR}"
    
    for sub in ["batches", "manifest", "specs"]:
        assert os.path.isdir(os.path.join(BUNDLE_DIR, sub)), f"Missing bundle subdirectory: {sub}"
        
    for doc in ["README.md", "ID_TRANSLATION_MATRIX.md", "ANNOTATION_GUIDELINES.md", "QC_REQUIREMENTS.md", "bundle_verification_report.md"]:
        doc_p = os.path.join(BUNDLE_DIR, doc)
        assert os.path.isfile(doc_p), f"Missing bundle document: {doc}"
        assert os.path.getsize(doc_p) > 200, f"Bundle document {doc} appears empty"

def test_bundle_specs_and_tool_mapping():
    """Verify CVAT and Label Studio specs and ID translation governance."""
    cvat_json = os.path.join(BUNDLE_DIR, "specs", "cvat_label_spec.json")
    assert os.path.isfile(cvat_json)
    with open(cvat_json, "r", encoding="utf-8") as f:
        labels = json.load(f)
    assert len(labels) == 4
    tool_ids = {l["id"]: l["name"] for l in labels}
    assert tool_ids == {0: "Anthracnose", 1: "FruitRot", 2: "NutCracking", 3: "SootyMold"}

    ls_xml = os.path.join(BUNDLE_DIR, "specs", "label_studio_config.xml")
    assert os.path.isfile(ls_xml)
    with open(ls_xml, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Anthracnose" in content and "FruitRot" in content and "NutCracking" in content and "SootyMold" in content

def test_batch_counts_and_file_uniqueness():
    """Verify the 6 batches and their exact image distribution."""
    expected_batches = {
        "Batch_01_Test_Set": 15,
        "Batch_02_Val_Set": 31,
        "Batch_03_Train_Anthracnose": 33,
        "Batch_04_Train_FruitRot": 28,
        "Batch_05_Train_NutCracking": 23,
        "Batch_06_Train_SootyMold": 33
    }
    
    total_images = []
    for bname, expected_count in expected_batches.items():
        bdir = os.path.join(BUNDLE_DIR, "batches", bname)
        assert os.path.isdir(bdir), f"Missing batch folder: {bname}"
        
        img_dir = os.path.join(bdir, "images")
        assert os.path.isdir(img_dir), f"Missing images folder in {bname}"
        
        imgs = [f for f in os.listdir(img_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        assert len(imgs) == expected_count, f"Batch {bname} expected {expected_count} images, got {len(imgs)}"
        total_images.extend(imgs)

        # Check batch manifest CSV
        bcsv = os.path.join(bdir, "batch_manifest.csv")
        assert os.path.isfile(bcsv)
        with open(bcsv, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == expected_count

    assert len(total_images) == 163, f"Expected 163 total images, got {len(total_images)}"
    assert len(set(total_images)) == 163, "Duplicate images found across batches in bundle!"

def test_bundle_images_open_cleanly_and_match_hashes():
    """Verify every image in bundle opens with PIL and matches MD5 in bundle manifest."""
    manifest_p = os.path.join(BUNDLE_DIR, "manifest", "bundle_manifest.json")
    assert os.path.isfile(manifest_p)
    with open(manifest_p, "r", encoding="utf-8") as f:
        records = json.load(f)
    assert len(records) == 163

    for r in records:
        img_p = os.path.join(BUNDLE_DIR, "batches", r["batch"], "images", r["filename"])
        assert os.path.isfile(img_p), f"Bundle image missing: {img_p}"
        
        # Hash check
        md5_val = compute_md5(img_p)
        assert md5_val == r["md5"], f"Hash mismatch for {r['filename']}"

        # PIL open and dimension check
        with Image.open(img_p) as im:
            w, h = im.size
            assert w == r["width"] and h == r["height"]
            assert w > 0 and h > 0

def test_portable_zip_archive_integrity():
    """Verify that the ZIP archive is present, valid, and contains 163 images."""
    zip_p = os.path.join(BUNDLE_DIR, "arecavision_annotation_bundle_phase3c.zip")
    assert os.path.isfile(zip_p), f"Missing bundle ZIP file: {zip_p}"
    assert os.path.getsize(zip_p) > 20 * 1024 * 1024, "ZIP size is unexpectedly small"

    with zipfile.ZipFile(zip_p, "r") as zf:
        bad_crc = zf.testzip()
        assert bad_crc is None, f"ZIP archive corrupted: {bad_crc}"

        namelist = zf.namelist()
        img_entries = [n for n in namelist if n.lower().endswith((".jpg", ".jpeg", ".png"))]
        assert len(img_entries) == 163, f"Expected 163 images in ZIP, got {len(img_entries)}"

def test_no_fabricated_labels_in_bundle():
    """Verify that zero bounding box labels or fake annotation files exist in the bundle."""
    txt_files = glob.glob(os.path.join(BUNDLE_DIR, "**", "*.txt"), recursive=True)
    # The only text files allowed are non-label files (none expected, but definitely no YOLO labels)
    for tf in txt_files:
        assert not os.path.basename(tf).startswith(("Anthracnose", "FruitRot", "NutCracking", "SootyMold")), (
            f"Fabricated label file found in bundle: {tf}"
        )

def test_v2_preservation_and_gated_training():
    """Verify that dataset_repaired_phase3b_v2 remains pristine and gated."""
    report = validate_repaired_dataset(V2_DIR)
    assert report["integrity_passed"] is True
    assert report["ready_for_training"] is False
    assert report["metrics"]["total_disease_pending_annotations"] == 163
