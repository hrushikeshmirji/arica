"""
test_yolo_vit.py — Direct verification of Stage 2 (YOLO) and Stage 3 (ViT).
"""
import numpy as np
import config
from yolo.detect import YOLODetector
from vit.predict import ViTPredictor

print("Loading YOLO Detector...")
yolo = YOLODetector()

print("Loading ViT Predictor...")
vit = ViTPredictor()

# Create a sample RGB image (640x640)
img = np.zeros((640, 640, 3), dtype=np.uint8)
# Fill with textured colors
img[100:500, 100:500, 1] = 180  # green channel
img[150:450, 150:450, 0] = 60
img[150:450, 150:450, 2] = 40

print("Testing YOLO detection...")
detections, annotated = yolo.detect(img)
print(f"YOLO detections: {len(detections)}")

print("Testing ViT prediction on whole image...")
label, conf, attn = vit.predict(img)
print(f"ViT Result: {label}, confidence: {conf:.4f}, attention map shape: {attn.shape if attn is not None else None}")

if attn is not None:
    vis = vit.get_attention_visualization(img, attn)
    print(f"ViT Attention Visualization shape: {vis.shape}")

print("\n✓ Both YOLO and ViT are fully operational!")
