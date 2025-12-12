"""Train a simple fusion meta-model stacking domain scores."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

EXP_DIR = Path("experiments")
OUT_MODEL = Path("experiments/fusion/models/fusion_meta_model.pkl")
OUT_METRICS = Path("experiments/fusion/metrics/metrics.json")


def _load_scores() -> pd.DataFrame:
    """Try to load fusion_scores.csv; otherwise build from domain scores."""
    fusion_path = EXP_DIR / "fusion/fusion_scores.csv"
    if fusion_path.exists():
        try:
            return pd.read_csv(fusion_path)
        except Exception:
            pass

    # fallback: merge fraud/cyber/behavior scores if available
    dfs = []
    fraud = EXP_DIR / "fraud/scores.csv"
    cyber = EXP_DIR / "cyber/scores.csv"
    beh = EXP_DIR / "behavior/scores.csv"

    base = pd.DataFrame()
    if fraud.exists():
        try:
            fdf = pd.read_csv(fraud)
            fcol = next((c for c in ["supervised_score", "y_score", "prob_1"] if c in fdf), None)
            lcol = next((c for c in ["label", "y_true", "target"] if c in fdf), None)
            if fcol and lcol:
                base["fraud_score"] = fdf[fcol].astype(float)
                base["label"] = fdf[lcol].astype(int)
        except Exception:
            pass
    if cyber.exists():
        try:
            cdf = pd.read_csv(cyber)
            ccol = next((c for c in ["supervised_score", "y_score", "prob_1"] if c in cdf), None)
            if ccol:
                base["cyber_score"] = cdf[ccol].astype(float).reindex(base.index, fill_value=0)
        except Exception:
            pass
    if beh.exists():
        try:
            bdf = pd.read_csv(beh)
            bcol = next((c for c in ["anomaly_score", "lof_score", "score"] if c in bdf), None)
            if bcol:
                base["behavior_score"] = bdf[bcol].astype(float).reindex(base.index, fill_value=0)
        except Exception:
            pass

    # fill missing
    for col in ["fraud_score", "cyber_score", "behavior_score"]:
        if col not in base:
            base[col] = 0.0
    if "label" not in base:
        base["label"] = np.where(base["fraud_score"] > 0.8, 1, 0)

    base["fusion_score"] = base[["fraud_score", "cyber_score", "behavior_score"]].mean(axis=1)
    return base


def main():
    df = _load_scores()
    features = [c for c in df.columns if c != "label"]
    X = df[features].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = GradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, OUT_MODEL)

    OUT_METRICS.parent.mkdir(parents=True, exist_ok=True)
    with OUT_METRICS.open("w") as f:
        json.dump(report, f, indent=2)

    print(f"Saved fusion meta-model to {OUT_MODEL}")
    print(f"Metrics written to {OUT_METRICS}")


if __name__ == "__main__":
    main()
