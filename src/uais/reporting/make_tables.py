"""Generate summary tables from experiments metrics (mean±sd if available)."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np

DOMAINS = ["fraud", "cyber", "behavior", "nlp", "vision", "fusion"]


def gather_metrics(domain: str) -> pd.DataFrame:
    metrics_dir = Path("experiments") / domain / "metrics"
    dfs = []
    if metrics_dir.exists():
        for csv in metrics_dir.glob("*.csv"):
            try:
                df = pd.read_csv(csv)
                df["source"] = csv.name
                dfs.append(df)
            except Exception:
                pass
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def make_summary():
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    for domain in DOMAINS:
        df = gather_metrics(domain)
        if df.empty:
            continue
        summaries = []
        if {"Metric", "Value"}.issubset(df.columns):
            summary = df.groupby("Metric")["Value"].agg(["mean", "std"]).reset_index()
            summaries.append(summary)
        cv_path = Path("experiments") / domain / "metrics" / "cv_metrics.csv"
        if cv_path.exists():
            try:
                cv_df = pd.read_csv(cv_path)
                if "fold_roc_auc" in cv_df.columns:
                    summary_cv = pd.DataFrame({
                        "Metric": ["cv_roc_auc"],
                        "mean": [cv_df["fold_roc_auc"].mean()],
                        "std": [cv_df["fold_roc_auc"].std()]
                    })
                    summaries.append(summary_cv)
            except Exception:
                pass
        if summaries:
            final = pd.concat(summaries, ignore_index=True)
        else:
            final = df.describe(include="all")
        out_path = reports_dir / f"metrics_{domain}.csv"
        final.to_csv(out_path, index=False)
        print(f"Wrote {out_path}")


if __name__ == "__main__":  # pragma: no cover
    make_summary()
