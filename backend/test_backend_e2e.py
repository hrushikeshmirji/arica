"""
test_backend_e2e.py — Direct test for FastAPI backend validation and ML inference.
"""
import io
from pathlib import Path
import time
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

def test_health():
    print("Testing /health...")
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "ok"
    assert data["yolo_trained"] is True
    print("✓ /health passed:", data)

def test_reject_empty_file():
    print("Testing empty file rejection...")
    files = {"image": ("empty.jpg", b"", "image/jpeg")}
    resp = client.post("/api/v1/detect", files=files)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    json_data = resp.json()
    assert json_data["success"] is False
    assert "empty" in json_data["error"]["message"].lower()
    print("✓ Empty file rejected with 400:", json_data["error"]["message"])

def test_reject_non_image_file():
    print("Testing non-image file rejection...")
    files = {"image": ("malicious.txt", b"Hello this is plain text, not an image", "text/plain")}
    resp = client.post("/api/v1/detect", files=files)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    json_data = resp.json()
    assert json_data["success"] is False
    print("✓ Non-image file rejected with 400:", json_data["error"]["message"])

def test_reject_oversized_file():
    print("Testing oversized file (>10MB) rejection...")
    fake_large_bytes = b"0" * (11 * 1024 * 1024)
    files = {"image": ("huge.jpg", fake_large_bytes, "image/jpeg")}
    resp = client.post("/api/v1/detect", files=files)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    json_data = resp.json()
    assert json_data["success"] is False
    assert "10mb" in json_data["error"]["message"].lower() or "too large" in json_data["error"]["message"].lower()
    print("✓ Oversized file rejected with 400:", json_data["error"]["message"])

def test_corrupted_image_handling():
    print("Testing corrupted image with spoofed image/jpeg content-type header...")
    garbage_bytes = b"not-a-valid-jpeg-image-bytes-garbage-payload"
    files = {"image": ("corrupted.jpg", garbage_bytes, "image/jpeg")}
    submit_resp = client.post("/api/v1/detect", files=files)
    assert submit_resp.status_code == 400, f"Expected 400, got {submit_resp.status_code}: {submit_resp.text}"
    json_data = submit_resp.json()
    assert json_data["success"] is False
    assert "invalid image content" in json_data["error"]["message"].lower() or "unsupported" in json_data["error"]["message"].lower()
    print("✓ Corrupted/spoofed image rejected with 400:", json_data["error"]["message"])

def test_valid_image_inference():
    print("Testing real end-to-end inference with known arecanut image...")
    areca_path = Path(r"d:\dataset_raw\dataset_raw\areca_healthy\existing_healthy_1.jpg")
    if areca_path.is_file():
        with open(areca_path, "rb") as f:
            jpeg_bytes = f.read()
    else:
        # Fallback to creating a test image if dataset not available
        arr = np.full((224, 224, 3), 128, dtype=np.uint8)
        arr[40:180, 40:180, :] = [34, 139, 34]
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()

    files = {"image": ("test_areca.jpg", jpeg_bytes, "image/jpeg")}
    submit_resp = client.post("/api/v1/detect", files=files)
    assert submit_resp.status_code == 200, f"Submit failed: {submit_resp.text}"
    submit_data = submit_resp.json()
    assert submit_data["success"] is True
    job_id = submit_data["data"]["job_id"]
    print(f"✓ Job submitted: {job_id}")

    # Poll until done
    for _ in range(30):
        time.sleep(0.5)
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert status_resp.status_code == 200, f"Poll failed: {status_resp.text}"
        status_data = status_resp.json()
        assert status_data["success"] is True
        job_info = status_data["data"]
        status = job_info["status"]
        if status in ("done", "failed"):
            break

    assert status == "done", f"Job did not finish successfully: {job_info}"
    result = job_info["result"]
    print("✓ Inference completed successfully!")
    print(f"  Disease: {result['disease']}")
    print(f"  Confidence: {result['confidence']}% (Scale 0-100: {0 <= result['confidence'] <= 100})")
    print(f"  Severity: {result['severity']}")
    print(f"  Treatments count: {len(result['treatments'])}")
    print(f"  Model breakdown: {result['modelBreakdown']}")
    print(f"  YOLO boxes count: {len(result['yoloBoxes'])}")
    assert 0 <= result["confidence"] <= 100
    assert len(result["treatments"]) > 0

def test_gate_rejection_non_arecanut():
    print("Testing Stage-1 EfficientNet gate rejection on known non-arecanut image...")
    non_areca_path = Path(r"d:\dataset_raw\dataset_raw\non_areca\download_1.png")
    if non_areca_path.is_file():
        with open(non_areca_path, "rb") as f:
            img_bytes = f.read()
    else:
        # Fallback to synthetic non-arecanut pattern
        arr = np.full((224, 224, 3), 128, dtype=np.uint8)
        arr[40:180, 40:180, :] = [34, 139, 34]
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="JPEG")
        img_bytes = buf.getvalue()

    files = {"image": ("non_areca.png", img_bytes, "image/png")}
    submit_resp = client.post("/api/v1/detect", files=files)
    assert submit_resp.status_code == 200, f"Submit failed: {submit_resp.text}"
    submit_data = submit_resp.json()
    assert submit_data["success"] is True
    job_id = submit_data["data"]["job_id"]
    print(f"✓ Non-arecanut job submitted: {job_id}")

    # Poll until done or failed
    for _ in range(30):
        time.sleep(0.5)
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert status_resp.status_code == 200, f"Poll failed: {status_resp.text}"
        status_data = status_resp.json()
        assert status_data["success"] is True
        job_info = status_data["data"]
        status = job_info["status"]
        if status in ("done", "failed"):
            break

    assert status == "done", f"Expected job to complete gracefully at Stage-1 gate, got: {status}"
    result = job_info.get("result", {})
    assert result.get("disease") == "Not an Arecanut image", f"Unexpected disease result: {result.get('disease')}"
    assert result.get("severity") == "Non-Arecanut", f"Unexpected severity: {result.get('severity')}"
    print(f"✓ Gatekeeper correctly rejected non-arecanut image gracefully: {result.get('description')[:60]}...")

def test_all_rest_endpoints():
    print("Testing full REST API suite...")

    # Health
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

    # Dashboard KPI
    r = client.get("/api/v1/dashboard/kpi")
    assert r.status_code == 200 and r.json()["data"]["totalTrees"] == 12540

    # Dashboard Trends
    r = client.get("/api/v1/dashboard/trends")
    assert r.status_code == 200 and len(r.json()["data"]) >= 5

    # Dashboard Distribution
    r = client.get("/api/v1/dashboard/distribution")
    assert r.status_code == 200 and len(r.json()["data"]) == 4

    # Plantation Summary
    r = client.get("/api/v1/plantation/summary")
    assert r.status_code == 200 and len(r.json()["data"]["blocks"]) >= 5

    # Add Block
    r = client.post("/api/v1/plantation/blocks", json={"id": "Block Test", "trees": 1500, "diseasedTrees": 100})
    assert r.status_code == 200 and r.json()["data"]["health"] == 93

    # Delete Block
    r = client.delete("/api/v1/plantation/blocks/Block Test")
    assert r.status_code == 200 and r.json()["data"]["deleted"] is True

    # Notifications
    r = client.get("/api/v1/notifications")
    assert r.status_code == 200 and r.json()["data"]["unreadCount"] >= 0

    # Read all notifications
    r = client.put("/api/v1/notifications/read-all")
    assert r.status_code == 200 and r.json()["data"]["success"] is True

    # Assistant History & Chat
    r = client.get("/api/v1/assistant/history")
    assert r.status_code == 200 and len(r.json()["data"]) >= 1

    r = client.post("/api/v1/assistant/chat", json={"message": "How do I control Koleroga fruit rot?"})
    assert r.status_code == 200 and "Bordeaux" in r.json()["data"]["reply"]

    # Weather
    r = client.get("/api/v1/weather?city=Madikeri")
    assert r.status_code == 200 and r.json()["data"]["city"] == "Madikeri"

    # Auth
    r = client.post("/api/v1/auth/login", json={"email": "tester@arecavision.ai"})
    assert r.status_code == 200 and r.json()["data"]["user"]["email"] == "tester@arecavision.ai"

    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 200 and "jwt" in r.json()["data"]["token"]

    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200 and r.json()["data"]["logged_out"] is True

    # Reports
    r = client.post("/api/v1/reports/export", json={"type": "summary", "format": "csv"})
    assert r.status_code == 200 and "Date,Block" in r.text

    r = client.post("/api/v1/reports/export", json={"type": "detailed", "format": "pdf"})
    assert r.status_code == 200 and "%PDF" in r.text

    print("✓ All REST API endpoints validated successfully!")

if __name__ == "__main__":
    test_health()
    test_reject_empty_file()
    test_reject_non_image_file()
    test_reject_oversized_file()
    test_corrupted_image_handling()
    test_valid_image_inference()
    test_gate_rejection_non_arecanut()
    test_all_rest_endpoints()
    print("\n==========================================")
    print("ALL BACKEND VALIDATION & E2E TESTS PASSED!")
    print("==========================================")

