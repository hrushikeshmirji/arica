"""
backend/tests/run_a6_audit_uploads.py — Audit last 50 non-test uploads in arecavision.db / uploads.
"""

import os
import sys
import json
import sqlite3
import numpy as np
from PIL import Image, ImageOps

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

import config
from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor

RESULTS_DIR = os.path.join(REPO_ROOT, "backend", "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
DB_PATH = os.path.join(REPO_ROOT, "backend", "data", "arecavision.db")
UPLOADS_DIR = os.path.join(REPO_ROOT, "backend", "data", "uploads")

print("Initializing models for A6 Upload Audit...")
cnn_pred = CNNPredictor()
vit_pred = ViTPredictor()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get recent completed jobs with result_json
c.execute("""
    SELECT id, created_at, result_json 
    FROM jobs 
    WHERE status='done' AND result_json IS NOT NULL 
    ORDER BY rowid DESC
""")
all_jobs = c.fetchall()

print(f"Total done jobs in DB: {len(all_jobs)}")

# Extract unique image uploads
audited = []
seen_files = set()

for job_id, created_at, res_json_str in all_jobs:
    try:
        res = json.loads(res_json_str)
    except Exception:
        continue
        
    img_url = res.get("imageUrl") or ""
    if not img_url:
        continue
        
    fname = os.path.basename(img_url)
    if fname in seen_files:
        continue
        
    local_path = os.path.join(UPLOADS_DIR, fname)
    if not os.path.isfile(local_path):
        continue
        
    seen_files.add(fname)
    
    # Run through pipeline
    try:
        with open(local_path, "rb") as f:
            raw_bytes = f.read()
        im = Image.open(local_path)
        try:
            im = ImageOps.exif_transpose(im)
        except Exception:
            pass
        rgb = np.asarray(im.convert("RGB"))
        
        gate_lbl, gate_conf = cnn_pred.predict(rgb)
        gate_score = float(gate_conf) * 100.0
        
        tta = vit_pred.predict_tta_ensemble(rgb)
        vit_top3 = [(d["disease"], round(float(d["probability"]), 1)) for d in tta["differential"][:3]]
        
        # Original stored result
        orig_disease = res.get("disease", "")
        orig_stage = res.get("stage", "")
        orig_conf = res.get("confidence", 0)
        yolo_boxes = res.get("yoloBoxes", [])
        box_count = len(yolo_boxes)
        
        # Categorize
        # Is it non-areca?
        if gate_lbl != "Arecanut" or gate_score < 75.0:
            category = "Gated (Non-Arecanut / Low Gate)"
        elif "Review Required" in orig_disease or orig_stage == "Review Required":
            category = "Correctly Gated (Review Required - No YOLO Lesions)"
        elif "Low confidence" in orig_disease or orig_stage == "Low confidence":
            category = "Correctly Gated (Low Confidence Floor)"
        elif orig_stage == "Detected":
            # Confident diagnosis issued
            category = "Confident Issued Diagnosis"
        else:
            category = f"Other ({orig_stage})"
            
        audited.append({
            "job_id": job_id,
            "filename": fname,
            "created_at": created_at,
            "file_size": len(raw_bytes),
            "gate_label": gate_lbl,
            "gate_score": round(gate_score, 1),
            "vit_predicted": tta["label"],
            "vit_conf": round(float(tta["confidence"]) * 100.0, 1),
            "vit_top3": vit_top3,
            "yolo_box_count": box_count,
            "stored_stage": orig_stage,
            "stored_label_displayed": orig_disease,
            "stored_conf": orig_conf,
            "category": category
        })
        
        if len(audited) >= 50:
            break
    except Exception as e:
        print(f"Error processing {fname}: {e}")

print(f"\nAudited {len(audited)} unique non-test uploads.")

# Compute statistics
category_counts = {}
for a in audited:
    cat = a["category"]
    category_counts[cat] = category_counts.get(cat, 0) + 1

print("\n--- CATEGORY SUMMARY ---")
for cat, count in category_counts.items():
    print(f"  {cat}: {count} ({count/len(audited)*100:.1f}%)")

out_file = os.path.join(RESULTS_DIR, "a6_last_50_uploads.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump({
        "total_audited": len(audited),
        "summary": category_counts,
        "items": audited
    }, f, indent=2)

print(f"\nSaved audit results to: {out_file}")
