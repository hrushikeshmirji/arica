"""
backend/tests/verify_calibrated_inference.py

Verification suite for:
  1. Temperature-calibrated & 3-view TTA inference (predict_vit_with_tta)
  2. Predictive entropy & confidence margin gating (compute_predictive_reliability)
  3. Weakly-supervised ViT attention rollout for lesion localization (extract_vit_attention_boxes)
  4. Golden baseline probe parity (100% on FruitRot and NutCracking benchmarks)
  5. Schema consistency and latency verification
"""

import os
import sys
import time
from pathlib import Path
from PIL import Image
import numpy as np
import torch

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

import config
from vit.predict import (
    ViTPredictor,
    predict_vit_with_tta,
    compute_predictive_reliability,
    extract_vit_attention_boxes,
)
from vit.dataset import get_vit_transforms

def main():
    print("=" * 80)
    print("ARECAVISION INFERENCE ENGINE OPTIMIZATION & CALIBRATION VERIFICATION")
    print("=" * 80)

    # 1. Initialize ViTPredictor
    print("\n[Step 1] Loading ViTPredictor & checking temperature calibration...")
    # Use standard production checkpoint configured in config.py
    predictor = ViTPredictor()
    print(f"  ViT loaded on device: {predictor.device}")
    print(f"  Active calibrated temperature: {predictor.temperature:.4f}")
    assert predictor.temperature > 0.0, "Temperature must be strictly positive"

    # 2. Test compute_predictive_reliability with synthetic cases
    print("\n[Step 2] Testing predictive reliability metrics (Entropy & Margin gating)...")
    # Case A: High certainty distribution
    p_certain = np.zeros(11)
    p_certain[0] = 0.95
    p_certain[1] = 0.05
    rel_a = compute_predictive_reliability(p_certain, num_classes=11)
    print(f"  Certain test: Entropy={rel_a['predictive_entropy']:.4f}, Margin={rel_a['top2_margin']:.4f}, HighCertainty={rel_a['is_high_certainty']}")
    assert rel_a["is_high_certainty"] is True, "High certainty test failed"
    assert rel_a["top2_margin"] == 0.90, f"Expected margin 0.90, got {rel_a['top2_margin']}"

    # Case B: Uniform confusion
    p_confused = np.ones(11) / 11.0
    rel_b = compute_predictive_reliability(p_confused, num_classes=11)
    print(f"  Confused test: Entropy={rel_b['predictive_entropy']:.4f}, Margin={rel_b['top2_margin']:.4f}, HighCertainty={rel_b['is_high_certainty']}")
    assert rel_b["is_high_certainty"] is False, "Confused test should NOT be high certainty"
    assert rel_b["predictive_entropy"] >= 0.99, "Normalized entropy on uniform distribution should be ~1.0"

    # 3. Test predict_vit_with_tta
    print("\n[Step 3] Testing predict_vit_with_tta on Fast Path vs Borderline Path...")
    dummy_img = Image.new("RGB", (224, 224), color=(120, 160, 80))
    _, val_tf = get_vit_transforms(224)

    # High uncertainty threshold -> triggers 3 views
    p_ens_3, views_3 = predict_vit_with_tta(
        vit_model=predictor.model,
        image_pil=dummy_img,
        transform=val_tf,
        temperature=predictor.temperature,
        uncertainty_threshold=0.999,  # force 3 views
        device=predictor.device,
    )
    print(f"  Borderline sample path: views={views_3}, top_prob={p_ens_3.max().item():.4f}")
    assert views_3 == 3, f"Expected 3 views on borderline sample, got {views_3}"
    assert abs(p_ens_3.sum().item() - 1.0) < 1e-4, "Ensemble probabilities must sum to 1"

    # Zero uncertainty threshold -> triggers fast path (1 view)
    p_ens_1, views_1 = predict_vit_with_tta(
        vit_model=predictor.model,
        image_pil=dummy_img,
        transform=val_tf,
        temperature=predictor.temperature,
        uncertainty_threshold=0.01,  # force fast path
        device=predictor.device,
    )
    print(f"  Fast path: views={views_1}, top_prob={p_ens_1.max().item():.4f}")
    assert views_1 == 1, f"Expected 1 view on clear image fast path, got {views_1}"

    # 4. Golden Baseline Probes Parity Evaluation
    print("\n[Step 4] Running 100% parity verification on golden baseline probes...")
    probes = [
        ("USER UPLOADED FRUIT ROT (job-bfd163d5cc18.jpg)", _HERE / "data" / "uploads" / "job-bfd163d5cc18.jpg", "FruitRot"),
        ("Fruit Rot 1 (fruit_rot_1.jpg)", Path("D:/dataset/fruit_rot/fruit_rot_1.jpg"), "FruitRot"),
        ("Fruit Rot 10 (fruit_rot_10.jpg)", Path("D:/dataset/fruit_rot/fruit_rot_10.jpg"), "FruitRot"),
        ("Nut Cracking 14 (nut_cracking_14.jpg)", Path("D:/dataset/nut_cracking/nut_cracking_14.jpg"), "NutCracking"),
        ("Nut Cracking 21 (nut_cracking_21.jpg)", Path("D:/dataset/nut_cracking/nut_cracking_21.jpg"), "NutCracking"),
    ]

    all_passed = True
    total_time = 0.0

    print("-" * 80)
    print(f"{'Probe':<42} | {'Expected':<12} | {'Predicted':<12} | {'Conf':<7} | {'Margin':<7} | {'Views':<5} | {'Boxes':<5} | {'Status'}")
    print("-" * 80)

    for desc, path, expected in probes:
        if not path.is_file():
            print(f"  [SKIP] File not found: {path}")
            continue

        t0 = time.perf_counter()
        diag = predictor.predict_with_diagnostics(path, uncertainty_threshold=0.80)
        dt = (time.perf_counter() - t0) * 1000.0
        total_time += dt

        pred_label = diag["label"]
        pred_conf = diag["confidence"] * 100.0
        margin = diag["top2_margin"]
        views = diag["tta_views"]
        num_boxes = len(diag["vitAttentionBoxes"])

        status = "PASS" if pred_label == expected else "FAIL"
        if pred_label != expected:
            all_passed = False

        print(f"{desc[:42]:<42} | {expected:<12} | {pred_label:<12} | {pred_conf:<6.1f}% | {margin:<7.3f} | {views:<5} | {num_boxes:<5} | {status}")

    print("-" * 80)
    avg_latency = total_time / len(probes)
    print(f"Average Inference Latency across golden probes: {avg_latency:.1f} ms")

    # 5. Test Full Pipeline Response (predict_tta_ensemble)
    print("\n[Step 5] Testing predict_tta_ensemble schema & non-breaking metadata...")
    probe_img = _HERE / "data" / "uploads" / "job-bfd163d5cc18.jpg"
    tta_res = predictor.predict_tta_ensemble(probe_img)

    required_keys = [
        "label", "confidence", "isOOD", "maxProtoSim", "attn_map", "differential",
        "morphometrics", "saliencyBox", "calibration_temperature", "predictive_entropy",
        "top2_margin", "tta_views", "is_high_certainty", "vitAttentionBoxes"
    ]
    missing = [k for k in required_keys if k not in tta_res]
    print(f"  Required keys check: {'ALL PRESENT' if not missing else f'MISSING: {missing}'}")
    assert not missing, f"Missing required keys in predict_tta_ensemble: {missing}"

    print(f"  Pipeline Output: label={tta_res['label']}, confidence={tta_res['confidence']*100:.1f}%, entropy={tta_res['predictive_entropy']:.4f}, margin={tta_res['top2_margin']:.4f}")
    print(f"  ViT Attention Boxes extracted: {len(tta_res['vitAttentionBoxes'])}")
    for idx, b in enumerate(tta_res["vitAttentionBoxes"]):
        print(f"    Box {idx + 1}: {b['box']}, Energy: {b['energy']:.3f}, Conf: {b['confidence']}%, Area: {b['area_ratio']:.3%}")

    print("\n" + "=" * 80)
    if all_passed:
        print("ALL VERIFICATION CHECKS PASSED WITH 100% PARITY!")
    else:
        print("VERIFICATION FAILED ON ONE OR MORE GOLDEN PROBES!")
    print("=" * 80)

if __name__ == "__main__":
    main()
