"""Train a simple recommender/meta-action classifier from existing scores."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


EXP_DIR = Path("experiments")
OUT_MODEL = Path("models/recommender/recommender_model.pkl")
OUT_METRICS = EXP_DIR / "recommender/metrics/metrics.json"
OUT_EXP_DIR = EXP_DIR / "recommender"


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _from_fusion() -> pd.DataFrame:
    fusion_path = EXP_DIR / "fusion/fusion_scores.csv"
    df = _load_csv(fusion_path)
    if df.empty:
        return df
    # expected columns may vary; try common names
    for col in ["fraud", "fraud_score"]:
        if col in df.columns:
            df["fraud_score"] = df[col]
            break
    for col in ["cyber", "cyber_score"]:
        if col in df.columns:
            df["cyber_score"] = df[col]
            break
    for col in ["behavior", "behavior_score"]:
        if col in df.columns:
            df["behavior_score"] = df[col]
            break
    if "fusion_score" not in df.columns and {"fraud_score", "cyber_score", "behavior_score"} <= set(
        df.columns
    ):
        df["fusion_score"] = df[["fraud_score", "cyber_score", "behavior_score"]].mean(axis=1)
    # label fallback
    if "action" not in df.columns:
        df["action"] = np.where(
            df.get("fusion_score", 0) > 0.8,
            "BLOCK",
            np.where(
                df.get("fusion_score", 0) > 0.6,
                "REVIEW",
                np.where(df.get("fusion_score", 0) > 0.4, "MONITOR", "ALLOW"),
            ),
        )
    keep = ["fraud_score", "cyber_score", "behavior_score", "fusion_score", "action"]
    return df[[c for c in keep if c in df.columns]]


def _from_domain_scores() -> pd.DataFrame:
    frames: List[pd.DataFrame] = []

    fraud_df = _load_csv(EXP_DIR / "fraud/scores.csv")
    if not fraud_df.empty:
        score_col = next(
            (c for c in ["supervised_score", "y_score", "prob_1"] if c in fraud_df), None
        )
        label_col = next((c for c in ["label", "y_true", "target"] if c in fraud_df), None)
        if score_col and label_col:
            tmp = pd.DataFrame(
                {
                    "fraud_score": fraud_df[score_col].astype(float),
                    "action": np.where(fraud_df[label_col] == 1, "BLOCK", "ALLOW"),
                }
            )
            tmp["cyber_score"] = 0.0
            tmp["behavior_score"] = 0.0
            tmp["fusion_score"] = tmp["fraud_score"]
            frames.append(tmp)

    cyber_df = _load_csv(EXP_DIR / "cyber/scores.csv")
    if not cyber_df.empty:
        score_col = next(
            (c for c in ["supervised_score", "y_score", "prob_1"] if c in cyber_df), None
        )
        label_col = next(
            (c for c in ["label", "y_true", "target", "attack"] if c in cyber_df), None
        )
        if score_col and label_col:
            tmp = pd.DataFrame(
                {
                    "cyber_score": cyber_df[score_col].astype(float),
                    "action": np.where(cyber_df[label_col] == 1, "BLOCK", "ALLOW"),
                }
            )
            tmp["fraud_score"] = 0.0
            tmp["behavior_score"] = 0.0
            tmp["fusion_score"] = tmp["cyber_score"]
            frames.append(tmp)

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


def build_dataset() -> pd.DataFrame:
    df = _from_fusion()
    if not df.empty:
        return df
    df = _from_domain_scores()
    if df.empty:
        # final fallback: synthetic tiny dataset
        data = {
            "fraud_score": [0.1, 0.9, 0.2, 0.75],
            "cyber_score": [0.2, 0.1, 0.8, 0.7],
            "behavior_score": [0.1, 0.1, 0.6, 0.5],
        }
        df = pd.DataFrame(data)
        df["fusion_score"] = df.mean(axis=1)
        df["action"] = np.where(
            df["fusion_score"] > 0.8,
            "BLOCK",
            np.where(
                df["fusion_score"] > 0.6,
                "REVIEW",
                np.where(df["fusion_score"] > 0.4, "MONITOR", "ALLOW"),
            ),
        )
    return df


def main():
    df = build_dataset()
    features = [c for c in df.columns if c != "action"]
    X = df[features].values
    y = df["action"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, OUT_MODEL)

    OUT_METRICS.parent.mkdir(parents=True, exist_ok=True)
    with OUT_METRICS.open("w") as f:
        json.dump(report, f, indent=2)

    print(f"Saved recommender model to {OUT_MODEL}")
    print(f"Metrics written to {OUT_METRICS}")


if __name__ == "__main__":
    main()
