# ArecaVision AI 2.0 — Feature Inventory & Verification Matrix

This document tracks all user-facing and backend features within `D:\ArecaVision_Combined`. Each capability is classified as **Verified Operational**, **Partially Operational / Heuristic**, or **Synthetic / Unverified Mock**.

---

## 1. Feature Verification Matrix

| Route | Feature Name | Backend Integration Point | Operational Status | Ground Truth Description |
| :--- | :--- | :--- | :--- | :--- |
| `/` | **Landing Page** | Static / Client | **Verified Operational** | Multilingual landing page presenting clinical sample cases, disease severity indicators, and navigation links. |
| `/detection` | **Clinical AI Detection Studio** | `POST /api/v1/detect`<br>`GET /api/v1/jobs/:id` | **Verified Operational** | Real 3-stage PyTorch inference engine (EfficientNet-B0 + YOLOv8n + ViT-B/16). Supports drag-and-drop file upload, asynchronous polling, XAI feature visualization, and treatment guidelines. |
| `/diseases` | **Disease Library** | `GET /api/v1/diseases` | **Verified Operational** | Complete clinical catalog covering 11 betel palm conditions (5 validated, 6 experimental) with symptom guides and multilingual treatments (EN, KN, HI). |
| `/scans` | **Scan History** | `GET /api/v1/scans`<br>`DELETE /api/v1/scans/:id` | **Verified Operational** | Persistent scan history stored in SQLite `scans` table. Supports search filtering by disease, block ID, severity, and export. |
| `/admin` | **Administration & Security** | `POST /api/v1/auth/*`<br>`GET /api/v1/admin/*` | **Verified Operational** | JWT authentication, bcrypt password hashing, `must_change_password` access controls, and admin audit logging. |
| `/` | **System Health Telemetry** | `GET /health`<br>`GET /api/v1/health` | **Verified Operational** | Live health check reporting API status, YOLO checkpoint availability, and CPU/CUDA compute device. |
| `/dashboard` | **Operational Dashboard** | `GET /api/v1/dashboard/kpi`<br>`GET /api/v1/dashboard/trends` | **Partially Operational** | Real Quick Diagnostic upload shortcut; KPI numbers and disease trends are derived from local SQLite scans, but fallback to synthetic defaults if database is empty. |
| `/reports` | **Diagnostic Reports** | `POST /api/v1/reports/export` | **Partially Operational** | Backend serves formatted summary data; client generates printable agronomic reports and browser print layouts. |
| `/map` | **Plantation GIS Map** | `GET /api/v1/plantation/blocks`<br>`PUT /api/v1/plantation/blocks/:id` | **Heuristic / Simulated** | Serves 8 predefined static plantation blocks stored in SQLite (`block-a1`, `block-a2`, `block-b1`, `block-b2`, `block-c1`, `block-c2`, `block-d1`, `block-d2`). Does not integrate with live GPS telemetry, drone feeds, or external GIS Shapefiles. |
| `/weather` | **Weather Intelligence** | `GET /api/v1/weather` | **Heuristic / Simulated** | Serves simulated regional microclimate values (temperature, relative humidity, precipitation). Does not connect to live external weather APIs (e.g. OpenWeatherMap). |
| `/risk` | **Risk Forecast** | `GET /api/v1/risk/forecast` | **Heuristic / Simulated** | Calculates a 5-day disease spread risk index using humidity/temperature threshold equations (`calculate_epidemiological_risk`). Not validated against multi-season agricultural trials. |
| `/assistant` | **AI Agronomist Chatbot** | `POST /api/v1/assistant/chat` | **Rule-Based Retrieval** | Keyword-based agronomic catalog matching; does not query live external LLMs (Gemini/OpenAI) unless external API credentials are provided. |
| Modal | **Live Camera Studio** | Browser `getUserMedia` | **Hardware Dependent** | Captures photos using local webcam hardware. Fails if user denies camera permissions or runs in a headless environment. |

---

## 2. Detailed Capability Analysis

### A. Core Diagnostic Engine (Verified Operational)
- **Input Formats:** Accepts JPEG, PNG, WEBP, BMP up to 10 MB.
- **Stage 1 (Gatekeeper):** EfficientNet-B0 rejects non-arecanut images below 0.5180 confidence, preventing false positive misdiagnoses on background foliage, humans, vehicles, or unrelated crops.
- **Stage 2 (Region Detector):** YOLOv8n isolates pathological lesions and nut bunches, returning relative bounding coordinates (`top`, `left`, `width`, `height`).
- **Stage 3 (Classifier):** Vision Transformer (ViT-B/16) applies Multi-Scale Test-Time Augmentation (0.9x, 1.0x, 1.1x) to classify disease type, stage, severity, and differential diagnoses.

### B. Supported Pathology Classes
1. **Validated Clinical Classes (High Confidence):**
   - Fruit Rot (Koleroga / Mahali — *Phytophthora meadii*)
   - Leaf Blight (Anthracnose — *Colletotrichum gloeosporioides*)
   - Nut Splitting (Nut Cracking — Physiological stress)
   - Sooty Mold (*Meliola betle*)
   - Healthy Areca Palm
2. **Experimental Research Classes:**
   - Bud Borer Infestation
   - Stem Bleeding (*Thielaviopsis paradoxa*)
   - Stem Cracking
   - Fungal Leaf Spot
   - Phytoplasma (Yellow Leaf Disease)
   - Yellow Leaf Chlorosis

---

## 3. Known Limitations & Caveats

1. **Database Runtime Dependencies:**
   - The application relies on `backend/data/arecavision.db`. If this file is missing or corrupted, the server auto-generates schema tables, but historical scans and plantation blocks reset to default seeds.
2. **Demo Mode vs. Production Mode:**
   - Controlled via `FRONTEND/.env` flag `VITE_DEMO_MODE=true/false`.
   - In Demo Mode (`true`), the frontend returns static mock profiles even if the backend is offline.
   - In Production Mode (`false`), all UI requests hit `http://localhost:8000/api/v1` and require an active Uvicorn backend process.
