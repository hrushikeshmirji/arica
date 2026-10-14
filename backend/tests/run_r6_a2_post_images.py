"""
run_r6_a2_post_images.py

Task A2:
POST 5 images:
- 3 where YOLO finds nothing (areca)
- 1 areca tested for detection if any exists
- 1 non-areca
Print full JSON for yoloBoxes, saliencyBox, modelBreakdown, and stage.
Save to backend/tests/results/r6_a2_post_5_images.json.
"""

import os
import sys
import time
import json
import requests

API_URL = "http://127.0.0.1:8000/api/v1/detect"
JOBS_URL = "http://127.0.0.1:8000/api/v1/jobs"
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

test_files = [
    ("areca_no_yolo_1", r"D:\dataset_raw\dataset_raw\areca_diseased_fungal_anthracnose\existing_anthracnose_28.jpg"),
    ("areca_no_yolo_2", r"D:\dataset_raw\dataset_raw\areca_healthy\existing_healthy_1.jpg"),
    ("areca_no_yolo_3", r"D:\dataset_raw\dataset_raw\areca_diseased_fungal_fruit_rot\existing_fruit_rot_63.jpg"),
    ("areca_candidate_detection", r"D:\dataset_raw\dataset_raw\areca_diseased_fungal_anthracnose\existing_anthracnose_1.jpg"),
    ("non_areca_bus", r"D:\ArecaVision_Combined\backend\tests\ood_probe\bus.jpg"),
]

records = []

for tag, fpath in test_files:
    bname = os.path.basename(fpath)
    print(f"\n{'='*70}\nPOST [{tag}]: {bname}")
    with open(fpath, "rb") as f:
        resp = requests.post(API_URL, files={"image": (bname, f, "image/jpeg")})
    
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")
        continue
    
    body = resp.json()
    job_id = body.get("data", body).get("job_id")
    
    # Poll
    res_obj = None
    t0 = time.time()
    while time.time() - t0 < 30:
        j_resp = requests.get(f"{JOBS_URL}/{job_id}")
        if j_resp.status_code == 200:
            jb = j_resp.json()
            jd = jb.get("data", jb)
            if jd.get("status") in ("done", "completed"):
                res_obj = jd.get("result")
                break
        time.sleep(0.3)
    
    if not res_obj:
        print("Timeout waiting for job completion")
        continue

    extracted = {
        "tag": tag,
        "filename": bname,
        "job_id": job_id,
        "stage": res_obj.get("stage"),
        "disease": res_obj.get("disease"),
        "confidence": res_obj.get("confidence"),
        "yoloBoxes": res_obj.get("yoloBoxes"),
        "saliencyBox": res_obj.get("saliencyBox"),
        "modelBreakdown": res_obj.get("modelBreakdown"),
    }
    records.append(extracted)
    print(json.dumps(extracted, indent=2))

out_path = os.path.join(RESULTS_DIR, "r6_a2_post_5_images.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2)

print(f"\nSaved results to {out_path}")
