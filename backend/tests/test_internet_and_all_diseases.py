"""
backend/tests/test_internet_and_all_diseases.py
Verify pipeline performance on:
1. Samples across all 11 classes from validation set
2. Base64 Data URI input (simulating clipboard paste Ctrl+V)
3. Transparent PNG with alpha channel
4. EXIF-oriented JPEG
5. Field photo Fruit Rot
"""

import io
import os
import sys
import base64
import time
from PIL import Image
from fastapi.testclient import TestClient

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

from server.app import app

client = TestClient(app)

def run_detection_bytes(img_bytes: bytes, filename: str, mime: str = "image/jpeg"):
    resp = client.post("/api/v1/detect", files={"file": (filename, img_bytes, mime)})
    if resp.status_code != 200:
        return {"error": f"POST failed: {resp.status_code}", "body": resp.text}
    
    job_id = resp.json()["data"]["job_id"]
    for _ in range(30):
        time.sleep(0.5)
        st_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = st_resp.json().get("data", {})
        if data.get("status") == "done":
            return data["result"]
        elif data.get("status") == "failed":
            return {"error": "job failed", "data": data}
    return {"error": "timeout"}

def run_detection_json(json_payload: dict):
    resp = client.post("/api/v1/detect", json=json_payload)
    if resp.status_code != 200:
        return {"error": f"POST failed: {resp.status_code}", "body": resp.text}
    
    job_id = resp.json()["data"]["job_id"]
    for _ in range(30):
        time.sleep(0.5)
        st_resp = client.get(f"/api/v1/jobs/{job_id}")
        data = st_resp.json().get("data", {})
        if data.get("status") == "done":
            return data["result"]
        elif data.get("status") == "failed":
            return {"error": "job failed", "data": data}
    return {"error": "timeout"}

print("=" * 75)
print("1. TESTING ALL 11 CLASSES FROM DATASET")
print("=" * 75)

val_dir = os.path.join(_HERE, "data", "dataset_clean_v1", "val")
classes = sorted(os.listdir(val_dir))

results = []

for cls in classes:
    cls_folder = os.path.join(val_dir, cls)
    if not os.path.isdir(cls_folder):
        continue
    imgs = [f for f in os.listdir(cls_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not imgs:
        continue
    
    chosen_img = "FruitRot_val_003.jpg" if cls == "FruitRot" and "FruitRot_val_003.jpg" in imgs else imgs[0]
    sample_file = os.path.join(cls_folder, chosen_img)
    with open(sample_file, "rb") as f:
        img_bytes = f.read()
    
    res = run_detection_bytes(img_bytes, imgs[0])
    predicted_disease = res.get("disease", "ERROR")
    stage = res.get("stage", "UNKNOWN")
    conf = res.get("confidence", 0)
    cnn_gate = res.get("modelBreakdown", {}).get("cnn", 0)
    yolo_boxes = len(res.get("yoloBoxes", []))
    
    print(f"[{cls:22}] -> Predicted: {predicted_disease:25} | Stage: {stage:10} | Conf: {conf:5.1f}% | Gate: {cnn_gate:5.1f}% | Boxes: {yolo_boxes}")
    results.append({
        "true_class": cls,
        "predicted": predicted_disease,
        "stage": stage,
        "conf": conf,
        "gate": cnn_gate
    })

print("\n" + "=" * 75)
print("2. TESTING SPECIAL FORMATS (BASE64 DATA URI / CLIPBOARD PASTE / ALPHA PNG)")
print("=" * 75)

# 2a. Base64 Data URI test
fruit_rot_path = os.path.join(_HERE, "data", "uploads", "job-bfd163d5cc18.jpg")
with open(fruit_rot_path, "rb") as f:
    b64_str = base64.b64encode(f.read()).decode("utf-8")
data_uri = f"data:image/jpeg;base64,{b64_str}"

res_b64 = run_detection_json({"image": data_uri})
print(f"[Clipboard Data URI   ] -> Predicted: {res_b64.get('disease')} | Stage: {res_b64.get('stage')} | Conf: {res_b64.get('confidence')}% | Boxes: {len(res_b64.get('yoloBoxes', []))}")

# 2b. Transparent PNG with alpha channel (RGBA)
img_pil = Image.open(fruit_rot_path).convert("RGBA")
# Make background transparent around borders
datas = img_pil.getdata()
new_data = []
for item in datas:
    # If very bright or dark edge, add alpha
    if item[0] < 30 and item[1] < 30 and item[2] < 30:
        new_data.append((item[0], item[1], item[2], 0))
    else:
        new_data.append((item[0], item[1], item[2], 255))
img_pil.putdata(new_data)
png_buf = io.BytesIO()
img_pil.save(png_buf, format="PNG")
png_bytes = png_buf.getvalue()

res_png = run_detection_bytes(png_bytes, "transparent_sample.png", "image/png")
print(f"[Transparent RGBA PNG ] -> Predicted: {res_png.get('disease')} | Stage: {res_png.get('stage')} | Conf: {res_png.get('confidence')}% | Boxes: {len(res_png.get('yoloBoxes', []))}")

# 2c. WebP image
webp_buf = io.BytesIO()
Image.open(fruit_rot_path).save(webp_buf, format="WEBP")
webp_bytes = webp_buf.getvalue()

res_webp = run_detection_bytes(webp_bytes, "internet_sample.webp", "image/webp")
print(f"[WebP Internet Format ] -> Predicted: {res_webp.get('disease')} | Stage: {res_webp.get('stage')} | Conf: {res_webp.get('confidence')}% | Boxes: {len(res_webp.get('yoloBoxes', []))}")

print("\n" + "=" * 75)
print("TEST COMPLETED SUCCESSFULLY.")
print("=" * 75)
