import os
import time
import json
import requests

RESULTS_DIR = r"D:\ArecaVision_Combined\backend\tests\results"
os.makedirs(RESULTS_DIR, exist_ok=True)
BASE_URL = "http://127.0.0.1:8000/api/v1"

def submit_and_poll(files=None, json_data=None):
    if json_data:
        resp = requests.post(f"{BASE_URL}/detect", json=json_data, timeout=10)
    else:
        resp = requests.post(f"{BASE_URL}/detect", files=files, timeout=10)
    print(f"Submit HTTP {resp.status_code}: {resp.text}")
    resp_body = resp.json()
    data = resp_body.get("data") or {}
    job_id = data.get("job_id") or data.get("jobId") or resp_body.get("job_id")
    if not job_id:
        return resp_body

    # Poll
    for _ in range(30):
        time.sleep(1.0)
        p_resp = requests.get(f"{BASE_URL}/jobs/{job_id}", timeout=10)
        p_body = p_resp.json()
        p_data = p_body.get("data") or p_body
        if p_data.get("status") == "done":
            return p_data
        elif p_data.get("status") == "failed":
            return p_data
    return p_data

def main():
    results = {}

    # Test 1: Real Areca Sample
    print("=== 1. Real Areca Sample (existing_healthy_1.jpg) ===")
    areca_path = r"D:\dataset_raw\dataset_raw\areca_healthy\existing_healthy_1.jpg"
    with open(areca_path, "rb") as f:
        res1 = submit_and_poll(files={"image": ("existing_healthy_1.jpg", f, "image/jpeg")})
    print(f"Disease:    {res1.get('result', {}).get('disease')}")
    print(f"Stage:      {res1.get('result', {}).get('stage')}")
    print(f"Confidence: {res1.get('result', {}).get('confidence')}%")
    results["real_areca_sample"] = res1

    time.sleep(2.5)

    # Test 2: bus.jpg
    print("\n=== 2. bus.jpg (tests/ood_probe/bus.jpg) ===")
    bus_path = r"D:\ArecaVision_Combined\backend\tests\ood_probe\bus.jpg"
    with open(bus_path, "rb") as f:
        res2 = submit_and_poll(files={"image": ("bus.jpg", f, "image/jpeg")})
    print(f"Disease:    {res2.get('result', {}).get('disease')}")
    print(f"Stage:      {res2.get('result', {}).get('stage')}")
    print(f"Confidence: {res2.get('result', {}).get('confidence')}%")
    results["bus_jpg"] = res2

    time.sleep(2.5)

    # Test 3: non_areca specimen
    print("\n=== 3. non_areca Specimen ===")
    res3 = submit_and_poll(json_data={"specimenId": "non_areca"})
    print(f"Disease:    {res3.get('result', {}).get('disease')}")
    print(f"Stage:      {res3.get('result', {}).get('stage')}")
    print(f"Confidence: {res3.get('result', {}).get('confidence')}%")
    results["non_areca_specimen"] = res3

    out_path = os.path.join(RESULTS_DIR, "backend_e2e_round4.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved e2e results to {out_path}")

if __name__ == "__main__":
    main()
