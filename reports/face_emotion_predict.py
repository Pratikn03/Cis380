"""
Face emotion prediction module using PyTorch.
"""

import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import io
from pathlib import Path

MODEL_PATH = Path("models/vision/face_emotion/model.pt")
CLASSES_PATH = Path("models/vision/face_emotion/classes.txt")


class FaceEmotionModelNotTrainedError(Exception):
    pass


# Definition must match src/train/train_face_emotion.py
class SmallCNN(nn.Module):
    def __init__(self, classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Linear(128, classes)

    def forward(self, x):
        x = self.features(x)
        x = x.flatten(1)
        return self.classifier(x)


def _load_model():
    if not MODEL_PATH.exists() or not CLASSES_PATH.exists():
        raise FaceEmotionModelNotTrainedError("Face emotion model artifacts not found.")

    classes = CLASSES_PATH.read_text(encoding="utf-8").splitlines()
    num_classes = len(classes)

    checkpoint = torch.load(MODEL_PATH, map_location="cpu")
    arch = checkpoint.get("arch", "small_cnn")

    if arch == "resnet18":
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    else:
        model = SmallCNN(classes=num_classes)

    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, classes


def predict_face_emotion(image_bytes: bytes, filename: str, top_k: int = 3) -> dict:
    try:
        model, classes = _load_model()
    except FaceEmotionModelNotTrainedError:
        return {
            "filename": filename,
            "emotion": "unknown",
            "confidence": 0.0,
            "top_k": [],
            "error": "Model not trained",
        }

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # Transforms must match training
        transform = transforms.Compose(
            [
                transforms.Resize((96, 96)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

        img_tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            outputs = model(img_tensor)
            probs = torch.softmax(outputs, dim=1)[0]

        top_probs, top_indices = torch.topk(probs, min(top_k, len(classes)))

        top_k_results = []
        for i in range(len(top_indices)):
            idx = top_indices[i].item()
            top_k_results.append({"label": classes[idx], "prob": float(top_probs[i].item())})

        return {
            "filename": filename,
            "emotion": top_k_results[0]["label"],
            "confidence": top_k_results[0]["prob"],
            "top_k": top_k_results,
        }
    except Exception as e:
        return {"error": str(e)}
