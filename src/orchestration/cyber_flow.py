"""Prefect flow for cyber intrusion modeling with MLflow logging and explainability export."""

import mlflow
import numpy as np
import pandas as pd
from prefect import flow, task
from sklearn.model_selection import train_test_split

from uais.data.load_cyber_data import load_cyber_data
from uais.features.cyber_features import build_cyber_feature_table
from uais.supervised.train_cyber_supervised import CyberModelConfig, train_cyber_model
from uais.utils.mlflow_utils import load_mlflow_settings, setup_mlflow
from uais.utils.paths import domain_paths


@task
def load_data_task():
    return load_cyber_data()


@task
def feature_task(df):
    return build_cyber_feature_table(df)


@task
def train_task(df):
    target_col = "label"
    X = df.drop(columns=[target_col])
    y = df[target_col]
    corr = df.corr(numeric_only=True)[target_col].abs().sort_values(ascending=False)
    leak_features = [idx for idx, val in corr.items() if idx != target_col and val > 0.95]
    if leak_features:
        print(f"[warn] Potential leakage features with high correlation to target: {leak_features}")
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    config = CyberModelConfig()
    model, metrics = train_cyber_model(X_train, y_train, X_val, y_val, config)

    mlflow.log_params(
        {
            "model_type": config.model_type,
            "max_depth": config.max_depth,
            "learning_rate": config.learning_rate,
            "max_iter": config.max_iter,
            "n_estimators": config.n_estimators,
        }
    )
    mlflow.log_metrics(metrics)

    # Export scores and feature importances
    y_val_proba = model.predict_proba(X_val)[:, 1]
    from uais.utils.metrics import best_f1_threshold

    best_thr = best_f1_threshold(y_val.values, y_val_proba)
    mlflow.log_metric("best_f1_threshold", best_thr)

    paths = domain_paths("cyber")
    paths["experiments"].mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"score": y_val_proba, "label": y_val.values}).to_csv(
        paths["experiments"] / "scores.csv", index=False
    )
    if hasattr(model, "feature_importances_"):
        fi = model.feature_importances_
    elif hasattr(model, "coef_"):
        fi = np.abs(model.coef_).ravel()
    else:
        fi = None
    if fi is not None:
        pd.DataFrame({"feature": X.columns, "importance": fi}).to_csv(
            paths["experiments"] / "feature_importances.csv", index=False
        )

    # SHAP summary plot (best effort)
    try:
        import shap  # noqa: F401
        import matplotlib.pyplot as plt

        sample = X_val.sample(n=min(200, len(X_val)), random_state=42)
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(sample)
        plots_dir = paths["experiments"] / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        plt.figure()
        shap.summary_plot(shap_values, sample, show=False)
        plt.tight_layout()
        plt.savefig(plots_dir / "shap_summary.png", dpi=150)
        plt.close()
    except Exception as exc:  # pragma: no cover
        print(f"SHAP generation skipped: {exc}")

    return metrics.get("accuracy", float("nan"))


@flow(name="Cyber Flow")
def cyber_pipeline():
    settings = load_mlflow_settings()
    setup_mlflow(experiment_name=settings["experiment_name"], tracking_uri=settings["tracking_uri"])

    with mlflow.start_run(run_name="cyber_flow"):
        df_raw = load_data_task()
        df_feat = feature_task(df_raw)
        acc = train_task(df_feat)
        print(f"Cyber pipeline completed. Accuracy: {acc:.4f}")


if __name__ == "__main__":
    cyber_pipeline()
