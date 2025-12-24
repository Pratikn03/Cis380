"""
Feature builder for MovieLens-style data.
- Input: data/raw/recommendation/movielens.csv with columns userId,movieId,rating
- Output: features dataframe with user/item stats and labels (rating>=4 -> 1)
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "recommendation" / "movielens.csv"


def load_movielens() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} not found. Expected columns userId,movieId,rating")
    df = pd.read_csv(DATA_PATH)
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
    df = df.copy()
    df["label"] = (df["rating"] >= 4.0).astype(int)

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
        "items": df["movieId"].unique().tolist(),
    }
    return X, y, meta


if __name__ == "__main__":
    df = load_movielens()
    X, y, meta = build_features(df)
    print("Built features:", X.shape, "labels:", y.shape)
