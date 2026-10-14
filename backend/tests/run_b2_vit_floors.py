"""
run_b2_vit_floors.py

Part B2 of ArecaVision Round 5:
- Evaluate ViT on the exact leak-free val set (95 images from vit_leak_free_eval.json)
- Tabulate precision vs coverage across:
  * Top-1 probability thresholds
  * Top1 - Top2 margin thresholds
  * Special analysis for "Healthy" vs diseased
- Save the table to backend/tests/results/vit_confidence_floors.json
- Print recommended provisional thresholds.
"""

import os
import glob
import random
import json
import math
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from torchvision import transforms

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, _HERE)
os.chdir(_HERE)

import config
from vit.model import ViTClassifier

RESULTS_DIR = os.path.join(_HERE, "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

RAW_DIR = r"D:\dataset_raw\dataset_raw"
CATEGORY_TO_DISEASE = {
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "areca_pest_bud_borer": "BudBorer",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "areca_healthy": "Healthy",
    "areca_diseased_fungal_leaf_spot": "LeafSpotComplex",
    "areca_diseased_physiological_nut_cracking": "NutCracking",
    "areca_diseased_phytoplasma_yellow_leaf": "PhytoplasmaYellowLeaf",
    "areca_diseased_fungal_sooty_mold": "SootyMold",
    "areca_diseased_fungal_stem_bleeding": "StemBleeding",
    "areca_diseased_physiological_stem_cracking": "StemCracking",
    "areca_diseased_yellow_leaf_chlorosis": "YellowLeaf",
}

class_to_idx = {name: i for i, name in enumerate(config.DISEASE_CLASSES)}
idx_to_class = {i: name for i, name in enumerate(config.DISEASE_CLASSES)}
val_ratio = 0.2

random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

val_files_by_class = {}
for cat_folder, disease_name in CATEGORY_TO_DISEASE.items():
    cls_idx = class_to_idx[disease_name]
    files = sorted(glob.glob(os.path.join(RAW_DIR, cat_folder, "*.*")))
    random.shuffle(files)
    n_val = int(len(files) * val_ratio)
    val_files_by_class[cls_idx] = files[:n_val]

# Load dropped files from vit_leak_free_eval.json
leak_free_eval_path = os.path.join(RESULTS_DIR, "vit_leak_free_eval.json")
with open(leak_free_eval_path, "r") as f:
    eval_json = json.load(f)

dropped_val_files = set(item["val_file"] for item in eval_json["dropped_details"])

# Exact 95 leak-free files
val_leak_free = []
for cls_idx, files in val_files_by_class.items():
    for f in files:
        if f not in dropped_val_files:
            val_leak_free.append((f, cls_idx))

print(f"Total leak-free validation images: {len(val_leak_free)}")

# Load ViT model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ViTClassifier(num_classes=len(config.DISEASE_CLASSES), pretrained=False).to(device)
ckpt = torch.load("vit/checkpoints/vit_b16.pth", map_location=device, weights_only=False)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

tf_base = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])

results = []
for fpath, true_cls in val_leak_free:
    with Image.open(fpath) as img:
        t = tf_base(img.convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(t)
        probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()
        
    top_indices = np.argsort(probs)[::-1]
    top1_idx = int(top_indices[0])
    top2_idx = int(top_indices[1])
    top1_prob = float(probs[top1_idx])
    top2_prob = float(probs[top2_idx])
    margin = float(top1_prob - top2_prob)
    is_correct = bool(top1_idx == true_cls)
    
    results.append({
        "file": fpath,
        "filename": os.path.basename(fpath),
        "true_class": idx_to_class[true_cls],
        "pred_class": idx_to_class[top1_idx],
        "top1_prob": round(top1_prob, 4),
        "top2_prob": round(top2_prob, 4),
        "margin": round(margin, 4),
        "is_correct": is_correct,
        "is_pred_healthy": bool(idx_to_class[top1_idx] == "Healthy"),
        "is_true_healthy": bool(idx_to_class[true_cls] == "Healthy"),
    })

N = len(results)
print(f"Baseline accuracy on leak-free set: {sum(r['is_correct'] for r in results)}/{N} ({sum(r['is_correct'] for r in results)/N:.2%})")

# Tabulate across top-1 probability thresholds
prob_thresholds = [0.30, 0.40, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
margin_thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

prob_table = []
for th in prob_thresholds:
    covered = [r for r in results if r["top1_prob"] >= th]
    cov_count = int(len(covered))
    cov_pct = float(cov_count / N)
    correct_count = int(sum(r["is_correct"] for r in covered))
    prec = float(correct_count / cov_count) if cov_count > 0 else 0.0
    prob_table.append({
        "threshold": float(th),
        "covered": cov_count,
        "coverage_pct": round(cov_pct * 100, 1),
        "correct": correct_count,
        "precision_pct": round(prec * 100, 1),
    })

margin_table = []
for m_th in margin_thresholds:
    covered = [r for r in results if r["margin"] >= m_th]
    cov_count = int(len(covered))
    cov_pct = float(cov_count / N)
    correct_count = int(sum(r["is_correct"] for r in covered))
    prec = float(correct_count / cov_count) if cov_count > 0 else 0.0
    margin_table.append({
        "margin_threshold": float(m_th),
        "covered": cov_count,
        "coverage_pct": round(cov_pct * 100, 1),
        "correct": correct_count,
        "precision_pct": round(prec * 100, 1),
    })

# Special analysis for "Healthy" predictions
healthy_preds = [r for r in results if r["is_pred_healthy"]]
print(f"\nTotal predictions of 'Healthy': {len(healthy_preds)}")
for h in healthy_preds:
    print(f"  {h['filename']}: True={h['true_class']}, top1_p={h['top1_prob']:.4f}, margin={h['margin']:.4f}, correct={h['is_correct']}")

healthy_table = []
for th in prob_thresholds:
    cov_h = [r for r in healthy_preds if r["top1_prob"] >= th]
    cov_count = int(len(cov_h))
    cov_pct = float(cov_count / len(healthy_preds)) if healthy_preds else 0.0
    correct_count = int(sum(r["is_correct"] for r in cov_h))
    prec = float(correct_count / cov_count) if cov_count > 0 else 0.0
    healthy_table.append({
        "threshold": float(th),
        "covered": cov_count,
        "coverage_pct": round(cov_pct * 100, 1),
        "correct": correct_count,
        "precision_pct": round(prec * 100, 1),
    })

# Recommended provisional thresholds
recommended = {
    "status": "provisional",
    "disease_prob_floor": 0.50,
    "disease_margin_floor": 0.10,
    "healthy_prob_floor": 0.70,
    "healthy_margin_floor": 0.25,
    "notes": "All thresholds are provisional and subject to clinical field validation on unselected specimens."
}

out_data = {
    "total_leak_free_val": N,
    "baseline_accuracy": float(sum(r["is_correct"] for r in results) / N),
    "prob_threshold_table": prob_table,
    "margin_threshold_table": margin_table,
    "healthy_prediction_table": healthy_table,
    "recommended_provisional_floors": recommended,
    "individual_predictions": results
}

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

out_path = os.path.join(RESULTS_DIR, "vit_confidence_floors.json")
with open(out_path, "w") as f:
    json.dump(out_data, f, indent=2, cls=NpEncoder)

print(f"\nSaved vit confidence floors table to {out_path}")
