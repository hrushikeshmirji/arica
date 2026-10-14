"""
cnn/model.py — EfficientNet-B0 binary gate for Stage-1 arecanut detection.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torchvision import models


class CNNClassifier(nn.Module):
    """EfficientNet-B0 binary classifier (Arecanut vs Not_Arecanut).

    ``forward`` returns raw logits for use with CrossEntropyLoss.
    Use ``predict_proba`` during inference.
    """

    def __init__(
        self,
        num_classes: int = 2,
        pretrained: bool = True,
        dropout: float = 0.40,
        freeze_backbone: bool = False,
    ) -> None:
        super().__init__()
        if num_classes != 2:
            raise ValueError("Stage-1 CNN must have exactly 2 output classes.")

        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        self.backbone = models.efficientnet_b0(weights=weights)
        in_features = self.backbone.classifier[1].in_features

        # Custom head: Dropout → Linear(1280→512) → BN → ReLU → Dropout → Linear(512→2)
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(512, num_classes),
        )

        if freeze_backbone:
            for p in self.backbone.features.parameters():
                p.requires_grad = False

    # ------------------------------------------------------------------
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    @torch.inference_mode()
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Softmax probabilities — shape [batch, 2]."""
        return torch.softmax(self(x), dim=1)
