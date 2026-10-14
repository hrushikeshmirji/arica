import os
import zipfile
import hashlib
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKUP_DIR = r"D:\arecavision_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

DATASET_V2_DIR = os.path.join(REPO_ROOT, "backend", "yolo", "dataset_repaired_phase3b_v2")
ZIP_DEST = os.path.join(BACKUP_DIR, "dataset_repaired_phase3b_v2_backup.zip")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()

print(f"Creating zip backup of:\n  {DATASET_V2_DIR}\nto:\n  {ZIP_DEST} ...")

with zipfile.ZipFile(ZIP_DEST, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(DATASET_V2_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, os.path.dirname(DATASET_V2_DIR))
            zf.write(full_path, rel_path)
    
    clean_manifest_path = os.path.join(REPO_ROOT, "backend", "data", "clean_dataset_manifest.json")
    if os.path.exists(clean_manifest_path):
        zf.write(clean_manifest_path, os.path.join("data", "clean_dataset_manifest.json"))
        print(f"Added {clean_manifest_path} to archive.")

file_size = os.path.getsize(ZIP_DEST)
sha256_hash = compute_sha256(ZIP_DEST)

print("\n=== DATASET BACKUP VERIFICATION ===")
print(f"Backup Path:    {ZIP_DEST}")
print(f"Size (Bytes):   {file_size}")
print(f"Size (MB):      {file_size / (1024 * 1024):.2f} MB")
print(f"SHA-256:        {sha256_hash}")

# Save record in results/train/backup_info.json
record_path = os.path.join(REPO_ROOT, "results", "train", "dataset_backup_info.json")
import json
with open(record_path, "w", encoding="utf-8") as f:
    json.dump({
        "backup_path": ZIP_DEST,
        "source_dir": DATASET_V2_DIR,
        "size_bytes": file_size,
        "sha256": sha256_hash,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }, f, indent=2)
print(f"Recorded in:    {record_path}")
