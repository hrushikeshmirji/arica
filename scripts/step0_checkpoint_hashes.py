import os
import glob
import json
import hashlib
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_PATH = os.path.join(REPO_ROOT, "results", "train", "checkpoint_hashes_before.json")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

BASELINES = {
    "CNN": "62A43C03CD72AD73B26FE1E40A278FC33211EC4388A29B45FF5F0ADBD339AAFF".upper(),
    "ViT": "98D11021FE5D61E2661CCDEFFE6E4B8EAF0DB4BEB17672B5B7F55F945C85B112".upper(),
    "YOLO best.pt": "13D87EAF7A5C6FBDE6A31B40D0520F477A2A12C87E5C4540412D18A49374FD8B".upper(),
}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()

search_dirs = [
    os.path.join(REPO_ROOT, "backend"),
    os.path.join(REPO_ROOT, "runs"),
]

checkpoint_files = []
for sdir in search_dirs:
    for ext in ("*.pt", "*.pth"):
        for fp in glob.glob(os.path.join(sdir, "**", ext), recursive=True):
            if "venv" in fp:
                continue
            checkpoint_files.append(fp)

checkpoint_files = sorted(list(set(checkpoint_files)))

results = {}
comparisons = {}

for fp in checkpoint_files:
    rel_path = os.path.relpath(fp, REPO_ROOT).replace("\\", "/")
    st = os.stat(fp)
    sha256 = compute_sha256(fp)
    mtime_dt = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    
    results[rel_path] = {
        "size_bytes": st.st_size,
        "mtime": st.st_mtime,
        "mtime_iso": mtime_dt,
        "sha256": sha256
    }

# Baseline verification
cnn_path = "backend/cnn/checkpoints/cnn_efficientnet_b0.pth"
vit_path = "backend/vit/checkpoints/vit_b16.pth"
yolo_path = "backend/yolo/checkpoints/best.pt"

comparisons["CNN"] = {
    "file": cnn_path,
    "actual_sha256": results.get(cnn_path, {}).get("sha256"),
    "expected_sha256": BASELINES["CNN"],
    "match": results.get(cnn_path, {}).get("sha256") == BASELINES["CNN"]
}

comparisons["ViT"] = {
    "file": vit_path,
    "actual_sha256": results.get(vit_path, {}).get("sha256"),
    "expected_sha256": BASELINES["ViT"],
    "match": results.get(vit_path, {}).get("sha256") == BASELINES["ViT"]
}

comparisons["YOLO best.pt"] = {
    "file": yolo_path,
    "actual_sha256": results.get(yolo_path, {}).get("sha256"),
    "expected_sha256": BASELINES["YOLO best.pt"],
    "match": results.get(yolo_path, {}).get("sha256") == BASELINES["YOLO best.pt"]
}

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "checkpoints": results,
    "baseline_comparisons": comparisons
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)

print(f"Wrote checkpoint verification to: {OUTPUT_PATH}")
print(f"Total checkpoints inspected: {len(results)}")
print("\n=== BASELINE COMPARISON RESULTS ===")
for model, comp in comparisons.items():
    status = "MATCH" if comp["match"] else "MISMATCH"
    print(f"[{status}] {model} ({comp['file']})")
    print(f"  Actual:   {comp['actual_sha256']}")
    print(f"  Expected: {comp['expected_sha256']}")

print("\n=== ALL INSPECTED CHECKPOINTS ===")
for path, info in results.items():
    print(f"{path}:")
    print(f"  Size: {info['size_bytes']} bytes | MTime: {info['mtime_iso']}")
    print(f"  SHA-256: {info['sha256']}")
