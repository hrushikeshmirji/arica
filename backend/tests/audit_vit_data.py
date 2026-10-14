import os
import glob
import json
from collections import Counter, defaultdict
import numpy as np
from PIL import Image

RAW_DIR = r"D:\dataset_raw\dataset_raw"
RESULTS_DIR = r"D:\ArecaVision_Combined\backend\tests\results"
os.makedirs(RESULTS_DIR, exist_ok=True)

ARECA_CLASSES = [
    "areca_diseased_fungal_anthracnose",
    "areca_pest_bud_borer",
    "areca_diseased_fungal_fruit_rot",
    "areca_healthy",
    "areca_diseased_fungal_leaf_spot",
    "areca_diseased_physiological_nut_cracking",
    "areca_diseased_phytoplasma_yellow_leaf",
    "areca_diseased_fungal_sooty_mold",
    "areca_diseased_fungal_stem_bleeding",
    "areca_diseased_physiological_stem_cracking",
    "areca_diseased_yellow_leaf_chlorosis"
]

SIX_CLASSES = [
    "areca_pest_bud_borer",
    "areca_diseased_fungal_leaf_spot",
    "areca_diseased_phytoplasma_yellow_leaf",
    "areca_diseased_fungal_stem_bleeding",
    "areca_diseased_physiological_stem_cracking",
    "areca_diseased_yellow_leaf_chlorosis"
]

def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

def hamming_dist(h1, h2):
    return bin(h1 ^ h2).count('1')

def cluster_hashes(hashes, max_dist=6):
    n = len(hashes)
    visited = [False] * n
    clusters = []
    for i in range(n):
        if not visited[i]:
            visited[i] = True
            c = [i]
            queue = [i]
            while queue:
                curr = queue.pop(0)
                for j in range(n):
                    if not visited[j] and hamming_dist(hashes[curr], hashes[j]) <= max_dist:
                        visited[j] = True
                        c.append(j)
                        queue.append(j)
            clusters.append(c)
    return len(clusters)

class_audit = {}
all_files_info = []

print("=== AUDITING ViT 11 CLASS FOLDERS ===")
header = f"{'Folder':<42} | {'Count':<5} | {'Clusters':<8} | {'Filename Pattern Examples'}"
print(header)
print("-" * 90)

for cname in ARECA_CLASSES:
    cdir = os.path.join(RAW_DIR, cname)
    files = sorted(glob.glob(os.path.join(cdir, "*.*")))
    sizes = []
    hashes = []
    fnames = []
    patterns = Counter()
    
    for f in files:
        bname = os.path.basename(f)
        fnames.append(bname)
        # Identify pattern
        if bname.startswith("download"):
            patterns["download_*.ext"] += 1
        elif bname.startswith("IMG") or bname.startswith("DSC"):
            patterns["camera_IMG_*.ext"] += 1
        elif "_" in bname and bname.split("_")[0].isalpha():
            patterns[f"{bname.split('_')[0]}_*.ext"] += 1
        else:
            patterns["other"] += 1
            
        try:
            with Image.open(f) as img:
                sizes.append(img.size)
                h = dhash(img)
                hashes.append(h)
                all_files_info.append({
                    "path": f,
                    "filename": bname,
                    "class": cname,
                    "hash": h,
                    "size": img.size
                })
        except Exception:
            pass

    n_clusters = cluster_hashes(hashes, max_dist=6) if hashes else 0
    size_counts = Counter(sizes)
    pat_str = ", ".join([f"{k}({v})" for k, v in patterns.most_common(2)])
    print(f"{cname:<42} | {len(files):<5} | {n_clusters:<8} | {pat_str}")
    
    class_audit[cname] = {
        "file_count": len(files),
        "dhash_clusters_h6": n_clusters,
        "filename_patterns": dict(patterns),
        "top_resolutions": [f"{w}x{h} ({cnt})" for (w, h), cnt in size_counts.most_common(3)],
        "min_size": list(min(sizes, key=lambda s: s[0]*s[1])) if sizes else [],
        "max_size": list(max(sizes, key=lambda s: s[0]*s[1])) if sizes else []
    }

# Cross-class duplicate check (Hamming <= 6)
print("\n=== CROSS-CLASS DUPLICATE CHECK (HAMMING <= 6) ===")
cross_class_pairs = []
n_all = len(all_files_info)

for i in range(n_all):
    for j in range(i + 1, n_all):
        if all_files_info[i]["class"] != all_files_info[j]["class"]:
            dist = hamming_dist(all_files_info[i]["hash"], all_files_info[j]["hash"])
            if dist <= 6:
                pair = {
                    "dist": dist,
                    "file_a": all_files_info[i]["filename"],
                    "class_a": all_files_info[i]["class"],
                    "file_b": all_files_info[j]["filename"],
                    "class_b": all_files_info[j]["class"]
                }
                cross_class_pairs.append(pair)

print(f"Total cross-class duplicate/near-duplicate pairs found: {len(cross_class_pairs)}")
for p in cross_class_pairs[:20]:
    print(f"  [dist={p['dist']}] {p['class_a']}/{p['file_a']} <--> {p['class_b']}/{p['file_b']}")

# Check whether six 51-image classes are duplicates of each other
print("\n=== RELATIONSHIP AMONG THE SIX 51-IMAGE CLASSES ===")
six_pairs = [p for p in cross_class_pairs if p["class_a"] in SIX_CLASSES and p["class_b"] in SIX_CLASSES]
print(f"Duplicate pairs strictly between the six 51-image classes: {len(six_pairs)}")
for p in six_pairs:
    print(f"  [dist={p['dist']}] {p['class_a']}/{p['file_a']} <--> {p['class_b']}/{p['file_b']}")

six_vs_others = [p for p in cross_class_pairs if (p["class_a"] in SIX_CLASSES and p["class_b"] not in SIX_CLASSES) or (p["class_b"] in SIX_CLASSES and p["class_a"] not in SIX_CLASSES)]
print(f"\nDuplicate pairs between the six 51-image classes and the other 5 classes: {len(six_vs_others)}")
for p in six_vs_others:
    print(f"  [dist={p['dist']}] {p['class_a']}/{p['file_a']} <--> {p['class_b']}/{p['file_b']}")

out_audit = {
    "classes": class_audit,
    "total_cross_class_pairs": len(cross_class_pairs),
    "six_classes_internal_pairs": len(six_pairs),
    "six_classes_vs_other_pairs": len(six_vs_others),
    "cross_class_pairs": cross_class_pairs
}

json_path = os.path.join(RESULTS_DIR, "vit_data_audit.json")
with open(json_path, "w") as f:
    json.dump(out_audit, f, indent=2)
print(f"\nSaved audit to {json_path}")
