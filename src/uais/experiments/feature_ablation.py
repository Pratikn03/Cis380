"""Feature engineering ablation runner (tabular).

Runs multiple feature-engineering configs on a chosen domain (default: fraud),
trains a quick classifier, and writes metrics/plots for comparison.

Configs:
- none
- poly
- binning
- poly_binning
- vif_binning (simple VIF-based filter + binning)
- mi_filter (mutual information feature selection)

Outputs:
- metrics CSV: experiments/<domain>/ablations/<config>_metrics.csv
- summary CSV: experiments/<domain>/ablations/summary.csv
- plot: figures/ablations/<domain>_ablation.png
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import KBinsDiscretizer, OneHotEncoder, PolynomialFeatures, StandardScaler
from sklearn.impute import SimpleImputer

from uais.data.load_datasets import load_fraud_data, load_cyber_data
from uais.features.fraud_features import build_fraud_feature_table
from uais.features.cyber_features import build_cyber_feature_table
from uais.utils.metrics import compute_classification_metrics


def _drop_high_cardinality_categoricals(df: pd.DataFrame, target_col: str, max_card: int = 50) -> Tuple[pd.DataFrame, list[str]]:
    cat_cols = df.drop(columns=[target_col]).select_dtypes(exclude=[np.number]).columns
    drop_cols = [c for c in cat_cols if df[c].nunique(dropna=True) > max_card]
    if drop_cols:
        df = df.drop(columns=drop_cols)
        print(f"[info] Dropped high-cardinality categorical columns (> {max_card} uniques): {drop_cols}")
    return df, drop_cols


def compute_vif_filter(df: pd.DataFrame, target_col: str, thresh: float = 10.0) -> pd.DataFrame:
    X = df.drop(columns=[target_col]).select_dtypes(include=[np.number])
    X_imputed = X.fillna(X.median())
    df_imputed = X_imputed.join(df[target_col])
    cols = X_imputed.columns.tolist()
    keep = []
    for col in cols:
        y = df_imputed[col].values
        X_other = df_imputed.drop(columns=[col, target_col]).values
        if X_other.shape[1] == 0:
            keep.append(col)
            continue
        lr = LinearRegression()
        lr.fit(X_other, y)
        r2 = lr.score(X_other, y)
        vif = 1.0 / (1.0 - r2 + 1e-8)
        if vif <= thresh:
            keep.append(col)
    kept_df = df[keep + [target_col]].copy()
    return kept_df


def build_fe_pipeline(df: pd.DataFrame, target_col: str, config: str, max_cat_cardinality: int = 50) -> Pipeline:
    feature_df = df.drop(columns=[target_col])
    num_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols_raw = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()
    cat_cols = []
    for col in cat_cols_raw:
        n_unique = feature_df[col].nunique(dropna=True)
        if max_cat_cardinality is None or n_unique <= max_cat_cardinality:
            cat_cols.append(col)

    transformers = []
    num_steps = [("imputer", SimpleImputer(strategy="median"))]

    if config in {"poly", "poly_binning"}:
        num_steps.append(("poly", PolynomialFeatures(degree=2, include_bias=False)))
    if config in {"binning", "poly_binning", "vif_binning"}:
        num_steps.append(("bin", KBinsDiscretizer(n_bins=5, encode="ordinal", strategy="quantile")))
    num_steps.append(("scaler", StandardScaler()))
    transformers.append(("num", Pipeline(num_steps), num_cols))

    if cat_cols:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols))

    pre = ColumnTransformer(transformers)
    clf = HistGradientBoostingClassifier(random_state=42)
    pipe = Pipeline([("preprocessor", pre), ("model", clf)])
    return pipe


def run_ablation(domain: str = "fraud", max_rows: int | None = 200_000) -> Dict[str, Dict[str, float]]:
    domain = domain.lower()
    if domain == "fraud":
        df_raw = load_fraud_data()
        df = build_fraud_feature_table(df_raw)
        target_col = "Class"
    elif domain == "cyber":
        df_raw = load_cyber_data()
        df = build_cyber_feature_table(df_raw)
        target_col = "label"
    else:
        raise ValueError("Only fraud or cyber supported for ablation.")

    if max_rows is not None and len(df) > max_rows:
        df = df.sample(n=max_rows, random_state=42).reset_index(drop=True)
        print(f"[info] Subsampled {domain} dataset to {max_rows} rows for ablation.")

    configs = ["none", "poly", "binning", "poly_binning", "vif_binning", "mi_filter"]
    results: Dict[str, Dict[str, float]] = {}

    for cfg in configs:
        df_use = df.copy()
        df_use, dropped_cols = _drop_high_cardinality_categoricals(df_use, target_col=target_col, max_card=50)
        if cfg == "vif_binning":
            df_use = compute_vif_filter(df_use, target_col=target_col)
        if cfg == "mi_filter":
            Xtmp = df_use.drop(columns=[target_col]).copy()
            ytmp = df_use[target_col]
            cat_cols_tmp = Xtmp.select_dtypes(exclude=[np.number]).columns
            if len(cat_cols_tmp) > 0:
                for col in cat_cols_tmp:
                    Xtmp[col] = Xtmp[col].astype("category").cat.codes
            Xtmp = Xtmp.fillna(Xtmp.median(numeric_only=True))
            mi = mutual_info_classif(Xtmp, ytmp, discrete_features=False, random_state=42)
            topk = min(20, Xtmp.shape[1])
            keep_idx = np.argsort(mi)[-topk:]
            keep_cols = Xtmp.columns[keep_idx].tolist()
            df_use = df_use[keep_cols + [target_col]]

        X = df_use.drop(columns=[target_col])
        y = df_use[target_col]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        if cfg == "none" and X.select_dtypes(exclude=[np.number]).empty:
            model = HistGradientBoostingClassifier(random_state=42)
            model.fit(X_train, y_train)
            proba = model.predict_proba(X_test)[:, 1]
        else:
            pipe = build_fe_pipeline(df_use, target_col, cfg)
            pipe.fit(X_train, y_train)
            proba = pipe.predict_proba(X_test)[:, 1]

        metrics = compute_classification_metrics(y_test.values, proba, threshold=0.5)
        results[cfg] = metrics

        out_dir = Path("experiments") / domain / "ablations"
        out_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([metrics]).to_csv(out_dir / f"{cfg}_metrics.csv", index=False)

    summary = pd.DataFrame.from_dict(results, orient="index")
    out_dir = Path("experiments") / domain / "ablations"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "summary.csv")

    fig_dir = Path("figures") / "ablations"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.bar(summary.index, summary["roc_auc"])
    plt.ylabel("ROC-AUC")
    plt.title(f"{domain.title()} Feature Ablation")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(fig_dir / f"{domain}_ablation.png", dpi=150)
    plt.close()

    return results


if __name__ == "__main__":  # pragma: no cover
    run_ablation("fraud")
