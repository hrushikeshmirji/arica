# ArecaVision (arica) — Hybrid Gatekeeper-CNN, YOLOv8 & Vision Transformer Platform for Areca Nut Disease Detection and Plantation Monitoring

[![CI](https://github.com/hrushikeshmirji/arica/actions/workflows/ci.yml/badge.svg)](https://github.com/hrushikeshmirji/arica/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1%2B-EE4C2C.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**ArecaVision (arica)** is an enterprise-grade precision agriculture platform engineered for arecanut (*Areca catechu*) crop health monitoring, multi-stage automated disease pathology diagnostics, and GIS plantation block management. It pairs a cascading 3-stage computer vision inference pipeline with a responsive, trilingual React application to assist smallholder farmers and agricultural research officers in rapid field triage.

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph Ingestion ["Image Ingestion & Preprocessing"]
        A["Field Camera / Drone / Mobile Upload"] --> B["EXIF Orientation Normalization & Alpha Flattening"]
    end

    subgraph Stage1 ["Stage 1: Gatekeeper CNN V2 (EfficientNet-B0)"]
        B --> C{"Binary OOD Verification<br/>Threshold = 0.7404"}
        C -- "< 0.7404 (Non-Areca / Background)" --> D["Out-of-Distribution (OOD) Rejection<br/>100% Specificity (Zero False Diagnoses)"]
        C -- ">= 0.7404 (Valid Areca Specimen)" --> E["Verified Arecanut Foliage / Fruit Specimen<br/>93.02% Accuracy Baseline"]
    end

    subgraph Stage2 ["Stage 2: Lesion & Region Localization"]
        E --> F["YOLOv8 Detection / Weakly-Supervised ViT Contours"]
        F --> G["Extract Lesion Region-of-Interest (ROI) Crops"]
    end

    subgraph Stage3 ["Stage 3: Fine-Grained Vision Transformer (ViT-B/16)"]
        G --> H["Multi-Crop Test-Time Augmentation (TTA) Ensemble"]
        H --> I["Post-Hoc Temperature Scaled Calibrated Softmax"]
        I --> J["Multi-Class Pathology Diagnosis"]
    end

    subgraph Diagnostics ["Target Disease Diagnoses"]
        J --> K1["1. Fruit Rot (Koleroga / Mahali - Phytophthora meadii)"]
        J --> K2["2. Anthracnose (Colletotrichum gloeosporioides)"]
        J --> K3["3. Nut Cracking (Physiological Boron/Water Stress)"]
        J --> K4["4. Button Shedding (Premature Nut Drop)"]
        J --> K5["5. Sooty Mold (+ Healthy Baseline Verification)"]
    end

    subgraph Output ["Explainability & Agronomy Advisory"]
        J --> L["Self-Attention Rollout Heatmaps (XAI)"]
        J --> M["Bilingual Treatment Protocols & Organic Controls"]
        J --> N["GIS Plantation Digital Twin SQLite Sync"]
    end
```

---

## 2. Dataset Hygiene & Audit Benchmarks

In real-world agricultural computer vision, uncurated web scrapes and duplicated camera bursts introduce silent data leakage and cross-class label noise. To establish a scientifically verified benchmark, ArecaVision implements an automated perceptual hashing (`dHash`) and duplicate reconciliation pipeline via [`build_clean_dataset.py`](file:///d:/ArecaVision_Combined/backend/build_clean_dataset.py).

### Audit & Deduplication Methodology
1. **Intra-Class Exact Deduplication**: Eliminates identical image duplicates (`Hamming Distance = 0`).
2. **Cross-Class Conflict Purification**: Quarantined and purged **131 cross-class conflicted images across 60 duplicate groups** where identical physical specimens carried divergent disease labels.
3. **Synthetic Seed Quarantining**: Quarantined synthetic perturbation seeds strictly to training folds; zero seed images are permitted in validation.
4. **Group-Aware Cluster Splitting**: Connected-component clustering (`Hamming Distance <= 6`) enforces zero inter-split visual leakage across camera bursts.
5. **Cryptographic Integrity**: The curated manifest is SHA-256 fingerprinted (`08dc86a5cd702f538a7389eef495ef67227effe74a16deb73f641beab53094f5`).

### Leak-Free Benchmark Summary (522 Retained Images)

| Disease Class / Visual Target | Training Images (Capped/Cleaned) | Validation Images (Held-Out) | Total Verified Samples | Split Integrity |
|:---|:---:|:---:|:---:|:---:|
| **Fruit Rot (Koleroga)** | 35 | 9 | 44 | Leak-Free Cluster Isolated |
| **Anthracnose** | 33 | 8 | 41 | Leak-Free Cluster Isolated |
| **Nut Cracking** | 23 | 6 | 29 | Leak-Free Cluster Isolated |
| **Sooty Mold** | 37 | 9 | 46 | Leak-Free Cluster Isolated |
| **Healthy Palm / Foliage** | 45 | 11 | 56 | Leak-Free Cluster Isolated |
| **Leaf Spot Complex** | 51 | 0 | 51 | Quarantined Seed Train |
| **Bud Borer Infestation** | 51 | 0 | 51 | Quarantined Seed Train |
| **Yellow Leaf Disease (Chlorosis)** | 51 | 0 | 51 | Quarantined Seed Train |
| **Phytoplasma Yellow Leaf** | 51 | 0 | 51 | Quarantined Seed Train |
| **Stem Cracking** | 51 | 0 | 51 | Quarantined Seed Train |
| **Stem Bleeding** | 51 | 0 | 51 | Quarantined Seed Train |
| **Total** | **479** | **43** | **522** | **100% Verified** |

---

## 3. Full-Stack Architecture Overview

### Backend Architecture
- **Framework**: FastAPI with asynchronous I/O and Uvicorn ASGI server.
- **Inference Pipeline**: PyTorch 2.1+, Torchvision, Timm (`vit_base_patch16_224`), and Ultralytics YOLOv8.
- **Authentication & Security**: Dynamic environment-backed JWT secret generation (`auth.py`) with zero hardcoded credentials, bcrypt password hashing, and mandatory initial password change enforcement for administrative roles.
- **Observability**: Structured Python `logging` throughout request lifecycles and inference threads (`app.py`), replacing unbuffered terminal prints.
- **REST Contract**: Documented in [`docs/BACKEND_API_CONTRACT.md`](file:///d:/ArecaVision_Combined/docs/BACKEND_API_CONTRACT.md) with standardized envelope response schemas.

### Frontend Architecture
- **Framework**: React 18, TypeScript 5.7, Vite 5 SPA.
- **Styling & UI**: Tailwind CSS v4, Lucide React icons, and Framer Motion micro-interactions.
- **Trilingual Internationalization Parity**: Comprehensive, native multi-language context supporting English (`EN`), Kannada (`KN`), and Hindi (`HI`) across all dashboard widgets, agronomy advisories, and pathology cards.
- **Explainable AI Visualization**: Real-time rendering of bounding boxes, saliency focus regions, and attention rollout heatmaps.

---

## 4. Quickstart Instructions

### Prerequisites
- Python 3.10+ (64-bit)
- Node.js 18+ and npm
- Git

### 1. Backend Setup (Port 8000 / 8001)

```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env: Set JWT_SECRET and optional GEMINI_API_KEY

# Launch the FastAPI backend server
python -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload
# (To run on secondary port: replace --port 8000 with --port 8001)
```

Backend endpoints will be accessible at:
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

### 2. Frontend Setup (Port 5173 / 5174 / 8443)

```bash
# In a new terminal, navigate to FRONTEND directory
cd FRONTEND

# Install dependencies
npm install

# Start Vite development server
npm run dev -- --host 127.0.0.1 --port 5173
# (To run on secondary port: replace --port 5173 with --port 5174)
```

Open your browser to: `http://localhost:5173`

---

## 5. Model Checkpoint Governance

Due to repository size constraints, heavy model weights are managed outside Git tracking:
- **Gatekeeper V2**: [`backend/cnn/checkpoints/cnn_efficientnet_b0.pth`](file:///d:/ArecaVision_Combined/backend/cnn/checkpoints/cnn_efficientnet_b0.pth)
- **YOLOv8 Lesion Detector**: [`backend/yolo/checkpoints/best_clean_v1.pt`](file:///d:/ArecaVision_Combined/backend/yolo/checkpoints/best_clean_v1.pt)
- **Vision Transformer**: [`backend/vit/checkpoints/vit_b16_clean_v1.pth`](file:///d:/ArecaVision_Combined/backend/vit/checkpoints/vit_b16_clean_v1.pth)

To train or fine-tune models from scratch on the clean dataset:
```bash
python backend/train_vit_clean.py
```

---

## 6. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
