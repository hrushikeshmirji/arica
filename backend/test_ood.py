import os
import cv2
from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor

cnn = CNNPredictor()
vit = ViTPredictor('vit/checkpoints/vit_b16_clean_v1.pth')

ood_dir = 'tests/ood_probe'
if os.path.exists(ood_dir):
    print("=== OOD PROBE TEST ===")
    for f in os.listdir(ood_dir):
        p = os.path.join(ood_dir, f)
        img_bgr = cv2.imread(p)
        if img_bgr is None: continue
        img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        cnn_lbl, cnn_conf = cnn.predict(img)
        vit_tta = vit.predict_tta_ensemble(img)
        lbl = vit_tta.get("label")
        conf = vit_tta.get("confidence")
        is_ood = vit_tta.get("isOOD")
        sim = vit_tta.get("maxProtoSim")
        print(f"{f}: CNN={cnn_lbl} ({cnn_conf:.2f}) | ViT={lbl} ({conf:.2f}, isOOD={is_ood}, sim={sim:.3f})")
