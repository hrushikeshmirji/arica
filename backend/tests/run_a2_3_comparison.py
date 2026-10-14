"""
backend/tests/run_a2_3_comparison.py — Audit job-bfd163d5cc18 and 3 other recent jobs.
Compares DB stored label, Dashboard/History display label, and fresh Detection pipeline run.
Also compares timestamps: job creation vs model checkpoints vs code mtime.
"""

import os
import sys
import json
import sqlite3
import datetime
import numpy as np
from PIL import Image, ImageOps

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

import config
from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor
from yolo.detect import YOLODetector

DB_PATH = os.path.join(REPO_ROOT, "backend", "data", "arecavision.db")
UPLOADS_DIR = os.path.join(REPO_ROOT, "backend", "data", "uploads")
RESULTS_DIR = os.path.join(REPO_ROOT, "backend", "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# 1. Inspect Checkpoints and Code Timestamps
checkpoints_info = {}
for name, p in [
    ("CNN_CHECKPOINT", config.CNN_CHECKPOINT),
    ("VIT_CHECKPOINT", config.VIT_CHECKPOINT),
    ("YOLO_CHECKPOINT", config.YOLO_CHECKPOINT),
    ("SERVER_APP_PY", os.path.join(REPO_ROOT, "backend", "server", "app.py")),
]:
    if os.path.exists(p):
        st = os.stat(p)
        mtime_utc = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat()
        checkpoints_info[name] = {
            "path": p,
            "mtime": mtime_utc,
            "size": st.st_size
        }
    else:
        checkpoints_info[name] = {"path": p, "status": "NOT FOUND"}

print("=== CHECKPOINT & CODE TIMESTAMPS ===")
for k, v in checkpoints_info.items():
    print(f"  {k}: {v.get('mtime', v.get('status'))}")

# 2. Jobs to evaluate
target_jobs = [
    "job-bfd163d5cc18",  # User's uploaded fruit rot photo (classified as Nut Cracking)
    "job-cf4231f24196",  # Recent image 1
    "job-c79ebdc59016",  # Recent non-areca image
    "job-d654c45f88d5",  # Another job with Nut Cracking
]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("\nInitializing models for fresh inference...")
cnn_pred = CNNPredictor()
vit_pred = ViTPredictor()
yolo_det = YOLODetector()

job_evaluations = []

for jid in target_jobs:
    c.execute("SELECT id, created_at, result_json FROM jobs WHERE id=?", (jid,))
    row = c.fetchone()
    if not row:
        print(f"Job {jid} not found!")
        continue
    
    job_id, created_at, res_json_str = row
    res_db = json.loads(res_json_str) if res_json_str else {}
    
    # Check scans table
    c.execute("SELECT id, disease, confidence, status, severity FROM scans WHERE image_url LIKE ?", (f"%{jid}%",))
    scan_row = c.fetchone()
    
    stored_disease = res_db.get("disease", "")
    stored_stage = res_db.get("stage", "")
    stored_conf = res_db.get("confidence", 0)
    stored_top3 = res_db.get("differentialDiagnosis", [])
    
    # UI Card / History representation
    # On Dashboard: renders scanResult.disease
    # On History: renders scan.disease (if in scans, else from localStorage)
    dashboard_card_text = stored_disease
    history_row_text = scan_row[1] if scan_row else "(Not synced to scans table: stage != Detected)"
    
    # Run fresh inference on the uploaded image
    img_url = res_db.get("imageUrl", "")
    fname = os.path.basename(img_url) if img_url else f"{jid}.jpg"
    local_path = os.path.join(UPLOADS_DIR, fname)
    
    fresh_eval = {}
    if os.path.exists(local_path):
        im = Image.open(local_path)
        try:
            im = ImageOps.exif_transpose(im)
        except Exception:
            pass
        rgb = np.asarray(im.convert("RGB"))
        
        gl, gc = cnn_pred.predict(rgb)
        gate_conf = float(gc) * 100.0
        
        detections, _annotated_bgr = yolo_det.detect(rgb)
        yolo_boxes = [d for d in (detections or []) if float(d.get("confidence", 0)) >= 0.25]
        
        tta = vit_pred.predict_tta_ensemble(rgb)
        vit_top = tta["label"]
        vit_conf = float(tta["confidence"]) * 100.0
        vit_top3 = [(d["disease"], round(float(d["probability"]), 1)) for d in tta["differential"][:3]]
        
        # Apply app.py pipeline rules
        from server.app import DISEASE_DISPLAY_NAMES
        top_display = DISEASE_DISPLAY_NAMES.get(vit_top, vit_top)
        
        is_zero_yolo = (not yolo_boxes and vit_top != "Healthy")
        if gl != "Arecanut" or gate_conf < 75.0:
            fresh_disease = "Not an Arecanut image"
            fresh_stage = "Gatekeeper Defense"
        elif is_zero_yolo:
            fresh_disease = f"Review Required: No Lesions Detected ({top_display})"
            fresh_stage = "Review Required"
        elif vit_top == "Healthy" and vit_conf < 70.0:
            fresh_disease = f"Low confidence: {top_display}"
            fresh_stage = "Low confidence"
        elif vit_top != "Healthy" and vit_conf < 50.0:
            fresh_disease = f"Low confidence: {top_display}"
            fresh_stage = "Low confidence"
        else:
            fresh_disease = top_display
            fresh_stage = "Detected"
            
        fresh_eval = {
            "fresh_disease": fresh_disease,
            "fresh_stage": fresh_stage,
            "gate_label": gl,
            "gate_conf": round(gate_conf, 1),
            "yolo_boxes_count": len(yolo_boxes),
            "vit_top": vit_top,
            "vit_conf": round(vit_conf, 1),
            "vit_top3": vit_top3
        }
    else:
        fresh_eval = {"error": f"Image file {local_path} does not exist"}

    differ = (stored_disease != fresh_eval.get("fresh_disease")) or (stored_stage != fresh_eval.get("fresh_stage"))

    eval_record = {
        "job_id": job_id,
        "created_at_utc": created_at,
        "image_file": fname,
        "stored_db_disease": stored_disease,
        "stored_db_stage": stored_stage,
        "stored_db_confidence": stored_conf,
        "stored_db_top3": stored_top3,
        "dashboard_card_text": dashboard_card_text,
        "history_row_text": history_row_text,
        "fresh_run": fresh_eval,
        "stored_vs_fresh_differs": differ
    }
    job_evaluations.append(eval_record)
    
    print(f"\n--- Job: {job_id} ({created_at}) ---")
    print(f"  Stored in DB:      [{stored_stage}] {stored_disease} ({stored_conf}%)")
    print(f"  Dashboard Card:    {dashboard_card_text}")
    print(f"  History Page:      {history_row_text}")
    print(f"  Fresh Detection:   [{fresh_eval.get('fresh_stage')}] {fresh_eval.get('fresh_disease')}")
    print(f"  Differs?           {differ}")

output_payload = {
    "checkpoint_and_code_timestamps": checkpoints_info,
    "evaluated_jobs": job_evaluations
}

out_path = os.path.join(RESULTS_DIR, "a2_3_job_comparisons.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2)

print(f"\nSaved A2.3 comparison to: {out_path}")
