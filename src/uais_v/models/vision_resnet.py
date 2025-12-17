"""Vision anomaly classifier using a pretrained ResNet backbone."""
from dataclasses import dataclass

import torch
from torch import nn
from torchvision import models


@dataclass
class VisionConfig:
    model_name: str = "resnet18"
    num_classes: int = 2
    pretrained: bool = True


def build_resnet_classifier(cfg: VisionConfig) -> nn.Module:
    if cfg.model_name == "resnet18":
        backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT if cfg.pretrained else None)
    else:
        backbone = models.resnet34(weights=models.ResNet34_Weights.DEFAULT if cfg.pretrained else None)
    in_feat = backbone.fc.in_features
    backbone.fc = nn.Linear(in_feat, cfg.num_classes)
    return backbone


__all__ = ["VisionConfig", "build_resnet_classifier"]
