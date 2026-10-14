"""
test_zero_yolo_detections.py — Regression tests for zero YOLO detections handling in FastAPI backend.

Verifies:
1. Zero YOLO detections + predicted disease (e.g., Anthracnose) produces an explicit
   Review Required / Uncertain diagnosis without false disease confirmation or digital twin taint.
2. Zero YOLO detections + confirmed Healthy produces validated Healthy outcome.
3. Non-empty YOLO detections + confirmed disease preserves the existing confirmed diagnosis flow.
4. Boundary case: Low confidence Healthy (< 70%) with zero YOLO detections is marked Low confidence / Uncertain.
5. Boundary case: Narrow margin Healthy (< 25% margin) with zero YOLO detections is marked Low confidence / Uncertain.
6. Boundary case: detect() returning None instead of [] is handled safely without exception.
7. Boundary case: Zero YOLO detections with Experimental Disease Class correctly retains experimental flag and Review Required.
8. Job cancellation halts cleanly at cancellation checkpoints without modifying results.
"""

import io
import os
import sys
import uuid
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from PIL import Image

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

from server import app as server_app


@pytest.fixture
def dummy_jpeg_bytes():
    buf = io.BytesIO()
    img = Image.new("RGB", (128, 128), color=(40, 160, 40))
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_zero_yolo_detections_with_predicted_disease(dummy_jpeg_bytes):
    """When YOLO detects 0 boxes and ViT predicts Anthracnose, outcome must be Review Required."""
    job_id = str(uuid.uuid4())
    server_app._jobs[job_id] = {
        "status": "processing",
        "progressPercent": 10,
        "currentStage": "QUEUED",
    }

    mock_morph = {
        "healthyPct": 88.0,
        "chloroticPct": 8.0,
        "necroticPct": 4.0,
        "lesionCoveragePct": 5.0,
    }
    mock_differential = [
        {"disease": "Anthracnose", "probability": 85.0},
        {"disease": "Healthy", "probability": 10.0},
        {"disease": "FruitRot", "probability": 5.0},
    ]

    with patch.object(server_app.cnn_predictor, "predict", return_value=("Arecanut", 0.96)), \
         patch.object(server_app.yolo_detector, "detect", return_value=([], np.zeros((128, 128, 3), dtype=np.uint8))), \
         patch.object(server_app.vit_predictor, "predict_tta_ensemble", return_value={
             "label": "Anthracnose",
             "confidence": 0.85,
             "differential": mock_differential,
             "morphometrics": mock_morph,
             "saliencyBox": None,
             "attn_map": np.zeros((14, 14), dtype=np.float32),
             "isOOD": False,
         }), \
         patch.object(server_app.vit_predictor, "get_attention_visualization", return_value=np.zeros((128, 128, 3), dtype=np.uint8)), \
         patch.object(server_app.sqlite_db, "record_scan_and_sync_twin") as mock_twin_sync, \
         patch.object(server_app.sqlite_db, "update_job"):

        server_app._run_inference(job_id, dummy_jpeg_bytes, block_id="block-a1")

        job_state = server_app._jobs.get(job_id)
        assert job_state is not None
        assert job_state["status"] == "done"

        result = job_state["result"]
        # Must be explicitly marked as Review Required / Uncertain
        assert result["stage"] == "Review Required"
        assert result["severity"] == "Uncertain"
        assert "Review Required: No Lesions Detected" in result["disease"]
        assert result["isValidatedClass"] is False
        assert result["yoloBoxes"] == []

        # Must NOT prescribe chemical fungicides without localized lesion evidence
        assert any("Consult a certified agronomist" in t for t in result["treatments"])
        assert not any("Copper Oxychloride" in t for t in result["treatments"])

        # Crucially: Plantation Twin must NOT be updated with an unconfirmed infection!
        mock_twin_sync.assert_not_called()


def test_zero_yolo_detections_with_confirmed_healthy(dummy_jpeg_bytes):
    """When YOLO detects 0 boxes and ViT confirms Healthy with high confidence, outcome must be Healthy."""
    job_id = str(uuid.uuid4())
    server_app._jobs[job_id] = {
        "status": "processing",
        "progressPercent": 10,
        "currentStage": "QUEUED",
    }

    mock_morph = {
        "healthyPct": 98.0,
        "chloroticPct": 1.5,
        "necroticPct": 0.5,
        "lesionCoveragePct": 0.5,
    }
    mock_differential = [
        {"disease": "Healthy", "probability": 96.0},
        {"disease": "Anthracnose", "probability": 2.0},
        {"disease": "FruitRot", "probability": 1.0},
    ]

    with patch.object(server_app.cnn_predictor, "predict", return_value=("Arecanut", 0.98)), \
         patch.object(server_app.yolo_detector, "detect", return_value=([], np.zeros((128, 128, 3), dtype=np.uint8))), \
         patch.object(server_app.vit_predictor, "predict_tta_ensemble", return_value={
             "label": "Healthy",
             "confidence": 0.96,
             "differential": mock_differential,
             "morphometrics": mock_morph,
             "saliencyBox": None,
             "attn_map": np.zeros((14, 14), dtype=np.float32),
             "isOOD": False,
         }), \
         patch.object(server_app.vit_predictor, "get_attention_visualization", return_value=np.zeros((128, 128, 3), dtype=np.uint8)), \
         patch.object(server_app.sqlite_db, "record_scan_and_sync_twin", return_value={"scanId": job_id, "blockId": "block-a1"}), \
         patch.object(server_app.sqlite_db, "update_job"):

        server_app._run_inference(job_id, dummy_jpeg_bytes, block_id="block-a1")

        job_state = server_app._jobs.get(job_id)
        assert job_state is not None
        assert job_state["status"] == "done"

        result = job_state["result"]
        assert result["disease"] == "Healthy"
        assert result["severity"] == "Healthy"
        assert result["isValidatedClass"] is True
        assert result["yoloBoxes"] == []


def test_non_empty_yolo_detections_confirmed_disease(dummy_jpeg_bytes):
    """When YOLO detects lesions and ViT confirms disease, existing confirmed pipeline flow is preserved."""
    job_id = str(uuid.uuid4())
    server_app._jobs[job_id] = {
        "status": "processing",
        "progressPercent": 10,
        "currentStage": "QUEUED",
    }

    dummy_crop = np.zeros((50, 50, 3), dtype=np.uint8)
    mock_detections = [
        {
            "box": (10, 10, 80, 80),
            "confidence": 0.88,
            "class_name": "Anthracnose",
            "crop": dummy_crop,
        }
    ]
    mock_morph = {
        "healthyPct": 75.0,
        "chloroticPct": 15.0,
        "necroticPct": 10.0,
        "lesionCoveragePct": 12.0,
    }
    mock_differential = [
        {"disease": "Anthracnose", "probability": 89.0},
        {"disease": "Healthy", "probability": 6.0},
        {"disease": "FruitRot", "probability": 3.0},
    ]

    with patch.object(server_app.cnn_predictor, "predict", return_value=("Arecanut", 0.96)), \
         patch.object(server_app.yolo_detector, "detect", return_value=(mock_detections, np.zeros((128, 128, 3), dtype=np.uint8))), \
         patch.object(server_app.vit_predictor, "predict_tta_ensemble", return_value={
             "label": "Anthracnose",
             "confidence": 0.89,
             "differential": mock_differential,
             "morphometrics": mock_morph,
             "saliencyBox": None,
             "attn_map": np.zeros((14, 14), dtype=np.float32),
             "isOOD": False,
             "yoloCropLabels": ["Anthracnose"],
         }), \
         patch.object(server_app.vit_predictor, "get_attention_visualization", return_value=np.zeros((128, 128, 3), dtype=np.uint8)), \
         patch.object(server_app.sqlite_db, "record_scan_and_sync_twin", return_value={"scanId": job_id, "blockId": "block-a1"}), \
         patch.object(server_app.sqlite_db, "update_job"):

        server_app._run_inference(job_id, dummy_jpeg_bytes, block_id="block-a1")

        job_state = server_app._jobs.get(job_id)
        assert job_state is not None
        assert job_state["status"] == "done"

        result = job_state["result"]
        assert result["disease"] == "Anthracnose"
        assert result["stage"] == "Detected"
        assert result["severity"] in ["Moderate", "Severe"]
        assert result["isValidatedClass"] is True
        assert len(result["yoloBoxes"]) == 1


def test_zero_yolo_low_confidence_healthy_becomes_uncertain(dummy_jpeg_bytes):
    """When YOLO has 0 boxes and ViT predicts Healthy with <70% conf, outcome must be Low confidence/Uncertain."""
    job_id = str(uuid.uuid4())
    server_app._jobs[job_id] = {
        "status": "processing",
        "progressPercent": 10,
        "currentStage": "QUEUED",
    }

    mock_morph = {
        "healthyPct": 85.0,
        "chloroticPct": 10.0,
        "necroticPct": 5.0,
        "lesionCoveragePct": 5.0,
    }
    # Probability 65% is below the 70% provisional healthy floor
    mock_differential = [
        {"disease": "Healthy", "probability": 65.0},
        {"disease": "Anthracnose", "probability": 25.0},
        {"disease": "FruitRot", "probability": 10.0},
    ]

    with patch.object(server_app.cnn_predictor, "predict", return_value=("Arecanut", 0.95)), \
         patch.object(server_app.yolo_detector, "detect", return_value=([], np.zeros((128, 128, 3), dtype=np.uint8))), \
         patch.object(server_app.vit_predictor, "predict_tta_ensemble", return_value={
             "label": "Healthy",
             "confidence": 0.65,
             "differential": mock_differential,
             "morphometrics": mock_morph,
             "saliencyBox": None,
             "attn_map": np.zeros((14, 14), dtype=np.float32),
             "isOOD": False,
         }), \
         patch.object(server_app.vit_predictor, "get_attention_visualization", return_value=np.zeros((128, 128, 3), dtype=np.uint8)), \
         patch.object(server_app.sqlite_db, "record_scan_and_sync_twin") as mock_twin_sync, \
         patch.object(server_app.sqlite_db, "update_job"):

        server_app._run_inference(job_id, dummy_jpeg_bytes, block_id="block-a1")

        job_state = server_app._jobs.get(job_id)
        assert job_state is not None
        assert job_state["status"] == "done"

        result = job_state["result"]
        assert result["stage"] == "Low confidence"
        assert result["severity"] == "Uncertain"
        assert "Low confidence: Healthy" in result["disease"]
        mock_twin_sync.assert_not_called()


def test_zero_yolo_narrow_margin_healthy_becomes_uncertain(dummy_jpeg_bytes):
    """When YOLO has 0 boxes and ViT margin is <25%, outcome must be Low confidence/Uncertain."""
    job_id = str(uuid.uuid4())
    server_app._jobs[job_id] = {
        "status": "processing",
        "progressPercent": 10,
        "currentStage": "QUEUED",
    }

    mock_morph = {
        "healthyPct": 88.0,
        "chloroticPct": 8.0,
        "necroticPct": 4.0,
        "lesionCoveragePct": 4.0,
    }
    # 72% - 55% = 17% margin, which is below the 25% provisional healthy margin floor
    mock_differential = [
        {"disease": "Healthy", "probability": 72.0},
        {"disease": "Anthracnose", "probability": 55.0},
        {"disease": "FruitRot", "probability": 5.0},
    ]

    with patch.object(server_app.cnn_predictor, "predict", return_value=("Arecanut", 0.95)), \
         patch.object(server_app.yolo_detector, "detect", return_value=([], np.zeros((128, 128, 3), dtype=np.uint8))), \
         patch.object(server_app.vit_predictor, "predict_tta_ensemble", return_value={
             "label": "Healthy",
             "confidence": 0.72,
             "differential": mock_differential,
             "morphometrics": mock_morph,
             "saliencyBox": None,
             "attn_map": np.zeros((14, 14), dtype=np.float32),
             "isOOD": False,
         }), \
         patch.object(server_app.vit_predictor, "get_attention_visualization", return_value=np.zeros((128, 128, 3), dtype=np.uint8)), \
         patch.object(server_app.sqlite_db, "record_scan_and_sync_twin") as mock_twin_sync, \
         patch.object(server_app.sqlite_db, "update_job"):

        server_app._run_inference(job_id, dummy_jpeg_bytes, block_id="block-a1")

        job_state = server_app._jobs.get(job_id)
        assert job_state is not None
        assert job_state["status"] == "done"

        result = job_state["result"]
        assert result["stage"] == "Low confidence"
        assert result["severity"] == "Uncertain"
        assert "Low confidence: Healthy" in result["disease"]
        mock_twin_sync.assert_not_called()


def test_zero_yolo_handles_none_detections_safely(dummy_jpeg_bytes):
    """When YOLO detector returns None for detections, system must handle safely without TypeError."""
    job_id = str(uuid.uuid4())
    server_app._jobs[job_id] = {
        "status": "processing",
        "progressPercent": 10,
        "currentStage": "QUEUED",
    }

    mock_morph = {
        "healthyPct": 80.0,
        "chloroticPct": 10.0,
        "necroticPct": 10.0,
        "lesionCoveragePct": 8.0,
    }
    mock_differential = [
        {"disease": "FruitRot", "probability": 88.0},
        {"disease": "Healthy", "probability": 8.0},
        {"disease": "Anthracnose", "probability": 4.0},
    ]

    with patch.object(server_app.cnn_predictor, "predict", return_value=("Arecanut", 0.95)), \
         patch.object(server_app.yolo_detector, "detect", return_value=(None, np.zeros((128, 128, 3), dtype=np.uint8))), \
         patch.object(server_app.vit_predictor, "predict_tta_ensemble", return_value={
             "label": "FruitRot",
             "confidence": 0.88,
             "differential": mock_differential,
             "morphometrics": mock_morph,
             "saliencyBox": None,
             "attn_map": np.zeros((14, 14), dtype=np.float32),
             "isOOD": False,
         }), \
         patch.object(server_app.vit_predictor, "get_attention_visualization", return_value=np.zeros((128, 128, 3), dtype=np.uint8)), \
         patch.object(server_app.sqlite_db, "record_scan_and_sync_twin") as mock_twin_sync, \
         patch.object(server_app.sqlite_db, "update_job"):

        server_app._run_inference(job_id, dummy_jpeg_bytes, block_id="block-a1")

        job_state = server_app._jobs.get(job_id)
        assert job_state is not None
        assert job_state["status"] == "done"

        result = job_state["result"]
        assert result["stage"] == "Review Required"
        assert result["severity"] == "Uncertain"
        assert "Review Required: No Lesions Detected" in result["disease"]
        mock_twin_sync.assert_not_called()


def test_zero_yolo_experimental_disease_class(dummy_jpeg_bytes):
    """When YOLO detects 0 boxes and ViT predicts an experimental class (e.g. LeafSpotComplex), outcome is Review Required."""
    job_id = str(uuid.uuid4())
    server_app._jobs[job_id] = {
        "status": "processing",
        "progressPercent": 10,
        "currentStage": "QUEUED",
    }

    mock_morph = {
        "healthyPct": 82.0,
        "chloroticPct": 12.0,
        "necroticPct": 6.0,
        "lesionCoveragePct": 7.0,
    }
    mock_differential = [
        {"disease": "LeafSpotComplex", "probability": 86.0},
        {"disease": "Healthy", "probability": 10.0},
        {"disease": "Anthracnose", "probability": 4.0},
    ]

    with patch.object(server_app.cnn_predictor, "predict", return_value=("Arecanut", 0.95)), \
         patch.object(server_app.yolo_detector, "detect", return_value=([], np.zeros((128, 128, 3), dtype=np.uint8))), \
         patch.object(server_app.vit_predictor, "predict_tta_ensemble", return_value={
             "label": "LeafSpotComplex",
             "confidence": 0.86,
             "differential": mock_differential,
             "morphometrics": mock_morph,
             "saliencyBox": None,
             "attn_map": np.zeros((14, 14), dtype=np.float32),
             "isOOD": False,
         }), \
         patch.object(server_app.vit_predictor, "get_attention_visualization", return_value=np.zeros((128, 128, 3), dtype=np.uint8)), \
         patch.object(server_app.sqlite_db, "record_scan_and_sync_twin") as mock_twin_sync, \
         patch.object(server_app.sqlite_db, "update_job"):

        server_app._run_inference(job_id, dummy_jpeg_bytes, block_id="block-a1")

        job_state = server_app._jobs.get(job_id)
        assert job_state is not None
        assert job_state["status"] == "done"

        result = job_state["result"]
        assert result["stage"] == "Review Required"
        assert result["severity"] == "Uncertain"
        assert result["isExperimentalClass"] is True
        assert result["isValidatedClass"] is False
        mock_twin_sync.assert_not_called()


def test_job_cancellation_halts_cleanly(dummy_jpeg_bytes):
    """When _was_cancelled returns True, _run_inference halts immediately without modifying results."""
    job_id = str(uuid.uuid4())
    server_app._jobs[job_id] = {
        "status": "failed",
        "error": "Cancelled by user",
    }

    with patch.object(server_app.cnn_predictor, "predict", return_value=("Arecanut", 0.96)), \
         patch.object(server_app, "_was_cancelled", return_value=True), \
         patch.object(server_app.yolo_detector, "detect") as mock_yolo, \
         patch.object(server_app.sqlite_db, "update_job") as mock_update_job:

        server_app._run_inference(job_id, dummy_jpeg_bytes, block_id="block-a1")

        # Must halt before YOLO is invoked
        mock_yolo.assert_not_called()
        # Must not write completion or results to SQLite
        completed_calls = [c for c in mock_update_job.call_args_list if "done" in c[0] or "COMPLETED" in c[0]]
        assert len(completed_calls) == 0
