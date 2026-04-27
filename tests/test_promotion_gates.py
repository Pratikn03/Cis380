from __future__ import annotations

import json
from pathlib import Path


def test_promotion_writes_manifest_card_and_hash(tmp_path, monkeypatch):
    from scripts import promote_model

    monkeypatch.setattr(promote_model, "ROOT", tmp_path)
    monkeypatch.setattr(promote_model, "REPORT_JSON", tmp_path / "reports" / "PROMOTION_GATE.json")
    monkeypatch.setattr(promote_model, "REPORT_MD", tmp_path / "reports" / "PROMOTION_GATE.md")

    artifact = tmp_path / "models" / "demo.bin"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"model")
    metrics = tmp_path / "metrics.json"
    metrics.write_text(json.dumps({"test": {"roc_auc": 0.93}}), encoding="utf-8")
    dataset = tmp_path / "data" / "demo"
    dataset.mkdir(parents=True)
    (dataset / "rows.csv").write_text("x,y\n1,0\n", encoding="utf-8")

    gates = {
        "release_name": "test-release",
        "default_max_regression_pct": 2.0,
        "domains": {
            "demo": {
                "model_name": "demo-model",
                "version": "1.0.0",
                "artifact": str(artifact),
                "metrics": str(metrics),
                "dataset": str(dataset),
                "dataset_version_source": str(dataset),
                "baselines": {"test.roc_auc": 0.90},
                "gates": [
                    {
                        "metric": "test.roc_auc",
                        "op": ">=",
                        "baseline": "test.roc_auc",
                        "relative_min_delta_pct": 2.0,
                    }
                ],
            }
        },
    }
    manifest = tmp_path / "artifacts" / "release" / "model-manifest.json"

    result = promote_model.promote_domain(
        "demo", gates["domains"]["demo"], gates, manifest_path=manifest, sha="abc123"
    )

    assert result["status"] == "pass"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    entry = payload["models"][0]
    assert entry["domain"] == "demo"
    assert entry["thresholdResult"] == "pass"
    assert Path(tmp_path / entry["path"]).exists()
    card = tmp_path / entry["modelCard"]
    assert "## Intended Use" in card.read_text(encoding="utf-8")
    assert "## Ethical Risks" in card.read_text(encoding="utf-8")
    assert entry["artifactSha256"]
    assert entry["trainingGitSha"] == "abc123"


def test_failed_promotion_does_not_mutate_manifest(tmp_path, monkeypatch):
    from scripts import promote_model

    monkeypatch.setattr(promote_model, "ROOT", tmp_path)

    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model")
    metrics = tmp_path / "metrics.json"
    metrics.write_text(json.dumps({"score": 0.50}), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schemaVersion": 2, "models": []}), encoding="utf-8")
    before = manifest.read_text(encoding="utf-8")

    cfg = {
        "model_name": "demo-model",
        "artifact": str(artifact),
        "metrics": str(metrics),
        "dataset": str(tmp_path),
        "dataset_version_source": str(tmp_path),
        "baselines": {"score": 0.90},
        "gates": [{"metric": "score", "op": ">=", "value": 0.90}],
    }
    result = promote_model.promote_domain(
        "demo", cfg, {"domains": {"demo": cfg}}, manifest_path=manifest, sha="abc123"
    )

    assert result["status"] == "fail"
    assert manifest.read_text(encoding="utf-8") == before


def test_regression_detection_uses_lower_is_better():
    from scripts import promote_model

    cfg = {
        "lower_is_better": ["avg_wer"],
        "baselines": {"avg_wer": 0.20, "f1": 0.80},
    }
    gates = {"default_max_regression_pct": 2.0}
    values = {"avg_wer": 0.21, "f1": 0.77}

    failures = promote_model.evaluate_regressions("demo", cfg, gates, values)

    assert {item["metric"] for item in failures} == {"avg_wer", "f1"}
