# ArecaVision AI — Arecanut Disease Detection & Plantation Analytics

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF.svg)](https://vitejs.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ArecaVision is an end-to-end precision agriculture platform designed for arecanut (betel nut) farmers, agronomists, and agricultural researchers. It integrates a 3-stage computer vision inference pipeline with a responsive web dashboard for real-time disease detection, severity scoring, explainable AI (XAI) attention heatmaps, and agronomic management advisories.

---

## Architecture Overview

```
                      [ User Input Image ]
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ Stage 1: CNN Gatekeeper (EfficientNet-B0)   │
        │ - Verifies arecanut tree/fruit specimen      │
        │ - Rejects Out-of-Distribution (OOD) photos   │
        └──────────────────────┬───────────────────────┘
                               │ (Valid Specimen)
                               ▼
        ┌──────────────────────────────────────────────┐
        │ Stage 2: YOLO Lesion Detector (YOLOv8)      │
        │ - Localizes disease lesions & anomalies      │
        │ - Extracts high-resolution bounding boxes   │
        └──────────────────────┬───────────────────────┘
                               │ (Cropped Lesion Bounding Boxes)
                               ▼
        ┌──────────────────────────────────────────────┐
        │ Stage 3: Vision Transformer (ViT-B/16)       │
        │ - Fine-grained multi-class classification   │
        │ - Severity estimation & attention rollout    │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
     [ Diagnosis + Confidence + Explainability + Agronomy Action ]
```

### Supported Diagnoses
- **Fruit Rot / Koleroga** (*Phytophthora meadii*)
- **Yellow Leaf Disease (YLD)**
- **Leaf Spot Complex**
- **Bud Borer Infestation**
- **Stem Bleeding & Stem Cracking**
- **Sooty Mold**
- **Nut Cracking**
- **Healthy Plant / Leaf Verification**

---

## Repository Structure

```
ArecaVision_Combined/
├── FRONTEND/                # React 18 + Vite + TailwindCSS Web Application
│   ├── src/                 # UI components, pages, hooks, state management
│   ├── public/              # Static assets, hero visuals, sample images
│   └── package.json
├── backend/                 # FastAPI Python Application
│   ├── cnn/                 # Stage 1: CNN Gatekeeper models & inference
│   ├── yolo/                # Stage 2: YOLO lesion detector
│   ├── vit/                 # Stage 3: Vision Transformer fine-grained classifier
│   ├── pipeline/            # Multi-stage orchestrator & ensemble logic
│   ├── server/              # FastAPI REST endpoints & WebSocket handlers
│   ├── services/            # Agronomy engine, database services, Gemini AI
│   └── requirements.txt     # Python dependencies
├── docs/                    # Architecture diagrams, specifications & audits
├── scripts/                 # Benchmark utilities & test suites
├── start.bat                # One-click Windows runner
└── README.md
```

---

## Quick Start Guide

### Prerequisites
- **Python**: 3.10+ (64-bit)
- **Node.js**: 18+ and npm
- **Git**

### Option A: One-Click Launch (Windows)
Double-click `start.bat` in the project root. It will:
1. Verify Python & Node.js installations.
2. Initialize virtual environments and install missing dependencies.
3. Launch the FastAPI backend on `http://127.0.0.1:8000`.
4. Launch the Vite frontend on `http://127.0.0.1:8443`.

---

### Option B: Manual Setup

#### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your optional GEMINI_API_KEY for conversational AI

# Run the FastAPI server
python -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
# In a new terminal, navigate to FRONTEND
cd FRONTEND

# Install dependencies
npm install

# Start the development server
npm run dev -- --host 127.0.0.1
```

Access the frontend application at: `http://localhost:8443`  
Access API interactive documentation at: `http://localhost:8000/docs`

---

## Model Checkpoints

Due to GitHub file size limits, large pre-trained weights (`*.pth` files exceeding 100MB) are kept outside git history:
- Place `vit_b16.pth` in `backend/vit/checkpoints/`
- Place `cnn_efficientnet_b0.pth` in `backend/cnn/checkpoints/`
- Place `best.pt` in `backend/yolo/checkpoints/`

Training and fine-tuning scripts are provided in `backend/` for training your own checkpoints from scratch.

---

## Key Features

- **Explainable AI (XAI)**: Generates self-attention rollout maps highlighting exact disease lesions.
- **Out-of-Distribution Rejection**: Prevents false diagnoses by filtering out non-arecanut imagery.
- **Agronomic Treatment Plans**: Automated, localized chemical and organic control measures.
- **Field Analytics Dashboard**: Plantation block tracking, disease incidence trends, and weather risk correlations.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
