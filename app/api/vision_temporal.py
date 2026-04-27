from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/vision/video_temporal", tags=["vision-temporal"])


def _load_legacy_video_predictor():
    src_dir = Path(__file__).resolve().parents[2] / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from app.legacy.api.routes.vision import vision_video_predict

    return vision_video_predict


@router.post("/predict")
async def predict(
    file: UploadFile = File(...),
    fps: float = 1.0,
    max_frames: int = 30,
    top_k: int = 3,
):
    """Score video with the canonical frame + temporal-confidence model.

    The promotion gate validates ``models/vision/video_temporal_model.pkl``.
    Reusing the legacy video predictor keeps this endpoint on the same served
    artifact instead of loading the older unpromoted LSTM checkpoint.
    """

    video_predict = _load_legacy_video_predictor()
    return await video_predict(
        file=file,
        fps=fps,
        max_frames=max_frames,
        top_k=top_k,
    )
