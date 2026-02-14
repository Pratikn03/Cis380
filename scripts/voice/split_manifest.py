from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


def _split_by_speaker(
    df: pd.DataFrame,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
    max_attempts: int = 25,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
    speakers = df["speaker_id"].astype(str)
    for attempt in range(max_attempts):
        gss = GroupShuffleSplit(n_splits=1, train_size=train_ratio, random_state=seed + attempt)
        train_idx, temp_idx = next(gss.split(df, groups=speakers))
        train_df = df.iloc[train_idx]
        temp_df = df.iloc[temp_idx]

        temp_speakers = temp_df["speaker_id"].astype(str)
        val_share = val_ratio / max(1e-6, (val_ratio + test_ratio))
        gss2 = GroupShuffleSplit(n_splits=1, train_size=val_share, random_state=seed + attempt)
        val_idx, test_idx = next(gss2.split(temp_df, groups=temp_speakers))
        val_df = temp_df.iloc[val_idx]
        test_df = temp_df.iloc[test_idx]

        labels = set(df["label"].unique())
        if labels.issubset(set(train_df["label"])) and labels.issubset(set(val_df["label"])) and labels.issubset(
            set(test_df["label"])
        ):
            return train_df, val_df, test_df

    return train_df, val_df, test_df


def _stats(df: pd.DataFrame) -> dict[str, object]:
    return {
        "rows": len(df),
        "labels": df["label"].value_counts().to_dict(),
        "speakers": df["speaker_id"].nunique(),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Speaker‑independent split of voice manifest.")
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=Path("data/raw/voice"))
    ap.add_argument("--train-ratio", type=float, default=0.8)
    ap.add_argument("--val-ratio", type=float, default=0.1)
    ap.add_argument("--test-ratio", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = pd.read_csv(args.manifest)
    if "speaker_id" not in df.columns:
        raise SystemExit("manifest missing required column: speaker_id")

    train_df, val_df, test_df = _split_by_speaker(
        df, args.train_ratio, args.val_ratio, args.test_ratio, args.seed
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.out_dir / "manifest.train.csv"
    val_path = args.out_dir / "manifest.val.csv"
    test_path = args.out_dir / "manifest.test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    summary = {
        "train": _stats(train_df),
        "val": _stats(val_df),
        "test": _stats(test_df),
    }
    stats_path = args.out_dir / "manifest.split.summary.json"
    stats_path.write_text(json.dumps(summary, indent=2))

    print(f"[split] train={len(train_df)} val={len(val_df)} test={len(test_df)}")
    print(f"[split] summary -> {stats_path}")


if __name__ == "__main__":
    main()
