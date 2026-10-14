"""
test_real_sample.py — Test backend with a real sample image from Unsplash.
"""
import time
import requests
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

def test_unsplash_sample():
    print("Testing real sample image download and inference...")
    url = "https://images.unsplash.com/photo-1518050947974-4be8c7469f0c?w=800&auto=format&fit=crop&q=80"
    
    try:
        img_resp = requests.get(url, timeout=10)
        img_resp.raise_for_status()
        img_bytes = img_resp.content
        print(f"Downloaded sample image ({len(img_bytes)} bytes)")
    except Exception as e:
        print(f"Skipping remote download test (network issue): {e}")
        return

    files = {"image": ("koleroga_sample.jpg", img_bytes, "image/jpeg")}
    submit_resp = client.post("/api/v1/detect", files=files)
    assert submit_resp.status_code == 200, f"Submit failed: {submit_resp.text}"
    submit_data = submit_resp.json()
    assert submit_data["success"] is True
    job_id = submit_data["data"]["job_id"]
    print(f"Job submitted: {job_id}")

    for _ in range(40):
        time.sleep(0.5)
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert status_resp.status_code == 200
        job_info = status_resp.json()["data"]
        status = job_info["status"]
        if status in ("done", "failed"):
            break

    assert status == "done", f"Inference failed: {job_info}"
    result = job_info["result"]
    print("\n✓ Full Pipeline Result on Real Sample:")
    print(f"  Disease: {result['disease']}")
    print(f"  Confidence: {result['confidence']}%")
    print(f"  Severity: {result['severity']}")
    print(f"  Treatments: {result['treatments']}")
    print(f"  YOLO Boxes: {result['yoloBoxes']}")
    print(f"  Has Attention Map: {bool(result['attentionMapUrl'])}")
    print(f"  Model Breakdown: {result['modelBreakdown']}")

if __name__ == "__main__":
    test_unsplash_sample()
