"""
run_b4_eval_uncertain_and_rejected.py

Part B4 of ArecaVision Round 5:
- 10 rejected negatives: print raw score vs displayed confidence and explain 99.5% capping.
- 3 areca and 3 non-areca in Uncertain band: run through API /api/v1/detect.
- Confirm stage = 'Gatekeeper Uncertain', no disease diagnosis, and verify language handling (en, kn, hi).
- Save results to backend/tests/results/gate_uncertain_and_rejected.json.
"""

import os
import sys
import glob
import json
import time
import requests
import torch
from PIL import Image

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)
os.chdir(_HERE)

from cnn.predict import CNNPredictor

RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

pred = CNNPredictor()

# 1. Ten rejected negatives analysis
neg_pool = [
    os.path.join(_HERE, "tests", "ood_probe", "bus.jpg"),
    os.path.join(_HERE, "tests", "ood_probe", "banana_bunch.jpg"),
    os.path.join(_HERE, "tests", "ood_probe", "banana_single.jpg"),
]

# Pick additional 7 non_areca images with score < 0.5180
non_areca_all = sorted(glob.glob(r"D:\dataset_raw\dataset_raw\non_areca\*.*"))
for f in non_areca_all:
    if len(neg_pool) >= 10:
        break
    label, conf = pred.predict(f)
    if label == "Not_Arecanut":
        neg_pool.append(f)

rejected_results = []
print("=" * 85)
print("PART B4 (1): 10 REJECTED NEGATIVES (RAW SCORE vs DISPLAYED CONFIDENCE)")
print("=" * 85)
header = f"{'Filename':<28} | {'Raw P(areca)':<14} | {'1.0 - raw':<14} | {'Rejection Conf':<16} | {'Displayed Conf'}"
print(header)
print("-" * len(header))

for p in neg_pool:
    pil_img = pred._to_pil(p)
    w, h = pil_img.size
    t_full = pred._tf(pil_img)
    cw, ch = int(w * 0.75), int(h * 0.75)
    cx, cy = (w - cw) // 2, (h - ch) // 2
    center_img = pil_img.crop((cx, cy, cx + cw, cy + ch)) if (cw >= 32 and ch >= 32) else pil_img
    t_center = pred._tf(center_img)
    batch = torch.stack([t_full, t_center], dim=0).to(pred.device)
    probs_batch = pred.model.predict_proba(batch)
    raw_areca = float((probs_batch[0, 0].item() + probs_batch[1, 0].item()) / 2.0)
    
    rejection_conf = max(1.0 - raw_areca, 0.50)
    displayed_conf = min(0.995, float(rejection_conf))
    
    bname = os.path.basename(p)
    print(f"{bname:<28} | {raw_areca:<14.6f} | {1.0 - raw_areca:<14.6f} | {rejection_conf:<16.6f} | {displayed_conf*100:<6.1f}%")
    
    rejected_results.append({
        "file": p,
        "filename": bname,
        "raw_p_areca": raw_areca,
        "one_minus_raw": 1.0 - raw_areca,
        "rejection_conf_raw": rejection_conf,
        "displayed_conf_percent": round(displayed_conf * 100, 1),
        "is_capped_at_99_5": (displayed_conf == 0.995)
    })

# Explanation string
explanation = (
    "Both bus.jpg and the non_areca specimen produce a raw areca score extremely close to 0.0 "
    "(e.g. 0.000000 to 0.001690). Under cnn/predict.py line 88-89, rejection_conf = max(1.0 - areca_score, 0.50), "
    "which evaluates to ~0.9983 to ~0.9999. The displayed confidence is computed as min(0.995, float(rejection_conf)) * 100.0, "
    "which caps the reported probability at exactly 99.5% to prevent claiming 100.0% certainty."
)

# 2. 3 areca and 3 non-areca images in the Uncertain band
areca_uncertain_files = [
    r"D:\dataset_raw\dataset_raw\areca_diseased_fungal_fruit_rot\existing_fruit_rot_21.jpg",
    r"D:\dataset_raw\dataset_raw\areca_diseased_fungal_fruit_rot\existing_fruit_rot_36.jpg",
    r"D:\dataset_raw\dataset_raw\areca_diseased_physiological_nut_cracking\existing_nut_cracking_35.jpg",
]

non_areca_uncertain_files = [
    r"D:\dataset_raw\dataset_raw\non_areca\download_1423.jpg",
    r"D:\dataset_raw\dataset_raw\non_areca\download_172.png",
    r"D:\dataset_raw\dataset_raw\non_areca\download_576.jpeg",
]

uncertain_probes = [("areca", f) for f in areca_uncertain_files] + [("non_areca", f) for f in non_areca_uncertain_files]

API_URL = "http://127.0.0.1:8000/api/v1/detect"
JOBS_URL = "http://127.0.0.1:8000/api/v1/jobs"

print("\n" + "=" * 85)
print("PART B4 (2): 6 UNCERTAIN BAND PROBES THROUGH API")
print("=" * 85)

uncertain_api_results = []
for probe_type, fpath in uncertain_probes:
    bname = os.path.basename(fpath)
    label, conf = pred.predict(fpath)
    print(f"\nSubmitting [{probe_type}] {bname} (predict: {label}, conf={conf:.4f})...")
    
    with open(fpath, "rb") as f:
        resp = requests.post(API_URL, files={"image": (bname, f, "image/jpeg")})
    
    if resp.status_code != 200:
        print(f"Failed to submit: {resp.status_code} {resp.text}")
        continue
    
    j_info = resp.json()
    data = j_info.get("data") if isinstance(j_info.get("data"), dict) else j_info
    job_id = data.get("job_id")
    
    # Poll
    result = None
    start_t = time.time()
    while time.time() - start_t < 30:
        j_resp = requests.get(f"{JOBS_URL}/{job_id}")
        if j_resp.status_code == 200:
            j_body = j_resp.json()
            j_data = j_body.get("data") if isinstance(j_body.get("data"), dict) else j_body
            if j_data.get("status") in ("done", "completed"):
                result = j_data.get("result")
                break
        time.sleep(0.3)
    
    if result:
        stage = result.get("stage")
        disease = result.get("disease")
        has_disease_diag = (disease not in ("Gatekeeper Uncertain", "Not an Arecanut image") and bool(result.get("differentialDiagnosis")))
        retake_photo = result.get("retakePhoto") or {}
        
        print(f"  Result -> Stage: {stage} | Disease: {disease}")
        print(f"  No disease diagnosis confirmed: {not has_disease_diag}")
        print(f"  Language text (EN): {retake_photo.get('en')}")
        print(f"  Language text (KN): [Kannada UTF-8 present: {bool(retake_photo.get('kn'))}, length={len(retake_photo.get('kn', ''))}]")
        print(f"  Language text (HI): [Hindi UTF-8 present: {bool(retake_photo.get('hi'))}, length={len(retake_photo.get('hi', ''))}]")
        
        uncertain_api_results.append({
            "probe_type": probe_type,
            "filename": bname,
            "job_id": job_id,
            "raw_gate_score": conf,
            "returned_stage": stage,
            "returned_disease": disease,
            "has_disease_diagnosis": bool(has_disease_diag),
            "retakePhoto_en": retake_photo.get("en"),
            "retakePhoto_kn": retake_photo.get("kn"),
            "retakePhoto_hi": retake_photo.get("hi"),
            "stage_is_gatekeeper_uncertain": (stage == "Gatekeeper Uncertain"),
        })

output_data = {
    "rejected_negatives_10": rejected_results,
    "capping_explanation": explanation,
    "uncertain_band_probes": uncertain_api_results
}

out_file = os.path.join(RESULTS_DIR, "gate_uncertain_and_rejected.json")
with open(out_file, "w") as f:
    json.dump(output_data, f, indent=2)

print(f"\nSaved results to {out_file}")
