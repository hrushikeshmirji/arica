"""
run_r6_a6_triage.py

Task A6:
- Drop uploads created by test scripts (dataset-hash or ood_probe matches).
- Print the genuine upload count, accepted/rejected/uncertain/low-confidence counts,
  zero-box count, and how often ViT top-1 is a seed_* class with p>=0.8.
- Save output to backend/tests/results/r6_a6_genuine_triage.json.
"""

import os
import sys
import glob
import json
import sqlite3
import hashlib

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

UPLOADS_DIR = os.path.join(_HERE, "data", "uploads")
DB_PATH = os.path.join(_HERE, "data", "arecavision.db")
DATASET_ROOT = r"D:\dataset_raw\dataset_raw"
OOD_PROBE_DIR = os.path.join(_HERE, "tests", "ood_probe")

def get_file_sha256(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

# 1. Build hash database of test script files
known_hashes = {}
print("Hashing all dataset images and ood_probe images...")
for p in glob.glob(os.path.join(DATASET_ROOT, "**", "*.*"), recursive=True):
    if p.lower().endswith(('.jpg', '.jpeg', '.png')):
        sh = get_file_sha256(p)
        if sh:
            known_hashes[sh] = p

for p in glob.glob(os.path.join(OOD_PROBE_DIR, "*.*")):
    if p.lower().endswith(('.jpg', '.jpeg', '.png')):
        sh = get_file_sha256(p)
        if sh:
            known_hashes[sh] = p

print(f"Total known test/dataset hashes: {len(known_hashes)}")

# 2. Inspect all files in uploads
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, status, stage, result_json, created_at FROM jobs")
jobs = cur.fetchall()

jobs_by_upload = {}
for j in jobs:
    if not j["result_json"]:
        continue
    try:
        res = json.loads(j["result_json"])
        img_url = res.get("imageUrl", "")
        if img_url:
            fname = os.path.basename(img_url)
            jobs_by_upload[fname] = (j, res)
    except Exception:
        pass

upload_files = sorted(glob.glob(os.path.join(UPLOADS_DIR, "*.*")))
print(f"Total files in uploads dir: {len(upload_files)}")

# The six seed classes
SEED_DISEASE_KEYS = {
    "Bud Borer",
    "Leaf Spot Complex",
    "Stem Bleeding",
    "Stem Cracking",
    "Phytoplasma Yellow Leaf",
    "Yellow Leaf Disease",
}

genuine_uploads = []
dropped_uploads = []

for up_path in upload_files:
    fname = os.path.basename(up_path)
    sh = get_file_sha256(up_path)
    
    if sh in known_hashes:
        dropped_uploads.append({
            "filename": fname,
            "matched_source": known_hashes[sh],
            "sha256": sh
        })
        continue
    
    # Check if job exists
    job_info, res = jobs_by_upload.get(fname, (None, None))
    
    stage = res.get("stage", "Unknown") if res else (job_info["stage"] if job_info else "No_Job")
    yolo_boxes = res.get("yoloBoxes", []) if res else []
    disease = res.get("disease", "Unknown") if res else "Unknown"
    conf = res.get("confidence", 0.0) if res else 0.0
    
    # Differential diagnosis / top-1 check
    differential = res.get("differentialDiagnosis", []) if res else []
    top1_disease = differential[0]["disease"] if differential else disease
    top1_prob = differential[0]["probability"] / 100.0 if differential else (conf / 100.0)
    
    is_seed_class_ge_80 = (top1_disease in SEED_DISEASE_KEYS) and (top1_prob >= 0.80)
    
    genuine_uploads.append({
        "filename": fname,
        "sha256": sh,
        "job_id": job_info["id"] if job_info else None,
        "stage": stage,
        "disease": disease,
        "confidence": conf,
        "yolo_box_count": len(yolo_boxes),
        "top1_disease": top1_disease,
        "top1_prob": top1_prob,
        "is_seed_class_ge_80": is_seed_class_ge_80
    })

print("=" * 80)
print(f"TRIAGE RESULTS:")
print(f"Total uploaded files in uploads dir : {len(upload_files)}")
print(f"Dropped (matched dataset/probe hash): {len(dropped_uploads)}")
print(f"Genuine user uploads                : {len(genuine_uploads)}")
print("=" * 80)

# Stage counts among genuine uploads
accepted_count = sum(1 for g in genuine_uploads if "detected" in g["stage"].lower())
rejected_count = sum(1 for g in genuine_uploads if "defense" in g["stage"].lower() or "rejected" in g["stage"].lower())
uncertain_count = sum(1 for g in genuine_uploads if "uncertain" in g["stage"].lower())
low_conf_count = sum(1 for g in genuine_uploads if "low confidence" in g["stage"].lower())
other_count = len(genuine_uploads) - (accepted_count + rejected_count + uncertain_count + low_conf_count)

zero_box_count = sum(1 for g in genuine_uploads if g["yolo_box_count"] == 0)
seed_ge_80_count = sum(1 for g in genuine_uploads if g["is_seed_class_ge_80"])

print(f"Stage Breakdown (Genuine Uploads):")
print(f"  Accepted (Detected) : {accepted_count}")
print(f"  Rejected (Gatekeeper Defense) : {rejected_count}")
print(f"  Gatekeeper Uncertain : {uncertain_count}")
print(f"  Low confidence       : {low_conf_count}")
if other_count > 0:
    print(f"  Other / Incomplete   : {other_count}")

print(f"\nZero YOLO Box Count   : {zero_box_count} / {len(genuine_uploads)} ({(zero_box_count / max(1, len(genuine_uploads))) * 100:.1f}%)")
print(f"ViT Top-1 in seed_* with p>=0.80 : {seed_ge_80_count} / {len(genuine_uploads)} ({(seed_ge_80_count / max(1, len(genuine_uploads))) * 100:.1f}%)")

triage_summary = {
    "total_uploads": len(upload_files),
    "dropped_count": len(dropped_uploads),
    "genuine_count": len(genuine_uploads),
    "stages": {
        "accepted": accepted_count,
        "rejected": rejected_count,
        "uncertain": uncertain_count,
        "low_confidence": low_conf_count,
        "other": other_count
    },
    "zero_box_count": zero_box_count,
    "vit_top1_seed_class_ge_80": seed_ge_80_count,
    "genuine_records": genuine_uploads
}

out_path = os.path.join(RESULTS_DIR, "r6_a6_genuine_triage.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(triage_summary, f, indent=2)

print(f"\nSaved triage summary to {out_path}")
