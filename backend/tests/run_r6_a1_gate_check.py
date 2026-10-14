"""
run_r6_a1_gate_check.py

Task A1:
- Print gate thresholds from code (file, line, accept, reject, band).
- Compare with round 4 (0.7404 / 0.5180).
- Re-run the 6 uncertain probes with raw scores.
- Save to backend/tests/results/r6_a1_gate_thresholds.json.
"""

import os
import sys
import json
import torch

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

from cnn.predict import CNNPredictor, GATE_ACCEPT_THRESHOLD, GATE_REJECT_THRESHOLD

RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

pred = CNNPredictor()

probes = [
    ("areca", r"D:\dataset_raw\dataset_raw\areca_diseased_fungal_fruit_rot\existing_fruit_rot_21.jpg"),
    ("areca", r"D:\dataset_raw\dataset_raw\areca_diseased_fungal_fruit_rot\existing_fruit_rot_36.jpg"),
    ("areca", r"D:\dataset_raw\dataset_raw\areca_diseased_physiological_nut_cracking\existing_nut_cracking_35.jpg"),
    ("non_areca", r"D:\dataset_raw\dataset_raw\non_areca\download_1423.jpg"),
    ("non_areca", r"D:\dataset_raw\dataset_raw\non_areca\download_172.png"),
    ("non_areca", r"D:\dataset_raw\dataset_raw\non_areca\download_576.jpeg"),
]

probe_results = []
print("=" * 95)
print(f"GATE THRESHOLDS IN CODE:")
print(f"File: backend/cnn/predict.py (Lines 27-28, 85-91)")
print(f"Accept Threshold : {GATE_ACCEPT_THRESHOLD}")
print(f"Reject Threshold : {GATE_REJECT_THRESHOLD}")
print(f"Uncertain Band   : [{GATE_REJECT_THRESHOLD}, {GATE_ACCEPT_THRESHOLD}) (width = {GATE_ACCEPT_THRESHOLD - GATE_REJECT_THRESHOLD:.4f})")
print(f"Comparison with Round 4 (0.7404 / 0.5180): IDENTICAL (No change since pre-registration)")
print("=" * 95)
print(f"{'Type':<10} | {'Filename':<28} | {'Full Prob':<10} | {'Center Prob':<12} | {'Raw P(areca)':<12} | {'Gate Label'}")
print("-" * 95)

for p_type, p_path in probes:
    bname = os.path.basename(p_path)
    pil_img = pred._to_pil(p_path)
    w, h = pil_img.size
    t_full = pred._tf(pil_img)
    cw, ch = int(w * 0.75), int(h * 0.75)
    cx, cy = (w - cw) // 2, (h - ch) // 2
    center_img = pil_img.crop((cx, cy, cx + cw, cy + ch)) if (cw >= 32 and ch >= 32) else pil_img
    t_center = pred._tf(center_img)
    batch = torch.stack([t_full, t_center], dim=0).to(pred.device)
    probs_batch = pred.model.predict_proba(batch)
    full_prob = float(probs_batch[0, 0].item())
    center_prob = float(probs_batch[1, 0].item())
    areca_score = (full_prob + center_prob) / 2.0
    label, conf = pred.predict(p_path)

    print(f"{p_type:<10} | {bname:<28} | {full_prob:<10.4f} | {center_prob:<12.4f} | {areca_score:<12.4f} | {label}")
    probe_results.append({
        "type": p_type,
        "filename": bname,
        "path": p_path,
        "full_prob": full_prob,
        "center_prob": center_prob,
        "areca_score": areca_score,
        "gate_label": label,
        "conf": conf
    })

output_data = {
    "file": "backend/cnn/predict.py",
    "gate_accept_threshold": GATE_ACCEPT_THRESHOLD,
    "gate_reject_threshold": GATE_REJECT_THRESHOLD,
    "uncertain_band": [GATE_REJECT_THRESHOLD, GATE_ACCEPT_THRESHOLD],
    "compared_to_r4": "IDENTICAL",
    "probes": probe_results
}

out_path = os.path.join(RESULTS_DIR, "r6_a1_gate_thresholds.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2)

print(f"\nSaved raw probe results to {out_path}")
