"""
Brand recognition API endpoints.
"""

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from src.vision.brand.recognizer import predict_image_bytes

router = APIRouter(prefix="/api/vision/brand", tags=["brand"])


@router.post("/predict")
async def predict_brand(
    file: UploadFile = File(...),
    conf: float = Query(0.25, ge=0.0, le=1.0, description="Confidence threshold"),
    kind: str = Query("logo", description="Model kind (logo, car, fashion)"),
):
    """
    Detect brands/logos in an uploaded image.
    """
    try:
        image_bytes = await file.read()
        detections = predict_image_bytes(image_bytes, conf=conf, kind=kind)
        return {
            "filename": file.filename,
            "detections": detections,
            "count": len(detections),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brand detection failed: {e}")
