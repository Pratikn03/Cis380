from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable


CARD_ROOT = Path("docs/model_cards")


def _render_kv(items: Dict[str, Any]) -> str:
    lines = []
    for key, value in sorted(items.items()):
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) if lines else "- (none)"


def render_model_card(
    *,
    model_name: str,
    version: str,
    dataset: str,
    metrics: Dict[str, Any],
    artifact_path: str,
    status: str,
    run_id: str | None = None,
    intended_use: str = "Production inference and evaluation",
    limitations: str = "Performance depends on data quality; validate before deployment.",
) -> str:
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"# Model Card: {model_name} (v{version})\n\n"
        f"## Overview\n"
        f"- Model name: {model_name}\n"
        f"- Version: {version}\n"
        f"- Status: {status}\n"
        f"- Created: {created_at}\n"
        f"- Dataset: {dataset}\n"
        f"- Artifact: {artifact_path}\n"
        f"- Run ID: {run_id or 'n/a'}\n\n"
        f"## Intended Use\n{intended_use}\n\n"
        f"## Metrics\n"
        f"{_render_kv(metrics)}\n\n"
        f"## Limitations\n{limitations}\n\n"
        f"## Raw Metadata\n"
        "```json\n"
        f"{json.dumps(metrics, indent=2)}\n"
        "```\n"
    )


def write_model_card(
    *,
    model_name: str,
    version: str,
    dataset: str,
    metrics: Dict[str, Any],
    artifact_path: str,
    status: str,
    run_id: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    target_dir = output_dir or (CARD_ROOT / model_name)
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"MODEL_CARD_{version}.md" if version else "MODEL_CARD.md"
    path = target_dir / filename
    card = render_model_card(
        model_name=model_name,
        version=version,
        dataset=dataset,
        metrics=metrics,
        artifact_path=artifact_path,
        status=status,
        run_id=run_id,
    )
    path.write_text(card, encoding="utf-8")
    return path


def _load_metrics(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


DEFAULT_MODELS: Iterable[Dict[str, Any]] = [
    {
        "model_name": "fraud",
        "dataset": "data/raw/fraud",
        "metrics_path": "experiments/fraud/metrics/metrics.json",
        "artifact_path": "models/fraud/supervised/fraud_model.pkl",
    },
    {
        "model_name": "cyber",
        "dataset": "data/raw/cyber",
        "metrics_path": "experiments/cyber/metrics/metrics.json",
        "artifact_path": "models/cyber/supervised/cyber_model.pkl",
    },
    {
        "model_name": "behavior",
        "dataset": "data/raw/behavior",
        "metrics_path": "experiments/behavior/metrics/metrics.json",
        "artifact_path": "models/behavior/behavior_lof.pkl",
    },
    {
        "model_name": "vision",
        "dataset": "data/raw/vision",
        "metrics_path": "experiments/vision/metrics/metrics.json",
        "artifact_path": "models/vision/resnet/model.pt",
    },
    {
        "model_name": "recommender",
        "dataset": "data/raw/recommendation",
        "metrics_path": "experiments/recommender/metrics/metrics.json",
        "artifact_path": "models/recommender/recommender_model.pkl",
    },
    {
        "model_name": "fusion",
        "dataset": "experiments/fusion",
        "metrics_path": "experiments/fusion/metrics/metrics.json",
        "artifact_path": "models/fusion/fusion_meta_model.pkl",
    },
]


def generate_default_cards(version: str | None = None) -> list[Path]:
    tag = version or datetime.utcnow().strftime("%Y%m%d")
    created: list[Path] = []
    for entry in DEFAULT_MODELS:
        metrics = _load_metrics(Path(entry["metrics_path"]))
        path = write_model_card(
            model_name=entry["model_name"],
            version=tag,
            dataset=entry["dataset"],
            metrics=metrics,
            artifact_path=entry["artifact_path"],
            status="staging",
        )
        created.append(path)
    return created
