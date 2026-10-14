"""
run_a4_real_photo_triage.py

Part A4 of ArecaVision Round 5:
- Build backend/tests/results/real_photo_triage.csv from backend/data/uploads joined to jobs.
- Columns: job_id, filename, stage_reached, raw_gate_p_areca, vit_top3, yolo_box_count, truth_label
- truth_label must be completely EMPTY.
"""

import os
import sys
import csv
import json
import sqlite3
import torch
from PIL import Image

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)
os.chdir(_HERE)

from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor

RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
UPLOADS_DIR = os.path.join(_HERE, "data", "uploads")
DB_PATH = os.path.join(_HERE, "data", "arecavision.db")

print("Initializing predictors...")
cnn_pred = CNNPredictor()
vit_pred = ViTPredictor()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

upload_files = sorted([f for f in os.listdir(UPLOADS_DIR) if f.endswith((".jpg", ".jpeg", ".png"))])
print(f"Found {len(upload_files)} upload files in {UPLOADS_DIR}")

triage_rows = []

for u in upload_files:
    job_id = os.path.splitext(u)[0]
    file_path = os.path.join(UPLOADS_DIR, u)
    
    cursor.execute("SELECT stage, result_json FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    
    stage_db = row[0] if row else "UNKNOWN"
    res = {}
    if row and row[1]:
        try:
            res = json.loads(row[1])
        except Exception:
            pass
            
    stage_reached = res.get("stage") or stage_db
    
    # Calculate exact raw gate p_areca
    try:
        with Image.open(file_path) as img:
            pil_rgb = img.convert("RGB")
            w, h = pil_rgb.size
            t_full = cnn_pred._tf(pil_rgb)
            cw, ch = int(w * 0.75), int(h * 0.75)
            cx, cy = (w - cw) // 2, (h - ch) // 2
            center_img = pil_rgb.crop((cx, cy, cx + cw, cy + ch)) if (cw >= 32 and ch >= 32) else pil_rgb
            t_center = cnn_pred._tf(center_img)
            batch = torch.stack([t_full, t_center], dim=0).to(cnn_pred.device)
            probs = cnn_pred.model.predict_proba(batch)
            raw_p_areca = round(float((probs[0, 0].item() + probs[1, 0].item()) / 2.0), 4)
    except Exception as e:
        raw_p_areca = None
    
    # ViT top-3
    diff_diag = res.get("differentialDiagnosis") or []
    if diff_diag:
        vit_top3 = "; ".join([f"{d.get('disease')}: {d.get('probability')}%" for d in diff_diag[:3]])
    else:
        # If job was rejected by gatekeeper, result_json has no ViT diagnosis.
        # Run ViT predictor to report what ViT would predict if unblocked
        try:
            top_preds = vit_pred.predict(file_path, return_top_k=3)
            vit_top3 = "; ".join([f"{cls_name}: {round(p * 100, 1)}%" for cls_name, p in top_preds[:3]])
        except Exception:
            vit_top3 = "N/A"
            
    # YOLO box count
    yolo_boxes = res.get("yoloBoxes") or []
    yolo_count = len(yolo_boxes)
    
    triage_rows.append({
        "job_id": job_id,
        "filename": u,
        "stage_reached": stage_reached,
        "raw_gate_p_areca": raw_p_areca,
        "vit_top3": vit_top3,
        "yolo_box_count": yolo_count,
        "truth_label": ""  # Explicitly EMPTY column
    })

csv_path = os.path.join(RESULTS_DIR, "real_photo_triage.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["job_id", "filename", "stage_reached", "raw_gate_p_areca", "vit_top3", "yolo_box_count", "truth_label"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in triage_rows:
        writer.writerow(r)

print(f"Successfully generated {csv_path} with {len(triage_rows)} rows.")
