from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Row:
    module: str
    dataset: str
    metric: str
    value: str
    artifact: str


def _fmt_float(value: float | None) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.4f}"
    except Exception:
        return "N/A"


def _read_metrics_csv(path: Path) -> dict[str, float]:
    """Read a metrics CSV into {metric: value}.

    Supported formats:
    - Metric,mean,std
    - Metric,Value
    """
    if not path.exists():
        return {}
    metrics: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return {}
        value_key = (
            "mean"
            if "mean" in reader.fieldnames
            else "Value" if "Value" in reader.fieldnames else None
        )
        if value_key is None:
            return {}
        for row in reader:
            metric = (row.get("Metric") or "").strip()
            raw = (row.get(value_key) or "").strip()
            if not metric or raw == "":
                continue
            try:
                metrics[metric] = float(raw)
            except Exception:
                continue
    return metrics


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _extract_classification_report(report: dict) -> dict[str, float]:
    """Return {accuracy, weighted_f1, macro_f1} from sklearn classification_report output_dict."""
    out: dict[str, float] = {}
    acc = report.get("accuracy")
    if isinstance(acc, (int, float)):
        out["accuracy"] = float(acc)
    weighted = report.get("weighted avg") or {}
    macro = report.get("macro avg") or {}
    wf1 = weighted.get("f1-score")
    mf1 = macro.get("f1-score")
    if isinstance(wf1, (int, float)):
        out["weighted_f1"] = float(wf1)
    if isinstance(mf1, (int, float)):
        out["macro_f1"] = float(mf1)
    return out


def _extract_ncf_last_val_acc(payload: dict) -> float | None:
    hist = payload.get("history")
    if not isinstance(hist, list) or not hist:
        return None
    last = hist[-1]
    if not isinstance(last, dict):
        return None
    val_acc = last.get("val_acc")
    if isinstance(val_acc, (int, float)):
        return float(val_acc)
    return None


def _to_markdown(rows: list[Row]) -> str:
    header = "| Module | Dataset | Metric | Value | Artifact |\n|---|---|---:|---:|---|\n"
    lines = [
        f"| {r.module} | {r.dataset} | {r.metric} | {r.value} | `{r.artifact}` |" for r in rows
    ]
    return header + "\n".join(lines) + "\n"


def generate_rows() -> list[Row]:
    rows: list[Row] = []

    def add_report_rows(
        *,
        module: str,
        dataset: str,
        artifact: str,
        metrics_path: Path,
        metrics_order: list[tuple[str, str]],
    ) -> None:
        metrics = _read_metrics_csv(metrics_path)
        for metric_key, metric_label in metrics_order:
            rows.append(
                Row(
                    module=module,
                    dataset=dataset,
                    metric=metric_label,
                    value=_fmt_float(metrics.get(metric_key)),
                    artifact=artifact,
                )
            )

    # Core SentinelForge domain metrics (tracked, stable).
    add_report_rows(
        module="Fraud",
        dataset="fraud_features.parquet",
        artifact="models/fraud/supervised/fraud_model.pkl",
        metrics_path=Path("reports/metrics_fraud.csv"),
        metrics_order=[
            ("roc_auc", "ROC-AUC"),
            ("pr_auc", "PR-AUC"),
            ("f1", "F1"),
            ("accuracy", "Accuracy"),
        ],
    )
    add_report_rows(
        module="Cyber",
        dataset="unsw_nb15_features.parquet",
        artifact="models/cyber/supervised/cyber_model.pkl",
        metrics_path=Path("reports/metrics_cyber.csv"),
        metrics_order=[
            ("roc_auc", "ROC-AUC"),
            ("pr_auc", "PR-AUC"),
            ("f1", "F1"),
            ("accuracy", "Accuracy"),
        ],
    )
    add_report_rows(
        module="Behavior",
        dataset="r4_2_raw.parquet",
        artifact="models/behavior/behavior_lof.pkl",
        metrics_path=Path("reports/metrics_behavior.csv"),
        metrics_order=[
            ("roc_auc", "ROC-AUC"),
            ("pr_auc", "PR-AUC"),
            ("f1", "F1"),
            ("accuracy", "Accuracy"),
        ],
    )
    add_report_rows(
        module="Fusion",
        dataset="fusion_scores.csv",
        artifact="experiments/fusion/models/fusion_meta_model.pkl",
        metrics_path=Path("reports/metrics_fusion.csv"),
        metrics_order=[
            ("roc_auc", "ROC-AUC"),
            ("pr_auc", "PR-AUC"),
            ("f1", "F1"),
            ("accuracy", "Accuracy"),
        ],
    )

    vision_artifact = "models/vision/resnet/model.pt"
    if not Path(vision_artifact).exists() and Path("models/vision/resnet_smoke/model.pt").exists():
        vision_artifact = "models/vision/resnet_smoke/model.pt"
    add_report_rows(
        module="Vision (image)",
        dataset="processed/vision (train+val)",
        artifact=vision_artifact,
        metrics_path=Path("reports/metrics_vision.csv"),
        metrics_order=[
            ("roc_auc", "ROC-AUC"),
            ("pr_auc", "PR-AUC"),
            ("f1", "F1"),
            ("accuracy", "Accuracy"),
        ],
    )

    # Voice: artifact-only (training metrics are not standardized in the repo yet).
    voice_artifact = "models/voice_emotion.pkl"
    rows.append(
        Row(
            module="Voice",
            dataset="CREMA-D / custom wav",
            metric="Artifact",
            value="OK" if Path(voice_artifact).exists() else "N/A",
            artifact=voice_artifact,
        )
    )

    # Recommender metrics: best-effort from experiment JSONs (may be absent in a clean clone).
    xgb_metrics_path = Path("experiments/recommender/metrics/recommender_metrics.json")
    xgb_report = _read_json(xgb_metrics_path)
    xgb_metrics = _extract_classification_report(xgb_report)
    for key, label in [("accuracy", "Accuracy"), ("weighted_f1", "Weighted-F1")]:
        rows.append(
            Row(
                module="Recommender (XGBoost)",
                dataset="movielens.csv",
                metric=label,
                value=_fmt_float(xgb_metrics.get(key)),
                artifact="models/recommender/recommender_model.pkl",
            )
        )

    ncf_metrics_path = Path("experiments/recommender/metrics/recommender_ncf_metrics.json")
    ncf_payload = _read_json(ncf_metrics_path)
    rows.append(
        Row(
            module="Recommender (NCF)",
            dataset="movielens.csv",
            metric="Val-Acc (last)",
            value=_fmt_float(_extract_ncf_last_val_acc(ncf_payload)),
            artifact="models/recommender/recommender_ncf.pt",
        )
    )

    movielens_metrics_path = Path("experiments/recommender/metrics/movielens_metrics.json")
    movielens_report = _read_json(movielens_metrics_path)
    movielens_metrics = _extract_classification_report(movielens_report)
    for key, label in [("accuracy", "Accuracy"), ("weighted_f1", "Weighted-F1")]:
        rows.append(
            Row(
                module="Recommender (GBDT)",
                dataset="movielens.csv (sample)",
                metric=label,
                value=_fmt_float(movielens_metrics.get(key)),
                artifact="models/recommender/movielens_model.pkl",
            )
        )

    return rows


def generate_markdown() -> str:
    rows = generate_rows()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    md = f"_Last updated: {ts}_\n\n" + _to_markdown(rows)
    return md


def main() -> None:
    md = generate_markdown()
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/benchmarks.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
