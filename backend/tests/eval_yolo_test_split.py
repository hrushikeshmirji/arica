import os
import json
import glob
from ultralytics import YOLO

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_HERE)

RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

ckpt_path = os.path.join(_HERE, "yolo", "checkpoints", "best.pt")
data_yaml = os.path.join(_HERE, "yolo", "dataset.yaml")

print(f"Loading YOLO model from: {ckpt_path}")
model = YOLO(ckpt_path)

# 1. Evaluate on TEST split (39 images)
print("\n--- Running model.val() on TEST split (39 images) ---")
metrics = model.val(data=data_yaml, split="test", imgsz=640, device="cpu", verbose=True)

# Ultralytics metrics extraction
map50 = float(metrics.box.map50)
map50_95 = float(metrics.box.map)
mp = float(metrics.box.mp)
mr = float(metrics.box.mr)

class_names = model.names
per_class_results = {}
for i, c_idx in enumerate(metrics.box.ap_class_index):
    c_name = class_names[c_idx]
    p_val = float(metrics.box.p[i])
    r_val = float(metrics.box.r[i])
    ap50_val = float(metrics.box.ap50[i])
    per_class_results[c_name] = {
        "class_id": int(c_idx),
        "precision": p_val,
        "recall": r_val,
        "mAP50": ap50_val
    }

print("\n=== TEST SPLIT OVERALL METRICS ===")
print(f"mAP50:      {map50:.4f} ({map50:.2%})")
print(f"mAP50-95:   {map50_95:.4f} ({map50_95:.2%})")
print(f"Mean Prec:  {mp:.4f} ({mp:.2%})")
print(f"Mean Rec:   {mr:.4f} ({mr:.2%})")

print("\n=== PER-CLASS METRICS (TEST SPLIT) ===")
header = f"{'Class':<25} | {'Precision':<12} | {'Recall':<12} | {'mAP50':<12}"
print(header)
print("-" * len(header))
for c_name, c_data in per_class_results.items():
    print(f"{c_name:<25} | {c_data['precision']:<12.4%} | {c_data['recall']:<12.4%} | {c_data['mAP50']:<12.4%}")

# 2. Count predictions on VAL split at conf=0.25 and conf=0.10
val_img_dir = os.path.join(_HERE, "yolo", "dataset", "images", "val")
val_imgs = sorted(glob.glob(os.path.join(val_img_dir, "*.*")))
n_val = len(val_imgs)
print(f"\n--- Checking predictions on VAL split ({n_val} images) ---")

preds_at_25 = 0
preds_at_10 = 0

for img_p in val_imgs:
    res_25 = model.predict(source=img_p, conf=0.25, verbose=False, device="cpu")
    if len(res_25[0].boxes) > 0:
        preds_at_25 += 1

    res_10 = model.predict(source=img_p, conf=0.10, verbose=False, device="cpu")
    if len(res_10[0].boxes) > 0:
        preds_at_10 += 1

print(f"Validation images with >= 1 detection at conf=0.25: {preds_at_25}/{n_val} ({preds_at_25/n_val:.2%})")
print(f"Validation images with >= 1 detection at conf=0.10: {preds_at_10}/{n_val} ({preds_at_10/n_val:.2%})")

# Save results
out_json = {
    "test_split": {
        "n_images": 39,
        "mAP50": map50,
        "mAP50_95": map50_95,
        "mean_precision": mp,
        "mean_recall": mr,
        "per_class": per_class_results
    },
    "val_split_predictions": {
        "n_val_images": n_val,
        "conf_0_25_detected": preds_at_25,
        "conf_0_25_share": preds_at_25 / n_val if n_val > 0 else 0,
        "conf_0_10_detected": preds_at_10,
        "conf_0_10_share": preds_at_10 / n_val if n_val > 0 else 0
    }
}

json_path = os.path.join(RESULTS_DIR, "yolo_val_test.json")
with open(json_path, "w") as f:
    json.dump(out_json, f, indent=2)
print(f"\nSaved results to {json_path}")
