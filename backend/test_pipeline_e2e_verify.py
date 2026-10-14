import time
import json
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

# Test with a real sample image
with open("FRONTEND/public/samples/sample_anthracnose.jpg", "rb") as f:
    img_bytes = f.read()

print(f"Sending image ({len(img_bytes)} bytes) to /api/v1/detect...")
resp = client.post("/api/v1/detect", files={"image": ("sample_anthracnose.jpg", img_bytes, "image/jpeg")})
print("POST /api/v1/detect status:", resp.status_code)
print("POST response:", resp.json())
assert resp.status_code == 200
job_id = resp.json()["data"]["job_id"]

# Poll job
status = None
for i in range(30):
    time.sleep(0.3)
    sresp = client.get(f"/api/v1/jobs/{job_id}")
    data = sresp.json()["data"]
    status = data["status"]
    progress = data.get("progressPercent", 0)
    print(f"Poll {i+1}: status={status}, progress={progress}%")
    if status in ("done", "failed"):
        break

assert status == "done", f"Job failed: {data}"
result = data["result"]
print("\n=== RAW JOB RESULT PAYLOAD ===")
# Print payload (shortening long data URI for clarity)
clean_result = dict(result)
if clean_result.get("attentionMapUrl"):
    clean_result["attentionMapUrl"] = clean_result["attentionMapUrl"][:50] + "... [base64 data truncated]"
print(json.dumps(clean_result, indent=2))

print("\n=== VALIDATION CHECKS ===")
print("CNN Gatekeeper Score:", result["modelBreakdown"]["cnn"], "%")
print("YOLO Average Score:", result["modelBreakdown"]["yolo"], "%")
print("ViT Top Score:", result["modelBreakdown"]["vit"], "%")
print("Top Disease:", result["disease"])
print("Severity:", result["severity"])
print("Attention Map present:", bool(result.get("attentionMapUrl")))
print("YOLO Boxes count:", len(result["yoloBoxes"]))
for idx, box in enumerate(result["yoloBoxes"]):
    print(f"  Box {idx}: label={box['label']}, top={box['top']}, left={box['left']}, width={box['width']}, height={box['height']}")
    assert box["top"].endswith("%"), f"Top not a % string: {box['top']}"
    assert box["left"].endswith("%"), f"Left not a % string: {box['left']}"
    assert box["width"].endswith("%"), f"Width not a % string: {box['width']}"
    assert box["height"].endswith("%"), f"Height not a % string: {box['height']}"

print("\nAll bounding box coordinates verified as percentage strings!")
print("Stage 1 (CNN Gatekeeper), Stage 2 (YOLOv8 Detection), Stage 3 (ViT Attention & Classification) all executed successfully!")
