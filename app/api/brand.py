from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/api/vision/brand", tags=["vision", "brand"])


@router.post("/predict")
async def predict_brand(file: UploadFile = File(...), conf: float = 0.25):
    """Predict brand logos from an uploaded image.

    Returns a list of detections: {brand, confidence, bbox:[x1,y1,x2,y2]}.
    """
    try:
        image_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read upload: {exc}") from exc

    try:
        from src.vision.brand.recognizer import model_path, predict_image_bytes

        detections = predict_image_bytes(image_bytes, conf=conf)
        return {"detections": detections, "model_path": model_path()}
    except RuntimeError as exc:
        # Model missing or ultralytics missing. Mark service unavailable.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
