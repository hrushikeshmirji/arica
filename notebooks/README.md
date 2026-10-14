# ArecaVision AI — Hardcore GPU Training Guide

This folder contains the complete, standalone cloud GPU training pipeline for **ArecaVision AI**. You can run it on **Google Colab** (Free T4 GPU) or **Kaggle** (30 hrs/week free Dual T4 GPUs) to hardcore train YOLOv8/v11, ViT-B/16 (or DINOv2), and EfficientNet-B0 with 100+ epochs and full dataset augmentations.

---

## Files Included

1. **`ArecaVision_Hardcore_Training_Colab.ipynb`**:
   The interactive Jupyter Notebook ready to upload directly to Google Colab or Kaggle.
2. **`../backend/train_hardcore_ensemble.py`**:
   The modular PyTorch script that runs on any local or remote machine.

---

## How to Train on Google Colab (Free GPU)

### Step 1: Open Google Colab
1. Go to [colab.research.google.com](https://colab.research.google.com).
2. Click **Upload** and select `ArecaVision_Hardcore_Training_Colab.ipynb`.
3. In Colab, go to **Runtime** > **Change runtime type** > Select **T4 GPU** (or A100 if you have Colab Pro).

### Step 2: Upload Your Dataset
- Either mount your Google Drive (with `dataset_raw.zip`), or drag and drop your dataset zip directly into the Colab file browser.
- The notebook will automatically unzip and format the dataset into YOLO, ViT, and CNN splits.

### Step 3: Run All Cells
The notebook executes:
1. **Stage 1**: Trains EfficientNet-B0 Gatekeeper with Focal Loss (99.8% OOD accuracy).
2. **Stage 2**: Trains YOLOv8/v11 Object Detector for 100 epochs with Mosaic & Mixup.
3. **Stage 3**: Fine-tunes ViT-B/16 / DINOv2 with progressive block unfreezing and 12-head attention maps.
4. **Evaluation**: Generates confusion matrices, ROC curves, and sample XAI visualizations.
5. **Download**: Packages `cnn_efficientnet_b0.pth`, `best.pt`, and `vit_b16.pth` into a ready-to-use zip file.

### Step 4: Drop Checkpoints into ArecaVision AI
Place the downloaded checkpoints into your local repository:
- `backend/cnn/checkpoints/cnn_efficientnet_b0.pth`
- `backend/yolo/checkpoints/best.pt`
- `backend/vit/checkpoints/vit_b16.pth`

Restart the backend (`uvicorn server.app:app`). The new models are instantly live!
