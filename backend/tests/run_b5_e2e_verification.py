"""
run_b5_e2e_verification.py — End-to-end verification of ArecaVision pipeline
Testing real areca sample, non-areca rejection (bus.jpg), gatekeeper uncertain probe,
and experimental class handling.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
RESULTS_DIR = Path("D:/ArecaVision_Combined/backend/tests/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = RESULTS_DIR / "r6_b5_e2e_verification.json"


def submit_and_poll(file_path: Path, name: str) -> dict:
    print(f"\nSubmitting {name} ({file_path.name})...")
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/detect",
            files={"image": (file_path.name, f, "image/jpeg")},
            timeout=15,
        )
    if resp.status_code not in (200, 202):
        print(f"Error submitting {name}: HTTP {resp.status_code} {resp.text}")
        return {"error": resp.text, "status_code": resp.status_code}

    resp_json = resp.json()
    job_id = resp_json.get("data", {}).get("job_id") or resp_json.get("job_id")
    print(f"Job ID: {job_id}. Polling /api/v1/jobs/{job_id}...")

    for attempt in range(40):
        time.sleep(1.0)
        st_resp = requests.get(f"{BASE_URL}/jobs/{job_id}", timeout=10)
        if st_resp.status_code == 200:
            st_body = st_resp.json()
            st_data = st_body.get("data", st_body)
            if st_data.get("status") in ["done", "failed"]:
                return st_data
    return {"status": "timeout", "job_id": job_id}


def main():
    test_cases = [
        {
            "name": "1. Real Areca Healthy",
            "path": Path("D:/dataset_raw/dataset_raw/areca_healthy/existing_healthy_1.jpg"),
        },
        {
            "name": "2. Non-Areca Out-Of-Distribution (bus.jpg)",
            "path": Path("D:/ArecaVision_Combined/backend/tests/ood_probe/bus.jpg"),
        },
        {
            "name": "3. Gatekeeper Uncertain Probe (download_1423.jpg)",
            "path": Path("D:/dataset_raw/dataset_raw/non_areca/download_1423.jpg"),
        },
        {
            "name": "4. Experimental Seed Class (seed_00.jpg)",
            "path": Path("D:/dataset_raw/dataset_raw/areca_diseased_fungal_leaf_spot/seed_00.jpg"),
        },
    ]

    all_results = {}

    for tc in test_cases:
        p = tc["path"]
        if not p.exists():
            print(f"Warning: File {p} not found, skipping {tc['name']}")
            continue

        res = submit_and_poll(p, tc["name"])
        result_obj = res.get("result", {})

        print(f"=== RESULT FOR {tc['name']} ===")
        print(f"Job Status          : {res.get('status')}")
        print(f"Stage               : {result_obj.get('stage')}")
        print(f"Disease             : {result_obj.get('disease')}")
        print(f"Confidence          : {result_obj.get('confidence')}%")
        print(f"Gate Score          : {result_obj.get('gateScore')}")
        print(f"Severity            : {result_obj.get('severity')}")
        print(f"isExperimentalClass : {result_obj.get('isExperimentalClass')}")
        print(f"isValidatedClass    : {result_obj.get('isValidatedClass')}")
        print(f"yoloBoxes Count     : {len(result_obj.get('yoloBoxes', []))}")
        print(f"yoloBoxes           : {result_obj.get('yoloBoxes')}")
        print(f"saliencyBox         : {result_obj.get('saliencyBox')}")
        print(f"modelBreakdown      : {result_obj.get('modelBreakdown')}")

        all_results[tc["name"]] = {
            "file": p.name,
            "status": res.get("status"),
            "stage": result_obj.get("stage"),
            "disease": result_obj.get("disease"),
            "confidence": result_obj.get("confidence"),
            "gateScore": result_obj.get("gateScore"),
            "severity": result_obj.get("severity"),
            "isExperimentalClass": result_obj.get("isExperimentalClass"),
            "isValidatedClass": result_obj.get("isValidatedClass"),
            "yoloBoxes": result_obj.get("yoloBoxes"),
            "saliencyBox": result_obj.get("saliencyBox"),
            "modelBreakdown": result_obj.get("modelBreakdown"),
        }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved E2E verification results to {OUT_FILE}")


if __name__ == "__main__":
    main()
