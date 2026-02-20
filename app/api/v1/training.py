from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/training", tags=["training"])

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_DOMAINS = ("fraud", "cyber", "behavior", "vision", "voice", "recommender", "fusion")

MODEL_PATHS: dict[str, tuple[Path, ...]] = {
    "fraud": (Path("models/fraud/supervised/fraud_model.pkl"),),
    "cyber": (Path("models/cyber/supervised/cyber_model.pkl"),),
    "behavior": (
        Path("models/behavior/behavior_autoencoder.pkl"),
        Path("models/behavior/behavior_lof.pkl"),
    ),
    "vision": (
        Path("models/vision/resnet/model.pt"),
        Path("models/vision/face_emotion/model.pt"),
        Path("artifacts/brand/yolo_logo_det.pt"),
    ),
    "voice": (
        Path("models/voice_emotion.pkl"),
        Path("models/voice_emotion_ssl"),
    ),
    "recommender": (
        Path("models/recommender/recommender_model.pkl"),
        Path("models/recommender/recommender_meta.joblib"),
        Path("models/recommender/movielens_model.pkl"),
        Path("models/recommender/movielens_meta.joblib"),
    ),
    "fusion": (Path("models/fusion/fusion_meta_model.pkl"),),
}


class TrainingMetrics(BaseModel):
    accuracy: float | None = None
    f1: float | None = None
    auc: float | None = None
    precision: float | None = None
    recall: float | None = None


class TrainingDomain(BaseModel):
    domain: str
    status: str
    datasetReady: bool
    modelReady: bool
    metrics: TrainingMetrics | None = None
    sourcePath: str
    updatedAt: str | None = None
    blockers: list[str]


class TrainingOverview(BaseModel):
    generatedAt: str | None = None
    domains: list[TrainingDomain]
    readyCount: int
    totalCount: int


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out:  # NaN
        return None
    return out


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_json_with_error(path: Path) -> tuple[dict[str, Any] | None, bool]:
    if not path.exists():
        return None, False
    try:
        return json.loads(path.read_text(encoding="utf-8")), False
    except OSError:
        return None, False
    except json.JSONDecodeError:
        return None, True


def _read_metrics_csv(path: Path) -> dict[str, float] | None:
    if not path.exists():
        return None
    rows: dict[str, float] = {}
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            headers = {h.lower(): h for h in (reader.fieldnames or [])}
            metric_col = headers.get("metric")
            value_col = headers.get("value")
            if metric_col and value_col:
                for row in reader:
                    key = str(row.get(metric_col, "")).strip().lower()
                    val = _safe_float(row.get(value_col))
                    if key and val is not None:
                        rows[key] = val
            else:
                fh.seek(0)
                reader_plain = csv.reader(fh)
                header = next(reader_plain, [])
                if len(header) == 2:
                    for row in reader_plain:
                        if len(row) != 2:
                            continue
                        key = row[0].strip().lower()
                        val = _safe_float(row[1])
                        if key and val is not None:
                            rows[key] = val
    except OSError:
        return None
    return rows or None


def _collect_metric_values(payload: Any, prefix: str = "") -> dict[str, float]:
    values: dict[str, float] = {}
    if isinstance(payload, dict):
        for key, raw in payload.items():
            clean_key = f"{prefix}{str(key).lower()}" if prefix else str(key).lower()
            num = _safe_float(raw)
            if num is not None:
                values[clean_key] = num
            else:
                nested = _collect_metric_values(raw, f"{clean_key}_")
                values.update(nested)
    return values


def _pick_metric(values: dict[str, float], aliases: tuple[str, ...]) -> float | None:
    hits: list[float] = []
    for key, value in values.items():
        for alias in aliases:
            if key == alias or key.endswith(f"_{alias}"):
                hits.append(value)
                break
    return max(hits) if hits else None


def _extract_metrics(metrics_json: dict[str, Any] | None, metrics_csv: dict[str, float] | None) -> TrainingMetrics | None:
    values: dict[str, float] = {}
    if metrics_json:
        preferred = None
        for key in ("test", "val", "hybrid", "anomaly"):
            candidate = metrics_json.get(key)
            if isinstance(candidate, dict):
                preferred = candidate
                break
        values.update(_collect_metric_values(preferred if preferred is not None else metrics_json))
    if metrics_csv:
        values.update(metrics_csv)

    metrics = TrainingMetrics(
        accuracy=_pick_metric(values, ("accuracy", "acc")),
        f1=_pick_metric(values, ("f1", "f1_score")),
        auc=_pick_metric(values, ("roc_auc", "auc", "auroc")),
        precision=_pick_metric(values, ("precision",)),
        recall=_pick_metric(values, ("recall",)),
    )
    if all(getattr(metrics, field) is None for field in ("accuracy", "f1", "auc", "precision", "recall")):
        return None
    return metrics


def _training_audit(root: Path) -> dict[str, Any] | None:
    return _read_json(root / "reports" / "TRAINING_DATA.json")


def _domain_entry_status(domain: str, audit: dict[str, Any] | None) -> bool:
    if not audit:
        return False

    required = audit.get("required", [])
    optional = audit.get("optional", [])
    required_names = {
        "fraud": ("Fraud (creditcard.csv)",),
        "cyber": ("Cyber (UNSW_NB15_training-set.csv)",),
        "behavior": ("Behavior (online_shoppers_intention.csv)",),
        "voice": ("Voice emotion (wav folders)",),
    }
    optional_names = {
        "recommender": ("MovieLens recommender",),
    }

    def _is_ok(items: list[dict[str, Any]], names: tuple[str, ...]) -> bool:
        for item in items:
            if item.get("name") in names and str(item.get("status", "")).lower() == "ok":
                return True
        return False

    if domain in required_names:
        return _is_ok(required, required_names[domain])

    if domain == "vision":
        vision_tokens = ("vision", "face emotion", "video temporal")
        for item in optional:
            name = str(item.get("name", "")).lower()
            if any(token in name for token in vision_tokens) and str(item.get("status", "")).lower() == "ok":
                return True
        return False

    if domain in optional_names:
        return _is_ok(optional, optional_names[domain])

    if domain == "fusion":
        return all(_domain_entry_status(dep, audit) for dep in ("fraud", "cyber", "behavior"))

    return False


def _model_ready(root: Path, domain: str) -> bool:
    paths = MODEL_PATHS.get(domain, ())
    if not paths:
        return False
    if domain in {"behavior", "vision", "voice"}:
        return any((root / p).exists() for p in paths)
    if domain == "recommender":
        primary = (
            root / "models/recommender/recommender_model.pkl"
        ).exists() and (root / "models/recommender/recommender_meta.joblib").exists()
        movielens = (
            root / "models/recommender/movielens_model.pkl"
        ).exists() and (root / "models/recommender/movielens_meta.joblib").exists()
        return primary or movielens
    return all((root / p).exists() for p in paths)


def _metrics_sources(
    root: Path,
    domain: str,
) -> tuple[Path | None, dict[str, Any] | None, dict[str, float] | None, bool]:
    json_candidates = [
        root / "experiments" / domain / "metrics" / "metrics.json",
    ]
    csv_candidates = [
        root / "experiments" / domain / "metrics" / "metrics.csv",
    ]
    if domain == "vision":
        json_candidates.extend(
            [
                root / "experiments" / "vision" / "video_temporal" / "metrics.json",
                root / "experiments" / "vision" / "temporal_lstm" / "metrics.json",
            ]
        )
    elif domain == "recommender":
        json_candidates.extend(
            [
                root / "experiments" / "recommender" / "metrics" / "recommender_metrics.json",
                root / "experiments" / "recommender" / "metrics" / "movielens_metrics.json",
            ]
        )
    elif domain == "voice":
        json_candidates.extend(
            [
                root / "reports" / "execution_voice_pipeline_summary.json",
                root / "reports" / "evaluation_voice_metrics_summary.json",
            ]
        )

    metrics_parse_error = False
    for path in json_candidates:
        data, parse_error = _read_json_with_error(path)
        if parse_error:
            metrics_parse_error = True
            continue
        if data is not None:
            return path, data, None, metrics_parse_error

    for path in csv_candidates:
        data = _read_metrics_csv(path)
        if data is not None:
            return path, None, data, metrics_parse_error

    return None, None, None, metrics_parse_error


def _build_domain(root: Path, domain: str, audit: dict[str, Any] | None) -> TrainingDomain:
    dataset_ready = _domain_entry_status(domain, audit)
    model_ready = _model_ready(root, domain)
    source_path, metrics_json, metrics_csv, metrics_parse_error = _metrics_sources(root, domain)
    metrics = _extract_metrics(metrics_json, metrics_csv)

    blockers: list[str] = []
    if audit is None:
        blockers.append("missing_training_audit")
    if not dataset_ready:
        blockers.append("dataset_not_ready")
    if not model_ready:
        blockers.append("model_not_ready")
    if metrics is None:
        blockers.append("metrics_parse_error" if metrics_parse_error else "metrics_missing")
    elif metrics_parse_error:
        blockers.append("metrics_parse_error")

    if dataset_ready and model_ready and metrics is not None:
        status = "ready"
    elif dataset_ready or model_ready or metrics is not None:
        status = "warning"
    else:
        status = "missing"

    updated_at: str | None = None
    if source_path and source_path.exists():
        updated_at = datetime.fromtimestamp(source_path.stat().st_mtime, UTC).replace(microsecond=0).isoformat()

    return TrainingDomain(
        domain=domain,
        status=status,
        datasetReady=dataset_ready,
        modelReady=model_ready,
        metrics=metrics,
        sourcePath=str(source_path) if source_path else "",
        updatedAt=updated_at,
        blockers=blockers,
    )


def build_training_overview(root: Path | None = None) -> TrainingOverview:
    root_path = root or REPO_ROOT
    audit = _training_audit(root_path)
    domains = [_build_domain(root_path, domain, audit) for domain in CORE_DOMAINS]
    generated_at = (audit or {}).get("generated_at") if isinstance(audit, dict) else None

    return TrainingOverview(
        generatedAt=str(generated_at) if generated_at else _now_utc(),
        domains=domains,
        readyCount=sum(1 for domain in domains if domain.status == "ready"),
        totalCount=len(domains),
    )


@router.get("/overview", response_model=TrainingOverview)
def training_overview() -> TrainingOverview:
    return build_training_overview()


@router.get("/domain/{domain}", response_model=TrainingDomain)
def training_domain(domain: str) -> TrainingDomain:
    normalized = domain.strip().lower()
    if normalized not in CORE_DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    overview = build_training_overview()
    for entry in overview.domains:
        if entry.domain == normalized:
            return entry
    raise HTTPException(status_code=404, detail=f"Domain '{domain}' not available")
