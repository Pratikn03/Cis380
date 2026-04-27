from __future__ import annotations

import json
import os
import random
import shutil
from pathlib import Path
from typing import Any

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _resolve_device(value: str | None) -> str:
    requested = (value or "auto").strip().lower()
    if requested != "auto":
        return requested
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "0"
    except Exception:
        pass
    return "cpu"


def _best_results_csv(run_dir: Path) -> dict[str, Any]:
    import csv

    path = run_dir / "results.csv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {}

    def score(row: dict[str, Any]) -> float:
        value = _float_metric(row, "metrics/accuracy_top1", "metrics/accuracy_top1(B)", "top1")
        return float(value) if value is not None else float("-inf")

    return max(rows, key=score)


def _pick_weight(run_dir: Path) -> Path:
    for candidate in (run_dir / "weights" / "best.pt", run_dir / "weights" / "last.pt"):
        if candidate.exists():
            return candidate
    matches = sorted(run_dir.rglob("best.pt"))
    if matches:
        return matches[-1]
    raise FileNotFoundError(f"No YOLO classification weights found under {run_dir}")


def _float_metric(row: dict[str, Any], *names: str) -> float | None:
    normalized = {"".join(ch.lower() for ch in key if ch.isalnum()): value for key, value in row.items()}
    for name in names:
        key = "".join(ch.lower() for ch in name if ch.isalnum())
        if key in normalized:
            try:
                return float(normalized[key])
            except (TypeError, ValueError):
                return None
    return None


def _link_or_copy(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    try:
        dest.symlink_to(source.resolve())
    except OSError:
        shutil.copy2(source, dest)


def _collect_split_images(split_dir: Path) -> dict[str, list[Path]]:
    classes: dict[str, list[Path]] = {}
    for class_dir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
        images = sorted(
            p
            for p in class_dir.rglob("*")
            if p.is_file()
            and not p.name.startswith("._")
            and p.suffix.lower() in _IMAGE_EXTS
        )
        if images:
            classes[class_dir.name] = images
    return classes


def _write_subset_split(
    *,
    source_split: Path,
    dest_split: Path,
    max_images: int,
    seed: int,
) -> None:
    if dest_split.exists():
        shutil.rmtree(dest_split)
    by_class = _collect_split_images(source_split)
    if not by_class:
        raise FileNotFoundError(f"No images found under {source_split}")
    per_class = max(1, int(max_images) // max(1, len(by_class))) if max_images > 0 else 0
    rng = random.Random(seed)
    for class_name, images in by_class.items():
        chosen = list(images)
        if per_class > 0 and len(chosen) > per_class:
            chosen = rng.sample(chosen, k=per_class)
        for idx, image in enumerate(chosen):
            dest = dest_split / class_name / f"{idx:06d}{image.suffix.lower()}"
            _link_or_copy(image, dest)
    for ghost in dest_split.rglob("._*"):
        ghost.unlink(missing_ok=True)


def _maybe_build_subset_data_dir(data_dir: Path, *, seed: int) -> Path:
    train_max = int(os.getenv("VISION_CLS_TRAIN_MAX_IMAGES", "0"))
    val_max = int(os.getenv("VISION_CLS_VAL_MAX_IMAGES", "0"))
    if train_max <= 0 and val_max <= 0:
        return data_dir

    subset_root = Path(".cache") / "vision_yolo_cls_subset"
    subset_root.mkdir(parents=True, exist_ok=True)
    if train_max > 0:
        _write_subset_split(
            source_split=data_dir / "train",
            dest_split=subset_root / "train",
            max_images=train_max,
            seed=seed,
        )
    else:
        _write_subset_split(
            source_split=data_dir / "train",
            dest_split=subset_root / "train",
            max_images=0,
            seed=seed,
        )
    if val_max > 0:
        _write_subset_split(
            source_split=data_dir / "val",
            dest_split=subset_root / "val",
            max_images=val_max,
            seed=seed + 1,
        )
    else:
        _write_subset_split(
            source_split=data_dir / "val",
            dest_split=subset_root / "val",
            max_images=0,
            seed=seed + 1,
        )
    return subset_root


def main() -> int:
    try:
        from ultralytics import YOLO, settings
    except Exception as exc:
        raise RuntimeError("ultralytics is required for YOLO classification training.") from exc

    try:
        settings.update(
            {
                "clearml": False,
                "comet": False,
                "dvc": False,
                "hub": False,
                "mlflow": False,
                "neptune": False,
                "raytune": False,
                "tensorboard": False,
                "wandb": False,
            }
        )
    except Exception as exc:
        print(f"[vision-yolo-cls] Could not disable Ultralytics callbacks: {exc}")

    data_dir = Path(os.getenv("VISION_CLS_DATA", "data/processed/vision"))
    if not (data_dir / "train").exists() or not (data_dir / "val").exists():
        raise FileNotFoundError(f"Expected ImageFolder train/val layout under {data_dir}")

    model_name = os.getenv("VISION_CLS_MODEL", "yolov8n-cls.pt")
    epochs = int(os.getenv("VISION_CLS_EPOCHS", "50"))
    imgsz = int(os.getenv("VISION_CLS_IMGSZ", "224"))
    batch = int(os.getenv("VISION_CLS_BATCH", "32"))
    workers = int(os.getenv("VISION_CLS_WORKERS", "0"))
    fraction = float(os.getenv("VISION_CLS_FRACTION", "1.0"))
    patience = int(os.getenv("VISION_CLS_PATIENCE", str(epochs)))
    seed = int(os.getenv("VISION_CLS_SEED", "42"))
    device = _resolve_device(os.getenv("VISION_CLS_DEVICE", "auto"))
    data_dir = _maybe_build_subset_data_dir(data_dir, seed=seed)

    model = YOLO(model_name)
    results = model.train(
        data=str(data_dir),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=workers,
        fraction=fraction,
        patience=patience,
        seed=seed,
        device=device,
        project="runs/classify",
        name="sentifargo_realfake",
        exist_ok=True,
        verbose=False,
        plots=False,
    )
    run_dir = Path(getattr(results, "save_dir", "runs/classify/sentifargo_realfake"))
    weight = _pick_weight(run_dir)
    out_dir = Path("models/vision/yolo_cls")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "best.pt"
    shutil.copy2(weight, out_path)

    export_paths: list[str] = []
    try:
        exported = model.export(format="onnx", int8=False)
        if exported:
            export_paths.append(str(exported))
    except Exception as exc:
        print(f"[vision-yolo-cls] ONNX export skipped: {exc}")
    try:
        exported = model.export(format="onnx", int8=True)
        if exported:
            export_paths.append(str(exported))
    except Exception as exc:
        print(f"[vision-yolo-cls] INT8 export skipped: {exc}")

    row = _best_results_csv(run_dir)
    top1 = _float_metric(row, "metrics/accuracy_top1", "metrics/accuracy_top1(B)", "top1")
    top5 = _float_metric(row, "metrics/accuracy_top5", "top5")
    accuracy = top1 if top1 is not None else 0.0
    metrics = {
        "accuracy": float(accuracy),
        "f1": float(accuracy),
        "roc_auc": float(accuracy),
        "top1": float(accuracy),
        "top5": float(top5) if top5 is not None else None,
        "model": model_name,
        "epochs": epochs,
        "fraction": fraction,
        "artifact": str(out_path),
        "exports": export_paths,
    }
    metrics = {key: value for key, value in metrics.items() if value is not None}
    metrics_path = Path("experiments/vision/metrics/metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"[vision-yolo-cls] saved weights: {out_path}")
    print(f"[vision-yolo-cls] wrote metrics: {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
