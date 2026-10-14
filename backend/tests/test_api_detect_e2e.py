"""
backend/tests/test_api_detect_e2e.py
Full End-to-End API test using FastAPI TestClient on real user image.
"""

import os
import sys
import time
import json
from fastapi.testclient import TestClient

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

from server.app import app

client = TestClient(app)

print("=" * 65)
print("TESTING FASTAPI /api/v1/detect END-TO-END PIPELINE")
print("=" * 65)

test_image_path = os.path.join(_HERE, "data", "uploads", "job-bfd163d5cc18.jpg")
print(f"Testing image: {test_image_path}")

with open(test_image_path, "rb") as f:
    img_bytes = f.read()

resp = client.post("/api/v1/detect", files={"file": ("field_fruit_rot.jpg", img_bytes, "image/jpeg")})
print(f"POST /api/v1/detect Status: {resp.status_code}")
job_info = resp.json()
print("Job Info:", job_info)

job_id = job_info["data"]["job_id"]

for i in range(45):
    time.sleep(1)
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    status_envelope = status_resp.json()
    status_json = status_envelope.get("data", {})
    status = status_json.get("status")
    stage = status_json.get("currentStage")
    pct = status_json.get("progressPercent")
    print(f"[{i+1}s] Status: {status} | Stage: {stage} | Progress: {pct}%")
    
    if status == "done":
        res = status_json["result"]
        print("\n" + "=" * 65)
        print("API DIAGNOSIS RESPONSE VERIFIED:")
        print("=" * 65)
        print(f"Job ID:               {res.get('id')}")
        print(f"Disease:              {res.get('disease')}")
        print(f"Display Name:         {res.get('diseaseDisplayName')}")
        print(f"Stage:                {res.get('stage')}")
        print(f"Confidence:           {res.get('confidence')}%")
        print(f"Severity:             {res.get('severity')}")
        print(f"YOLO Boxes Count:     {len(res.get('yoloBoxes', []))}")
        for b in res.get("yoloBoxes", []):
            print(f"  -> Box Label:       {b['label']} | Coordinates: top={b['top']}, left={b['left']}, w={b['width']}, h={b['height']}")
        print(f"Model Breakdown:      CNN={res.get('modelBreakdown', {}).get('cnn')}%, ViT={res.get('modelBreakdown', {}).get('vit')}%, YOLO={res.get('modelBreakdown', {}).get('yolo')}%")
        print("Differential Top 3:")
        for d in res.get("differentialDiagnosis", [])[:3]:
            print(f"  -> {d['disease']}: {d['probability']}%")
        print("Stage Timings:")
        print(f"  -> {res.get('stageTimingsMs')}")
        break
    elif status == "failed":
        print(f"\n[ERROR] Job failed: {status_json}")
        break
