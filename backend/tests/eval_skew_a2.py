import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from PIL import Image
import torch
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2
from torchvision import transforms
from cnn.model import CNNClassifier

def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

RAW_DIR = r'D:\dataset_raw\dataset_raw'
NON_ARECA_CAT = 'non_areca'

non_areca_raw = [f for f in glob.glob(os.path.join(RAW_DIR, NON_ARECA_CAT, '*')) if os.path.isfile(f)]
seen_hashes = {}
non_areca_dedup = []
for f in non_areca_raw:
    try:
        with Image.open(f) as img:
            h = dhash(img)
            if h not in seen_hashes:
                seen_hashes[h] = f
                non_areca_dedup.append(f)
    except Exception:
        pass

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = CNNClassifier(num_classes=2, pretrained=False).to(device)
ckpt = torch.load('cnn/checkpoints/cnn_efficientnet_b0.pth', map_location=device, weights_only=False)
model.load_state_dict(ckpt['model_state_dict'])
model.eval()

# (i) PIL/torchvision Resize
tf_pil = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# (ii) cv2/Albumentations Resize
tf_alb = A.Compose([
    A.Resize(224, 224),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])

def eval_image(fpath):
    with Image.open(fpath) as img:
        t_pil = tf_pil(img.convert('RGB')).unsqueeze(0).to(device)
    bgr = cv2.imread(fpath, cv2.IMREAD_COLOR)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    t_alb = tf_alb(image=rgb)['image'].unsqueeze(0).to(device)
    with torch.no_grad():
        p_pil = torch.softmax(model(t_pil), dim=1)[0, 0].item()
        p_alb = torch.softmax(model(t_alb), dim=1)[0, 0].item()
    return p_pil, p_alb

# Find the 18 false accepts under PIL
false_accepts = []
for f in non_areca_dedup:
    try:
        p_pil, p_alb = eval_image(f)
        if p_pil >= 0.5:
            false_accepts.append((f, p_pil, p_alb))
    except Exception:
        pass

print(f"Total False Accepts found under PIL: {len(false_accepts)}")
print("\n=== THE 18 RAW-MODEL FALSE ACCEPTS ===")
header = f"{'Filename':<30} | {'P(areca) PIL (train)':<22} | {'P(areca) cv2 (infer)':<22} | {'cv2 Status':<12}"
print(header)
print("-" * len(header))
fa_basenames = set()
for f, p_pil, p_alb in false_accepts:
    bname = os.path.basename(f)
    fa_basenames.add(bname)
    status = 'False Accept' if p_alb >= 0.5 else 'Rejected'
    print(f"{bname:<30} | {p_pil:<22.4%} | {p_alb:<22.4%} | {status:<12}")

print("\n=== THE FOUR PROBE IMAGES ===")
probes = ['download_1333.jpg', 'download_1696.jpg', 'download_1423.jpg', 'download_580.jpeg']
header_probe = f"{'Filename':<30} | {'P(areca) PIL (train)':<22} | {'P(areca) cv2 (infer)':<22} | {'In 18 FAs?':<12}"
print(header_probe)
print("-" * len(header_probe))
for p in probes:
    match = [f for f in non_areca_raw if os.path.basename(f) == p]
    if match:
        p_pil, p_alb = eval_image(match[0])
        in_fa = 'YES' if p in fa_basenames else 'NO'
        print(f"{p:<30} | {p_pil:<22.4%} | {p_alb:<22.4%} | {in_fa:<12}")
    else:
        print(f"{p:<30} | NOT FOUND")
