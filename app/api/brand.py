"""
Brand recognition API endpoints.
"""

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

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
        import io

        from PIL import Image

        from src.vision.brand.recognizer import model_path, predict_image_bytes

        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        detections = predict_image_bytes(image_bytes, conf=conf, kind=kind)
        return {
            "filename": file.filename,
            "kind": kind,
            "confidence_threshold": conf,
            "model_path": model_path(kind),
            "image": {"width": width, "height": height},
            "detections": detections,
            "count": len(detections),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brand detection failed: {e}")
