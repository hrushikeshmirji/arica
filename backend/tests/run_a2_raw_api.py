"""
backend/tests/run_a2_raw_api.py — Run A2 part (i): Raw API POST /api/v1/detect (5 repeats per image).
"""

import os
import sys
import time
import json
import hashlib
import requests

API_URL = "http://127.0.0.1:8000/api/v1/detect"
JOBS_URL = "http://127.0.0.1:8000/api/v1/jobs"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_DIR = os.path.join(REPO_ROOT, "backend", "tests", "test_images")
RESULTS_DIR = os.path.join(REPO_ROOT, "backend", "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

test_images = [
    ("1_dataset_fruit_rot", os.path.join(TEST_DIR, "1_dataset_fruit_rot.jpg")),
    ("2_dataset_healthy", os.path.join(TEST_DIR, "2_dataset_healthy.jpg")),
    ("3_alpha_png", os.path.join(TEST_DIR, "3_alpha.png")),
    ("4_format_webp", os.path.join(TEST_DIR, "4_format.webp")),
    ("5_exif_rotated", os.path.join(TEST_DIR, "5_exif_rotated.jpg")),
    ("6_non_areca", os.path.join(TEST_DIR, "6_non_areca.jpg")),
]

results = {}

print("=== PART A2: RAW API EXPERIMENT (5 REPEATS PER IMAGE) ===")

for tag, path in test_images:
    with open(path, "rb") as f:
        file_bytes = f.read()
    file_sha256 = hashlib.sha256(file_bytes).hexdigest().upper()
    file_size = len(file_bytes)
    fname = os.path.basename(path)
    
    # Guess mime type
    if fname.endswith(".png"):
        ctype = "image/png"
    elif fname.endswith(".webp"):
        ctype = "image/webp"
    else:
        ctype = "image/jpeg"

    print(f"\n--- Testing Image: {fname} ({file_size} bytes, SHA256: {file_sha256[:16]}...) ---")
    
    repeats_data = []
    
    for rep in range(1, 6):
        t0 = time.time()
        files = {"image": (fname, file_bytes, ctype)}
        data = {"blockId": "block-a1"}
        
        resp = requests.post(API_URL, files=files, data=data)
        if resp.status_code != 200:
            print(f"  Rep {rep}: Failed POST status {resp.status_code}: {resp.text}")
            repeats_data.append({"repeat": rep, "error": f"POST failed {resp.status_code}"})
            continue
            
        submit_json = resp.json()
        job_id = submit_json.get("data", submit_json).get("job_id")
        
        # Poll
        job_result = None
        poll_count = 0
        timeout = False
        while True:
            poll_resp = requests.get(f"{JOBS_URL}/{job_id}")
            if poll_resp.status_code == 200:
                p_body = poll_resp.json()
                p_data = p_body.get("data", p_body)
                status = p_data.get("status")
                if status in ("done", "completed"):
                    job_result = p_data.get("result")
                    break
                elif status == "failed":
                    job_result = {"error": p_data.get("error")}
                    break
            poll_count += 1
            if time.time() - t0 > 25:
                timeout = True
                break
            time.sleep(0.3)
            
        elapsed = round(time.time() - t0, 3)
        
        if timeout:
            print(f"  Rep {rep}: TIMEOUT after {elapsed}s")
            repeats_data.append({"repeat": rep, "timeout": True, "elapsed": elapsed})
        else:
            diff = job_result.get("differentialDiagnosis", []) if job_result else []
            vit_top3 = [(d.get("disease"), d.get("probability")) for d in diff[:3]]
            gate_score = job_result.get("modelBreakdown", {}).get("cnn") if job_result else None
            stage = job_result.get("stage") if job_result else None
            disease = job_result.get("disease") if job_result else None
            conf = job_result.get("confidence") if job_result else None
            
            print(f"  Rep {rep} ({elapsed}s): Gate={gate_score}% | Stage={stage} | Disease='{disease}' ({conf}%) | Top-3={vit_top3}")
            
            repeats_data.append({
                "repeat": rep,
                "job_id": job_id,
                "elapsed_s": elapsed,
                "gate_score": gate_score,
                "stage": stage,
                "disease": disease,
                "confidence": conf,
                "vit_top3": vit_top3,
                "full_result": job_result,
            })

    results[tag] = {
        "filename": fname,
        "size_bytes": file_size,
        "sha256": file_sha256,
        "content_type": ctype,
        "options": {"blockId": "block-a1"},
        "repeats": repeats_data,
    }

out_file = os.path.join(RESULTS_DIR, "a2_raw_api_repeats.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nAll 6 images (5 repeats each) saved to: {out_file}")
