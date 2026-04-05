"""CLI: behavior anomaly detection run (autoencoder + LOF) using current components."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from uais.anomaly.evaluate_anomaly import evaluate_anomaly_scores
from uais.anomaly.train_autoencoder import train_autoencoder
from uais.anomaly.train_lof import train_lof
from uais.config.config_loader import load_config
from uais.data.behavior_insider import augment_insider_patterns, insider_summary
from uais.data.load_behavior_data import load_behavior_data
from uais.features.behavior_features import build_behavior_feature_table
from uais.utils.logging_utils import setup_logging
from uais.utils.metrics import compute_confusion_matrix
from uais.utils.paths import domain_paths, ensure_directories

logger = setup_logging(__name__)


def save_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    logger.info("Saved %s", path)


def main():
    ensure_directories()
    cfg = load_config("behavior")
    target_col = cfg.get("data", {}).get("target", "Revenue")
    drop_cols = cfg.get("data", {}).get("drop_columns")
    run_tag = os.getenv("BEHAVIOR_RUN_TAG")

    sample_env = os.getenv("Sentifargo_BEHAVIOR_SAMPLE_SIZE")
    sample_size = int(sample_env) if sample_env else None
    if sample_size is not None and sample_size <= 0:
        sample_size = None

    data_path = os.getenv("BEHAVIOR_DATA_PATH")
    if data_path:
        df_raw = load_behavior_data(csv_path=data_path, n_rows=sample_size, allow_synthetic=False)
    else:
        df_raw = load_behavior_data(cfg, n_rows=sample_size)
    df_feats = build_behavior_feature_table(
        df_raw, target_column=target_col, drop_columns=drop_cols
    )

    augment_cfg = cfg.get("augmentation", {})
    env_toggle = os.getenv("BEHAVIOR_AUGMENT_INSIDER")
    if env_toggle is not None:
        enable_aug = env_toggle.strip().lower() in {"1", "true", "yes", "on"}
    else:
        enable_aug = bool(augment_cfg.get("insider_patterns", False))

    augmentation_info: dict[str, object] = {"enabled": enable_aug}
    if enable_aug:
        ratio = float(os.getenv("BEHAVIOR_INSIDER_RATIO", augment_cfg.get("insider_ratio", 0.05)))
        max_rows = os.getenv("BEHAVIOR_INSIDER_MAX_ROWS", augment_cfg.get("insider_max_rows"))
        max_rows_val = int(max_rows) if max_rows not in (None, "") else None
        seed = int(os.getenv("BEHAVIOR_INSIDER_SEED", augment_cfg.get("insider_seed", 42)))
        df_feats = augment_insider_patterns(
            df_feats,
            target_column=target_col,
            ratio=ratio,
            seed=seed,
            max_rows=max_rows_val,
        )
        augmentation_info.update(
            {
                "ratio": ratio,
                "max_rows": max_rows_val,
                "seed": seed,
                "summary": insider_summary(df_feats, target_column=target_col),
            }
        )
        logger.info(
            "Behavior insider augmentation enabled (ratio=%.3f, max_rows=%s, seed=%s). Summary=%s",
            ratio,
            str(max_rows_val),
            seed,
            augmentation_info["summary"],
        )
    X = df_feats.drop(columns=[target_col])
    y = df_feats[target_col].astype(int)

    # Split for evaluation even though models are unsupervised.
    stratify = y if y.nunique(dropna=False) > 1 else None
    if stratify is None:
        logger.warning(
            "Behavior target column '%s' has <2 classes; splitting without stratify and metrics may be non-informative.",
            target_col,
        )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, stratify=stratify, random_state=42
    )

    preprocessor = StandardScaler()

    ae_model, _, _ = train_autoencoder(
        pd.concat([X_train, y_train], axis=1), target_col, preprocessor, cfg, "behavior"
    )
    ae_scores_test = ae_model.predict(preprocessor.transform(X_test))
    ae_recon_error = np.mean((preprocessor.transform(X_test) - ae_scores_test) ** 2, axis=1)
    ae_metrics_raw = evaluate_anomaly_scores(
        y_test, ae_recon_error, cfg.get("training", {}).get("anomaly_contamination", 0.05)
    )
    ae_threshold = float(ae_metrics_raw.get("threshold", 0.0))
    ae_preds = (ae_recon_error >= ae_threshold).astype(int)
    ae_cm = compute_confusion_matrix(np.asarray(y_test), np.asarray(ae_preds))
    ae_cm_list = ae_cm.astype(int).tolist()
    ae_tn, ae_fp, ae_fn, ae_tp = (
        (ae_cm_list[0][0], ae_cm_list[0][1], ae_cm_list[1][0], ae_cm_list[1][1])
        if len(ae_cm_list) == 2
        else (0, 0, 0, 0)
    )
    ae_fpr = float(ae_fp / max(ae_fp + ae_tn, 1))
    ae_metrics = {f"autoencoder_{k}": v for k, v in ae_metrics_raw.items()}

    lof_model, _, _ = train_lof(
        pd.concat([X_train, y_train], axis=1), target_col, preprocessor, cfg, "behavior"
    )
    lof_scores_test = -lof_model.score_samples(preprocessor.transform(X_test))
    lof_metrics_raw = evaluate_anomaly_scores(
        y_test, lof_scores_test, cfg.get("training", {}).get("anomaly_contamination", 0.05)
    )
    lof_threshold = float(lof_metrics_raw.get("threshold", 0.0))
    lof_preds = (lof_scores_test >= lof_threshold).astype(int)
    lof_cm = compute_confusion_matrix(np.asarray(y_test), np.asarray(lof_preds))
    lof_cm_list = lof_cm.astype(int).tolist()
    lof_tn, lof_fp, lof_fn, lof_tp = (
        (lof_cm_list[0][0], lof_cm_list[0][1], lof_cm_list[1][0], lof_cm_list[1][1])
        if len(lof_cm_list) == 2
        else (0, 0, 0, 0)
    )
    lof_fpr = float(lof_fp / max(lof_fp + lof_tn, 1))
    lof_metrics = {f"lof_{k}": v for k, v in lof_metrics_raw.items()}

    metrics = {
        **ae_metrics,
        **lof_metrics,
        "autoencoder_confusion": {"tn": ae_tn, "fp": ae_fp, "fn": ae_fn, "tp": ae_tp},
        "autoencoder_fpr": ae_fpr,
        "lof_confusion": {"tn": lof_tn, "fp": lof_fp, "fn": lof_fn, "tp": lof_tp},
        "lof_fpr": lof_fpr,
    }
    if run_tag:
        metrics["run_tag"] = run_tag
    metrics["augmentation"] = augmentation_info

    paths = domain_paths("behavior")
    metrics_path_env = os.getenv("BEHAVIOR_METRICS_PATH")
    if metrics_path_env:
        metrics_path = Path(metrics_path_env)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        metrics_dir = paths["experiments"] / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = metrics_dir / "metrics.json"
    save_json(metrics, metrics_path)
    pd.DataFrame([{"Metric": k, "Value": v} for k, v in metrics.items()]).to_csv(
        metrics_path.with_suffix(".csv"), index=False
    )

    # Normalize autoencoder errors for fusion friendliness.
    ae_norm = (ae_recon_error - ae_recon_error.min()) / (np.ptp(ae_recon_error) + 1e-8)
    scores_path_env = os.getenv("BEHAVIOR_SCORES_PATH")
    scores_path = Path(scores_path_env) if scores_path_env else paths["experiments"] / "scores.csv"
    pd.DataFrame({"score": ae_norm, "label": y_test.values}).to_csv(scores_path, index=False)
    logger.info("Saved scores to %s", scores_path)

    logger.info("Behavior experiment complete")


if __name__ == "__main__":
    main()
