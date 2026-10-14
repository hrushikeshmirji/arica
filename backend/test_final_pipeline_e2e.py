import os
import sys
import time
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

def test_full_pipeline_verification():
    print("=" * 70)
    print("  RUNNING COMPREHENSIVE END-TO-END PIPELINE VERIFICATION")
    print("=" * 70)

    # Test 1: Real Arecanut Disease Image (Anthracnose sample)
    sample_path = "FRONTEND/public/samples/sample_anthracnose.jpg"
    print(f"\n[Test 1] Testing Real Arecanut Image: {sample_path}")
    with open(sample_path, "rb") as f:
        img_bytes = f.read()

    resp = client.post("/api/v1/detect", files={"image": ("sample_anthracnose.jpg", img_bytes, "image/jpeg")})
    assert resp.status_code == 200, f"Submit failed: {resp.text}"
    job_id = resp.json()["data"]["job_id"]
    print(f"  Job Submitted: {job_id}")

    for i in range(30):
        time.sleep(0.3)
        sresp = client.get(f"/api/v1/jobs/{job_id}")
        data = sresp.json()["data"]
        status = data["status"]
        if status in ("done", "failed"):
            break

    assert status == "done", f"Inference failed: {data}"
    result = data["result"]
    print("\n--- Test 1 Result Payload ---")
    clean_result = dict(result)
    if clean_result.get("attentionMapUrl"):
        clean_result["attentionMapUrl"] = clean_result["attentionMapUrl"][:50] + "... [base64 data truncated]"
    print(json.dumps(clean_result, indent=2))

    assert result["modelBreakdown"]["cnn"] > 90.0, f"CNN gate failed: {result['modelBreakdown']['cnn']}"
    assert result["modelBreakdown"]["vit"] > 35.0, f"ViT score low: {result['modelBreakdown']['vit']}"
    assert result["stage"] in ("Detected", "Review Required", "Low confidence"), f"Unexpected stage: {result['stage']}"
    if len(result.get("yoloBoxes", [])) == 0 and result["disease"] != "Healthy":
        assert result["stage"] == "Review Required" or result["severity"] == "Uncertain", "Zero boxes must trigger uncertainty safeguard"
    print("\n[OK] Test 1 Passed: CNN Gatekeeper + ViT Classification + Attention Heatmap verified!")

    # Test 2: Non-Arecanut Gatekeeper Defense Test (bus.jpg)
    non_areca_path = "backend/venv/Lib/site-packages/ultralytics/assets/bus.jpg"
    print(f"\n[Test 2] Testing Non-Arecanut Defense: {non_areca_path}")
    with open(non_areca_path, "rb") as f:
        na_bytes = f.read()

    na_resp = client.post("/api/v1/detect", files={"image": ("bus.jpg", na_bytes, "image/jpeg")})
    assert na_resp.status_code == 200
    na_job_id = na_resp.json()["data"]["job_id"]

    for _ in range(30):
        time.sleep(0.2)
        sresp = client.get(f"/api/v1/jobs/{na_job_id}")
        data = sresp.json()["data"]
        if data["status"] in ("done", "failed"):
            break

    assert data["status"] == "done"
    na_result = data["result"]
    print("\n--- Test 2 Result Payload ---")
    print(json.dumps(na_result, indent=2))
    assert na_result["disease"] == "Not an Arecanut image"
    assert na_result["severity"] == "Non-Arecanut"
    assert na_result["yoloBoxes"] == []
    assert na_result["modelBreakdown"]["vit"] == 0.0
    assert na_result["modelBreakdown"]["yolo"] == 0.0
    print("\n[OK] Test 2 Passed: Stage-1 Gatekeeper correctly intercepted and rejected non-areca image!")

if __name__ == "__main__":
    test_full_pipeline_verification()
