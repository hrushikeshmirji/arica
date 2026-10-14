import os
import glob
import json
import random
from collections import defaultdict
from PIL import Image

random.seed(42)

RAW_DIR = r"D:\dataset_raw\dataset_raw"
RESULTS_DIR = r"D:\ArecaVision_Combined\backend\tests\results"
os.makedirs(RESULTS_DIR, exist_ok=True)

ARECA_CATS = [
    "areca_diseased_fungal_anthracnose",
    "areca_diseased_fungal_fruit_rot",
    "areca_diseased_fungal_sooty_mold",
    "areca_diseased_physiological_nut_cracking",
    "areca_healthy"
]
NON_ARECA_CAT = "non_areca"

# Recreate exact fast_train_gate.py split
areca_files = []
for cat in ARECA_CATS:
    areca_files.extend(glob.glob(os.path.join(RAW_DIR, cat, "*.*")))

non_areca_files = glob.glob(os.path.join(RAW_DIR, NON_ARECA_CAT, "*.*"))

random.shuffle(areca_files)
random.shuffle(non_areca_files)

selected_non_areca = non_areca_files[:700]

val_ratio = 0.2
n_areca_val = int(len(areca_files) * val_ratio)  # 69
n_non_val = int(len(selected_non_areca) * val_ratio)  # 140

areca_train = areca_files[n_areca_val:]  # 280
areca_val = areca_files[:n_areca_val]    # 69

non_train = selected_non_areca[n_non_val:]  # 560
non_val = selected_non_areca[:n_non_val]    # 140

unselected_raw = non_areca_files[700:]

def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

def hamming_dist(h1, h2):
    return bin(h1 ^ h2).count('1')

import numpy as np

seen_hashes = set()
for f in selected_non_areca:
    try:
        with Image.open(f) as img:
            seen_hashes.add(dhash(img))
    except Exception:
        pass

non_never_used = []
never_used_hashes = []
for f in unselected_raw:
    try:
        with Image.open(f) as img:
            h = dhash(img)
            if h not in seen_hashes:
                seen_hashes.add(h)
                non_never_used.append(f)
                never_used_hashes.append(h)
    except Exception:
        pass

print(f"Areca All: {len(areca_files)} (Seen: {len(areca_train)}, Val: {len(areca_val)})")
print(f"Negatives Seen: {len(non_train)}")
print(f"Negatives Val:  {len(non_val)}")
print(f"Negatives Never-used: {len(non_never_used)}")

# Cluster never-used by dHash (Hamming <= 6)
n_nu = len(non_never_used)
visited = [False] * n_nu
clusters = []
for i in range(n_nu):
    if not visited[i]:
        visited[i] = True
        c = [i]
        queue = [i]
        while queue:
            curr = queue.pop(0)
            for j in range(n_nu):
                if not visited[j] and hamming_dist(never_used_hashes[curr], never_used_hashes[j]) <= 6:
                    visited[j] = True
                    c.append(j)
                    queue.append(j)
        clusters.append(c)

print(f"Formed {len(clusters)} clusters from {n_nu} never-used images.")

# Split clusters into SELECT and REPORT halves
random.seed(42)
random.shuffle(clusters)

select_indices = []
report_indices = []

target_half = n_nu // 2
current_select = 0

for c in clusters:
    if current_select < target_half:
        select_indices.extend(c)
        current_select += len(c)
    else:
        report_indices.extend(c)

select_files = [non_never_used[i] for i in select_indices]
report_files = [non_never_used[i] for i in report_indices]

print(f"SELECT Split (for threshold choice): {len(select_files)} images")
print(f"REPORT Split (for final reporting):  {len(report_files)} images")

frozen_splits = {
    "counts": {
        "areca_all_349": len(areca_files),
        "areca_seen_280": len(areca_train),
        "areca_val_69": len(areca_val),
        "negatives_seen_560": len(non_train),
        "negatives_val_140": len(non_val),
        "negatives_never_used_1170": len(non_never_used),
        "negatives_select": len(select_files),
        "negatives_report": len(report_files)
    },
    "areca_train": areca_train,
    "areca_val": areca_val,
    "negatives_train": non_train,
    "negatives_val": non_val,
    "negatives_select": select_files,
    "negatives_report": report_files
}

out_file = os.path.join(RESULTS_DIR, "gate_frozen_splits.json")
with open(out_file, "w") as f:
    json.dump(frozen_splits, f, indent=2)
print(f"Saved frozen splits to {out_file}")
