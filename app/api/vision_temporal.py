from __future__ import annotations

import os
import tempfile

import cv2
import numpy as np
import torch
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.logger import logger

from app.models.vision.temporal.model import TemporalDeepfakeLSTM

router = APIRouter(prefix="/vision/video_temporal", tags=["vision-temporal"])

_model: tuple[TemporalDeepfakeLSTM, str] | None = None


def _load_model() -> tuple[TemporalDeepfakeLSTM, str]:
    global _model
    if _model is not None:
        return _model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TemporalDeepfakeLSTM(hidden=256, backbone="mobilenet_v3_small", freeze_backbone=True)
    checkpoint = os.environ.get("TEMPORAL_MODEL_PATH", "artifacts/vision_temporal/temporal_lstm.pt")
    if os.path.exists(checkpoint):
        state = torch.load(checkpoint, map_location=device)
        model.load_state_dict(state)
    model.to(device)
    model.eval()
    _model = (model, device)
    return _model


def _sample_clip(path: str, clip_len: int, size: int) -> torch.Tensor:
    cap = cv2.VideoCapture(path)
    frames = []
    while len(frames) < clip_len:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (size, size))
        frame = frame.astype(np.float32) / 255.0
        frames.append(frame)
    cap.release()

    if not frames:
        raise HTTPException(status_code=400, detail="No valid frames extracted from video.")

    while len(frames) < clip_len:
        frames.append(frames[-1])

    clip = np.stack(frames[:clip_len])
    clip_tensor = torch.tensor(clip, dtype=torch.float32).permute(0, 3, 1, 2).unsqueeze(0)
    return clip_tensor


@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded video is empty.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(data)
    tmp.flush()
    tmp_path = tmp.name

    try:
        clip_len = int(os.environ.get("HLS_CLIP_LEN", "16"))
        size = int(os.environ.get("HLS_FRAME_SIZE", "224"))

        tensor = _sample_clip(tmp_path, clip_len=clip_len, size=size)
        model, device = _load_model()
        tensor = tensor.to(device)
        with torch.no_grad():
            logits = model(tensor)
            prob = torch.sigmoid(logits).item()
        return {"prob_fake": prob, "label": "fake" if prob >= 0.5 else "real", "clip_len": clip_len}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Temporal predict failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        tmp.close()
        os.unlink(tmp_path)
