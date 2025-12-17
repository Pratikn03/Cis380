from __future__ import annotations

import torch
import torch.nn as nn
import torchvision.models as models


class TemporalDeepfakeLSTM(nn.Module):
    """Temporal deepfake classifier uses a frozen CNN behind an LSTM."""

    def __init__(self, hidden: int = 256, backbone: str = "mobilenet_v3_small", freeze_backbone: bool = True):
        super().__init__()
        if backbone == "mobilenet_v3_small":
            base = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
            feat_dim = base.classifier[0].in_features
            base.classifier = nn.Identity()
        else:
            base = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
            feat_dim = base.fc.in_features
            base.fc = nn.Identity()

        if freeze_backbone:
            for p in base.parameters():
                p.requires_grad = False

        self.backbone = base
        self.lstm = nn.LSTM(input_size=feat_dim, hidden_size=hidden, batch_first=True, bidirectional=True)
        self.classifier = nn.Sequential(
            nn.Linear(hidden * 2, hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, c, h, w = x.shape
        x = x.reshape(b * t, c, h, w)
        features = self.backbone(x)
        features = features.view(b, t, -1)
        out, _ = self.lstm(features)
        out = out[:, -1, :]
        logits = self.classifier(out)
        return logits
