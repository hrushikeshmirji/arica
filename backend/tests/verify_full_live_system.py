import time
import requests
import os
import json

BASE_URL = "http://127.0.0.1:8000"

def test_live_detect(image_path, expected_diagnosis=None, should_reject=False):
    if not os.path.exists(image_path):
        print(f"Skipping {image_path}: file not found")
        return None
    
    with open(image_path, "rb") as f:
        files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
        resp = requests.post(f"{BASE_URL}/api/v1/detect", files=files)
    
    if resp.status_code != 200:
        print(f"FAILED {image_path}: HTTP {resp.status_code} - {resp.text}")
        return None
    
    job = resp.json()["data"]
    job_id = job.get("job_id") or job.get("id")
    
    # Poll until done (max 10s)
    for _ in range(20):
        time.sleep(0.4)
        j_resp = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}").json()["data"]
        if j_resp.get("status") == "done":
            res = j_resp.get("result", {})
            disease = res.get("disease")
            display = res.get("diseaseDisplayName")
            conf = res.get("confidence")
            stage = res.get("stage")
            diff = res.get("differentialDiagnosis", [])
            
            passed = True
            if should_reject:
                passed = (disease == "Not an Arecanut image")
            elif expected_diagnosis:
                passed = (disease == expected_diagnosis or display == expected_diagnosis)
            
            status_str = "PASS" if passed else "FAIL"
            print(f"[{status_str}] {os.path.basename(image_path):22} -> Disease: '{disease}' ({conf}%) | Stage: {stage} | Diff: {[d['disease'] + ':' + str(d['probability']) + '%' for d in diff[:3]]}")
            return res
    print(f"TIMEOUT on {image_path}")
    return None

print("=== VERIFYING LIVE API ENDPOINT /api/v1/detect ===")

print("\n--- 1. Testing User Uploads that Previously Failed ---")
user_tests = [
    ("data/uploads/job-02a8ae76aafe.jpg", "Yellow Leaf Disease", False),
    ("data/uploads/job-a567509ee657.jpg", "Sooty Mold", False),
    ("data/uploads/job-8d3fdd69b77e.jpg", "Yellow Leaf Disease", False),
    ("data/uploads/job-9be4f34394e8.jpg", "Healthy", False),
    ("data/uploads/job-1d8a485000dc.jpg", "Yellow Leaf Disease", False),
    ("data/uploads/job-66e59a96c499.jpg", "Sooty Mold", False),
    ("data/uploads/job-a55555f036a3.jpg", "Yellow Leaf Disease", False),
    ("data/uploads/job-874abbbe7f09.jpg", "Healthy", False),
]
for p, exp, rej in user_tests:
    test_live_detect(p, exp, rej)

print("\n--- 2. Testing Core Pathology Differentiation (Fruit Rot vs Nut Cracking vs Leaf Spot) ---")
core_tests = [
    ("data/uploads/job-bfd163d5cc18.jpg", "Fruit Rot (Koleroga)", False),
    ("data/uploads/job-50d6db5a8310.jpg", "Nut Cracking", False),
    ("data/uploads/job-88dd4945ada1.jpg", "Leaf Spot Complex", False),
]
for p, exp, rej in core_tests:
    test_live_detect(p, exp, rej)

print("\n--- 3. Testing Non-Arecanut Defense (OOD Rejection) ---")
ood_tests = [
    ("tests/ood_probe/bus.jpg", "Not an Arecanut image", True),
    ("tests/ood_probe/banana_single.jpg", "Not an Arecanut image", True),
]
for p, exp, rej in ood_tests:
    test_live_detect(p, exp, rej)

print("\n=== ALL LIVE VERIFICATION RUNS COMPLETED ===")
