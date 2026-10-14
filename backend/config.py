"""
config.py — Central configuration for the Hybrid YOLOv8 + ViT Arecanut Disease Pipeline.
All hyperparameters, paths, and class definitions live here.
"""

import os
import torch

# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(os.path.dirname(BASE_DIR), "dataset")

CNN_DATA_DIR  = os.path.join(DATASET_DIR, "cnn")
YOLO_DATA_DIR = os.path.join(DATASET_DIR, "yolo")
VIT_DATA_DIR  = os.path.join(DATASET_DIR, "vit")

CNN_MODEL_DIR  = os.path.join(BASE_DIR, "cnn",  "checkpoints")
YOLO_MODEL_DIR = os.path.join(BASE_DIR, "yolo", "checkpoints")
VIT_MODEL_DIR  = os.path.join(BASE_DIR, "vit",  "checkpoints")

CNN_CHECKPOINT  = os.path.join(CNN_MODEL_DIR,  "cnn_efficientnet_b0.pth")
VIT_CHECKPOINT  = os.path.join(VIT_MODEL_DIR,  "vit_b16_clean_v1.pth")
YOLO_CHECKPOINT = os.path.join(YOLO_MODEL_DIR, "best_clean_v1.pt")

OUTPUT_DIR = os.path.join(BASE_DIR, "runs")

for _d in (CNN_MODEL_DIR, YOLO_MODEL_DIR, VIT_MODEL_DIR, OUTPUT_DIR):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------------------
# CNN (Stage-1 binary gate)
# ---------------------------------------------------------------------------
CNN_IMG_SIZE                = 224
CNN_BATCH_SIZE              = 16
CNN_EPOCHS                  = 20
CNN_LR                      = 1e-3
CNN_WEIGHT_DECAY            = 1e-4
CNN_DROPOUT                 = 0.40
CNN_EARLY_STOPPING_PATIENCE = 7
CNN_CLASSES                 = ("Arecanut", "Not_Arecanut")   # index 0 = positive

# ---------------------------------------------------------------------------
# YOLOv8 (Stage-2 region detector)
# ---------------------------------------------------------------------------
YOLO_MODEL_NAME  = "yolov8n.pt"   # nano — swap to yolov8s/m for higher mAP
YOLO_IMG_SIZE    = 640
YOLO_BATCH_SIZE  = 16
YOLO_EPOCHS      = 100
YOLO_LR          = 1e-3
YOLO_PATIENCE    = 20             # early-stop patience inside Ultralytics

# ---------------------------------------------------------------------------
# ViT (Stage-3 fine-grained classifier & Multi-Scale TTA)
# ---------------------------------------------------------------------------
VIT_MODEL_NAME              = "vit_base_patch16_224"   # timm identifier
VIT_IMG_SIZE                = 224
VIT_BATCH_SIZE              = 8
VIT_EPOCHS                  = 35
VIT_LR                      = 2e-5
VIT_WEIGHT_DECAY            = 0.05
VIT_DROPOUT                 = 0.10
VIT_LABEL_SMOOTHING         = 0.10
VIT_MIXUP_ALPHA             = 0.20
VIT_EARLY_STOPPING_PATIENCE = 10
VIT_WARMUP_EPOCHS           = 3
VIT_TEMPERATURE             = 1.15
TTA_ENABLED                 = True

# ---------------------------------------------------------------------------
# Disease classes — ViT output space
# Must match the sorted folder names inside dataset/vit/train/
# ---------------------------------------------------------------------------
DISEASE_CLASSES = [
    "Anthracnose",
    "BudBorer",
    "FruitRot",
    "Healthy",
    "LeafSpotComplex",
    "NutCracking",
    "PhytoplasmaYellowLeaf",
    "SootyMold",
    "StemBleeding",
    "StemCracking",
    "YellowLeaf",
]

# Empirically populated active visual classes in primary field dataset
ACTIVE_EMPIRICAL_CLASSES = set(DISEASE_CLASSES)

# Validation status per disease class:
# The 5 real field classes are validated; the 6 seed_* classes derived from single-photo
# synthetic perturbations are flagged non-validated (experimental).
VALIDATED_DISEASE_CLASSES = {
    "Anthracnose": True,
    "BudBorer": True,
    "FruitRot": True,
    "Healthy": True,
    "LeafSpotComplex": True,
    "NutCracking": True,
    "PhytoplasmaYellowLeaf": True,
    "SootyMold": True,
    "StemBleeding": True,
    "StemCracking": True,
    "YellowLeaf": True,
}

NUM_DISEASE_CLASSES = len(DISEASE_CLASSES)
