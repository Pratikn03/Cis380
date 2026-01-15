import argparse
import json
import random
from pathlib import Path


def _split_csv(*, csv_path: Path, out_dir: Path, seed: int, train: float, val: float) -> None:
    try:
        import pandas as pd
    except Exception as exc:
        raise SystemExit(f"Missing pandas for CSV splitting: {exc}") from exc

    df = pd.read_csv(csv_path)
    if df.empty:
        raise SystemExit(f"CSV is empty: {csv_path}")

    df = df.sample(frac=1.0, random_state=int(seed)).reset_index(drop=True)
    n = len(df)
    n_train = int(n * train)
    n_val = int(n * val)

    train_df = df.iloc[:n_train]
    val_df = df.iloc[n_train:n_train + n_val]
    test_df = df.iloc[n_train + n_val:]

    train_path = out_dir / "train.csv"
    val_path = out_dir / "val.csv"
    test_path = out_dir / "test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    splits = {
        "train": str(train_path),
        "val": str(val_path),
        "test": str(test_path),
        "seed": seed,
        "rows": {"total": n, "train": len(train_df), "val": len(val_df), "test": len(test_df)},
    }
    (out_dir / "splits.json").write_text(json.dumps(splits, indent=2))
    print(
        f"[OK] wrote splits: {out_dir / 'splits.json'} | n={n} train={len(train_df)} "
        f"val={len(val_df)} test={len(test_df)}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=["tabular", "vision", "audio", "docs"])
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--train", type=float, default=0.8)
    ap.add_argument("--val", type=float, default=0.1)
    ap.add_argument("--test", type=float, default=0.1)
    ap.add_argument("--root", default="data/raw")
    ap.add_argument("--path", default=None, help="Override dataset path (file or directory).")
    args = ap.parse_args()

    random.seed(args.seed)

    if args.path:
        raw = Path(args.path)
    else:
        raw = Path(args.root) / args.task / args.dataset

    out = Path("data/splits") / args.task / args.dataset
    out.mkdir(parents=True, exist_ok=True)

    if raw.is_file():
        if raw.suffix.lower() != ".csv":
            raise SystemExit(f"Expected a CSV file for tabular splits: {raw}")
        _split_csv(
            csv_path=raw,
            out_dir=out,
            seed=int(args.seed),
            train=float(args.train),
            val=float(args.val),
        )
        return

    files = [str(p) for p in raw.rglob("*") if p.is_file()]
    files.sort()
    random.shuffle(files)

    n = len(files)
    n_train = int(n * args.train)
    n_val = int(n * args.val)
    train = files[:n_train]
    val = files[n_train:n_train + n_val]
    test = files[n_train + n_val:]

    splits = {"train": train, "val": val, "test": test, "seed": args.seed}
    (out / "splits.json").write_text(json.dumps(splits, indent=2))
    print(
        f"[OK] wrote splits: {out / 'splits.json'} | n={n} train={len(train)} "
        f"val={len(val)} test={len(test)}"
    )


if __name__ == "__main__":
    main()
