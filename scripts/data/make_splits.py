from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


LABEL_CANDIDATES = (
    "label",
    "Class",
    "class",
    "target",
    "isFraud",
    "isfraud",
    "Revenue",
    "rating",
)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def _find_label_column(columns: list[str], requested: str | None = None) -> str | None:
    if requested and requested in columns:
        return requested
    lower = {col.lower(): col for col in columns}
    for candidate in LABEL_CANDIDATES:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def _split_lists(
    items: list[Any],
    *,
    labels: list[Any] | None,
    seed: int,
    train: float,
    val: float,
) -> tuple[list[Any], list[Any], list[Any]]:
    if not items:
        return [], [], []
    if labels is not None and len(set(labels)) > 1:
        try:
            from sklearn.model_selection import train_test_split

            train_items, temp_items, _train_y, temp_y = train_test_split(
                items,
                labels,
                train_size=train,
                random_state=int(seed),
                stratify=labels,
            )
            val_share = val / max(1.0 - train, 1e-12)
            val_items, test_items = train_test_split(
                temp_items,
                train_size=val_share,
                random_state=int(seed),
                stratify=temp_y if len(set(temp_y)) > 1 else None,
            )
            return list(train_items), list(val_items), list(test_items)
        except Exception:
            pass

    rng = random.Random(int(seed))
    shuffled = list(items)
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * train)
    n_val = int(n * val)
    return shuffled[:n_train], shuffled[n_train : n_train + n_val], shuffled[n_train + n_val :]


def _split_csv(
    *,
    csv_path: Path,
    out_dir: Path,
    seed: int,
    train: float,
    val: float,
    label_col: str | None = None,
    manifest_path: Path | None = None,
) -> None:
    try:
        import pandas as pd
    except Exception as exc:
        raise SystemExit(f"Missing pandas for CSV splitting: {exc}") from exc

    df = pd.read_csv(csv_path)
    if df.empty:
        raise SystemExit(f"CSV is empty: {csv_path}")

    df = df.reset_index(drop=False).rename(columns={"index": "_source_row"})
    exclusions: list[dict[str, Any]] = []
    duplicate_mask = df.drop(columns=["_source_row"]).duplicated(keep="first")
    if duplicate_mask.any():
        for row in df.loc[duplicate_mask, "_source_row"].astype(int).tolist():
            exclusions.append({"row": row, "reason": "duplicate"})
        df = df.loc[~duplicate_mask].reset_index(drop=True)

    label = _find_label_column([c for c in df.columns if c != "_source_row"], label_col)
    labels = df[label].astype(str).tolist() if label else None
    row_ids = df["_source_row"].astype(int).tolist()
    train_ids, val_ids, test_ids = _split_lists(
        row_ids, labels=labels, seed=seed, train=train, val=val
    )
    train_set = set(train_ids)
    val_set = set(val_ids)
    test_set = set(test_ids)

    train_df = df[df["_source_row"].isin(train_set)].drop(columns=["_source_row"])
    val_df = df[df["_source_row"].isin(val_set)].drop(columns=["_source_row"])
    test_df = df[df["_source_row"].isin(test_set)].drop(columns=["_source_row"])

    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "train.csv"
    val_path = out_dir / "val.csv"
    test_path = out_dir / "test.csv"
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    splits = {
        "domain": out_dir.name,
        "source": str(csv_path),
        "seed": int(seed),
        "strategy": "stratified" if labels is not None else "shuffled",
        "label_column": label,
        "ratios": {"train": train, "val": val, "test": round(1.0 - train - val, 6)},
        "train": train_ids,
        "val": val_ids,
        "test": test_ids,
        "paths": {"train": str(train_path), "val": str(val_path), "test": str(test_path)},
        "rows": {
            "total": int(len(df)),
            "train": int(len(train_df)),
            "val": int(len(val_df)),
            "test": int(len(test_df)),
            "excluded": int(len(exclusions)),
        },
        "exclusions": exclusions,
    }
    (out_dir / "splits.json").write_text(json.dumps(splits, indent=2), encoding="utf-8")
    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(splits, indent=2), encoding="utf-8")
        (manifest_path.parent / f"{manifest_path.stem}_exclusions.json").write_text(
            json.dumps(exclusions, indent=2), encoding="utf-8"
        )
    print(
        f"[OK] wrote splits: {out_dir / 'splits.json'} | n={len(df)} train={len(train_df)} "
        f"val={len(val_df)} test={len(test_df)} excluded={len(exclusions)}"
    )


def _class_label_from_path(path: Path, root: Path) -> str | None:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return None
    return rel.parts[0] if len(rel.parts) > 1 else None


def _is_readable(path: Path, task: str) -> bool:
    try:
        if task == "vision" and path.suffix.lower() in IMAGE_EXTS:
            from PIL import Image

            with Image.open(path) as image:
                image.verify()
        elif task == "audio" and path.suffix.lower() == ".wav":
            import wave

            with wave.open(str(path), "rb"):
                pass
        else:
            with path.open("rb") as handle:
                handle.read(1)
        return True
    except Exception:
        return False


def _split_files(
    *,
    raw: Path,
    out_dir: Path,
    task: str,
    seed: int,
    train: float,
    val: float,
    manifest_path: Path | None = None,
) -> None:
    files = sorted(path for path in raw.rglob("*") if path.is_file())
    exclusions: list[dict[str, Any]] = []
    kept: list[str] = []
    seen_keys: set[tuple[str, int]] = set()
    for path in files:
        rel = str(path)
        if not _is_readable(path, task):
            exclusions.append({"path": rel, "reason": "corrupt_or_unreadable"})
            continue
        key = (path.name, path.stat().st_size)
        if key in seen_keys:
            exclusions.append({"path": rel, "reason": "duplicate_name_size"})
            continue
        seen_keys.add(key)
        kept.append(rel)

    labels = [_class_label_from_path(Path(item), raw) for item in kept]
    label_values = labels if any(label is not None for label in labels) else None
    train_items, val_items, test_items = _split_lists(
        kept, labels=label_values, seed=seed, train=train, val=val
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    splits = {
        "domain": out_dir.name,
        "source": str(raw),
        "seed": int(seed),
        "strategy": "stratified" if label_values is not None else "shuffled",
        "ratios": {"train": train, "val": val, "test": round(1.0 - train - val, 6)},
        "train": train_items,
        "val": val_items,
        "test": test_items,
        "rows": {
            "total": len(kept),
            "train": len(train_items),
            "val": len(val_items),
            "test": len(test_items),
            "excluded": len(exclusions),
        },
        "exclusions": exclusions,
    }
    (out_dir / "splits.json").write_text(json.dumps(splits, indent=2), encoding="utf-8")
    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(splits, indent=2), encoding="utf-8")
        (manifest_path.parent / f"{manifest_path.stem}_exclusions.json").write_text(
            json.dumps(exclusions, indent=2), encoding="utf-8"
        )
    print(
        f"[OK] wrote splits: {out_dir / 'splits.json'} | n={len(kept)} "
        f"train={len(train_items)} val={len(val_items)} test={len(test_items)} "
        f"excluded={len(exclusions)}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=["tabular", "vision", "audio", "docs"])
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--domain", default=None, help="Canonical domain name for data/splits/<domain>.json.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--train", type=float, default=0.7)
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--test", type=float, default=0.15)
    ap.add_argument("--root", default="data/raw")
    ap.add_argument("--path", default=None, help="Override dataset path (file or directory).")
    ap.add_argument("--label-col", default=None)
    args = ap.parse_args()

    if abs((args.train + args.val + args.test) - 1.0) > 1e-6:
        raise SystemExit("--train + --val + --test must equal 1.0")

    random.seed(args.seed)

    raw = Path(args.path) if args.path else Path(args.root) / args.dataset
    if not raw.exists() and not args.path:
        legacy = Path(args.root) / args.task / args.dataset
        raw = legacy

    domain = args.domain or args.dataset
    out = Path("data/splits") / args.task / args.dataset
    manifest_path = Path("data/splits") / f"{domain}.json"

    if raw.is_file():
        if raw.suffix.lower() not in {".csv", ".tsv"}:
            raise SystemExit(f"Expected a CSV/TSV file for tabular splits: {raw}")
        _split_csv(
            csv_path=raw,
            out_dir=out,
            seed=int(args.seed),
            train=float(args.train),
            val=float(args.val),
            label_col=args.label_col,
            manifest_path=manifest_path,
        )
        return

    _split_files(
        raw=raw,
        out_dir=out,
        task=args.task,
        seed=int(args.seed),
        train=float(args.train),
        val=float(args.val),
        manifest_path=manifest_path,
    )


if __name__ == "__main__":
    main()
