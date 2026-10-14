"""
backend/tests/verify_clean_vit_results.py — Compare baseline ViT vs clean ViT on the user's Fruit Rot photo and test images.
"""

import os
import sys
import torch
import numpy as np
from PIL import Image
from torchvision import transforms

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

import config
from vit.model import ViTClassifier

CLASSES = config.DISEASE_CLASSES

# 1. Load Baseline Model
OLD_CKPT = os.path.join(REPO_ROOT, "backend", "vit", "checkpoints", "vit_b16.pth")
old_model = ViTClassifier(num_classes=11, pretrained=False)
old_state = torch.load(OLD_CKPT, map_location="cpu")
if "model_state_dict" in old_state:
    old_state = old_state["model_state_dict"]
old_model.load_state_dict(old_state)
old_model.eval()

# 2. Load New Clean Model
NEW_CKPT = os.path.join(REPO_ROOT, "backend", "vit", "checkpoints", "vit_b16_clean_v1.pth")
new_model = ViTClassifier(num_classes=11, pretrained=False)
new_model.load_state_dict(torch.load(NEW_CKPT, map_location="cpu"))
new_model.eval()

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict(model, pil_img):
    t = transform(pil_img).unsqueeze(0)
    with torch.no_grad():
        logits = model(t)
        probs = torch.softmax(logits, dim=1)[0]
    top_prob, top_idx = torch.topk(probs, 3)
    return [(CLASSES[idx.item()], round(prob.item() * 100, 1)) for idx, prob in zip(top_idx, top_prob)]

# Test Images
test_cases = [
    ("USER UPLOADED FRUIT ROT (job-bfd163d5cc18.jpg)", os.path.join(REPO_ROOT, "backend", "data", "uploads", "job-bfd163d5cc18.jpg")),
    ("Fruit Rot 1 (fruit_rot_1.jpg)", "D:/dataset/fruit_rot/fruit_rot_1.jpg"),
    ("Fruit Rot 4 (fruit_rot_4.jpg)", "D:/dataset/fruit_rot/fruit_rot_4.jpg"),
    ("Fruit Rot 10 (fruit_rot_10.jpg)", "D:/dataset/fruit_rot/fruit_rot_10.jpg"),
    ("Fruit Rot 24 (fruit_rot_24.jpg)", "D:/dataset/fruit_rot/fruit_rot_24.jpg"),
    ("Nut Cracking 14 (nut_cracking_14.jpg)", "D:/dataset/nut_cracking/nut_cracking_14.jpg"),
    ("Nut Cracking 21 (nut_cracking_21.jpg)", "D:/dataset/nut_cracking/nut_cracking_21.jpg"),
]

print("="*85)
print(f"{'Image Description':<40} | {'Old Baseline ViT':<20} | {'NEW Clean ViT':<20}")
print("="*85)

for desc, p in test_cases:
    if os.path.exists(p):
        im = Image.open(p).convert("RGB")
        old_top3 = predict(old_model, im)
        new_top3 = predict(new_model, im)
        
        old_str = f"{old_top3[0][0]} ({old_top3[0][1]}%)"
        new_str = f"{new_top3[0][0]} ({new_top3[0][1]}%)"
        print(f"{desc:<40} | {old_str:<20} | {new_str:<20}")
        print(f"   Old top-3: {old_top3}")
        print(f"   New top-3: {new_top3}\n")
print("="*85)
