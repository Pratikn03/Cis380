"""Prefect flow for cyber intrusion modeling with MLflow logging and explainability export.

Flow steps:
- Load raw cyber data
- Build features
- Train with train/val split
- Export scores/feature importances/SHAP for fusion and dashboard
"""

import shutil

import mlflow
import numpy as np
import pandas as pd
from prefect import flow, task
from sklearn.model_selection import train_test_split

from uais.data.load_cyber_data import load_cyber_data
from uais.features.cyber_features import build_cyber_feature_table
from uais.supervised.train_cyber_supervised import CyberModelConfig, train_cyber_model, cross_val_train_cyber
from uais.explainability.runner import export_tabular_explainability
from uais.utils.mlflow_utils import load_mlflow_settings, setup_mlflow
from uais.utils.paths import domain_paths
from uais.utils.stats import bootstrap_ci
from uais.utils.runtime import time_block, measure_proba


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
    train_time, (model, metrics) = time_block(
        train_cyber_model, X_train, y_train, X_val, y_val, config, True
    )

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
    mlflow.log_metric("train_time_sec", train_time)

    # Optional CV for stability
    try:
        models_cv, cv_metrics = cross_val_train_cyber(X_train, y_train, config, n_splits=3, random_state=42)
        metrics.update(cv_metrics)
        mlflow.log_metrics(cv_metrics)
        out_dir = domain_paths("cyber")["experiments"] / "metrics"
        out_dir.mkdir(parents=True, exist_ok=True)
        df_cv = pd.DataFrame({"fold_roc_auc": cv_metrics.get("cv_scores", [])})
        df_cv["mean"] = cv_metrics.get("cv_roc_auc_mean", np.nan)
        df_cv.to_csv(out_dir / "cv_metrics.csv", index=False)
    except Exception as exc:
        print(f"CV skipped: {exc}")

    # Export scores and feature importances
    y_val_proba = model.predict_proba(X_val)[:, 1]
    from uais.utils.metrics import best_f1_threshold

    best_thr = best_f1_threshold(y_val.values, y_val_proba)
    mlflow.log_metric("best_f1_threshold", best_thr)

    # Bootstrap CI for ROC-AUC
    try:
        from sklearn.metrics import roc_auc_score
        lower, upper = bootstrap_ci(y_val.values, y_val_proba, roc_auc_score)
        metrics["roc_auc_ci_lower"] = lower
        metrics["roc_auc_ci_upper"] = upper
        mlflow.log_metric("roc_auc_ci_lower", lower)
        mlflow.log_metric("roc_auc_ci_upper", upper)
    except Exception as exc:
        print(f"CI computation skipped: {exc}")

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

    # Explainability artifacts (SHAP + LIME)
    try:
        explain_dir = paths["experiments"] / "explainability"
        explain_dir.mkdir(parents=True, exist_ok=True)
        artifacts = export_tabular_explainability(
            model, X_train, X_val, explain_dir, class_names=["normal", "attack"]
        )
        plots_dir = paths["experiments"] / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        shap_path = artifacts.get("shap")
        lime_path = artifacts.get("lime")
        if shap_path:
            shutil.copy(shap_path, plots_dir / "shap_summary.png")
            mlflow.log_artifact(str(shap_path))
        if lime_path:
            shutil.copy(lime_path, plots_dir / "lime_tabular.txt")
            mlflow.log_artifact(str(lime_path))
    except Exception as exc:  # pragma: no cover
        print(f"Explainability generation skipped: {exc}")

    # Runtime metrics
    try:
        proba_time = measure_proba(model, X_val, n_runs=10)
        runtime_dir = paths["experiments"] / "metrics"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {"train_time_sec": [train_time], "predict_proba_sec_per_run": [proba_time]}
        ).to_csv(runtime_dir / "runtime.csv", index=False)
        mlflow.log_metric("predict_proba_sec_per_run", proba_time)
    except Exception as exc:
        print(f"Runtime logging skipped: {exc}")

    # Persist metrics for dashboard/aggregation
    metrics_dir = paths["experiments"] / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Metric": list(metrics.keys()), "Value": list(metrics.values())}).to_csv(
        metrics_dir / "metrics.csv", index=False
    )

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
