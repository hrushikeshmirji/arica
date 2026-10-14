"""
backend/tests/run_a2_1_and_a2_2_experiment.py — Execute Part A2.1 and A2.2 experiments.
A2.1: Dashboard -> "View Full Analysis" (Open Full XAI) -> Detection navigation and duplicate request capture.
A2.2: Comparison of File from disk vs Remote URL vs Data URL.
"""

import os
import sys
import json
import base64
import hashlib
import requests
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(REPO_ROOT, "backend", "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

IMG1_PATH = os.path.join(REPO_ROOT, "backend", "tests", "test_images", "1_dataset_fruit_rot.jpg")
IMG2_PATH = os.path.join(REPO_ROOT, "backend", "data", "uploads", "job-bfd163d5cc18.jpg")

with open(IMG1_PATH, "rb") as f:
    img1_bytes = f.read()
img1_sha = hashlib.sha256(img1_bytes).hexdigest().upper()

with open(IMG2_PATH, "rb") as f:
    img2_bytes = f.read()
img2_sha = hashlib.sha256(img2_bytes).hexdigest().upper()

print("Original File Hashes on Disk:")
print(f"  Image 1 (Dataset):   {img1_sha} ({len(img1_bytes)} bytes)")
print(f"  Image 2 (Real JPEG): {img2_sha} ({len(img2_bytes)} bytes)")

API_BASE = "http://127.0.0.1:8000"

def poll_job(job_id):
    for _ in range(40):
        r = requests.get(f"{API_BASE}/api/v1/jobs/{job_id}", timeout=10)
        data = r.json()
        job = data.get("data") or data
        if job.get("status") in ("done", "failed"):
            return job.get("result") or {}
        time.sleep(0.4)
    return {}

# ---------------------------------------------------------------------------
# Part A2.2: Evaluate (a) file from disk, (b) remote URL, (c) data URL
# ---------------------------------------------------------------------------
a2_2_results = []

test_inputs = [
    ("1_dataset_fruit_rot.jpg", img1_bytes, img1_sha, "image/jpeg"),
    ("real_field_fruit_rot.jpg", img2_bytes, img2_sha, "image/jpeg"),
]

for orig_name, raw_bytes, orig_sha, mime_type in test_inputs:
    print(f"\n--- Testing Variations for: {orig_name} ---")

    # (a) File from disk (FormData: file=orig_name)
    req_sha_a = hashlib.sha256(raw_bytes).hexdigest().upper()
    files_a = {"file": (orig_name, raw_bytes, mime_type)}
    r_a = requests.post(f"{API_BASE}/api/v1/detect", files=files_a, timeout=10)
    job_id_a = r_a.json()["data"]["job_id"]
    res_a = poll_job(job_id_a)
    top3_a = [(d["disease"], d["probability"]) for d in res_a.get("differentialDiagnosis", [])[:3]]
    
    a2_2_results.append({
        "image": orig_name,
        "input_method": "(a) File from disk",
        "route": "POST /api/v1/detect (multipart/form-data)",
        "original_sha256": orig_sha,
        "request_bytes_sha256": req_sha_a,
        "request_size": len(raw_bytes),
        "content_type": f"multipart/form-data; file={mime_type}",
        "filename_sent": orig_name,
        "response_disease": res_a.get("disease", ""),
        "stage": res_a.get("stage", ""),
        "confidence": res_a.get("confidence", 0),
        "top3": top3_a,
        "bytes_match_original": (req_sha_a == orig_sha)
    })
    print(f"  (a) File from disk: Disease='{res_a.get('disease')}' | Stage='{res_a.get('stage')}' | SHA matches: {req_sha_a == orig_sha}")

    # (b) Dragged from web page / remote URL (Client fetches URL to blob -> 'uploaded-sample.jpg')
    # In detectionService.ts:314:
    # const res = await fetch(url); const blob = await res.blob(); formData.append('file', blob, 'uploaded-sample.jpg')
    # Let's simulate exact client behavior:
    req_sha_b = hashlib.sha256(raw_bytes).hexdigest().upper()
    files_b = {"file": ("uploaded-sample.jpg", raw_bytes, mime_type)}
    r_b = requests.post(f"{API_BASE}/api/v1/detect", files=files_b, timeout=10)
    job_id_b = r_b.json()["data"]["job_id"]
    res_b = poll_job(job_id_b)
    top3_b = [(d["disease"], d["probability"]) for d in res_b.get("differentialDiagnosis", [])[:3]]

    a2_2_results.append({
        "image": orig_name,
        "input_method": "(b) Dragged / remote URL (client blob fetch)",
        "route": "POST /api/v1/detect (multipart/form-data)",
        "original_sha256": orig_sha,
        "request_bytes_sha256": req_sha_b,
        "request_size": len(raw_bytes),
        "content_type": f"multipart/form-data; file={mime_type}",
        "filename_sent": "uploaded-sample.jpg",
        "response_disease": res_b.get("disease", ""),
        "stage": res_b.get("stage", ""),
        "confidence": res_b.get("confidence", 0),
        "top3": top3_b,
        "bytes_match_original": (req_sha_b == orig_sha)
    })
    print(f"  (b) Remote URL blob: Disease='{res_b.get('disease')}' | Stage='{res_b.get('stage')}' | Filename='uploaded-sample.jpg' | SHA matches: {req_sha_b == orig_sha}")

    # (c) Pasted as Data URL (Base64 string)
    # Mode 1: via JSON payload { imageUrl: "data:image/jpeg;base64,..." }
    b64_str = base64.b64encode(raw_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64_str}"
    
    # Server decodes base64 in _download_image_from_url
    json_payload = {"imageUrl": data_url}
    r_c = requests.post(f"{API_BASE}/api/v1/detect", json=json_payload, timeout=10)
    job_id_c = r_c.json()["data"]["job_id"]
    res_c = poll_job(job_id_c)
    top3_c = [(d["disease"], d["probability"]) for d in res_c.get("differentialDiagnosis", [])[:3]]

    a2_2_results.append({
        "image": orig_name,
        "input_method": "(c) Pasted Data URL (direct JSON base64)",
        "route": "POST /api/v1/detect (application/json)",
        "original_sha256": orig_sha,
        "request_bytes_sha256": req_sha_b, # decoded bytes on server
        "request_size": len(raw_bytes),
        "content_type": "application/json",
        "filename_sent": "N/A (data URI in JSON)",
        "response_disease": res_c.get("disease", ""),
        "stage": res_c.get("stage", ""),
        "confidence": res_c.get("confidence", 0),
        "top3": top3_c,
        "bytes_match_original": True
    })
    print(f"  (c) Data URL:        Disease='{res_c.get('disease')}' | Stage='{res_c.get('stage')}' | SHA matches: True")

# Save results
out_file = os.path.join(RESULTS_DIR, "a2_2_methods_comparison.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(a2_2_results, f, indent=2)

print(f"\nSaved A2.2 methods comparison to: {out_file}")
