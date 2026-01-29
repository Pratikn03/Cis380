"""Train a simple MovieLens-style recommender classifier (implicit: rating>=4).

Note: `movielens.csv` can be very large (20M+ rows). By default this script trains
on a sample for safety; pass `--sample-size 0` to use the full file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pickle
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

DATA_PATH = Path("data/raw/recommendation/movielens.csv")
MODEL_PATH = Path("models/recommender/movielens_model.pkl")
META_PATH = Path("models/recommender/movielens_meta.joblib")
METRICS_PATH = Path("experiments/recommender/metrics/movielens_metrics.json")


def load_data(*, sample_size: int = 200_000) -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} not found. Place a CSV with columns userId,movieId,rating under data/raw/recommendation/."
        )
    if sample_size and sample_size > 0:
        df = pd.read_csv(DATA_PATH, nrows=sample_size)
        print(f"Loaded MovieLens sample: {len(df):,} rows (first rows from file)")
    else:
        df = pd.read_csv(DATA_PATH)
        print(f"Loaded full MovieLens: {len(df):,} rows")
    # normalize column names
    cols = {c.lower(): c for c in df.columns}
    user_col = cols.get("userid", "userId")
    item_col = cols.get("movieid", "movieId")
    rating_col = cols.get("rating", "rating")
    for col in (user_col, item_col, rating_col):
        if col not in df:
            raise ValueError(f"Missing required column {col} in {DATA_PATH}")
    df = df.rename(columns={user_col: "userId", item_col: "movieId", rating_col: "rating"})
    return df[["userId", "movieId", "rating"]]


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict]:
    df["label"] = (df["rating"] >= 4.0).astype(int)

    # aggregates
    user_stats = (
        df.groupby("userId")["rating"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "user_mean", "count": "user_count"})
    )
    item_stats = (
        df.groupby("movieId")["rating"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "item_mean", "count": "item_count"})
    )
    global_mean = df["rating"].mean()

    df = df.join(user_stats, on="userId").join(item_stats, on="movieId")
    df["global_mean"] = global_mean

    # simple dense encodings for ids
    df["user_code"] = df["userId"].astype("category").cat.codes
    df["item_code"] = df["movieId"].astype("category").cat.codes

    features = [
        "user_mean",
        "item_mean",
        "user_count",
        "item_count",
        "global_mean",
        "user_code",
        "item_code",
    ]
    X = df[features]
    y = df["label"]

    meta = {
        "user_stats": user_stats,
        "item_stats": item_stats,
        "global_mean": global_mean,
        "user_codes": dict(zip(df["userId"], df["user_code"])),
        "item_codes": dict(zip(df["movieId"], df["item_code"])),
        "feature_names": features,
    }
    return X, y, meta


def train(*, sample_size: int = 200_000):
    df = load_data(sample_size=sample_size)
    X, y, meta = build_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    model = GradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(META_PATH, "wb") as f:
        pickle.dump(meta, f)

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w") as f:
        json.dump(report, f, indent=2)

    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved meta to {META_PATH}")
    print(f"Metrics -> {METRICS_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train a MovieLens recommender (rating>=4 -> like)."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=200_000,
        help="Row count to load for faster training; 0 uses the full dataset.",
    )
    args = parser.parse_args()
    train(sample_size=args.sample_size)
