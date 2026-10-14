import os
import sys
import json
import math
import numpy as np
from PIL import Image
import cv2
import torch
from torchvision import transforms
import albumentations as A
from albumentations.pytorch import ToTensorV2
from sklearn.metrics import roc_auc_score

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

from cnn.model import CNNClassifier

RESULTS_DIR = os.path.join(_HERE, "tests", "results")
splits_file = os.path.join(RESULTS_DIR, "gate_frozen_splits.json")

with open(splits_file, "r") as f:
    splits_data = json.load(f)

areca_all = splits_data["areca_train"] + splits_data["areca_val"]
areca_val = splits_data["areca_val"]
neg_val = splits_data["negatives_val"]
neg_report = splits_data["negatives_report"]

def wilson_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0, 0.0
    z = 1.959963984540054
    p_hat = k / n
    denominator = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denominator
    margin = (z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denominator
    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)
    return p_hat, lower, upper

def format_wilson(k, n):
    p, l, u = wilson_interval(k, n)
    return f"{k:3d}/{n:3d} ({p:6.2%}) [{l:6.2%}, {u:6.2%}]"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CNNClassifier(num_classes=2, pretrained=False).to(device)
ckpt = torch.load("cnn/checkpoints/cnn_efficientnet_b0.pth", map_location=device, weights_only=False)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

# Shared preprocessing (PIL)
tf_pil = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Old Albumentations transform (cv2)
tf_alb = A.Compose([
    A.Resize(224, 224),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])

face_cascade = None
try:
    if hasattr(cv2, "CascadeClassifier"):
        face_cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
except Exception:
    pass

def eval_old_pipeline(fpath):
    bgr = cv2.imread(fpath, cv2.IMREAD_COLOR)
    if bgr is None:
        return {"decision": "REJECT", "score": 0.0}
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]

    # Heuristics
    # 1. Face
    rej_face = False
    try:
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.10, minNeighbors=4,
            minSize=(max(20, int(min(h, w) * 0.05)), max(20, int(min(h, w) * 0.05)))
        )
        if len(faces) > 0: rej_face = True
    except Exception:
        pass

    # 2. Poster
    small = cv2.resize(rgb, (64, 64), interpolation=cv2.INTER_AREA)
    quant = (small // 16) * 16
    reshaped = quant.reshape(-1, 3)
    _, counts = np.unique(reshaped, axis=0, return_counts=True)
    rej_poster = (float(counts.max()) / float(len(reshaped))) > 0.38

    # 3. Hue
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    botanical_mask = (hue >= 6) & (hue <= 90) & (sat >= 22) & (val >= 20) & (val <= 245)
    botanical_ratio = float(np.count_nonzero(botanical_mask)) / max(float(h * w), 1.0)
    rej_hue = botanical_ratio < 0.14

    # 4. Sky
    sky_mask = (hue >= 92) & (hue <= 135) & (sat >= 35) & (val >= 110)
    sky_ratio = float(np.count_nonzero(sky_mask)) / max(float(h * w), 1.0)
    rej_sky = (sky_ratio > 0.40) and (botanical_ratio < 0.52)

    # Multi-crop
    t_full = tf_alb(image=rgb)["image"]
    ch, cw = int(h * 0.75), int(w * 0.75)
    cy, cx = (h - ch) // 2, (w - cw) // 2
    center_crop = rgb[cy : cy + ch, cx : cx + cw] if (ch >= 32 and cw >= 32) else rgb
    t_center = tf_alb(image=center_crop)["image"]

    batch = torch.stack([t_full, t_center], dim=0).to(device)
    with torch.no_grad():
        probs = torch.softmax(model(batch), dim=1)
        full_p = probs[0, 0].item()
        center_p = probs[1, 0].item()
        mean_p = probs.mean(dim=0)[0].item()

    is_areca = (full_p >= 0.85) or (center_p >= 0.85) or (mean_p >= 0.80)
    if rej_face or rej_poster or rej_hue or rej_sky or not is_areca:
        decision = "REJECT"
    else:
        decision = "ACCEPT"
    return {"decision": decision, "score": mean_p}

ACCEPT_THRESH = 0.7404
REJECT_THRESH = 0.5180

def eval_new_pipeline(fpath):
    try:
        with Image.open(fpath) as img:
            rgb_pil = img.convert("RGB")
            w, h = rgb_pil.size
            t_full = tf_pil(rgb_pil)
            cw, ch = int(w * 0.75), int(h * 0.75)
            cx, cy = (w - cw) // 2, (h - ch) // 2
            center_pil = rgb_pil.crop((cx, cy, cx + cw, cy + ch)) if (cw >= 32 and ch >= 32) else rgb_pil
            t_center = tf_pil(center_pil)
    except Exception:
        return {"decision": "REJECT", "score": 0.0}

    batch = torch.stack([t_full, t_center], dim=0).to(device)
    with torch.no_grad():
        probs = torch.softmax(model(batch), dim=1)
        full_p = probs[0, 0].item()
        center_p = probs[1, 0].item()
        score = (full_p + center_p) / 2.0

    if score >= ACCEPT_THRESH:
        decision = "ACCEPT"
    elif score < REJECT_THRESH:
        decision = "REJECT"
    else:
        decision = "UNCERTAIN"

    return {"decision": decision, "score": score}

print("Evaluating sets under Old vs New Gate...")
sets = {
    "Areca All (349)": areca_all,
    "Areca Val (69)": areca_val,
    "Negatives Val (140)": neg_val,
    "Negatives REPORT (585)": neg_report,
}

eval_old = {k: [eval_old_pipeline(f) for f in v] for k, v in sets.items()}
eval_new = {k: [eval_new_pipeline(f) for f in v] for k, v in sets.items()}

# Metrics comparison
def get_stats_old(res_list, positive=True):
    n = len(res_list)
    if positive:
        # recall
        k = sum(1 for r in res_list if r["decision"] == "ACCEPT")
        return k, n, format_wilson(k, n)
    else:
        # false accept
        k = sum(1 for r in res_list if r["decision"] == "ACCEPT")
        return k, n, format_wilson(k, n)

def get_stats_new(res_list, positive=True):
    n = len(res_list)
    k_acc = sum(1 for r in res_list if r["decision"] == "ACCEPT")
    k_unc = sum(1 for r in res_list if r["decision"] == "UNCERTAIN")
    k_rej = sum(1 for r in res_list if r["decision"] == "REJECT")
    rate_str = format_wilson(k_acc, n)
    return k_acc, k_unc, k_rej, n, rate_str

print("\n" + "=" * 105)
print("2.5 OLD vs NEW GATE COMPARISON TABLE (95% WILSON INTERVALS)")
print("=" * 105)
col_fmt = "{:<25} | {:<32} | {:<42}"
print(col_fmt.format("Dataset Split", "OLD Gate (OR-Rule + Heuristics)", "NEW Gate (Single Score + Uncertain Band)"))
print("-" * 105)

# 1. Areca All
k_old, n_old, str_old = get_stats_old(eval_old["Areca All (349)"], positive=True)
k_acc, k_unc, k_rej, n_new, str_new = get_stats_new(eval_new["Areca All (349)"], positive=True)
print(col_fmt.format("Areca All (n=349)", f"Recall: {str_old}", f"Recall: {str_new} (Uncert: {k_unc}, Rej: {k_rej})"))

# 2. Areca Val
k_old, n_old, str_old = get_stats_old(eval_old["Areca Val (69)"], positive=True)
k_acc, k_unc, k_rej, n_new, str_new = get_stats_new(eval_new["Areca Val (69)"], positive=True)
print(col_fmt.format("Areca Val (n=69)", f"Recall: {str_old}", f"Recall: {str_new} (Uncert: {k_unc}, Rej: {k_rej})"))

# 3. Negatives Val
k_old, n_old, str_old = get_stats_old(eval_old["Negatives Val (140)"], positive=False)
k_acc, k_unc, k_rej, n_new, str_new = get_stats_new(eval_new["Negatives Val (140)"], positive=False)
print(col_fmt.format("Negatives Val (n=140)", f"FA Rate: {str_old}", f"FA Rate: {str_new} (Uncert: {k_unc}, Rej: {k_rej})"))

# 4. Negatives REPORT
k_old, n_old, str_old = get_stats_old(eval_old["Negatives REPORT (585)"], positive=False)
k_acc, k_unc, k_rej, n_new, str_new = get_stats_new(eval_new["Negatives REPORT (585)"], positive=False)
print(col_fmt.format("Negatives REPORT (n=585)", f"FA Rate: {str_old}", f"FA Rate: {str_new} (Uncert: {k_unc}, Rej: {k_rej})"))

# AUROC calculation on (Areca All + Negatives REPORT)
y_true = [1] * len(areca_all) + [0] * len(neg_report)
scores_old = [r["score"] for r in eval_old["Areca All (349)"]] + [r["score"] for r in eval_old["Negatives REPORT (585)"]]
scores_new = [r["score"] for r in eval_new["Areca All (349)"]] + [r["score"] for r in eval_new["Negatives REPORT (585)"]]

auroc_old = roc_auc_score(y_true, scores_old)
auroc_new = roc_auc_score(y_true, scores_new)

print("-" * 105)
print(col_fmt.format("AUROC (Areca All + REPORT)", f"{auroc_old:.4f} ({auroc_old:.2%})", f"{auroc_new:.4f} ({auroc_new:.2%})"))

out_results = {
    "thresholds": {"accept": ACCEPT_THRESH, "reject": REJECT_THRESH},
    "areca_all": {
        "old": {"accepted": k_old, "total": 349, "str": str_old},
        "new": {"accepted": k_acc, "uncertain": k_unc, "rejected": k_rej, "total": 349, "str": str_new}
    },
    "auroc": {
        "old": auroc_old,
        "new": auroc_new
    }
}

json_path = os.path.join(RESULTS_DIR, "gate_old_vs_new_comparison.json")
with open(json_path, "w") as f:
    json.dump(out_results, f, indent=2)
print(f"\nSaved comparison results to {json_path}")
