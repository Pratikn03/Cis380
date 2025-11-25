"""Grad-CAM utility for vision models."""
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms


def grad_cam(model: torch.nn.Module, image: Image.Image, target_layer: str = "layer4") -> np.ndarray:
    model.eval()
    activations = {}
    gradients = {}

    def forward_hook(module, inp, out):
        activations["value"] = out.detach()

    def backward_hook(module, grad_in, grad_out):
        gradients["value"] = grad_out[0].detach()

    layer = dict(model.named_modules()).get(target_layer)
    if layer is None:
        raise ValueError(f"Layer {target_layer} not found in model")

    handle_fwd = layer.register_forward_hook(forward_hook)
    handle_bwd = layer.register_full_backward_hook(backward_hook)

    preprocess = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    x = preprocess(image).unsqueeze(0)

    logits = model(x)
    score = torch.softmax(logits, dim=1)[0, 1]
    model.zero_grad()
    score.backward()

    acts = activations["value"]
    grads = gradients["value"]
    weights = grads.mean(dim=(2, 3), keepdim=True)
    cam = (weights * acts).sum(dim=1, keepdim=True)
    cam = torch.relu(cam)
    cam = torch.nn.functional.interpolate(cam, size=(224, 224), mode="bilinear", align_corners=False)
    cam = cam.squeeze().cpu().numpy()
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

    handle_fwd.remove()
    handle_bwd.remove()
    return cam


def save_gradcam(model: torch.nn.Module, image: Image.Image, out_path: Path, target_layer: str = "layer4") -> Path:
    cam = grad_cam(model, image, target_layer=target_layer)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path.with_suffix(".npy"), cam)

    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    plt.figure()
    plt.imshow(image.resize((224, 224)))
    plt.imshow(cam, cmap=cm.jet, alpha=0.4)
    plt.axis("off")
    plt.tight_layout()
    out_img = out_path if out_path.suffix else out_path.with_suffix(".png")
    plt.savefig(out_img, dpi=150)
    plt.close()
    return out_img


__all__ = ["grad_cam", "save_gradcam"]
