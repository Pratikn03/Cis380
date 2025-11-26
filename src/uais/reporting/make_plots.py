"""Generate plots from experiment metrics with optional CI bars if available."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DOMAINS = ["fraud", "cyber", "behavior", "nlp", "vision", "fusion"]


def plot_metric_bar(domain: str, metric: str = "roc_auc"):
    metrics_dir = Path("experiments") / domain / "metrics"
    if not metrics_dir.exists():
        return
    dfs = []
    for csv in metrics_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv)
            df["source"] = csv.stem
            dfs.append(df)
        except Exception:
            pass
    if not dfs:
        return
    df_all = pd.concat(dfs, ignore_index=True)
    if metric not in df_all.columns:
        return
    # If CI columns present, use as error bars
    err = None
    if f"{metric}_ci_lower" in df_all.columns and f"{metric}_ci_upper" in df_all.columns:
        lower = df_all[f"{metric}_ci_lower"].to_numpy()
        upper = df_all[f"{metric}_ci_upper"].to_numpy()
        err = [df_all[metric].to_numpy() - lower, upper - df_all[metric].to_numpy()]

    plt.figure(figsize=(6, 4))
    plt.bar(df_all["source"], df_all[metric], yerr=err, capsize=4)
    plt.ylabel(metric)
    plt.title(f"{domain.title()} {metric} comparison")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig_dir = Path("figures") / "reports"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_dir / f"{domain}_{metric}.png", dpi=300)
    plt.close()


def main():
    for d in DOMAINS:
        plot_metric_bar(d, "roc_auc")


if __name__ == "__main__":  # pragma: no cover
    main()
