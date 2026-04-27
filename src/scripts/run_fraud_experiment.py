"""
Run a full fraud experiment end-to-end (v1).

Steps:
1. Load raw fraud data.
2. Build feature table.
3. Split into train/val/test.
4. Train supervised fraud model.
5. Evaluate and print metrics.
6. (Optional) Train Isolation Forest and compute a hybrid score.
"""

from pathlib import Path
import json
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from uais.config.config_loader import load_config
from uais.data.load_fraud_data import load_fraud_data
from uais.features.fraud_features import build_fraud_feature_table
from uais.supervised.train_fraud_supervised import FraudModelConfig, train_fraud_model
from uais.utils.metrics import best_f1_threshold, compute_classification_metrics
from uais.anomaly.train_isolation_forest import train_isolation_forest, compute_anomaly_score
from uais.ensembles.blending import blend_supervised_and_anomaly
from uais.utils.paths import domain_paths, ensure_directories


def _fraud_config_to_dict(config: FraudModelConfig) -> dict:
    return {
        "model_type": config.model_type,
        "random_state": config.random_state,
        "max_depth": config.max_depth,
        "learning_rate": config.learning_rate,
        "max_iter": config.max_iter,
        "n_estimators": config.n_estimators,
        "class_weight_balanced": config.class_weight_balanced,
    }


def _fallback_sweep(
    X_train,
    y_train,
    X_val,
    y_val,
    *,
    max_iter: int,
    seed: int,
) -> tuple[FraudModelConfig, dict]:
    candidates = [
        FraudModelConfig(model_type="hist_gb", max_depth=4, learning_rate=0.08, max_iter=300),
        FraudModelConfig(model_type="hist_gb", max_depth=3, learning_rate=0.05, max_iter=500),
        FraudModelConfig(model_type="hist_gb", max_depth=6, learning_rate=0.08, max_iter=max_iter),
    ]
    best_cfg = candidates[0]
    best_auc = float("-inf")
    trials = []
    for idx, cfg in enumerate(candidates):
        cfg.random_state = seed + idx
        _, metrics = train_fraud_model(X_train, y_train, X_val, y_val, cfg)
        score = float(metrics.get("roc_auc", float("-inf")))
        trials.append({"params": _fraud_config_to_dict(cfg), "roc_auc": score})
        if score > best_auc:
            best_auc = score
            best_cfg = cfg
    return best_cfg, {
        "enabled": True,
        "backend": "deterministic_grid",
        "trials": trials,
        "best_value": best_auc,
        "best_params": _fraud_config_to_dict(best_cfg),
    }


def _select_fraud_config(
    X_train,
    y_train,
    X_val,
    y_val,
    *,
    max_iter: int,
    seed: int = 42,
) -> tuple[FraudModelConfig, dict]:
    n_trials = int(os.getenv("Sentifargo_FRAUD_OPTUNA_TRIALS", "30"))
    if n_trials <= 0:
        cfg = FraudModelConfig(model_type="hist_gb", max_depth=4, learning_rate=0.08, max_iter=300)
        return cfg, {"enabled": False, "best_params": _fraud_config_to_dict(cfg)}

    try:
        import optuna
    except Exception as exc:
        print(f"[fraud] Optuna unavailable; using deterministic fallback sweep ({exc}).")
        return _fallback_sweep(X_train, y_train, X_val, y_val, max_iter=max_iter, seed=seed)

    def objective(trial):
        cfg = FraudModelConfig(
            model_type="hist_gb",
            random_state=seed,
            max_depth=trial.suggest_int("max_depth", 2, 10),
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            max_iter=trial.suggest_int("max_iter", max(50, max_iter // 2), max(100, max_iter * 2)),
        )
        _, metrics = train_fraud_model(X_train, y_train, X_val, y_val, cfg)
        return float(metrics.get("roc_auc", 0.0))

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    timeout_env = os.getenv("Sentifargo_FRAUD_OPTUNA_TIMEOUT")
    timeout = int(timeout_env) if timeout_env else None
    study.optimize(objective, n_trials=n_trials, timeout=timeout)
    params = dict(study.best_trial.params)
    best_cfg = FraudModelConfig(
        model_type="hist_gb",
        random_state=seed,
        max_depth=int(params["max_depth"]),
        learning_rate=float(params["learning_rate"]),
        max_iter=int(params["max_iter"]),
    )
    return best_cfg, {
        "enabled": True,
        "backend": "optuna",
        "n_trials": len(study.trials),
        "best_value": float(study.best_value),
        "best_params": _fraud_config_to_dict(best_cfg),
    }


def main():
    ensure_directories()
    project_root = Path(__file__).resolve().parents[2]
    print(f"Project root: {project_root}")

    sample_env = os.getenv("Sentifargo_FRAUD_SAMPLE_SIZE")
    sample_size = int(sample_env) if sample_env else None
    if sample_size is not None and sample_size <= 0:
        sample_size = None

    max_iter_env = os.getenv("Sentifargo_FRAUD_MAX_ITER")
    max_iter = int(max_iter_env) if max_iter_env else 200
    skip_plots = os.getenv("Sentifargo_FRAUD_SKIP_PLOTS", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    # 1. Load raw data
    cfg = load_config("fraud")
    df_raw = load_fraud_data(cfg, n_rows=sample_size)
    print(f"Loaded raw fraud data with shape: {df_raw.shape}")

    # 2. Build features
    df_feats = build_fraud_feature_table(
        df_raw, time_column="Time", amount_column="Amount", target_column="Class"
    )
    print(f"Feature table shape: {df_feats.shape}")

    target_col = "Class"
    if target_col not in df_feats.columns:
        raise KeyError(f"Target column '{target_col}' not found in feature table.")

    X = df_feats.drop(columns=[target_col])
    y = df_feats[target_col].astype(int)

    # 3. Split into train/val/test (e.g., 60/20/20)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.4, stratify=y, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42
    )

    print(f"Train shape: {X_train.shape}, Val shape: {X_val.shape}, Test shape: {X_test.shape}")

    # 4. Train supervised model with validation-tuned hyperparameters.
    config, tuning_info = _select_fraud_config(
        X_train,
        y_train,
        X_val,
        y_val,
        max_iter=max_iter,
        seed=42,
    )
    print("[fraud] selected config:", _fraud_config_to_dict(config))
    model, val_metrics = train_fraud_model(X_train, y_train, X_val, y_val, config)
    if hasattr(model, "predict_proba"):
        y_val_prob_for_threshold = model.predict_proba(X_val)[:, 1]
    else:
        val_scores = model.decision_function(X_val)
        y_val_prob_for_threshold = 1.0 / (1.0 + np.exp(-val_scores))
    decision_threshold = best_f1_threshold(y_val.values, y_val_prob_for_threshold)

    retrain_best = os.getenv("Sentifargo_FRAUD_RETRAIN_TRAIN_VAL", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if retrain_best:
        X_train_full = pd.concat([X_train, X_val], axis=0)
        y_train_full = pd.concat([y_train, y_val], axis=0)
        model, _ = train_fraud_model(X_train_full, y_train_full, X_val, y_val, config)
    print("Validation metrics (supervised model):")
    for k, v in val_metrics.items():
        print(f"  {k}: {v:.4f}")

    # Evaluate on test set
    if hasattr(model, "predict_proba"):
        y_test_prob = model.predict_proba(X_test)[:, 1]
    else:
        scores = model.decision_function(X_test)
        y_test_prob = 1.0 / (1.0 + np.exp(-scores))

    test_metrics = compute_classification_metrics(
        y_test.values, y_test_prob, threshold=decision_threshold
    )
    test_metrics["threshold"] = float(decision_threshold)
    print("Test metrics (supervised model):")
    for k, v in test_metrics.items():
        print(f"  {k}: {v:.4f}")

    experiments_dir = project_root / "experiments" / "fraud"
    plots_dir = experiments_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    if not skip_plots:
        from uais.utils.plotting import plot_pr_curve, plot_roc_curve

        plot_roc_curve(
            y_test.values,
            y_test_prob,
            title="Fraud ROC (Supervised)",
            show=False,
            save_path=str(plots_dir / "roc_supervised.png"),
        )
        plot_pr_curve(
            y_test.values,
            y_test_prob,
            title="Fraud PR (Supervised)",
            show=False,
            save_path=str(plots_dir / "pr_supervised.png"),
        )
    else:
        print("Skipping fraud plotting for smoke run (Sentifargo_FRAUD_SKIP_PLOTS=true).")

    # 5. Train Isolation Forest on training data for anomaly scores (v1: use same features)
    iso_model, scaler = train_isolation_forest(X_train, contamination=0.01)
    anomaly_scores_test = compute_anomaly_score(iso_model, scaler, X_test)

    # 6. Compute blended / hybrid score
    hybrid_scores = blend_supervised_and_anomaly(
        y_test_prob, anomaly_scores_test, alpha=0.7, beta=0.3
    )

    hybrid_metrics = compute_classification_metrics(
        y_test.values, hybrid_scores, threshold=decision_threshold
    )
    hybrid_metrics["threshold"] = float(decision_threshold)
    print("Test metrics (hybrid supervised + anomaly):")
    for k, v in hybrid_metrics.items():
        print(f"  {k}: {v:.4f}")

    if not skip_plots:
        from uais.utils.plotting import plot_pr_curve, plot_roc_curve

        plot_roc_curve(
            y_test.values,
            hybrid_scores,
            title="Fraud ROC (Hybrid)",
            show=False,
            save_path=str(plots_dir / "roc_hybrid.png"),
        )
        plot_pr_curve(
            y_test.values,
            hybrid_scores,
            title="Fraud PR (Hybrid)",
            show=False,
            save_path=str(plots_dir / "pr_hybrid.png"),
        )

    # Persist artifacts for dashboard/API/fusion
    paths = domain_paths("fraud")
    (paths["models"] / "supervised").mkdir(parents=True, exist_ok=True)
    with open(paths["models"] / "supervised" / "fraud_model.pkl", "wb") as f:
        pickle.dump(model, f)

    metrics_out = {
        "val": val_metrics,
        "test": test_metrics,
        "hybrid": hybrid_metrics,
        "tuning": tuning_info,
    }
    metrics_dir = paths["experiments"] / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    with open(metrics_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_out, f, indent=2)

    # Flatten key metrics for Streamlit convenience
    pd.DataFrame(
        [
            {"Metric": "test_roc_auc", "Value": test_metrics.get("roc_auc", float("nan"))},
            {"Metric": "test_f1", "Value": test_metrics.get("f1", float("nan"))},
            {"Metric": "hybrid_roc_auc", "Value": hybrid_metrics.get("roc_auc", float("nan"))},
            {"Metric": "hybrid_f1", "Value": hybrid_metrics.get("f1", float("nan"))},
        ]
    ).to_csv(metrics_dir / "metrics.csv", index=False)

    scores_dir = paths["experiments"]
    scores_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"score": y_test_prob, "label": y_test.values}).to_csv(
        scores_dir / "scores.csv", index=False
    )

    print("Experiment completed. Plots saved to:", plots_dir)
    print("Artifacts saved under:", paths["experiments"])


if __name__ == "__main__":
    main()
