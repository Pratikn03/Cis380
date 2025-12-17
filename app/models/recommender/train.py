from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from app.models.recommender.features import default_items, preprocess_items

MODEL_PATH = Path("models/recommender.pkl")
DATA_ROOT = Path("data/raw/recommender")


def _load_raw_files(root: Path) -> pd.DataFrame:
    files = sorted(root.glob("*.csv"))
    frames: list[pd.DataFrame] = []
    for csv in files:
        try:
            df = pd.read_csv(csv)
        except Exception:
            continue
        df["source_file"] = csv.name
        frames.append(df)
    if not frames:
        return default_items()
    return pd.concat(frames, ignore_index=True)


def build_model(matrix: any, items: pd.DataFrame, vectorizer: TfidfVectorizer) -> dict[str, any]:
    return {"matrix": matrix, "items": items, "vectorizer": vectorizer}


def train(data_root: Path | None = None) -> dict[str, any]:
    root = data_root or DATA_ROOT
    raw = _load_raw_files(root)
    processed = preprocess_items(raw)
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    matrix = vectorizer.fit_transform(processed["metadata"])
    model = build_model(matrix=matrix, items=processed, vectorizer=vectorizer)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH, compress=3)
    return model


def build_model_from_items(items: pd.DataFrame) -> dict[str, any]:
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    matrix = vectorizer.fit_transform(items["metadata"])
    return build_model(matrix=matrix, items=items, vectorizer=vectorizer)


if __name__ == "__main__":
    model = train()
    print(f"Saved recommender with {model['items'].shape[0]} items to {MODEL_PATH}")
