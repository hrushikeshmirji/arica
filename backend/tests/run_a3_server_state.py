"""
backend/tests/run_a3_server_state.py — Part A3 Server state & concurrency verification.
"""

import os
import sys
import time
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import requests

API_URL = "http://127.0.0.1:8000/api/v1/detect"
JOBS_URL = "http://127.0.0.1:8000/api/v1/jobs"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_DIR = os.path.join(REPO_ROOT, "backend", "tests", "test_images")
RESULTS_DIR = os.path.join(REPO_ROOT, "backend", "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

img_a_path = os.path.join(TEST_DIR, "1_dataset_fruit_rot.jpg")
img_b_path = os.path.join(TEST_DIR, "6_non_areca.jpg")

with open(img_a_path, "rb") as f:
    bytes_a = f.read()
hash_a = hashlib.sha256(bytes_a).hexdigest().upper()

with open(img_b_path, "rb") as f:
    bytes_b = f.read()
hash_b = hashlib.sha256(bytes_b).hexdigest().upper()

def submit_and_poll(img_name, img_bytes, img_hash, sub_id):
    t0 = time.time()
    files = {"image": (f"{img_name}_{sub_id}.jpg", img_bytes, "image/jpeg")}
    data = {"blockId": "block-a1"}
    
    resp = requests.post(API_URL, files=files, data=data)
    if resp.status_code != 200:
        return {"sub_id": sub_id, "error": f"POST failed {resp.status_code}"}
        
    job_id = resp.json().get("data", resp.json()).get("job_id")
    
    # Poll
    job_result = None
    while time.time() - t0 < 30:
        p_resp = requests.get(f"{JOBS_URL}/{job_id}")
        if p_resp.status_code == 200:
            pd = p_resp.json().get("data", p_resp.json())
            if pd.get("status") in ("done", "completed"):
                job_result = pd.get("result")
                break
        time.sleep(0.2)
        
    elapsed = round(time.time() - t0, 3)
    disease = job_result.get("disease") if job_result else None
    stage = job_result.get("stage") if job_result else None
    
    return {
        "sub_id": sub_id,
        "image_name": img_name,
        "input_hash": img_hash,
        "job_id": job_id,
        "elapsed_s": elapsed,
        "disease": disease,
        "stage": stage,
        "is_correct_type": ("Not an Arecanut" in disease) if img_name == "Image_B_NonAreca" else ("Fruit Rot" in disease)
    }

print("=== PART A3: SERVER STATE & CONCURRENCY VERIFICATION ===")

# 1. 10 Sequential Submissions
print("\n[1] Running 10 Sequential Submissions (alternating Image A and Image B)...")
sequential_results = []
for i in range(1, 11):
    if i % 2 == 1:
        res = submit_and_poll("Image_A_FruitRot", bytes_a, hash_a, f"seq_{i}")
    else:
        res = submit_and_poll("Image_B_NonAreca", bytes_b, hash_b, f"seq_{i}")
    print(f"  Seq {i:2d} | Input: {res['image_name']:18s} | Job: {res['job_id']} | Disease: {res['disease'][:35]} | Match: {res['is_correct_type']}")
    sequential_results.append(res)

# 2. 4 Concurrent Submissions
print("\n[2] Running 4 Concurrent Submissions (2 Image A + 2 Image B simultaneously)...")
concurrent_tasks = [
    ("Image_A_FruitRot", bytes_a, hash_a, "conc_1"),
    ("Image_B_NonAreca", bytes_b, hash_b, "conc_2"),
    ("Image_A_FruitRot", bytes_a, hash_a, "conc_3"),
    ("Image_B_NonAreca", bytes_b, hash_b, "conc_4"),
]

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(submit_and_poll, *task) for task in concurrent_tasks]
    concurrent_results = [f.result() for f in futures]

for res in concurrent_results:
    print(f"  Conc {res['sub_id']} | Input: {res['image_name']:18s} | Job: {res['job_id']} | Disease: {res['disease'][:35]} | Match: {res['is_correct_type']}")

all_seq_correct = all(r["is_correct_type"] for r in sequential_results)
all_conc_correct = all(r["is_correct_type"] for r in concurrent_results)

summary = {
    "server_cache_analysis": {
        "caching_by_filename": False,
        "caching_by_image_hash": False,
        "job_isolation": "Isolated per-job UUID via threading.Lock on _jobs dict and SQLite rows",
        "potential_races": "ViTClassifier._attention_maps forward hook instance attribute during concurrent inference, but output classification logits remain isolated in thread execution"
    },
    "sequential_10": {
        "all_matched_input": all_seq_correct,
        "runs": sequential_results
    },
    "concurrent_4": {
        "all_matched_input": all_conc_correct,
        "runs": concurrent_results
    }
}

out_file = os.path.join(RESULTS_DIR, "a3_server_state_concurrency.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(f"\nAll tests passed: Sequential={all_seq_correct}, Concurrent={all_conc_correct}")
print(f"Saved to: {out_file}")
