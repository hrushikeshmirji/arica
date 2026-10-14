import os
import sys
import time
import json
import torch
import torch.nn as nn
import timm

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

from vit.model import ViTClassifier
from ultralytics import YOLO

os.makedirs(os.path.join(REPO_ROOT, "results", "train"), exist_ok=True)

print("=== STEP 0.4 BENCHMARK: ViT-B/16 & YOLOv8n Single-Batch Latency ===")

# -------------------------------------------------------------
# 1. ViT-B/16 Benchmark (batch=8, 224x224, CPU, last 2 blocks unfreezed)
# -------------------------------------------------------------
print("\n[1/2] Benchmarking ViT-B/16 forward + backward on CPU (batch=8, 224x224)...")
vit_model = ViTClassifier(num_classes=11, pretrained=False, freeze_backbone=True)
vit_model.unfreeze_last_n_blocks(2)
vit_model.train()

optimizer = torch.optim.AdamW(
    [p for p in vit_model.parameters() if p.requires_grad],
    lr=1e-4
)
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

dummy_vit_input = torch.randn(8, 3, 224, 224)
dummy_vit_target = torch.randint(0, 11, (8,))

# Warmup
optimizer.zero_grad()
out = vit_model(dummy_vit_input)
loss = criterion(out, dummy_vit_target)
loss.backward()
optimizer.step()

# Timed runs
vit_times = []
for i in range(3):
    t0 = time.perf_counter()
    optimizer.zero_grad()
    out = vit_model(dummy_vit_input)
    loss = criterion(out, dummy_vit_target)
    loss.backward()
    optimizer.step()
    t1 = time.perf_counter()
    vit_times.append(t1 - t0)

vit_sec_per_batch = sum(vit_times) / len(vit_times)
print(f"ViT-B/16 single-batch forward+backward: {vit_sec_per_batch:.3f} s (runs: {[round(t, 3) for t in vit_times]})")

# -------------------------------------------------------------
# 2. YOLOv8n Benchmark (batch=8, 640x640, CPU)
# -------------------------------------------------------------
print("\n[2/2] Benchmarking YOLOv8n training batch on CPU (batch=8, 640x640)...")
yolo = YOLO("yolov8n.pt")
yolo_model = yolo.model
yolo_model.train()
for p in yolo_model.parameters():
    p.requires_grad = True

yolo_opt = torch.optim.SGD(yolo_model.parameters(), lr=0.01)

dummy_yolo_input = torch.randn(8, 3, 640, 640)

# Warmup
yolo_opt.zero_grad()
out_yolo = yolo_model(dummy_yolo_input)
if isinstance(out_yolo, dict):
    loss_yolo = out_yolo['scores'].sum() if 'scores' in out_yolo else list(out_yolo.values())[0].sum()
elif isinstance(out_yolo, (list, tuple)):
    loss_yolo = sum(o.sum() for o in out_yolo if isinstance(o, torch.Tensor))
else:
    loss_yolo = out_yolo.sum()

loss_yolo.backward()
yolo_opt.step()

# Timed runs
yolo_times = []
for i in range(3):
    t0 = time.perf_counter()
    yolo_opt.zero_grad()
    out_yolo = yolo_model(dummy_yolo_input)
    if isinstance(out_yolo, dict):
        loss_yolo = out_yolo['scores'].sum() if 'scores' in out_yolo else list(out_yolo.values())[0].sum()
    elif isinstance(out_yolo, (list, tuple)):
        loss_yolo = sum(o.sum() for o in out_yolo if isinstance(o, torch.Tensor))
    else:
        loss_yolo = out_yolo.sum()
    loss_yolo.backward()
    yolo_opt.step()
    t1 = time.perf_counter()
    yolo_times.append(t1 - t0)

yolo_sec_per_batch = sum(yolo_times) / len(yolo_times)
print(f"YOLOv8n single-batch forward+backward: {yolo_sec_per_batch:.3f} s (runs: {[round(t, 3) for t in yolo_times]})")

# -------------------------------------------------------------
# 3. Training Plan Extrapolation
# -------------------------------------------------------------
# ViT:
# Train dataset size: ~480 images -> ~60 batches/epoch
# Proposed epochs: up to 20 epochs per variant (with early stopping patience 5)
# 2 variants (A and B): 2 * 20 = 40 epochs total = ~2400 batches
# Plus val inference (~45 images / 8 = 6 batches / epoch) ~ 0.3 * train time
vit_images_per_epoch = 480
vit_batches_per_epoch = 60
vit_max_epochs = 20
vit_runs = 2  # Variant A and Variant B
vit_total_train_batches = vit_batches_per_epoch * vit_max_epochs * vit_runs
vit_est_train_sec = vit_total_train_batches * vit_sec_per_batch
vit_est_val_sec = vit_est_train_sec * 0.15  # eval is forward-only and ~1/10th size
vit_total_sec = vit_est_train_sec + vit_est_val_sec
vit_total_hours = vit_total_sec / 3600.0

# YOLO:
# Proposed in prompt: 100 epochs, patience 20, batch 8
# Train images in dataset: 157 images -> ceil(157 / 8) = 20 batches / epoch
# 2 variants (4-class and 1-class lesion)
# Full 100 epochs * 20 batches = 2000 batches per variant = 4000 batches total
# (or with early stopping patience 20, say 30-50 epochs)
yolo_train_images = 157
yolo_batches_per_epoch = 20
yolo_planned_epochs = 100
yolo_variants = 2  # 4-class and lesion-only
yolo_total_train_batches = yolo_batches_per_epoch * yolo_planned_epochs * yolo_variants
yolo_est_train_sec = yolo_total_train_batches * yolo_sec_per_batch
yolo_est_val_sec = (40 / 8) * yolo_planned_epochs * yolo_variants * (yolo_sec_per_batch * 0.4)
yolo_total_sec = yolo_est_train_sec + yolo_est_val_sec
yolo_total_hours = yolo_total_sec / 3600.0

exceeds_4h = (vit_total_hours > 4.0) or (yolo_total_hours > 4.0)

results = {
    "vit_benchmark": {
        "batch_size": 8,
        "resolution": 224,
        "seconds_per_batch": round(vit_sec_per_batch, 4),
        "individual_runs_s": [round(t, 4) for t in vit_times],
        "batches_per_epoch": vit_batches_per_epoch,
        "max_epochs_per_variant": vit_max_epochs,
        "num_variants": vit_runs,
        "total_train_batches": vit_total_train_batches,
        "estimated_total_hours": round(vit_total_hours, 2),
        "exceeds_4h": vit_total_hours > 4.0
    },
    "yolo_benchmark": {
        "batch_size": 8,
        "resolution": 640,
        "seconds_per_batch": round(yolo_sec_per_batch, 4),
        "individual_runs_s": [round(t, 4) for t in yolo_times],
        "batches_per_epoch": yolo_batches_per_epoch,
        "planned_epochs_per_variant": yolo_planned_epochs,
        "num_variants": yolo_variants,
        "total_train_batches": yolo_total_train_batches,
        "estimated_total_hours": round(yolo_total_hours, 2),
        "exceeds_4h": yolo_total_hours > 4.0
    },
    "exceeds_4h_overall": exceeds_4h
}

out_file = os.path.join(REPO_ROOT, "results", "train", "benchmark_latency.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\n=== WALL-CLOCK TIME ESTIMATE SUMMARY ===")
print(f"ViT-B/16 Estimated Total (2 variants x 20 ep): {vit_total_hours:.2f} hours (Exceeds 4h: {vit_total_hours > 4.0})")
print(f"YOLOv8n Estimated Total (2 variants x 100 ep): {yolo_total_hours:.2f} hours (Exceeds 4h: {yolo_total_hours > 4.0})")
print(f"Overall exceeds 4-hour threshold: {exceeds_4h}")
print(f"Saved benchmark data to: {out_file}")
