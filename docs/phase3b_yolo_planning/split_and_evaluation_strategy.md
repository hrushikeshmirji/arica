# Phase 3B: Split Strategy and Benchmark Evaluation Criteria

## 1. Split Allocation Protocol

- **Partition Ratios**: 70% Train (~245 images), 15% Validation (~52 images), 15% Held-Out Test (~52 images).
- **Stratified Grouped Splitting**: Splitting must be stratified across all active disease classes and grouped by image perceptual hash to ensure identical or burst-captured images never cross between splits.
- **Held-Out Test Set Isolation**: The test split must remain completely untouched during model training, hyperparameter tuning, and threshold selection.

---

## 2. Model Acceptance & Gating Criteria

Any future trained YOLO model must satisfy all gating criteria before deployment:

| Evaluation Metric | Minimum Acceptable Threshold | Target Benchmark | Verification Dataset |
|:---|:---:|:---:|:---|
| **mAP@50 (Overall)** | $\ge 0.550$ | $\ge 0.700$ | Clean Held-Out Test Set |
| **mAP@50-95** | $\ge 0.350$ | $\ge 0.450$ | Clean Held-Out Test Set |
| **Mean Precision ($	ext{conf} \ge 0.25$)** | $\ge 0.650$ | $\ge 0.800$ | Clean Held-Out Test Set |
| **Healthy False Positive Rate** | **$< 3.0\%$** | **$0.0\%$** | 73 Clean Healthy Images |
| **Average Lesion Box Size** | $< 0.40$ (Width/Height) | Natural Lesion Geometry | Test Set Ground Truth |
