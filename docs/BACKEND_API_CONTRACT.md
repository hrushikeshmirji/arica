# ArecaVision 2.0 — Backend API Contract

## 1. Overview
This document specifies the exact request/response contracts for the ArecaVision backend (`backend/server/app.py`).

---

## 2. Authentication Endpoints

### 2.1 POST `/api/v1/auth/login`
- **Request Body**:
  ```json
  {
    "username": "user@example.com",
    "password": "userPassword"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "token": "<jwt_token>",
    "must_change_password": false,
    "user": {
      "id": "usr-12345",
      "username": "user",
      "role": "agronomist"
    }
  }
  ```

### 2.2 POST `/api/v1/auth/change-password`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "oldPassword": "currentPassword",
    "newPassword": "newSecurePassword123"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "message": "Password updated successfully"
  }
  ```

### 2.3 Password Change Enforcement (`must_change_password`)
- Default admin accounts seeded via `DEV_SEED_ADMIN=true` have `must_change_password=1`.
- Any authenticated user with `must_change_password=1` is **blocked** from calling any non-auth API endpoint (`/api/v1/*` except `/api/v1/auth/*`).
- Blocked requests receive:
  - **Status Code**: `403 Forbidden`
  - **Response Body**:
    ```json
    {
      "error": "PASSWORD_CHANGE_REQUIRED",
      "message": "You must change your initial password before accessing the system."
    }
    ```

---

## 3. Detection & Inference Endpoints

### 3.1 POST `/api/v1/detect`
- **Payload**: `multipart/form-data` with:
  - `file`: Image binary (`image/jpeg`, `image/png`, etc.)
  - `blockId` (optional): Plantation block ID (e.g. `block-a1`)
  - `specimenId` (optional): Specimen ID if selected from specimen gallery
- **Response (202 Accepted)**:
  ```json
  {
    "job_id": "job-abcd1234efgh",
    "status": "queued",
    "estimatedTimeSeconds": 3.0
  }
  ```

### 3.2 GET `/api/v1/detect/status/{job_id}`
- **Response (200 OK)**:
  ```json
  {
    "job_id": "job-abcd1234efgh",
    "status": "done",
    "progressPercent": 100,
    "currentStage": "COMPLETED",
    "result": { ... }
  }
  ```

---

## 4. Inference Result Contract (`result`)

### 4.1 Common Fields
| Field | Type | Description |
|---|---|---|
| `id` | string | Unique inference job ID (`job-<hex>`). |
| `disease` | string | Diagnosed condition or stage indicator. |
| `diseaseDisplayName` | string | Formatted disease name. |
| `confidence` | float | Percentage confidence (1 decimal place). |
| `gateScore` | float \| undefined | Gate rejection score ($1.0 - P(\text{areca})$ in percent, unclamped). Populated on Gatekeeper Defense. |
| `stage` | string | Final pipeline stage reached: `Detected`, `Low confidence`, `Gatekeeper Uncertain`, or `Gatekeeper Defense`. |
| `severity` | string | Severity indicator: `Healthy`, `Mild`, `Moderate`, `Severe`, `Critical`, `Non-Arecanut`, or `Uncertain`. |
| `isExperimentalClass` | boolean | True if the diagnosed class belongs to an experimental synthetic category without field validation. |
| `isValidatedClass` | boolean | True if the class is one of the 5 real-world field-validated classes. |
| `description` | string | Clinical description or explanatory notice. |
| `treatments` | string[] | Recommended interventions. |
| `organicControl` | string[] | Agronomic/organic management suggestions. |
| `yoloBoxes` | object[] | Bounding boxes from YOLO detector. **Strictly filtered to `confidence >= 0.25` with true model confidence.** Empty array if no detections meet threshold. |
| `saliencyBox` | object \| null | Heuristic saliency bounding box. Label is strictly `"saliency heuristic (not a trained detector)"` with **no confidence score**. |
| `modelBreakdown` | object | `{ "cnn": float, "vit": float, "yolo": float }`. `yolo` is `0.0` when `yoloBoxes` is empty. |
| `tissueMorphometrics` | object | Tissue health breakdown `{ "healthyPct", "chloroticPct", "necroticPct", "lesionCoveragePct" }`. |
| `differentialDiagnosis` | object[] | Top candidates `{ "disease", "probability" }`. |
| `stageTimingsMs` | object | Latency breakdown `{ "gatekeeperMs", "yoloMs", "vitTtaMs", "xaiRolloutMs", "totalMs" }`. |
| `processedAt` | string | ISO-8601 UTC timestamp. |
| `attentionMapUrl` | string | Data URI or URL to ViT 12-head attention rollout visualization. |

### 4.2 YOLO Bounding Box Object (`yoloBoxes[i]`)
```json
{
  "label": "Fruit Rot (Koleroga)",
  "confidence": 78.4,
  "top": "24.5%",
  "left": "31.2%",
  "width": "42.0%",
  "height": "38.6%",
  "color": "#ef4444"
}
```
*Note: Synthetic full-image or center boxes and confidence inflation formulas have been removed completely.*

### 4.3 Saliency Box Object (`saliencyBox`)
```json
{
  "label": "saliency heuristic (not a trained detector)",
  "top": "20.1%",
  "left": "15.4%",
  "width": "55.0%",
  "height": "60.2%",
  "color": "#f59e0b"
}
```
*Note: Saliency box has no confidence field and is never merged into `yoloBoxes`.*

### 4.4 Gatekeeper Uncertain Contract (`stage: "Gatekeeper Uncertain"`)
Returned when the Stage-1 gatekeeper classifies the image within the uncertainty margin (`areca_score` between threshold $\pm$ margin):
```json
{
  "id": "job-...",
  "disease": "Gatekeeper Uncertain",
  "diseaseDisplayName": "Gatekeeper Uncertain",
  "confidence": 54.2,
  "stage": "Gatekeeper Uncertain",
  "severity": "Uncertain",
  "description": "The gatekeeper model cannot verify whether this image contains an arecanut palm with sufficient certainty. Disease diagnosis was suspended to protect diagnostic accuracy. Please retake the photo.",
  "retakePhoto": {
    "en": "Gatekeeper uncertain. Please retake the photo with clearer focus and natural lighting on the arecanut palm.",
    "kn": "ಗೇಟ್‌ಕೀಪರ್ ಅನಿಶ್ಚಿತವಾಗಿದೆ. ದಯವಿಟ್ಟು ಅಡಿಕೆ ಮರದ ಮೇಲೆ ಸ್ಪಷ್ಟವಾದ ಬೆಳಕಿನಲ್ಲಿ ಪುನಃ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.",
    "hi": "गेटकीपर अनिश्चित है। कृपया सुपारी के पेड़ पर स्पष्ट फोकस और प्राकृतिक रोशनी में दोबारा फोटो लें।"
  },
  "yoloBoxes": [],
  "saliencyBox": null,
  "differentialDiagnosis": []
}
```

### 4.5 ViT Low-Confidence Contract (`stage: "Low confidence"`)
Returned when the ViT prediction falls below provisional confidence floors:
- **Disease classes**: Top-1 probability $< 0.50$ OR $(Top1 - Top2 \text{ margin}) < 0.10$.
- **Healthy class**: Top-1 probability $< 0.70$ OR $(Top1 - Top2 \text{ margin}) < 0.25$.

```json
{
  "id": "job-...",
  "disease": "Low confidence: Fruit Rot (Koleroga)",
  "diseaseDisplayName": "Low Confidence (Fruit Rot (Koleroga))",
  "confidence": 46.8,
  "stage": "Low confidence",
  "severity": "Uncertain",
  "description": "Model prediction fell below provisional confidence floors (provisional disease floor: 50.0%, healthy floor: 70.0%). Diagnostic uncertainty is elevated. Please consult an agronomist.",
  "consultAgronomist": {
    "en": "Prediction confidence is low. Please consult a qualified agronomist or your local Krishi Vigyan Kendra (KVK) for clinical diagnosis.",
    "kn": "ಮುನ್ನೋಟದ ವಿಶ್ವಾಸಾರ್ಹತೆ ಕಡಿಮೆಯಾಗಿದೆ. ದಯವಿಟ್ಟು ಸೂಕ್ತ ರೋಗನಿರ್ಣಯಕ್ಕಾಗಿ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರ (ಕೆವಿಕೆ) ಅಥವಾ ಕೃಷಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    "hi": "पूर्वानुमान का विश्वास स्तर कम है। कृपया सटीक निदान के लिए किसी योग्य कृषि विशेषज्ञ या नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
  },
  "differentialDiagnosis": [
    { "disease": "Fruit Rot (Koleroga)", "probability": 46.8 },
    { "disease": "Bud Borer", "probability": 41.2 },
    { "disease": "Healthy", "probability": 12.0 }
  ]
}
```

### 4.6 Experimental Research Classes Contract (`isExperimentalClass: true`)
When the model predicts one of the 6 unvalidated synthetic/research classes (`BudBorer`, `LeafSpotComplex`, `PhytoplasmaYellowLeaf`, `StemBleeding`, `StemCracking`, `YellowLeaf`):
- `stage` is routed strictly to `"Low confidence"`
- `severity` is set to `"Uncertain"`
- `isExperimentalClass` is `true`, `isValidatedClass` is `false`
- Clinical treatments are blocked and replaced with KVK/agronomic consultation advisory
- Differential diagnosis returns top 3 candidates

