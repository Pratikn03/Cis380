from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split STT manifest into train/val/test.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/raw/stt/manifest.csv"),
        help="Input manifest CSV.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--train", type=float, default=0.8, help="Train split ratio.")
    parser.add_argument("--val", type=float, default=0.1, help="Validation split ratio.")
    parser.add_argument("--test", type=float, default=0.1, help="Test split ratio.")
    parser.add_argument(
        "--group-by",
        type=str,
        default="speaker_id",
        help="Group key to avoid leakage (default: speaker_id).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = args.manifest
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    rows: List[Dict[str, str]] = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise SystemExit("Manifest is empty.")

    group_key = args.group_by
    groups: Dict[str, List[int]] = {}
    for idx, row in enumerate(rows):
        group_value = row.get(group_key) or f"__row_{idx}"
        groups.setdefault(group_value, []).append(idx)

    random.seed(args.seed)
    group_ids = list(groups.keys())
    random.shuffle(group_ids)

    total = len(group_ids)
    n_train = int(total * args.train)
    n_val = int(total * args.val)
    train_groups = set(group_ids[:n_train])
    val_groups = set(group_ids[n_train : n_train + n_val])
    test_groups = set(group_ids[n_train + n_val :])

    splits = {}
    for group in train_groups:
        splits[group] = "train"
    for group in val_groups:
        splits[group] = "val"
    for group in test_groups:
        splits[group] = "test"

    for row in rows:
        group_value = row.get(group_key) or ""
        row["split"] = splits.get(group_value, "train")

    base_dir = manifest_path.parent
    out_path = base_dir / "manifest.with_splits.csv"
    train_path = base_dir / "manifest.train.csv"
    val_path = base_dir / "manifest.val.csv"
    test_path = base_dir / "manifest.test.csv"

    fieldnames = list(rows[0].keys())
    if "split" not in fieldnames:
        fieldnames.append("split")

    def write_rows(path: Path, data: List[Dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    write_rows(out_path, rows)
    write_rows(train_path, [r for r in rows if r["split"] == "train"])
    write_rows(val_path, [r for r in rows if r["split"] == "val"])
    write_rows(test_path, [r for r in rows if r["split"] == "test"])

    print(f"[split] wrote {out_path}")
    print(f"[split] train={train_path} val={val_path} test={test_path}")


if __name__ == "__main__":
    main()
