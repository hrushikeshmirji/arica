import os
import glob
import json
import random
from collections import Counter
from PIL import Image, ImageDraw

random.seed(42)

BASE_DIR = r"D:\ArecaVision_Combined\backend\yolo\dataset"
RESULTS_DIR = r"D:\ArecaVision_Combined\backend\tests\results"
os.makedirs(RESULTS_DIR, exist_ok=True)

splits = ["train", "val", "test"]
boxes_by_split = {}
total_boxes = 0
large_boxes = 0  # w >= 0.85 and h >= 0.85
box_histogram = Counter()

for split in splits:
    lbl_dir = os.path.join(BASE_DIR, "labels", split)
    lbl_files = glob.glob(os.path.join(lbl_dir, "*.txt"))
    split_boxes = []
    for lf in lbl_files:
        with open(lf, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls_id = int(parts[0])
                    cx, cy, w, h = [float(x) for x in parts[1:5]]
                    rounded = (round(cx, 2), round(cy, 2), round(w, 2), round(h, 2))
                    box_histogram[rounded] += 1
                    total_boxes += 1
                    if w >= 0.85 and h >= 0.85:
                        large_boxes += 1
                    split_boxes.append({
                        "file": os.path.basename(lf),
                        "cls_id": cls_id,
                        "cx": cx,
                        "cy": cy,
                        "w": w,
                        "h": h
                    })
    boxes_by_split[split] = split_boxes

share_large = (large_boxes / total_boxes) if total_boxes > 0 else 0.0

print(f"Total YOLO bounding boxes analyzed: {total_boxes}")
print(f"Share with w >= 0.85 and h >= 0.85: {large_boxes}/{total_boxes} ({share_large:.2%})")
print("\nHistogram of (cx, cy, w, h) rounded to 2 decimals:")
for box_coords, count in box_histogram.most_common(10):
    print(f"  {box_coords}: {count} ({count/total_boxes:.2%})")

# Contact sheet of 12 random train images with GT boxes
train_img_dir = os.path.join(BASE_DIR, "images", "train")
train_lbl_dir = os.path.join(BASE_DIR, "labels", "train")
train_imgs = glob.glob(os.path.join(train_img_dir, "*.*"))
random.shuffle(train_imgs)
selected_imgs = train_imgs[:12]

contact_tiles = []
tile_size = (300, 300)

for img_path in selected_imgs:
    bname = os.path.basename(img_path)
    stem = os.path.splitext(bname)[0]
    lbl_path = os.path.join(train_lbl_dir, f"{stem}.txt")
    
    with Image.open(img_path) as img:
        img_rgb = img.convert("RGB")
        W, H = img_rgb.size
        draw = ImageDraw.Draw(img_rgb)
        
        if os.path.exists(lbl_path):
            with open(lbl_path, "r") as lf:
                for line in lf:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id = int(parts[0])
                        cx, cy, w, h = [float(x) for x in parts[1:5]]
                        x1 = int((cx - w / 2) * W)
                        y1 = int((cy - h / 2) * H)
                        x2 = int((cx + w / 2) * W)
                        y2 = int((cy + h / 2) * H)
                        draw.rectangle([x1, y1, x2, y2], outline="red", width=6)
                        draw.text((x1 + 8, y1 + 8), f"GT cls:{cls_id}", fill="yellow")
        
        img_thumb = img_rgb.resize(tile_size, Image.Resampling.LANCZOS)
        contact_tiles.append(img_thumb)

# Montage: 4 columns x 3 rows
montage_w = 4 * tile_size[0]
montage_h = 3 * tile_size[1]
montage = Image.new("RGB", (montage_w, montage_h), color=(30, 30, 30))

for idx, tile in enumerate(contact_tiles):
    r = idx // 4
    c = idx % 4
    montage.paste(tile, (c * tile_size[0], r * tile_size[1]))

montage_path = os.path.join(RESULTS_DIR, "yolo_gt_boxes_contact_sheet.png")
montage.save(montage_path)
print(f"\nSaved contact sheet to {montage_path}")

# Copy to brain artifact directory as well
brain_dir = r"C:\Users\Hrushikesh Mirji\.gemini\antigravity\brain\fe624d87-e861-458c-a7da-19cd9caa26ab"
if os.path.exists(brain_dir):
    montage.save(os.path.join(brain_dir, "yolo_gt_boxes_contact_sheet.png"))

# Save results JSON
results_json = {
    "total_boxes": total_boxes,
    "large_boxes_w085_h085": large_boxes,
    "share_large": share_large,
    "histogram_cx_cy_w_h": {str(k): v for k, v in box_histogram.items()},
    "splits_count": {s: len(boxes_by_split[s]) for s in splits},
    "montage_path": montage_path
}

with open(os.path.join(RESULTS_DIR, "yolo_labels_analysis.json"), "w") as f:
    json.dump(results_json, f, indent=2)
print(f"Saved results to {os.path.join(RESULTS_DIR, 'yolo_labels_analysis.json')}")
