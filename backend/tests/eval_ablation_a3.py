import os, sys, glob, random
import math
import numpy as np
from PIL import Image
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2
from torchvision import transforms
import torch

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

from cnn.model import CNNClassifier

def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

def wilson_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0, 0.0
    z = 1.959963984540054  # 95%
    p_hat = k / n
    denominator = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denominator
    margin = (z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denominator
    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)
    return p_hat, lower, upper

def format_wilson(k, n):
    p, l, u = wilson_interval(k, n)
    return f"{k:4d}/{n:4d} ({p:6.2%}) [{l:6.2%}, {u:6.2%}]"

RAW_DIR = r"D:\dataset_raw\dataset_raw"
ARECA_CATS = [
    "areca_diseased_fungal_anthracnose",
    "areca_diseased_fungal_fruit_rot",
    "areca_diseased_fungal_sooty_mold",
    "areca_diseased_physiological_nut_cracking",
    "areca_healthy"
]
NON_ARECA_CAT = "non_areca"

# Recreate exact split from fast_train_gate.py
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

areca_files = []
for cat in ARECA_CATS:
    areca_files.extend(glob.glob(os.path.join(RAW_DIR, cat, "*")))

non_areca_files = glob.glob(os.path.join(RAW_DIR, NON_ARECA_CAT, "*"))

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

# Unselected pool: non_areca_files[700:], deduped
unselected_raw = non_areca_files[700:]

# Build deduped sets using dHash
# We track hashes of train/val negatives to avoid cross-leakage into unselected pool
seen_hashes = set()
for f in selected_non_areca:
    try:
        with Image.open(f) as img:
            seen_hashes.add(dhash(img))
    except Exception:
        pass

non_never_used = []
for f in unselected_raw:
    try:
        with Image.open(f) as img:
            h = dhash(img)
            if h not in seen_hashes:
                seen_hashes.add(h)
                non_never_used.append(f)
    except Exception:
        pass

print(f"Group counts:")
print(f"  Areca seen-in-training: {len(areca_train)}")
print(f"  Areca val:              {len(areca_val)}")
print(f"  Negatives seen:         {len(non_train)}")
print(f"  Negatives val:          {len(non_val)}")
print(f"  Negatives never-used:   {len(non_never_used)}")

# Model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = CNNClassifier(num_classes=2, pretrained=False).to(device)
ckpt = torch.load('cnn/checkpoints/cnn_efficientnet_b0.pth', map_location=device, weights_only=False)
model.load_state_dict(ckpt['model_state_dict'])
model.eval()

# Transforms
tf_pil = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

tf_alb = A.Compose([
    A.Resize(224, 224),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])

def evaluate_image(fpath):
    # 1. PIL raw
    try:
        with Image.open(fpath) as img:
            t_pil = tf_pil(img.convert('RGB')).unsqueeze(0).to(device)
        with torch.no_grad():
            p_areca_pil = torch.softmax(model(t_pil), dim=1)[0, 0].item()
    except Exception:
        p_areca_pil = 0.0

    # 2. cv2 and heuristics
    bgr = cv2.imread(fpath, cv2.IMREAD_COLOR)
    if bgr is None:
        return {
            'pil_acc': False,
            'cv2_acc': False,
            'mc_acc': False,
            'prod_acc': False,
            'heur_face': False,
            'heur_poster': False,
            'heur_hue': False,
            'heur_sky': False,
        }
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]

    # cv2 raw
    t_alb = tf_alb(image=rgb)['image'].unsqueeze(0).to(device)
    with torch.no_grad():
        p_areca_cv2 = torch.softmax(model(t_alb), dim=1)[0, 0].item()

    # multi-crop OR rule
    ch, cw = int(h * 0.75), int(w * 0.75)
    cy, cx = (h - ch) // 2, (w - cw) // 2
    center_crop = rgb[cy : cy + ch, cx : cx + cw] if (ch >= 32 and cw >= 32) else rgb
    t_center = tf_alb(image=center_crop)['image'].unsqueeze(0).to(device)

    batch = torch.stack([t_alb.squeeze(0), t_center.squeeze(0)], dim=0)
    with torch.no_grad():
        probs_batch = torch.softmax(model(batch), dim=1)
        full_prob = float(probs_batch[0, 0].item())
        center_prob = float(probs_batch[1, 0].item())
        mean_prob = float(probs_batch.mean(dim=0)[0].item())
    
    mc_areca = (full_prob >= 0.85) or (center_prob >= 0.85) or (mean_prob >= 0.80)

    # Heuristic 1: Face (exactly as in cnn/predict.py)
    rej_face = False
    try:
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        face_cascade = cv2.CascadeClassifier(
            os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        )
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.10, minNeighbors=4,
            minSize=(max(20, int(min(h, w) * 0.05)), max(20, int(min(h, w) * 0.05)))
        )
        if len(faces) > 0:
            rej_face = True
    except Exception:
        pass

    # Heuristic 2: Poster
    small_rgb = cv2.resize(rgb, (64, 64), interpolation=cv2.INTER_AREA)
    quant = (small_rgb // 16) * 16
    reshaped = quant.reshape(-1, 3)
    _, counts = np.unique(reshaped, axis=0, return_counts=True)
    rej_poster = (float(counts.max()) / float(len(reshaped))) > 0.38

    # Heuristic 3: Botanical hue/chroma
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    botanical_mask = (hue >= 6) & (hue <= 90) & (sat >= 22) & (val >= 20) & (val <= 245)
    botanical_ratio = float(np.count_nonzero(botanical_mask)) / max(float(h * w), 1.0)
    rej_hue = botanical_ratio < 0.14

    # Heuristic 4: Sky
    sky_mask = (hue >= 92) & (hue <= 135) & (sat >= 35) & (val >= 110)
    sky_ratio = float(np.count_nonzero(sky_mask)) / max(float(h * w), 1.0)
    rej_sky = (sky_ratio > 0.40) and (botanical_ratio < 0.52)

    # Full production pipeline
    any_heuristic_reject = rej_face or rej_poster or rej_hue or rej_sky
    prod_areca = (not any_heuristic_reject) and mc_areca

    return {
        'pil_acc': p_areca_pil >= 0.50,
        'cv2_acc': p_areca_cv2 >= 0.50,
        'mc_acc': mc_areca,
        'prod_acc': prod_areca,
        'heur_face': rej_face,
        'heur_poster': rej_poster,
        'heur_hue': rej_hue,
        'heur_sky': rej_sky,
    }

groups = {
    'Areca seen-in-training (280)': areca_train,
    'Areca val (69)': areca_val,
    'Negatives seen (560)': non_train,
    'Negatives val (140)': non_val,
    'Negatives never-used (unselected)': non_never_used,
}

results = {}
for gname, flist in groups.items():
    print(f"Evaluating {gname}...")
    g_res = [evaluate_image(f) for f in flist]
    results[gname] = g_res

print("\n" + "=" * 90)
print("A3. CLEAN ABLATION TABLE: ACCEPTED / TOTAL (95% WILSON SCORE INTERVAL)")
print("=" * 90)
col_fmt = "{:<35} | {:<25} | {:<25} | {:<25} | {:<25}"
print(col_fmt.format("Group", "raw+PIL", "raw+OpenCV", "raw+OpenCV+Multi-Crop", "Full Production"))
print("-" * 140)

for gname, g_res in results.items():
    n = len(g_res)
    k_pil = sum(1 for r in g_res if r['pil_acc'])
    k_cv2 = sum(1 for r in g_res if r['cv2_acc'])
    k_mc  = sum(1 for r in g_res if r['mc_acc'])
    k_prd = sum(1 for r in g_res if r['prod_acc'])

    s_pil = format_wilson(k_pil, n)
    s_cv2 = format_wilson(k_cv2, n)
    s_mc  = format_wilson(k_mc, n)
    s_prd = format_wilson(k_prd, n)
    print(col_fmt.format(gname, s_pil, s_cv2, s_mc, s_prd))

print("\n" + "=" * 90)
print("PER-HEURISTIC BREAKDOWN: REJECTIONS ON ARECA VAL vs UNIQUE CATCHES ON NEGATIVES")
print("=" * 90)
# Areca val wrongful rejection:
areca_val_res = results['Areca val (69)']
n_aval = len(areca_val_res)

# All negatives pool:
all_neg_res = results['Negatives seen (560)'] + results['Negatives val (140)'] + results['Negatives never-used (unselected)']

h_names = [
    ('Face (Haar Cascade)', 'heur_face'),
    ('Poster (Quantization)', 'heur_poster'),
    ('Hue (Botanical Chroma)', 'heur_hue'),
    ('Sky (Blue Chroma)', 'heur_sky'),
]

print(f"{'Heuristic':<25} | {'Areca Val Wrongly Rejected':<28} | {'Negatives Uniquely Caught (vs Multi-crop)':<45}")
print("-" * 105)

for h_label, h_key in h_names:
    # Areca val wrongly rejected by this heuristic (would have been accepted by MC or overall)
    # Total areca val flagged by this heuristic:
    val_flagged = sum(1 for r in areca_val_res if r[h_key])
    # Val flagged that would have been accepted by MC:
    val_wrongly_rejected = sum(1 for r in areca_val_res if r[h_key] and r['mc_acc'])

    # Negatives uniquely caught: negative where MC accepted it, but this heuristic rejected it,
    # and NO other heuristic rejected it
    other_keys = [k for _, k in h_names if k != h_key]
    unique_catches = sum(1 for r in all_neg_res if r['mc_acc'] and r[h_key] and not any(r[ok] for ok in other_keys))
    total_catches_of_mc = sum(1 for r in all_neg_res if r['mc_acc'] and r[h_key])

    print(f"{h_label:<25} | {val_wrongly_rejected:2d}/{n_aval:2d} ({val_wrongly_rejected/n_aval:5.1%}) (total flagged: {val_flagged}) | {unique_catches:3d} unique catches ({total_catches_of_mc:3d} total catches when MC=accept)")
