"""FastAPI endpoint to serve UAIS-V predictions (fraud, cyber, fusion, NLP, vision)."""
from base64 import b64decode
from io import BytesIO
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="UAIS-V API", version="1.3")

project_root = Path(__file__).resolve().parents[2]
fraud_model_path = project_root / "models" / "fraud" / "supervised" / "fraud_model.pkl"
cyber_model_path = project_root / "models" / "cyber" / "supervised" / "cyber_model.pkl"
fusion_model_path = project_root / "experiments" / "fusion" / "models" / "fusion_meta_model.pkl"
nlp_model_dir = project_root / "models" / "nlp" / "distilbert"
vision_model_dir = project_root / "models" / "vision" / "resnet"

fraud_model = joblib.load(fraud_model_path) if fraud_model_path.exists() else None
cyber_model = joblib.load(cyber_model_path) if cyber_model_path.exists() else None
fusion_model = joblib.load(fusion_model_path) if fusion_model_path.exists() else None

# Lazy-loaded NLP / Vision artifacts
_nlp_artifacts_loaded = False
_nlp_model = None
_nlp_tokenizer = None
_vision_model = None


def _load_nlp():
    global _nlp_artifacts_loaded, _nlp_model, _nlp_tokenizer
    if _nlp_artifacts_loaded:
        return _nlp_model, _nlp_tokenizer
    try:
        import torch
        from uais_v.models.nlp_text_model import DistilBERTClassifier, get_tokenizer
    except Exception:
        _nlp_artifacts_loaded = True
        return None, None
    if not nlp_model_dir.exists():
        _nlp_artifacts_loaded = True
        return None, None
    tokenizer = get_tokenizer(str(nlp_model_dir))
    model = DistilBERTClassifier(str(nlp_model_dir), num_labels=2)
    state_path = nlp_model_dir / "model.pt"
    if state_path.exists():
        model.load_state_dict(torch.load(state_path, map_location="cpu"))
    model.eval()
    _nlp_model, _nlp_tokenizer = model, tokenizer
    _nlp_artifacts_loaded = True
    return model, tokenizer


def _load_vision():
    global _vision_model
    if _vision_model is not None:
        return _vision_model
    try:
        import torch
        from uais_v.models.vision_resnet import VisionConfig, build_resnet_classifier
    except Exception:
        _vision_model = False
        return None
    state_path = vision_model_dir / "model.pt"
    if not state_path.exists():
        _vision_model = False
        return None
    cfg = VisionConfig(model_name="resnet18", num_classes=2, pretrained=False)
    model = build_resnet_classifier(cfg)
    model.load_state_dict(torch.load(state_path, map_location="cpu"))
    model.eval()
    _vision_model = model
    return model


class FraudRequest(BaseModel):
    features: List[float]


class CyberRequest(BaseModel):
    features: List[float]


class FusionRequest(BaseModel):
    scores: Dict[str, float]


class NLPRequest(BaseModel):
    text: str


class VisionRequest(BaseModel):
    image_base64: str  # base64-encoded image (jpg/png)


@app.get("/")
def root():
    return {
        "message": "UAIS-V API active.",
        "available": {
            "fraud": fraud_model is not None,
            "cyber": cyber_model is not None,
            "fusion": fusion_model is not None,
            "nlp": nlp_model_dir.exists(),
            "vision": vision_model_dir.exists(),
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict_fraud")
def predict_fraud(req: FraudRequest):
    if fraud_model is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Fraud model not found.")
    X = np.array(req.features).reshape(1, -1)
    proba = fraud_model.predict_proba(X)[0, 1]
    return {"fraud_probability": float(proba)}


@app.post("/predict_cyber")
def predict_cyber(req: CyberRequest):
    if cyber_model is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cyber model not found.")
    X = np.array(req.features).reshape(1, -1)
    proba = cyber_model.predict_proba(X)[0, 1]
    return {"cyber_attack_probability": float(proba)}


@app.post("/predict_fusion")
def predict_fusion(req: FusionRequest):
    if fusion_model is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Fusion model not found.")
    keys = sorted(req.scores)
    X = np.array([[req.scores[k] for k in keys]])
    proba = fusion_model.predict_proba(X)[0, 1]
    return {"fusion_risk": float(proba), "domains": keys}


@app.post("/predict_nlp")
def predict_nlp(req: NLPRequest):
    model, tokenizer = _load_nlp()
    if model is None or tokenizer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="NLP model/tokenizer not available."
        )
    try:
        import torch
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Torch not available for NLP.")
    enc = tokenizer(req.text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
    with torch.no_grad():
        logits = model(enc["input_ids"], enc["attention_mask"])
        proba = torch.softmax(logits, dim=1)[:, 1].item()
    return {"nlp_suspicion_probability": float(proba)}


@app.post("/predict_vision")
def predict_vision(req: VisionRequest):
    model = _load_vision()
    if model is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vision model not available.")
    try:
        import torch
        from PIL import Image
        from torchvision import transforms
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Torch/torchvision/PIL not available for vision inference.",
        )

    try:
        img_bytes = b64decode(req.image_base64)
        image = Image.open(BytesIO(img_bytes)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid image: {exc}")

    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    x = transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(x)
        proba = torch.softmax(logits, dim=1)[:, 1].item()
    return {"vision_anomaly_probability": float(proba)}


__all__ = [
    "predict_fraud",
    "predict_cyber",
    "predict_fusion",
    "predict_nlp",
    "predict_vision",
    "root",
    "health",
]
