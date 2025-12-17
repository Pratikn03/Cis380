from __future__ import annotations

import os
import shutil
from pathlib import Path


def main() -> int:
    """Train a YOLOv8 logo/brand detector on the prepared YOLO dataset."""
    try:
        from ultralytics import YOLO
    except Exception as exc:
        raise RuntimeError(
            "ultralytics is not installed. Install dependencies from requirements.txt (ultralytics>=8.2.0)."
        ) from exc

    project_root = Path(__file__).resolve().parents[2]
    data_yaml = project_root / "data" / "processed" / "brand_yolo" / "brands.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(
            f"Missing YOLO dataset config at {data_yaml}. Run scripts/prepare_brand_data.py first."
        )

    model_name = os.getenv("BRAND_YOLO_MODEL", "yolov8s.pt")
    epochs = int(os.getenv("BRAND_EPOCHS", "50"))
    imgsz = int(os.getenv("BRAND_IMGSZ", "640"))
    batch = int(os.getenv("BRAND_BATCH", "16"))
    device = os.getenv("BRAND_DEVICE", "cpu")
    workers = int(os.getenv("BRAND_WORKERS", "4"))

    model = YOLO(model_name)
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        workers=workers,
    )

    # Locate best.pt in ultralytics run directory.
    run_dir = None
    try:
        run_dir = Path(results.save_dir)  # type: ignore[attr-defined]
    except Exception:
        pass
    if run_dir is None:
        # default location
        run_dir = project_root / "runs" / "detect"

    best_candidates = list(run_dir.rglob("best.pt"))
    if not best_candidates:
        raise FileNotFoundError(f"Could not find best.pt under {run_dir}. Training may have failed.")

    best_path = sorted(best_candidates, key=lambda p: len(str(p)))[0]
    out_dir = project_root / "artifacts" / "brand"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "yolo_logo_det.pt"
    shutil.copy2(best_path, out_path)

    print(f"Saved best weights to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
