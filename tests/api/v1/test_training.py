from __future__ import annotations

import json
from pathlib import Path

from app.api.v1.training import build_training_overview


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ["metric,value", *[f"{metric},{value}" for metric, value in rows]]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def _seed_training_audit(root: Path) -> None:
    _write_json(
        root / "reports" / "TRAINING_DATA.json",
        {
            "generated_at": "2026-02-14 00:00:00 UTC",
            "required": [
                {"name": "Fraud (creditcard.csv)", "status": "ok"},
                {"name": "Cyber (UNSW_NB15_training-set.csv)", "status": "ok"},
                {"name": "Behavior (online_shoppers_intention.csv)", "status": "ok"},
            ],
            "optional": [
                {"name": "Vision real/fake (raw)", "status": "ok"},
            ],
        },
    )


def _seed_core_metrics(root: Path) -> None:
    _write_json(
        root / "experiments" / "fraud" / "metrics" / "metrics.json",
        {"test": {"accuracy": 0.99, "roc_auc": 0.91, "f1": 0.62, "precision": 0.55, "recall": 0.71}},
    )
    _write_json(
        root / "experiments" / "cyber" / "metrics" / "metrics.json",
        {"test": {"accuracy": 0.90, "roc_auc": 0.97, "f1": 0.91, "precision": 0.90, "recall": 0.92}},
    )
    _write_json(
        root / "experiments" / "behavior" / "metrics" / "metrics.json",
        {"autoencoder_accuracy": 0.82, "autoencoder_f1": 0.16, "autoencoder_roc_auc": 0.53},
    )
    _write_json(
        root / "experiments" / "fusion" / "metrics" / "metrics.json",
        {"test": {"accuracy": 0.88, "roc_auc": 0.86, "f1": 0.81}},
    )
    _write_json(
        root / "experiments" / "vision" / "video_temporal" / "metrics.json",
        {"accuracy": 0.74, "f1": 0.70, "roc_auc": 0.79},
    )


def _seed_model_files(root: Path) -> None:
    files = [
        root / "models" / "fraud" / "supervised" / "fraud_model.pkl",
        root / "models" / "cyber" / "supervised" / "cyber_model.pkl",
        root / "models" / "behavior" / "behavior_lof.pkl",
        root / "models" / "fusion" / "fusion_meta_model.pkl",
        root / "models" / "vision" / "resnet" / "model.pt",
    ]
    for file in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("ok", encoding="utf-8")


def test_training_overview_full_fixture_ready(tmp_path: Path) -> None:
    _seed_training_audit(tmp_path)
    _seed_core_metrics(tmp_path)
    _seed_model_files(tmp_path)

    overview = build_training_overview(tmp_path)

    assert overview.totalCount == 5
    assert overview.readyCount == 5
    assert all(domain.status == "ready" for domain in overview.domains)
    assert overview.generatedAt == "2026-02-14 00:00:00 UTC"


def test_training_overview_partial_fixture_reports_warning(tmp_path: Path) -> None:
    _seed_training_audit(tmp_path)
    _seed_core_metrics(tmp_path)
    # Missing model files on purpose.

    overview = build_training_overview(tmp_path)
    fraud = next(domain for domain in overview.domains if domain.domain == "fraud")

    assert overview.readyCount < overview.totalCount
    assert fraud.status == "warning"
    assert "model_not_ready" in fraud.blockers
    assert fraud.metrics is not None


def test_training_overview_missing_fixture_returns_missing(tmp_path: Path) -> None:
    overview = build_training_overview(tmp_path)
    assert overview.readyCount == 0
    assert overview.totalCount == 5
    assert all(domain.status == "missing" for domain in overview.domains)
    assert all("missing_training_audit" in domain.blockers for domain in overview.domains)


def test_training_overview_uses_csv_metrics_fallback(tmp_path: Path) -> None:
    _seed_training_audit(tmp_path)
    _seed_model_files(tmp_path)
    _write_csv(
        tmp_path / "experiments" / "fraud" / "metrics" / "metrics.csv",
        [
            ("accuracy", "0.88"),
            ("roc_auc", "0.91"),
            ("f1", "0.71"),
            ("precision", "0.69"),
            ("recall", "0.74"),
        ],
    )

    overview = build_training_overview(tmp_path)
    fraud = next(domain for domain in overview.domains if domain.domain == "fraud")

    assert fraud.metrics is not None
    assert fraud.metrics.auc == 0.91
    assert fraud.metrics.f1 == 0.71
    assert "metrics_missing" not in fraud.blockers
    assert "metrics_parse_error" not in fraud.blockers


def test_training_overview_marks_corrupt_json_as_parse_error(tmp_path: Path) -> None:
    _seed_training_audit(tmp_path)
    _seed_model_files(tmp_path)
    bad_metrics = tmp_path / "experiments" / "fraud" / "metrics" / "metrics.json"
    bad_metrics.parent.mkdir(parents=True, exist_ok=True)
    bad_metrics.write_text("{bad-json", encoding="utf-8")

    overview = build_training_overview(tmp_path)
    fraud = next(domain for domain in overview.domains if domain.domain == "fraud")

    assert fraud.metrics is None
    assert "metrics_parse_error" in fraud.blockers
    assert "metrics_missing" not in fraud.blockers
