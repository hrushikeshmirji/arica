"""
vit/model.py — ViT-B/16 fine-grained disease classifier for Stage-3.

Architecture:
  • timm ViT-B/16 pretrained backbone (frozen initially)
  • Custom head: Dropout → LayerNorm → Linear(768 → num_classes)
  • Forward hook on last attention block to capture attention maps
  • Supports progressive unfreezing for fine-tuning
"""

from __future__ import annotations

import torch
import torch.nn as nn
import timm


class ViTClassifier(nn.Module):
    """ViT-B/16 disease classifier.

    Args:
        num_classes: Number of disease output classes.
        pretrained:  Load ImageNet-21k pretrained weights via timm.
        dropout:     Dropout rate applied before the final linear layer.
        freeze_backbone: If True, freeze all backbone parameters initially.
    """

    def __init__(
        self,
        num_classes: int = 11,
        pretrained: bool = True,
        dropout: float = 0.10,
        freeze_backbone: bool = True,
    ) -> None:
        super().__init__()
        self.model = timm.create_model(
            "vit_base_patch16_224",
            pretrained=pretrained,
            drop_rate=dropout,
            drop_path_rate=0.1,
        )

        # Freeze backbone for warm-up phase
        if freeze_backbone:
            for p in self.model.parameters():
                p.requires_grad = False

        # Replace classification head
        in_features = self.model.head.in_features
        self.model.head = nn.Sequential(
            nn.LayerNorm(in_features),
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        )

        # Attention map storage
        self._attention_maps: torch.Tensor | None = None
        self._hook_handle = self._register_attn_hook()

        # timm defaults fused_attn=True which bypasses the attn_drop layer,
        # preventing the forward hook above from ever firing.  Disable it on
        # every block so get_attention_maps() returns a real tensor in all
        # contexts (server, standalone scripts, evaluate_pipeline.py, tests).
        for blk in self.model.blocks:
            blk.attn.fused_attn = False

    # ------------------------------------------------------------------
    def _register_attn_hook(self):
        """Hook on the last transformer block's attention-drop layer."""
        try:
            layer = self.model.blocks[-1].attn.attn_drop
            return layer.register_forward_hook(self._attn_hook)
        except Exception as exc:
            print(f"[ViT] Warning: could not register attention hook — {exc}")
            return None

    def _attn_hook(self, _module, inputs, _output) -> None:
        # inputs[0]: [B, heads, N, N]  (post-softmax attention weights)
        self._attention_maps = inputs[0].detach()

    # ------------------------------------------------------------------
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    def get_attention_maps(self) -> torch.Tensor | None:
        """Return the last captured attention tensor [B, heads, N, N]."""
        return self._attention_maps

    # ------------------------------------------------------------------
    def unfreeze_last_n_blocks(self, n: int) -> None:
        """Progressively unfreeze the last *n* transformer blocks + head."""
        for p in self.model.head.parameters():
            p.requires_grad = True
        for block in self.model.blocks[-n:]:
            for p in block.parameters():
                p.requires_grad = True
        # Always unfreeze norm
        for p in self.model.norm.parameters():
            p.requires_grad = True

    def unfreeze_all(self) -> None:
        for p in self.model.parameters():
            p.requires_grad = True

    def trainable_params(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
