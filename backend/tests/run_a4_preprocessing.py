"""
backend/tests/run_a4_preprocessing.py — Part A4 Preprocessing impact analysis across formats and test images.
"""

import os
import sys
import json
import io
from PIL import Image, ImageOps
import numpy as np
import torch
import torchvision.transforms as T

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

import config
from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor

RESULTS_DIR = os.path.join(REPO_ROOT, "backend", "tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
TEST_IMAGES_DIR = os.path.join(REPO_ROOT, "backend", "tests", "test_images")

# Load 6 test images
test_files = [
    ("1_dataset_fruit_rot", os.path.join(TEST_IMAGES_DIR, "1_dataset_fruit_rot.jpg")),
    ("2_dataset_healthy", os.path.join(TEST_IMAGES_DIR, "2_dataset_healthy.jpg")),
    ("3_alpha_png", os.path.join(TEST_IMAGES_DIR, "3_alpha.png")),
    ("4_format_webp", os.path.join(TEST_IMAGES_DIR, "4_format.webp")),
    ("5_exif_rotated", os.path.join(TEST_IMAGES_DIR, "5_exif_rotated.jpg")),
    ("6_non_areca", os.path.join(TEST_IMAGES_DIR, "6_non_areca.jpg")),
]

all_inputs = {}
for name, path in test_files:
    with open(path, "rb") as f:
        all_inputs[name] = f.read()

# Base source image for 8 synthesized variations
SRC_IMG = os.path.join(TEST_IMAGES_DIR, "1_dataset_fruit_rot.jpg")
base_im = Image.open(SRC_IMG).convert("RGB")
w, h = base_im.size

# 1. RGBA (with 50% transparent background in corners)
rgba = base_im.convert("RGBA")
for x in range(min(80, w)):
    for y in range(min(80, h)):
        rgba.putpixel((x, y), (0, 0, 0, 0)) # fully transparent corner
buf_rgba = io.BytesIO()
rgba.save(buf_rgba, "PNG")
all_inputs["synth_1_rgba"] = buf_rgba.getvalue()

# 2. Palette ('P' with transparency)
buf_pal = io.BytesIO()
p_im = base_im.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
p_im.save(buf_pal, "PNG")
all_inputs["synth_2_palette"] = buf_pal.getvalue()

# 3. CMYK
buf_cmyk = io.BytesIO()
cmyk = base_im.convert("CMYK")
cmyk.save(buf_cmyk, "JPEG")
all_inputs["synth_3_cmyk"] = buf_cmyk.getvalue()

# 4. Grayscale ('L')
buf_gray = io.BytesIO()
gray = base_im.convert("L")
gray.save(buf_gray, "JPEG")
all_inputs["synth_4_grayscale"] = buf_gray.getvalue()

# 5. EXIF-rotated (Orientation = 6: 90 CW)
buf_exif = io.BytesIO()
exif = base_im.getexif()
exif[0x0112] = 6
base_im.save(buf_exif, "JPEG", exif=exif)
all_inputs["synth_5_exif_rotated"] = buf_exif.getvalue()

# 6. WebP
buf_webp = io.BytesIO()
base_im.save(buf_webp, "WEBP", quality=90)
all_inputs["synth_6_webp"] = buf_webp.getvalue()

# 7. Huge (3000 x 3000)
buf_huge = io.BytesIO()
huge = base_im.resize((3000, 3000), Image.Resampling.BILINEAR)
huge.save(buf_huge, "JPEG", quality=90)
all_inputs["synth_7_huge_3000px"] = buf_huge.getvalue()

# 8. Tiny (32 x 32)
buf_tiny = io.BytesIO()
tiny = base_im.resize((32, 32), Image.Resampling.BILINEAR)
tiny.save(buf_tiny, "JPEG")
all_inputs["synth_8_tiny_32px"] = buf_tiny.getvalue()

print(f"Total inputs to audit: {len(all_inputs)} (6 test + 8 synthesized)")

# Initialize models
print("Loading CNN and ViT models...")
cnn_pred = CNNPredictor()
vit_pred = ViTPredictor()

# ViT standard transformation pipeline
vit_transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def preprocess_current_pipeline(raw_bytes):
    """Current app.py behavior: Image.open + exif_transpose + convert('RGB')."""
    im = Image.open(io.BytesIO(raw_bytes))
    try:
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    im = im.convert("RGB")
    tensor = vit_transform(im)
    rgb_np = np.asarray(im)
    return im, tensor, rgb_np

def preprocess_alpha_flattened(raw_bytes):
    """Robust behavior: exif_transpose + white-canvas alpha flattening + convert('RGB')."""
    im = Image.open(io.BytesIO(raw_bytes))
    try:
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    if im.mode in ("RGBA", "LA") or ("transparency" in im.info):
        im_rgba = im.convert("RGBA")
        canvas = Image.new("RGBA", im_rgba.size, (255, 255, 255, 255))
        canvas.paste(im_rgba, (0, 0), im_rgba)
        im = canvas.convert("RGB")
    else:
        im = im.convert("RGB")
    tensor = vit_transform(im)
    rgb_np = np.asarray(im)
    return im, tensor, rgb_np

def preprocess_no_exif(raw_bytes):
    """Client route / canvas strip behavior where EXIF is ignored / stripped."""
    im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    tensor = vit_transform(im)
    rgb_np = np.asarray(im)
    return im, tensor, rgb_np

results = {}

print("\n" + "="*80)
print(f"{'Input Name':<22} | {'Max Diff':<9} | {'Cosine Sim':<10} | {'Current ViT':<20} | {'Flattened ViT':<20}")
print("="*80)

for name, raw_bytes in all_inputs.items():
    im_curr, t_curr, np_curr = preprocess_current_pipeline(raw_bytes)
    im_flat, t_flat, np_flat = preprocess_alpha_flattened(raw_bytes)
    im_noexif, t_noexif, np_noexif = preprocess_no_exif(raw_bytes)
    
    # Tensor comparisons: Current vs Flattened
    t1_flat = t_curr.flatten()
    t2_flat = t_flat.flatten()
    cos_sim = float(torch.nn.functional.cosine_similarity(t1_flat.unsqueeze(0), t2_flat.unsqueeze(0)).item())
    max_diff = float((t_curr - t_flat).abs().max().item())
    
    # Run predictions on Current
    gate_lbl_c, gate_conf_c = cnn_pred.predict(np_curr)
    tta_c = vit_pred.predict_tta_ensemble(np_curr)
    
    # Run predictions on Flattened
    gate_lbl_f, gate_conf_f = cnn_pred.predict(np_flat)
    tta_f = vit_pred.predict_tta_ensemble(np_flat)
    
    # Tensor comparison: Current vs No-EXIF
    t_noexif_flat = t_noexif.flatten()
    cos_sim_exif = float(torch.nn.functional.cosine_similarity(t1_flat.unsqueeze(0), t_noexif_flat.unsqueeze(0)).item())
    max_diff_exif = float((t_curr - t_noexif).abs().max().item())
    
    curr_vit_str = f"{tta_c['label']} ({tta_c['confidence']*100:.1f}%)"
    flat_vit_str = f"{tta_f['label']} ({tta_f['confidence']*100:.1f}%)"
    print(f"{name:<22} | {max_diff:<9.4f} | {cos_sim:<10.6f} | {curr_vit_str:<20} | {flat_vit_str:<20}")
    
    results[name] = {
        "bytes_len": len(raw_bytes),
        "tensor_vs_flattened": {
            "cosine_similarity": cos_sim,
            "max_abs_diff": max_diff,
        },
        "tensor_vs_no_exif": {
            "cosine_similarity": cos_sim_exif,
            "max_abs_diff": max_diff_exif,
        },
        "current_pipeline": {
            "gate_label": gate_lbl_c,
            "gate_conf": float(gate_conf_c),
            "vit_label": tta_c["label"],
            "vit_conf": float(tta_c["confidence"]),
            "vit_top3": [(d["disease"], float(d["probability"])) for d in tta_c["differential"][:3]],
        },
        "alpha_flattened_pipeline": {
            "gate_label": gate_lbl_f,
            "gate_conf": float(gate_conf_f),
            "vit_label": tta_f["label"],
            "vit_conf": float(tta_f["confidence"]),
            "vit_top3": [(d["disease"], float(d["probability"])) for d in tta_f["differential"][:3]],
        },
        "pipeline_predictions_match": (tta_c["label"] == tta_f["label"] and abs(tta_c["confidence"] - tta_f["confidence"]) < 0.001)
    }

out_path = os.path.join(RESULTS_DIR, "a4_preprocessing_comparison.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nSaved full comparison to:", out_path)
