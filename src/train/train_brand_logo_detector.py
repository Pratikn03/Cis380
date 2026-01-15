from __future__ import annotations

import os
import random
import shutil
from pathlib import Path
from typing import Any


def _resolve_device(requested: str | None) -> str:
    req = (requested or "").strip()
    if not req or req.lower() == "auto":
        try:  # pragma: no cover - depends on local hardware
            import torch

            if torch.backends.mps.is_available():
                return "mps"
            if torch.cuda.is_available():
                return "0"
        except Exception:
            pass
        return "cpu"
    return req


def _parse_bool(value: str | None, *, default: bool) -> bool:
    v = (value or "").strip().lower()
    if not v:
        return default
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    raise ValueError("Expected a boolean value (true/false/1/0).")


def _parse_cache(value: str | None) -> bool | str:
    v = (value or "").strip().lower()
    if not v or v in {"0", "false", "no", "off"}:
        return False
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"ram", "disk"}:
        return v
    raise ValueError("BRAND_CACHE must be one of: true|false|ram|disk")


_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def _resolve_split_paths(value: object, *, base_path: Path) -> list[Path]:
    def _one(v: object) -> Path:
        p = Path(str(v)).expanduser()
        return p if p.is_absolute() else base_path / p

    if isinstance(value, (list, tuple)):
        return [_one(v) for v in value]
    return [_one(value)]


def _read_image_list_file(path: Path, *, base_path: Path) -> list[Path]:
    images: list[Path] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        p = Path(s).expanduser()
        images.append(p if p.is_absolute() else base_path / p)
    return images


def _collect_images(roots: list[Path], *, base_path: Path) -> list[Path]:
    images: list[Path] = []
    for root in roots:
        if root.is_file():
            images.extend(_read_image_list_file(root, base_path=base_path))
            continue
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in _IMAGE_EXTS:
                images.append(p)
    return images


def _maybe_build_subset_yaml(
    *,
    data_yaml: Path,
    out_dir: Path,
    seed: int,
    train_max_images: int,
    val_max_images: int,
) -> Path:
    if train_max_images <= 0 and val_max_images <= 0:
        return data_yaml

    try:
        import yaml
    except Exception as exc:  # pragma: no cover - ultralytics depends on PyYAML anyway
        raise RuntimeError(f"Missing PyYAML dependency: {exc}") from exc

    cfg = yaml.safe_load(data_yaml.read_text(encoding="utf-8")) or {}
    base_path = Path(cfg.get("path") or data_yaml.parent).expanduser()

    if "train" not in cfg:
        raise ValueError(f"Dataset YAML missing required key 'train': {data_yaml}")

    train_roots = _resolve_split_paths(cfg["train"], base_path=base_path)
    val_key = "val" if "val" in cfg else ("test" if "test" in cfg else None)
    val_roots: list[Path] = []
    if val_key is not None:
        val_roots = _resolve_split_paths(cfg[val_key], base_path=base_path)

    rng = random.Random(int(seed))

    subset_cfg = dict(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)

    if train_max_images > 0:
        train_images = _collect_images(train_roots, base_path=base_path)
        if not train_images:
            raise FileNotFoundError(f"No train images found under: {train_roots}")
        if train_max_images < len(train_images):
            train_images = rng.sample(train_images, k=int(train_max_images))
        train_list = out_dir / f"brands_train_{len(train_images)}_seed{seed}.txt"
        train_list.write_text("\n".join(str(p) for p in train_images) + "\n", encoding="utf-8")
        subset_cfg["train"] = str(train_list)

    if val_key is not None and val_max_images > 0:
        val_images = _collect_images(val_roots, base_path=base_path)
        if not val_images:
            raise FileNotFoundError(f"No val images found under: {val_roots}")
        if val_max_images < len(val_images):
            val_images = rng.sample(val_images, k=int(val_max_images))
        val_list = out_dir / f"brands_val_{len(val_images)}_seed{seed}.txt"
        val_list.write_text("\n".join(str(p) for p in val_images) + "\n", encoding="utf-8")
        subset_cfg[val_key] = str(val_list)

    subset_yaml = out_dir / "brands_subset.yaml"
    subset_yaml.write_text(yaml.safe_dump(subset_cfg, sort_keys=False), encoding="utf-8")
    return subset_yaml


def _pick_checkpoint(run_dir: Path) -> Path:
    preferred = [run_dir / "weights" / "best.pt", run_dir / "weights" / "last.pt"]
    for p in preferred:
        if p.exists():
            return p

    best = [p for p in run_dir.rglob("best.pt") if p.is_file()]
    if best:
        return max(best, key=lambda p: p.stat().st_mtime)

    last = [p for p in run_dir.rglob("last.pt") if p.is_file()]
    if last:
        return max(last, key=lambda p: p.stat().st_mtime)

    raise FileNotFoundError(f"Could not find best.pt/last.pt under {run_dir}.")


def main() -> int:
    """Train a YOLOv8 logo/brand detector on the prepared YOLO dataset."""
    try:
        from ultralytics import YOLO
    except Exception as exc:
        raise RuntimeError(
            "ultralytics is not installed. Install dependencies from requirements.txt (ultralytics>=8.2.0)."
        ) from exc

    project_root = Path(__file__).resolve().parents[2]
    data_yaml = Path(
        os.getenv(
            "BRAND_DATA_YAML",
            project_root / "data" / "processed" / "brand_yolo" / "brands.yaml",
        )
    )
    if not data_yaml.exists():
        raise FileNotFoundError(
            f"Missing YOLO dataset config at {data_yaml}. Run scripts/prepare_brand_data.py first."
        )

    model_name = os.getenv("BRAND_YOLO_MODEL", "yolov8s.pt")
    epochs = int(os.getenv("BRAND_EPOCHS", "50"))
    imgsz = int(os.getenv("BRAND_IMGSZ", "640"))
    batch = int(os.getenv("BRAND_BATCH", "16"))
    workers = int(os.getenv("BRAND_WORKERS", "4"))
    device = _resolve_device(os.getenv("BRAND_DEVICE", "auto"))
    cache = _parse_cache(os.getenv("BRAND_CACHE", "false"))
    fraction = float(os.getenv("BRAND_FRACTION", "1.0"))
    patience = int(os.getenv("BRAND_PATIENCE", "100"))
    val_enabled = _parse_bool(os.getenv("BRAND_VAL"), default=True)
    seed = int(os.getenv("BRAND_SEED", "42"))
    train_max_images = int(os.getenv("BRAND_TRAIN_MAX_IMAGES", "0"))
    val_max_images = int(os.getenv("BRAND_VAL_MAX_IMAGES", "0"))

    if not (0.0 < fraction <= 1.0):
        raise ValueError("BRAND_FRACTION must be between (0.0, 1.0].")

    subset_dir = project_root / "artifacts" / "brand" / "_dataset_subsets"
    data_yaml = _maybe_build_subset_yaml(
        data_yaml=data_yaml,
        out_dir=subset_dir,
        seed=seed,
        train_max_images=train_max_images,
        val_max_images=val_max_images,
    )

    model = YOLO(model_name)
    train_kwargs: dict[str, Any] = {
        "data": str(data_yaml),
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "device": device,
        "workers": workers,
        "cache": cache,
        "fraction": fraction,
        "patience": patience,
        "val": val_enabled,
    }

    print(
        "[brand_yolo] config:",
        {
            "model": model_name,
            "data": str(data_yaml),
            "epochs": epochs,
            "imgsz": imgsz,
            "batch": batch,
            "device": device,
            "workers": workers,
            "cache": cache,
            "fraction": fraction,
            "patience": patience,
            "val": val_enabled,
            "seed": seed,
            "train_max_images": train_max_images,
            "val_max_images": val_max_images,
        },
    )

    results = None
    try:
        results = model.train(**train_kwargs)
    except KeyboardInterrupt:  # pragma: no cover
        print("\n[brand_yolo] Training interrupted. Attempting to export the latest checkpoint…")

    # Locate best.pt in ultralytics run directory.
    run_dir: Path | None = None
    if results is not None:
        try:
            run_dir = Path(results.save_dir)  # type: ignore[attr-defined]
        except Exception:
            run_dir = None
    if run_dir is None:
        detect_root = project_root / "runs" / "detect"
        candidates = [p for p in detect_root.iterdir()] if detect_root.exists() else []
        run_dir = max(
            (p for p in candidates if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            default=detect_root,
        )

    ckpt_path = _pick_checkpoint(run_dir)
    out_dir = project_root / "artifacts" / "brand"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(os.getenv("BRAND_OUT_PATH", str(out_dir / "yolo_logo_det.pt")))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ckpt_path, out_path)

    print(f"Saved YOLO weights to: {out_path} (from: {ckpt_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
