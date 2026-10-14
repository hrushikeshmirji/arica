"""
backend/tests/verify_end_to_end_clean_pipeline.py
Tests the entire 3-stage pipeline end-to-end on clean checkpoints.
"""

import os
import sys
import glob
import cv2
import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

import config
from cnn.predict import CNNPredictor
from yolo.detect import YOLODetector
from vit.predict import ViTPredictor

print("=" * 75)
print("ArecaVision AI — Clean 3-Stage Pipeline Comprehensive Verification")
print("=" * 75)
print(f"Device:          {config.DEVICE}")
print(f"CNN Checkpoint:  {config.CNN_CHECKPOINT}")
print(f"YOLO Checkpoint: {config.YOLO_CHECKPOINT}")
print(f"ViT Checkpoint:  {config.VIT_CHECKPOINT}")
print("-" * 75)

cnn = CNNPredictor()
yolo = YOLODetector()
vit = ViTPredictor()

test_cases = [
    ("User Field Photo (Fruit Rot)", "backend/data/uploads/job-bfd163d5cc18.jpg", "FruitRot"),
    ("Val FruitRot Sample 2", "backend/data/dataset_clean_v1/val/FruitRot/FruitRot_val_002.jpg", "FruitRot"),
    ("Val NutCracking Sample", "backend/data/dataset_clean_v1/val/NutCracking/NutCracking_val_001.jpg", "NutCracking"),
    ("Val Healthy Sample", "backend/data/dataset_clean_v1/val/Healthy/Healthy_val_001.jpg", "Healthy"),
    ("Val Anthracnose Sample", "backend/data/dataset_clean_v1/val/Anthracnose/Anthracnose_val_001.jpg", "Anthracnose"),
    ("Val SootyMold Sample", "backend/data/dataset_clean_v1/val/SootyMold/SootyMold_val_001.jpg", "SootyMold"),
    ("OOD Negative: Bus", "backend/tests/ood_probe/bus.jpg", "Not_Arecanut"),
    ("OOD Negative: Banana", "backend/tests/ood_probe/banana_single.jpg", "Not_Arecanut"),
]

results = []
for desc, path, expected in test_cases:
    if not os.path.exists(path):
        print(f"[SKIP] File not found: {path}")
        continue

    # Load image
    bgr = cv2.imread(path)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # 1. Gatekeeper
    gate_lbl, gate_conf = cnn.predict(rgb)

    # 2. YOLO
    if gate_lbl == "Arecanut":
        yolo_dets, _ = yolo.detect(rgb)
        yolo_crops = [d["crop"] for d in yolo_dets if "crop" in d]
    else:
        yolo_dets = []
        yolo_crops = []

    # 3. ViT TTA Ensemble
    if gate_lbl == "Arecanut":
        vit_out = vit.predict_tta_ensemble(rgb, yolo_crops=yolo_crops)
        diag_label = vit_out["label"]
        diag_conf = vit_out["confidence"]
        top_diff = vit_out.get("differential", [])[:3]
    else:
        diag_label = gate_lbl
        diag_conf = gate_conf
        top_diff = []

    # Check zero-YOLO condition
    is_zero_yolo = (len(yolo_dets) == 0 and diag_label != "Healthy" and gate_lbl == "Arecanut")
    stage = "Rejected" if gate_lbl != "Arecanut" else ("Review Required" if is_zero_yolo else "Detected")

    status = "PASS" if (diag_label == expected or (expected == "Not_Arecanut" and gate_lbl != "Arecanut")) else "FAIL"

    print(f"\nTest: [{desc}]")
    print(f"  Path:       {path}")
    print(f"  Gatekeeper: {gate_lbl} ({gate_conf*100:.1f}%)")
    print(f"  YOLO Dets:  {len(yolo_dets)} boxes")
    for d in yolo_dets[:2]:
        print(f"    -> Box: {d['class_name']} ({d['confidence']*100:.1f}%)")
    print(f"  ViT Diag:   {diag_label} ({diag_conf*100:.1f}%)")
    if top_diff:
        diff_str = ", ".join([f"{d['disease']}: {d['probability']}%" for d in top_diff])
        print(f"  Top Diff:   {diff_str}")
    print(f"  Stage:      {stage}")
    print(f"  Outcome:    [{status}] Expected: {expected} | Actual: {diag_label}")

    results.append({
        "desc": desc,
        "gate_label": gate_lbl,
        "yolo_count": len(yolo_dets),
        "diag_label": diag_label,
        "expected": expected,
        "status": status,
    })

print("\n" + "=" * 75)
print("SUMMARY RESULTS TABLE")
print("=" * 75)
header = f"{'Test Case':<32} | {'Expected':<12} | {'Gatekeeper':<12} | {'YOLO':<6} | {'Diagnosis':<14} | {'Status'}"
print(header)
print("-" * len(header))
for r in results:
    print(f"{r['desc']:<32} | {r['expected']:<12} | {r['gate_label']:<12} | {r['yolo_count']:<6} | {r['diag_label']:<14} | [{r['status']}]")

passes = sum(1 for r in results if r['status'] == 'PASS')
print("-" * len(header))
print(f"Total: {passes}/{len(results)} Passed ({passes/len(results)*100:.1f}%)")
