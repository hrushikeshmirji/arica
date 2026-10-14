import os
import cv2
import torch
from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor

cnn = CNNPredictor()
vit = ViTPredictor('vit/checkpoints/vit_b16_clean_v1.pth')

recent_jobs = [
    'job-02a8ae76aafe.jpg', 'job-a567509ee657.jpg', 'job-8d3fdd69b77e.jpg', 
    'job-9be4f34394e8.jpg', 'job-1d8a485000dc.jpg', 'job-66e59a96c499.jpg', 
    'job-a55555f036a3.jpg', 'job-874abbbe7f09.jpg'
]

print("=== DIAGNOSTIC REPORT ON RECENT USER UPLOADS ===")
for j in recent_jobs:
    p = os.path.join('data/uploads', j)
    if not os.path.exists(p):
        print(f"{j}: File not found")
        continue
    img_bgr = cv2.imread(p)
    if img_bgr is None:
        print(f"{j}: Failed to load image")
        continue
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    cnn_lbl, cnn_conf = cnn.predict(img_rgb)
    vit_lbl, vit_conf, _ = vit.predict(img_rgb)
    vit_tta = vit.predict_tta_ensemble(img_rgb)
    
    print(f"\nImage {j} (shape {img_rgb.shape}):")
    print(f"   CNN Gate: {cnn_lbl} (conf: {cnn_conf:.3f})")
    print(f"   ViT Single: {vit_lbl} (conf: {vit_conf:.3f})")
    print(f"   ViT TTA: {vit_tta.get('label')} (conf: {vit_tta.get('confidence'):.3f}, isOOD: {vit_tta.get('isOOD')}, sim: {vit_tta.get('maxProtoSim'):.3f})")
    print(f"   Diff: {vit_tta.get('differential')[:3]}")
