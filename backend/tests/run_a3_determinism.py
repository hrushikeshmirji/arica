"""
run_a3_determinism.py

Part A3 of ArecaVision Round 5:
- Determinism test: send one real areca image through /api/v1/detect 10 times.
- Report variation across runs (disease, confidence, stage, boxes, modelBreakdown, etc.).
- Quote the code that causes any variation.
- Save results to backend/tests/results/determinism_test.json.
"""

import os
import sys
import time
import json
import hashlib
import requests

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

IMAGE_PATH = r"D:\dataset_raw\dataset_raw\areca_healthy\existing_healthy_1.jpg"
API_URL = "http://127.0.0.1:8000/api/v1/detect"
JOBS_URL = "http://127.0.0.1:8000/api/v1/jobs"

print(f"Testing image: {IMAGE_PATH}")
if not os.path.isfile(IMAGE_PATH):
    print(f"Error: {IMAGE_PATH} does not exist!")
    sys.exit(1)

runs_data = []

for i in range(1, 11):
    print(f"\n[Run {i}/10] Submitting image to {API_URL}...")
    with open(IMAGE_PATH, "rb") as f:
        resp = requests.post(API_URL, files={"image": ("existing_healthy_1.jpg", f, "image/jpeg")})
    
    if resp.status_code != 200:
        print(f"Failed to submit: {resp.status_code} {resp.text}")
        continue
    
    job_info = resp.json()
    data = job_info.get("data") if isinstance(job_info.get("data"), dict) else job_info
    job_id = data.get("job_id")
    print(f"Job ID: {job_id}. Polling for completion...")
    
    # Poll job
    poll_url = f"{JOBS_URL}/{job_id}"
    start_t = time.time()
    result = None
    while time.time() - start_t < 30:
        j_resp = requests.get(poll_url)
        if j_resp.status_code == 200:
            j_body = j_resp.json()
            j_data = j_body.get("data") if isinstance(j_body.get("data"), dict) else j_body
            if j_data.get("status") in ("done", "completed"):
                result = j_data.get("result")
                break
            elif j_data.get("status") == "failed":
                print(f"Job failed: {j_data}")
                break
        time.sleep(0.3)
    
    if not result:
        print(f"Job {job_id} timed out or failed to return result!")
        continue
    
    # Analyze components
    att_map = result.get("attentionMap") or ""
    att_hash = hashlib.sha256(att_map.encode("utf-8")).hexdigest() if att_map else None
    
    h_map = result.get("heatmap") or ""
    h_hash = hashlib.sha256(h_map.encode("utf-8")).hexdigest() if h_map else None
    
    record = {
        "run_index": i,
        "job_id": job_id,
        "disease": result.get("disease"),
        "confidence": result.get("confidence"),
        "stage": result.get("stage"),
        "modelBreakdown": result.get("modelBreakdown"),
        "yoloBoxes": result.get("yoloBoxes"),
        "top3": result.get("top3"),
        "inferenceTimeMs": result.get("inferenceTimeMs"),
        "attentionMap_sha256": att_hash,
        "heatmap_sha256": h_hash,
    }
    runs_data.append(record)
    print(f"Run {i} complete: disease={record['disease']}, conf={record['confidence']}, boxes={len(record['yoloBoxes'] or [])}, time={record['inferenceTimeMs']}ms")

# Variation analysis
diseases = set(r["disease"] for r in runs_data)
confidences = [r["confidence"] for r in runs_data]
stages = set(r["stage"] for r in runs_data)
breakdowns = [json.dumps(r["modelBreakdown"], sort_keys=True) for r in runs_data]
boxes_repr = [json.dumps(r["yoloBoxes"], sort_keys=True) for r in runs_data]
top3_repr = [json.dumps(r["top3"], sort_keys=True) for r in runs_data]
att_hashes = set(r["attentionMap_sha256"] for r in runs_data)
heat_hashes = set(r["heatmap_sha256"] for r in runs_data)
timings = [r["inferenceTimeMs"] for r in runs_data if r["inferenceTimeMs"] is not None]

variation_summary = {
    "num_runs": len(runs_data),
    "unique_diseases": list(diseases),
    "is_disease_deterministic": len(diseases) == 1,
    "confidence_min": min(confidences) if confidences else None,
    "confidence_max": max(confidences) if confidences else None,
    "confidence_unique_count": len(set(confidences)),
    "is_confidence_deterministic": len(set(confidences)) == 1,
    "unique_stages": list(stages),
    "is_stage_deterministic": len(stages) == 1,
    "is_modelBreakdown_deterministic": len(set(breakdowns)) == 1,
    "is_yoloBoxes_deterministic": len(set(boxes_repr)) == 1,
    "is_top3_deterministic": len(set(top3_repr)) == 1,
    "unique_attentionMap_hashes": len(att_hashes),
    "is_attentionMap_deterministic": len(att_hashes) == 1,
    "unique_heatmap_hashes": len(heat_hashes),
    "is_heatmap_deterministic": len(heat_hashes) == 1,
    "timing_min_ms": min(timings) if timings else None,
    "timing_max_ms": max(timings) if timings else None,
    "timing_mean_ms": sum(timings) / len(timings) if timings else None,
}

print("\n" + "="*60)
print("DETERMINISM ANALYSIS SUMMARY")
print("="*60)
for k, v in variation_summary.items():
    print(f"{k}: {v}")

output_payload = {
    "summary": variation_summary,
    "runs": runs_data
}

out_file = os.path.join(RESULTS_DIR, "determinism_test.json")
with open(out_file, "w") as f:
    json.dump(output_payload, f, indent=2)

print(f"\nSaved determinism results to {out_file}")
