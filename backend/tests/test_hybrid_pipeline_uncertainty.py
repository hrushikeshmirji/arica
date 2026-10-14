"""
test_hybrid_pipeline_uncertainty.py — Regression tests for Standalone HybridPipeline uncertainty & gatekeeping.

Verifies:
1. Not_Arecanut stops the pipeline without invoking YOLO or ViT.
2. Gatekeeper_Uncertain stops the pipeline without invoking YOLO or ViT.
3. A confirmed Arecanut result continues through YOLO and ViT.
"""

import os
import sys
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

from pipeline.hybrid_pipeline import HybridPipeline


@pytest.fixture
def mocked_pipeline():
    """Create a HybridPipeline instance with mocked neural predictors."""
    with patch("pipeline.hybrid_pipeline.CNNPredictor") as mock_cnn_cls, \
         patch("pipeline.hybrid_pipeline.YOLODetector") as mock_yolo_cls, \
         patch("pipeline.hybrid_pipeline.ViTPredictor") as mock_vit_cls:

        mock_cnn = MagicMock()
        mock_yolo = MagicMock()
        mock_vit = MagicMock()

        mock_cnn_cls.return_value = mock_cnn
        mock_yolo_cls.return_value = mock_yolo
        mock_vit_cls.return_value = mock_vit

        pipe = HybridPipeline()
        yield pipe, mock_cnn, mock_yolo, mock_vit


def test_not_arecanut_stops_pipeline(mocked_pipeline):
    """Not_Arecanut must halt before YOLO and ViT."""
    pipe, mock_cnn, mock_yolo, mock_vit = mocked_pipeline

    mock_cnn.predict.return_value = ("Not_Arecanut", 0.32)
    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)

    result = pipe.predict(fake_img)

    assert result["is_arecanut"] is False
    assert result["cnn_label"] == "Not_Arecanut"
    assert result["cnn_conf"] == 0.32
    assert result["detections"] == []
    assert result["annotated_img"] is None
    assert "not an Arecanut image" in result["message"]

    mock_cnn.predict.assert_called_once()
    mock_yolo.detect.assert_not_called()
    mock_vit.predict.assert_not_called()


def test_gatekeeper_uncertain_stops_pipeline(mocked_pipeline):
    """Gatekeeper_Uncertain must halt before YOLO and ViT."""
    pipe, mock_cnn, mock_yolo, mock_vit = mocked_pipeline

    mock_cnn.predict.return_value = ("Gatekeeper_Uncertain", 0.65)
    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)

    result = pipe.predict(fake_img)

    assert result["is_arecanut"] is False
    assert result["cnn_label"] == "Gatekeeper_Uncertain"
    assert result["cnn_conf"] == 0.65
    assert result["detections"] == []
    assert result["annotated_img"] is None
    assert "Gatekeeper uncertain" in result["message"]

    mock_cnn.predict.assert_called_once()
    mock_yolo.detect.assert_not_called()
    mock_vit.predict.assert_not_called()


def test_confirmed_arecanut_continues_pipeline(mocked_pipeline):
    """Confirmed Arecanut proceeds through YOLO and ViT."""
    pipe, mock_cnn, mock_yolo, mock_vit = mocked_pipeline

    mock_cnn.predict.return_value = ("Arecanut", 0.95)
    dummy_crop = np.zeros((50, 50, 3), dtype=np.uint8)
    dummy_annotated = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_yolo.detect.return_value = (
        [
            {
                "box": (10, 10, 60, 60),
                "confidence": 0.88,
                "class_name": "Anthracnose",
                "crop": dummy_crop,
            }
        ],
        dummy_annotated,
    )
    mock_vit.predict.return_value = ("Anthracnose", 0.91, np.zeros((14, 14), dtype=np.float32))

    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    result = pipe.predict(fake_img)

    assert result["is_arecanut"] is True
    assert result["cnn_label"] == "Arecanut"
    assert len(result["detections"]) == 1
    assert result["detections"][0]["vit_class"] == "Anthracnose"
    assert result["detections"][0]["vit_conf"] == 0.91
    assert result["annotated_img"] is not None

    mock_cnn.predict.assert_called_once()
    mock_yolo.detect.assert_called_once()
    mock_vit.predict.assert_called_once()
