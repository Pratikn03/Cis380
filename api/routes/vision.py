from __future__ import annotations

from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.deps import require_auth
from uais.vision.train_vision_model import IMAGE_EXTENSIONS, VisionConfig, run_vision_experiment

router = APIRouter(prefix="/api/vision", tags=["vision"], dependencies=[Depends(require_auth)])

DEFAULT_DATASET = (
    "data/raw/vision/datasets/puneet6060/intel-image-classification/versions/2/seg_train/seg_train"
)


class VisionRequest(BaseModel):
    dataset_dir: str = Field(
        DEFAULT_DATASET,
        description="Relative path to an image classification dataset organized in class folders.",
    )
    run_experiment: bool = Field(
        False,
        description="Set to true to train a quick vision experiment using TensorFlow (may take longer).",
    )
    image_size: int = Field(128, gt=0, description="Height/width to resize images to.")
    batch_size: int = Field(32, gt=0, description="Batch size used during training when running experiments.")
    epochs: int = Field(1, gt=0, description="Number of epochs when running the optional experiment.")
    validation_split: float = Field(
        0.2,
        gt=0.0,
        lt=1.0,
        description="Validation split used when running the optional experiment.",
    )
    backbone: str = Field("simple_cnn", description="Backbone model for the optional experiment.")


def _summarize_classes(dataset_root: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for entry in dataset_root.iterdir():
        if not entry.is_dir():
            continue
        class_name = entry.name
        for img in entry.rglob("*"):
            if not img.is_file():
                continue
            if img.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            counts[class_name] += 1
    return dict(counts)


@router.post("/train")
def vision_experiment(req: VisionRequest):
    cfg = VisionConfig(
        dataset_dir=req.dataset_dir,
        image_size=req.image_size,
        batch_size=req.batch_size,
        epochs=req.epochs,
        validation_split=req.validation_split,
        backbone=req.backbone,
    )

    try:
        dataset_root = cfg.resolve_dir()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset directory not found: {req.dataset_dir}",
        ) from exc

    class_summary = _summarize_classes(dataset_root)
    payload = {
        "dataset_root": str(dataset_root),
        "class_counts": class_summary,
        "total_images": sum(class_summary.values()),
        "preview_message": "Vision dataset summary ready. Set run_experiment=true to train a small model.",
    }

    if req.run_experiment:
        try:
            metrics = run_vision_experiment(cfg)
        except Exception as exc:  # pragma: no cover - runtime errors bubbled to caller
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Vision experiment failed: {exc}",
            ) from exc
        payload["metrics"] = metrics
        payload["preview_message"] = "Vision experiment completed successfully."

    return payload
