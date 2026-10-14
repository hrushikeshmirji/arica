import sys, os, numpy as np
sys.path.insert(0, 'backend')
from PIL import Image
from vit.predict import ViTPredictor

vit = ViTPredictor()

# Test 5 genuine Nut Cracking images
print('--- GENUINE NUT CRACKING IMAGES ---')
nc_samples = ['nut_cracking_14.jpg', 'nut_cracking_20.jpg', 'nut_cracking_21.jpg', 'nut_cracking_39.jpg', 'nut_cracking_45.jpg']
for name in nc_samples:
    p = os.path.join('D:/dataset/nut_cracking', name)
    if os.path.exists(p):
        im = Image.open(p).convert('RGB')
        res = vit.predict_tta_ensemble(np.array(im))
        top_lbl = res['label']
        top_conf = res['confidence'] * 100
        print(f'{name}: Predicted={top_lbl} ({top_conf:.1f}%)')

# Test 5 Fruit Rot images
print('\n--- FRUIT ROT IMAGES ---')
fr_samples = ['fruit_rot_1.jpg', 'fruit_rot_4.jpg', 'fruit_rot_10.jpg', 'fruit_rot_23.jpg', 'fruit_rot_24.jpg']
for name in fr_samples:
    p = os.path.join('D:/dataset/fruit_rot', name)
    if os.path.exists(p):
        im = Image.open(p).convert('RGB')
        res = vit.predict_tta_ensemble(np.array(im))
        top_lbl = res['label']
        top_conf = res['confidence'] * 100
        print(f'{name}: Predicted={top_lbl} ({top_conf:.1f}%)')
