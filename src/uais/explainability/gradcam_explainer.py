"""Thin wrapper around the existing vision_gradcam utilities."""

from __future__ import annotations

from pathlib import Path
from PIL import Image

from uais.explainability.vision_gradcam import save_gradcam


def gradcam_on_image(model, image: Image.Image, out_path: str | Path, target_layer: str = "layer4") -> None:
    save_gradcam(model, image, out_path, target_layer=target_layer)


__all__ = ["gradcam_on_image"]
