from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - optional at import time
    yaml = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
TRAINING_DATA_PATH = REPORTS_DIR / "TRAINING_DATA.json"


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_yaml(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _csv_header(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            return [col.strip() for col in next(csv.reader(handle), [])]
    except Exception:
        return []


def _speaker_id_from_name(stem: str) -> str | None:
    lowered = stem.lower()
    explicit = re.search(r"(?:speaker|spk|user|actor)[-_]?(\d{1,5})", lowered)
    if explicit:
        return f"spk_{int(explicit.group(1)):04d}"
    parts = [part for part in re.split(r"[-_]", lowered) if part]
    for part in reversed(parts):
        if part.isdigit():
            return f"spk_{int(part):04d}"
    return None


def _deterministic_bucket(value: str, buckets: tuple[str, str, str] = ("train", "val", "test")) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    pick = int(digest[:8], 16) % 10
    if pick < 8:
        return buckets[0]
    if pick < 9:
        return buckets[1]
    return buckets[2]


@dataclass(frozen=True)
class SplitContractSpec:
    domain: str
    path: str
    required_tokens: tuple[str, ...]
    split_policy: dict[str, Any]


def _seed_usage_detected(text: str) -> bool:
    patterns = (
        r"random_state\s*=\s*42",
        r"random_state\s*=\s*seed\b",
        r"random_state\s*=\s*int\(\s*seed\s*\)",
        r"random_state\s*=\s*args\.seed\b",
        r"random_state\s*=\s*int\(\s*args\.seed\s*\)",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _default_seed_42_detected(text: str) -> bool:
    patterns = (
        r"\bseed\s*=\s*42\b",
        r"\bdefault\s*=\s*42\b",
        r"cfg\.get\(\s*[\"']seed[\"']\s*,\s*42\s*\)",
        r"os\.getenv\(\s*[\"'][^\"']*SEED[^\"']*[\"']\s*,\s*[\"']?42[\"']?\s*\)",
        r"seed\s*=\s*int\(\s*[^)]*42[^)]*\)",
        r"seed\s*=\s*int\(\s*seed_env\s*\)\s*if\s*seed_env\s*else\s*42",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _seed_contract_check(text: str) -> dict[str, Any]:
    usage_ok = _seed_usage_detected(text)
    default_ok = _default_seed_42_detected(text)
    return {
        "seed_usage_detected": usage_ok,
        "default_seed_42_detected": default_ok,
        "status": "ok" if usage_ok and default_ok else "mismatch",
    }


def _phase0_protocol_split_contract(root: Path) -> dict[str, Any]:
    specs = [
        SplitContractSpec(
            domain="fraud",
            path="src/scripts/run_fraud_experiment.py",
            required_tokens=(
                "test_size=0.4",
                "test_size=0.5",
                "stratify=y",
                "stratify=y_temp",
            ),
            split_policy={
                "shape": "two_stage",
                "effective": {"train": 0.6, "val": 0.2, "test": 0.2},
                "entity_policy": "card_or_account_disjoint_required",
            },
        ),
        SplitContractSpec(
            domain="cyber",
            path="src/scripts/run_cyber_experiment.py",
            required_tokens=(
                "test_size=0.4",
                "test_size=0.5",
                "stratify=y",
                "stratify=y_temp",
            ),
            split_policy={
                "shape": "two_stage",
                "effective": {"train": 0.6, "val": 0.2, "test": 0.2},
                "entity_policy": "flow_or_session_disjoint_required",
            },
        ),
        SplitContractSpec(
            domain="behavior",
            path="src/scripts/run_behavior_experiment.py",
            required_tokens=("test_size=0.3", "stratify=stratify"),
            split_policy={
                "shape": "single_stage",
                "effective": {"train": 0.7, "test": 0.3},
                "entity_policy": "user_disjoint_required",
            },
        ),
        SplitContractSpec(
            domain="voice",
            path="app/models/voice/emotion_train.py",
            required_tokens=("test_size=0.2", "stratify=y"),
            split_policy={
                "shape": "single_stage",
                "effective": {"train": 0.8, "test": 0.2},
                "entity_policy": "speaker_disjoint_required",
            },
        ),
        SplitContractSpec(
            domain="vision_temporal",
            path="src/train/train_video_temporal.py",
            required_tokens=("test_size=0.25",),
            split_policy={
                "shape": "single_stage",
                "effective": {"train": 0.75, "test": 0.25},
                "entity_policy": "video_source_disjoint_required",
            },
        ),
        SplitContractSpec(
            domain="recommender",
            path="src/uais/recommender/train_recommender.py",
            required_tokens=("test_size=0.2", "stratify=y"),
            split_policy={
                "shape": "single_stage",
                "effective": {"train": 0.8, "test": 0.2},
                "entity_policy": "user_time_disjoint_required",
            },
        ),
    ]

    checks: list[dict[str, Any]] = []
    for spec in specs:
        file_path = root / spec.path
        text = _read_text(file_path)
        missing = [token for token in spec.required_tokens if token not in text]
        seed_contract = _seed_contract_check(text)
        status = (
            "ok"
            if file_path.exists() and not missing and seed_contract["status"] == "ok"
            else "mismatch"
        )
        checks.append(
            {
                "domain": spec.domain,
                "path": spec.path,
                "file_exists": file_path.exists(),
                "file_sha256": _sha256(file_path),
                "required_tokens": list(spec.required_tokens),
                "missing_tokens": missing,
                "seed_contract": seed_contract,
                "status": status,
                "split_policy": spec.split_policy,
            }
        )

    return {
        "generated_at": _now_utc(),
        "phase": "P0",
        "status": "ok" if all(check["status"] == "ok" for check in checks) else "attention",
        "checks": checks,
        "notes": [
            "This contract pins split logic by source tokens and file hashes.",
            "Any source change requires explicit contract regeneration and review.",
        ],
    }


def _phase0_leakage_test_report(root: Path, training_data: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    cyber_cfg = _read_yaml(root / "configs" / "cyber_config.yaml")
    cyber_drop = cyber_cfg.get("data", {}).get("drop_columns", []) if cyber_cfg else []
    required_cyber_drop = {"id", "attack_cat"}
    drop_set = {str(col) for col in cyber_drop}
    checks.append(
        {
            "name": "cyber_drop_columns_include_known_leakage_fields",
            "path": "configs/cyber_config.yaml",
            "expected": sorted(required_cyber_drop),
            "found": sorted(drop_set),
            "status": "ok" if required_cyber_drop.issubset(drop_set) else "mismatch",
        }
    )

    fraud_cfg = _read_yaml(root / "configs" / "fraud_config.yaml")
    fraud_path = str(fraud_cfg.get("data", {}).get("path", ""))
    checks.append(
        {
            "name": "fraud_uses_single_canonical_dataset_path",
            "path": "configs/fraud_config.yaml",
            "expected_contains": "creditcard.csv",
            "found": fraud_path,
            "status": "ok" if "creditcard.csv" in fraud_path else "mismatch",
        }
    )

    voice_item = next(
        (item for item in training_data.get("required", []) if item.get("name") == "Voice emotion (wav folders)"),
        {},
    )
    speaker_count = int(voice_item.get("speaker_coverage", {}).get("speaker_count", 0) or 0)
    checks.append(
        {
            "name": "voice_speaker_identity_available_for_split_policy",
            "path": "reports/TRAINING_DATA.json",
            "speaker_count": speaker_count,
            "status": "ok" if speaker_count > 0 else "mismatch",
        }
    )

    # Basic leakage-sensitive column presence checks (informational).
    fraud_header = _csv_header(root / "data" / "raw" / "fraud" / "creditcard.csv")
    cyber_header = _csv_header(root / "data" / "raw" / "cyber" / "UNSW_NB15_training-set.csv")
    behavior_header = _csv_header(root / "data" / "raw" / "behavior" / "online_shoppers_intention.csv")
    checks.extend(
        [
            {
                "name": "fraud_label_column_detected",
                "path": "data/raw/fraud/creditcard.csv",
                "status": "ok" if any(col.lower() == "class" for col in fraud_header) else "missing",
            },
            {
                "name": "cyber_attack_cat_detected_and_must_not_be_used_as_feature",
                "path": "data/raw/cyber/UNSW_NB15_training-set.csv",
                "status": "ok" if any(col.lower() == "attack_cat" for col in cyber_header) else "warn",
            },
            {
                "name": "behavior_target_column_detected_or_placeholder_policy_required",
                "path": "data/raw/behavior/online_shoppers_intention.csv",
                "status": "ok" if any(col.lower() == "revenue" for col in behavior_header) else "warn",
            },
        ]
    )

    return {
        "generated_at": _now_utc(),
        "phase": "P0",
        "status": "ok" if all(check["status"] == "ok" for check in checks) else "attention",
        "checks": checks,
        "notes": [
            "Statuses marked warn indicate required policy enforcement even if source data is optional.",
            "This report does not replace runtime leakage tests; it enforces configuration-level safeguards.",
        ],
    }


def _phase0_reproducibility_report(root: Path) -> dict[str, Any]:
    tracked_files = [
        "configs/base_config.yaml",
        "configs/fraud_config.yaml",
        "configs/cyber_config.yaml",
        "configs/behavior_config.yaml",
        "src/scripts/run_fraud_experiment.py",
        "src/scripts/run_cyber_experiment.py",
        "src/scripts/run_behavior_experiment.py",
        "app/models/voice/emotion_train.py",
        "src/train/train_video_temporal.py",
        "src/uais/recommender/train_recommender.py",
    ]

    config_expectations = [
        ("configs/base_config.yaml", "seed: 42"),
        ("configs/fraud_config.yaml", "model_type: hist_gb"),
        ("configs/cyber_config.yaml", "model_type: hist_gb"),
    ]

    config_checks = []
    for rel_path, token in config_expectations:
        path = root / rel_path
        text = _read_text(path)
        config_checks.append(
            {
                "path": rel_path,
                "token": token,
                "status": "ok" if token in text else "mismatch",
            }
        )

    seed_paths = [
        "src/scripts/run_fraud_experiment.py",
        "src/scripts/run_cyber_experiment.py",
        "src/scripts/run_behavior_experiment.py",
        "app/models/voice/emotion_train.py",
        "src/uais/recommender/train_recommender.py",
    ]
    seed_checks = []
    for rel_path in seed_paths:
        path = root / rel_path
        contract = _seed_contract_check(_read_text(path))
        seed_checks.append({"path": rel_path, **contract})

    fingerprints = []
    for rel_path in tracked_files:
        path = root / rel_path
        fingerprints.append(
            {
                "path": rel_path,
                "exists": path.exists(),
                "sha256": _sha256(path),
            }
        )

    return {
        "generated_at": _now_utc(),
        "phase": "P0",
        "status": (
            "ok"
            if all(check["status"] == "ok" for check in config_checks + seed_checks)
            else "attention"
        ),
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
        },
        "config_checks": config_checks,
        "seed_checks": seed_checks,
        "tracked_fingerprints": fingerprints,
        "notes": [
            "Reproducibility requires stable data snapshots alongside code/config fingerprints.",
            "Use these file hashes as run lineage anchors.",
        ],
    }


def _phase1_data_quality_scorecard(training_data: dict[str, Any]) -> dict[str, Any]:
    required_items = list(training_data.get("required", []))
    optional_items = list(training_data.get("optional", []))
    items = [("required", item) for item in required_items] + [("optional", item) for item in optional_items]

    rows: list[dict[str, Any]] = []
    for tier, item in items:
        name = str(item.get("name", "unknown"))
        status = str(item.get("status", "missing")).lower()
        schema_status = str(item.get("schema", {}).get("status", "")).lower() if isinstance(item.get("schema"), dict) else ""

        score = 0
        if status == "ok":
            score += 60
        elif status in {"warn", "needs_preprocess"}:
            score += 30

        if schema_status == "ok":
            score += 20
        elif schema_status == "warn":
            score += 10

        # Voice-specific quality signals.
        class_balance = item.get("class_balance", {})
        if isinstance(class_balance, dict):
            missing_classes = class_balance.get("missing_classes", [])
            imbalance = class_balance.get("imbalance_ratio_max_to_min_nonzero")
            if isinstance(missing_classes, list) and not missing_classes:
                score += 10
            if isinstance(imbalance, (int, float)) and imbalance <= 2.5:
                score += 10
            if name == "Voice emotion (wav folders)" and item.get("voice_source") == "processed_balanced":
                score += 10

        if name == "Brand (LogoDet-3K raw)" and status == "ok":
            score += 10
        if (
            name == "Brand (prepared YOLO dataset)"
            and bool(item.get("train_exists"))
            and bool(item.get("val_exists"))
        ):
            score += 10

        score = min(100, score)
        rows.append(
            {
                "name": name,
                "tier": tier,
                "status": status,
                "schema_status": schema_status or None,
                "quality_score": score,
                "path": item.get("path"),
            }
        )

    required_rows = [row for row in rows if row["tier"] == "required"]
    optional_rows = [row for row in rows if row["tier"] == "optional"]
    avg_required_score = round(
        sum(row["quality_score"] for row in required_rows) / max(1, len(required_rows)), 2
    )
    avg_all_score = round(sum(row["quality_score"] for row in rows) / max(1, len(rows)), 2)
    low_quality_required = [row["name"] for row in required_rows if row["quality_score"] < 70]
    low_quality_optional = [row["name"] for row in optional_rows if row["quality_score"] < 70]
    status = "ok" if not low_quality_required and avg_required_score >= 85 else "attention"

    return {
        "generated_at": _now_utc(),
        "phase": "P1",
        "status": status,
        "avg_required_quality_score": avg_required_score,
        "avg_all_quality_score": avg_all_score,
        "items": rows,
        "low_quality_required_items": low_quality_required,
        "low_quality_optional_items": low_quality_optional,
        "gates": {
            "target_min_avg_score": 85,
            "target_no_item_below": 70,
            "required_only_blocking": True,
        },
    }


def _phase1_label_review_log(training_data: dict[str, Any]) -> dict[str, Any]:
    queue: list[dict[str, Any]] = []
    for item in training_data.get("required", []):
        name = str(item.get("name", ""))
        schema = item.get("schema") if isinstance(item.get("schema"), dict) else {}
        schema_status = str(schema.get("status", "ok")).lower() if schema else "ok"
        if schema_status in {"warn", "error"}:
            queue.append(
                {
                    "dataset": name,
                    "priority": "high",
                    "reason": f"schema_status={schema_status}",
                    "status": "open",
                }
            )
        if name == "Voice emotion (wav folders)":
            imbalance = item.get("class_balance", {}).get("imbalance_ratio_max_to_min_nonzero")
            if isinstance(imbalance, (int, float)) and imbalance > 2.0:
                queue.append(
                    {
                        "dataset": name,
                        "priority": "medium",
                        "reason": f"class_imbalance_ratio={imbalance}",
                        "status": "open",
                    }
                )

    if not queue:
        queue.append(
            {
                "dataset": "all",
                "priority": "low",
                "reason": "no_critical_label_warnings_detected",
                "status": "monitor",
            }
        )

    return {
        "generated_at": _now_utc(),
        "phase": "P1",
        "status": "ok" if all(item["priority"] == "low" for item in queue) else "attention",
        "policy": {
            "required_fields": ["dataset", "priority", "reason", "status"],
            "allowed_status": ["open", "in_review", "resolved", "monitor"],
        },
        "queue": queue,
    }


def _phase1_entity_overlap_audit(root: Path, training_data: dict[str, Any]) -> dict[str, Any]:
    voice_root = root / "data" / "raw" / "voice"
    speaker_to_bucket: dict[str, str] = {}
    for wav_path in voice_root.rglob("*.wav") if voice_root.exists() else []:
        speaker = _speaker_id_from_name(wav_path.stem)
        if speaker is None:
            continue
        speaker_to_bucket.setdefault(speaker, _deterministic_bucket(speaker))

    train_speakers = {speaker for speaker, bucket in speaker_to_bucket.items() if bucket == "train"}
    val_speakers = {speaker for speaker, bucket in speaker_to_bucket.items() if bucket == "val"}
    test_speakers = {speaker for speaker, bucket in speaker_to_bucket.items() if bucket == "test"}
    overlaps = {
        "train_val": sorted(train_speakers & val_speakers),
        "train_test": sorted(train_speakers & test_speakers),
        "val_test": sorted(val_speakers & test_speakers),
    }

    domain_status = []
    for domain in ("fraud", "cyber", "behavior", "recommender"):
        split_json = root / "data" / "processed" / domain / "splits.json"
        domain_status.append(
            {
                "domain": domain,
                "split_artifact": str(split_json.relative_to(root)),
                "status": "ready_for_overlap_check" if split_json.exists() else "missing_split_artifact",
            }
        )

    return {
        "generated_at": _now_utc(),
        "phase": "P1",
        "status": "ok" if all(len(v) == 0 for v in overlaps.values()) else "attention",
        "voice_speaker_overlap": {
            "speakers_total": len(speaker_to_bucket),
            "train_speakers": len(train_speakers),
            "val_speakers": len(val_speakers),
            "test_speakers": len(test_speakers),
            "overlaps": overlaps,
            "bucket_rule": "sha256(speaker_id) mod 10 -> train(<8), val(=8), test(=9)",
        },
        "other_domains": domain_status,
        "notes": [
            "For non-voice domains, overlap checks require persisted split artifacts with entity IDs.",
        ],
    }


def _read_ablation_summary(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, float]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cfg = str(row.get("", "")).strip() or str(row.get("Unnamed: 0", "")).strip()
            if not cfg:
                cfg = str(row.get("config", "")).strip()
            if not cfg:
                continue
            metrics: dict[str, float] = {}
            for key, value in row.items():
                if key in {"", "Unnamed: 0", "config"}:
                    continue
                try:
                    metrics[key] = float(value) if value not in {None, ""} else float("nan")
                except Exception:
                    continue
            rows[cfg] = metrics
    return rows


def _best_config(summary: dict[str, dict[str, float]], metric: str = "roc_auc") -> dict[str, Any]:
    if not summary:
        return {"config": None, "metric": metric, "value": None}
    best_cfg = None
    best_val = None
    for cfg, metrics in summary.items():
        value = metrics.get(metric)
        if value is None:
            continue
        if best_val is None or value > best_val:
            best_cfg = cfg
            best_val = value
    return {"config": best_cfg, "metric": metric, "value": best_val}


def _phase2_feature_ablation_matrix(root: Path) -> dict[str, Any]:
    domain_paths = {
        "fraud": root / "experiments" / "fraud" / "ablations" / "summary.csv",
        "cyber": root / "experiments" / "cyber" / "ablations" / "summary.csv",
    }

    matrix: dict[str, Any] = {}
    for domain, path in domain_paths.items():
        summary = _read_ablation_summary(path)
        baseline = summary.get("none", {})
        best = _best_config(summary, metric="roc_auc")
        deltas: dict[str, float] = {}
        if baseline and isinstance(best.get("value"), float):
            base_val = baseline.get("roc_auc")
            if isinstance(base_val, float):
                deltas["best_minus_none_roc_auc"] = round(best["value"] - base_val, 6)
        matrix[domain] = {
            "summary_path": str(path.relative_to(root)),
            "status": "ok" if summary else "missing",
            "configs": summary,
            "baseline_none": baseline,
            "best": best,
            "deltas": deltas,
        }

    status = (
        "ok"
        if matrix and all(v["status"] == "ok" and v["best"]["config"] for v in matrix.values())
        else "attention"
    )
    return {
        "generated_at": _now_utc(),
        "phase": "P2",
        "status": status,
        "domains": matrix,
        "notes": [
            "Run src/uais/experiments/feature_ablation.py for domains missing summary.csv.",
        ],
    }


def _phase2_feature_lineage(root: Path, training_data: dict[str, Any]) -> dict[str, Any]:
    def _feature_count_from_token(path: Path, token: str) -> int | None:
        text = _read_text(path)
        match = re.search(rf"{re.escape(token)}\s*=\s*(\d+)", text)
        if not match:
            return None
        return int(match.group(1))

    voice_count = _feature_count_from_token(root / "app" / "models" / "voice" / "emotion_train.py", "FEATURE_COUNT")
    temporal_count = len(re.findall(r'^\s*"[^"]+",?\s*$', _read_text(root / "src" / "uais_v" / "models" / "video_temporal.py"), flags=re.M))
    recommender_count = len(re.findall(r'^\s*"[^"]+",?\s*$', _read_text(root / "src" / "uais" / "recommender" / "feature_engineering.py"), flags=re.M))

    required_names = [item.get("name") for item in training_data.get("required", [])]
    optional_names = [item.get("name") for item in training_data.get("optional", [])]

    lineage = {
        "fraud": {
            "dataset": "Fraud (creditcard.csv)",
            "feature_builder": "src/uais/features/fraud_features.py",
            "trainer": "src/scripts/run_fraud_experiment.py",
            "notes": "time and amount derived features + tabular pipeline",
        },
        "cyber": {
            "dataset": "Cyber (UNSW_NB15_training-set.csv)",
            "feature_builder": "src/uais/features/cyber_features.py",
            "trainer": "src/scripts/run_cyber_experiment.py",
            "notes": "categorical encoding + rate features + supervised/anomaly branches",
        },
        "behavior": {
            "dataset": "Behavior (online_shoppers_intention.csv)",
            "feature_builder": "src/uais/features/behavior_features.py",
            "trainer": "src/scripts/run_behavior_experiment.py",
            "notes": "label placeholder supported + unsupervised anomaly stack",
        },
        "voice": {
            "dataset": "Voice emotion (wav folders)",
            "feature_builder": "app/models/voice/features.py",
            "trainer": "app/models/voice/emotion_train.py",
            "feature_count": voice_count,
            "notes": "MFCC + zcr + rms + pitch + spectral contrast",
        },
        "vision_temporal": {
            "dataset": "Video temporal (real/fake)",
            "feature_builder": "src/uais_v/models/video_temporal.py",
            "trainer": "src/train/train_video_temporal.py",
            "feature_count_approx": temporal_count,
            "notes": "temporal consistency descriptors for deepfake detection",
        },
        "recommender": {
            "dataset": "MovieLens recommender",
            "feature_builder": "src/uais/recommender/feature_engineering.py",
            "trainer": "src/uais/recommender/train_recommender.py",
            "feature_count_approx": recommender_count,
            "notes": "meta-risk features and action policy labels",
        },
        "fusion": {
            "dataset": "fusion_scores.csv or domain score outputs",
            "feature_builder": "src/train/train_fusion.py",
            "trainer": "src/uais/fusion/train_fusion_model.py",
            "notes": "meta-model over fraud/cyber/behavior score channels",
        },
    }

    return {
        "generated_at": _now_utc(),
        "phase": "P2",
        "status": "ok",
        "available_required_datasets": required_names,
        "available_optional_datasets": optional_names,
        "lineage": lineage,
    }


def _exists(root: Path, rel_path: str) -> bool:
    return (root / rel_path).exists()


def _count_py_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for file_path in path.rglob("*.py") if file_path.is_file())


def _read_metrics_summary(root: Path, rel_path: str) -> dict[str, Any]:
    payload = _read_json(root / rel_path)
    if not payload:
        return {"path": rel_path, "status": "missing"}
    summary = {"path": rel_path, "status": "ok"}
    for key in ("accuracy", "f1", "roc_auc", "pr_auc", "macro avg", "weighted avg"):
        if key in payload:
            summary[key] = payload[key]
    if "test" in payload and isinstance(payload["test"], dict):
        for key in ("accuracy", "f1", "roc_auc", "pr_auc"):
            if key in payload["test"]:
                summary[f"test_{key}"] = payload["test"][key]
    return summary


def _mypy_error_count(root: Path) -> int | None:
    audit_path = root / "reports" / "audit_20260121_074621" / "02_mypy.txt"
    text = _read_text(audit_path)
    if not text:
        return None
    return len(re.findall(r":\s*error:", text))


def _phase3_model_optimization(root: Path, *, target_uplift_pct: float) -> dict[str, Any]:
    metric_checks = {
        "fraud": _read_metrics_summary(root, "experiments/fraud/metrics/metrics.json"),
        "cyber": _read_metrics_summary(root, "experiments/cyber/metrics/metrics.json"),
        "behavior": _read_metrics_summary(root, "experiments/behavior/metrics/metrics.json"),
        "vision_temporal": _read_metrics_summary(root, "experiments/vision/video_temporal/metrics.json"),
        "recommender": _read_metrics_summary(root, "experiments/recommender/metrics/metrics.json"),
    }
    required_paths = [
        "app/models/voice/calibration.py",
        "src/mlops/confidence.py",
        "scripts/retrain_all_98.py",
    ]
    path_checks = [{"path": path, "exists": _exists(root, path)} for path in required_paths]
    status = (
        "ok"
        if all(item["status"] == "ok" for item in metric_checks.values())
        and all(item["exists"] for item in path_checks)
        else "attention"
    )
    return {
        "generated_at": _now_utc(),
        "phase": "P3",
        "status": status,
        "target_min_relative_uplift_pct": float(target_uplift_pct),
        "metrics": metric_checks,
        "required_paths": path_checks,
        "notes": [
            "Target uplift is a minimum objective, not a guaranteed outcome.",
            "Calibration artifacts are required for release-grade model selection.",
        ],
    }


def _phase4_robustness(root: Path) -> dict[str, Any]:
    checks = [
        {"path": "tests/test_voice_noise.py", "exists": _exists(root, "tests/test_voice_noise.py")},
        {
            "path": "scripts/monitor_video_temporal_drift.py",
            "exists": _exists(root, "scripts/monitor_video_temporal_drift.py"),
        },
        {
            "path": "app/streamlit_chatbot/handlers/static_fallbacks.py",
            "exists": _exists(root, "app/streamlit_chatbot/handlers/static_fallbacks.py"),
        },
        {"path": "ui-web/frontend/src/components/ResultCard.tsx", "exists": _exists(root, "ui-web/frontend/src/components/ResultCard.tsx")},
    ]
    status = "ok" if all(item["exists"] for item in checks) else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P4",
        "status": status,
        "checks": checks,
        "gates": {
            "required_noise_test_present": True,
            "required_drift_monitor_present": True,
            "required_fallback_handlers_present": True,
        },
    }


def _phase5_mlops(root: Path) -> dict[str, Any]:
    model_card_domains = ["fraud", "cyber", "behavior", "vision", "recommender", "fusion"]
    card_checks = [
        {
            "domain": domain,
            "exists": (
                (root / "docs" / "model_cards" / domain).exists()
                and any((root / "docs" / "model_cards" / domain).glob("*.md"))
            ),
        }
        for domain in model_card_domains
    ]
    checks = [
        {"path": "app/mlops/registry.py", "exists": _exists(root, "app/mlops/registry.py")},
        {"path": ".github/workflows/ci-cd.yml", "exists": _exists(root, ".github/workflows/ci-cd.yml")},
        {"path": "scripts/train_all.py", "exists": _exists(root, "scripts/train_all.py")},
    ]
    status = "ok" if all(item["exists"] for item in checks + card_checks) else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P5",
        "status": status,
        "checks": checks,
        "model_cards": card_checks,
    }


def _phase6_api_contracts(root: Path) -> dict[str, Any]:
    test_checks = [
        {"path": "tests/test_monitoring.py", "exists": _exists(root, "tests/test_monitoring.py")},
        {"path": "tests/api/v1/test_training.py", "exists": _exists(root, "tests/api/v1/test_training.py")},
        {"path": "tests/test_api_v1_contract.py", "exists": _exists(root, "tests/test_api_v1_contract.py")},
    ]
    api_checks = [
        {"path": "app/api/monitor.py", "exists": _exists(root, "app/api/monitor.py")},
        {"path": "app/api/v1/training.py", "exists": _exists(root, "app/api/v1/training.py")},
    ]
    monitor_text = _read_text(root / "app" / "api" / "monitor.py")
    typed_usage = "response_model=" in monitor_text
    status = "ok" if all(item["exists"] for item in test_checks + api_checks) and typed_usage else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P6",
        "status": status,
        "api_checks": api_checks,
        "contract_tests": test_checks,
        "typed_response_in_monitor": typed_usage,
    }


def _phase7_dashboard_quality(root: Path) -> dict[str, Any]:
    checks = [
        {"path": "ui-web/frontend/src/pages/Home.tsx", "exists": _exists(root, "ui-web/frontend/src/pages/Home.tsx")},
        {"path": "ui-web/frontend/src/components/Sidebar.tsx", "exists": _exists(root, "ui-web/frontend/src/components/Sidebar.tsx")},
        {"path": "app/streamlit_chatbot/app.py", "exists": _exists(root, "app/streamlit_chatbot/app.py")},
        {"path": "app/streamlit_chatbot/ui/theme.py", "exists": _exists(root, "app/streamlit_chatbot/ui/theme.py")},
    ]
    chat_page = _read_text(root / "ui-web" / "frontend" / "src" / "pages" / "Chat.tsx")
    has_confidence_ui = "Confidence:" in chat_page
    status = "ok" if all(item["exists"] for item in checks) and has_confidence_ui else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P7",
        "status": status,
        "checks": checks,
        "has_confidence_provenance_ui": has_confidence_ui,
    }


def _phase8_sre(root: Path) -> dict[str, Any]:
    checks = [
        {"path": "scripts/system_scorecard.py", "exists": _exists(root, "scripts/system_scorecard.py")},
        {"path": ".github/workflows/scorecard.yml", "exists": _exists(root, ".github/workflows/scorecard.yml")},
        {"path": "docs/TIER6_RUNBOOK.md", "exists": _exists(root, "docs/TIER6_RUNBOOK.md")},
        {"path": "docs/PRODUCTION_DEPLOYMENT.md", "exists": _exists(root, "docs/PRODUCTION_DEPLOYMENT.md")},
    ]
    status = "ok" if all(item["exists"] for item in checks) else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P8",
        "status": status,
        "checks": checks,
    }


def _phase9_security(root: Path) -> dict[str, Any]:
    checks = [
        {"path": "docs/SECURITY.md", "exists": _exists(root, "docs/SECURITY.md")},
        {"path": ".github/workflows/ci-cd.yml", "exists": _exists(root, ".github/workflows/ci-cd.yml")},
    ]
    ci_text = _read_text(root / ".github" / "workflows" / "ci-cd.yml")
    has_pip_audit = "pip-audit" in ci_text

    # Lightweight static check for obvious high-risk hardcoded credential patterns.
    # Keep it bounded to known config entrypoints to avoid heavy recursive scans.
    suspect_hits: list[str] = []
    files_scanned = 0
    candidate_paths = [
        "app/core/config.py",
        "app/main.py",
        "scripts/train_all.py",
        ".env",
        ".env.local",
        ".env.production",
    ]
    for rel_path in candidate_paths:
        path = root / rel_path
        if not path.exists() or not path.is_file():
            continue
        files_scanned += 1
        text = _read_text(path)
        if re.search(r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|BEGIN\s+PRIVATE\s+KEY)", text):
            suspect_hits.append(rel_path)

    status = "ok" if all(item["exists"] for item in checks) and has_pip_audit and not suspect_hits else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P9",
        "status": status,
        "checks": checks,
        "ci_has_pip_audit": has_pip_audit,
        "suspect_secret_hits": suspect_hits,
        "files_scanned": files_scanned,
    }


def _phase10_quality(root: Path) -> dict[str, Any]:
    mypy_errors = _mypy_error_count(root)
    tests_total = _count_py_files(root / "tests")
    checks = [
        {"path": ".github/workflows/quality-gates.yml", "exists": _exists(root, ".github/workflows/quality-gates.yml")},
        {"path": "tests/test_monitoring.py", "exists": _exists(root, "tests/test_monitoring.py")},
    ]
    status = "ok" if all(item["exists"] for item in checks) and tests_total > 0 else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P10",
        "status": status,
        "checks": checks,
        "mypy_error_count_baseline": mypy_errors,
        "python_test_file_count": tests_total,
        "gate_targets": {
            "mypy_errors_target": 0,
            "contract_tests_required": True,
        },
    }


def _phase11_docs_governance(root: Path) -> dict[str, Any]:
    checks = [
        {"path": "docs/ARCHITECTURE.md", "exists": _exists(root, "docs/ARCHITECTURE.md")},
        {"path": "docs/REPRODUCIBILITY.md", "exists": _exists(root, "docs/REPRODUCIBILITY.md")},
        {"path": "docs/CANONICAL.md", "exists": _exists(root, "docs/CANONICAL.md")},
        {"path": "docs/docs-manifest.yml", "exists": _exists(root, "docs/docs-manifest.yml")},
    ]
    model_card_count = (
        sum(1 for _ in (root / "docs" / "model_cards").rglob("*.md"))
        if (root / "docs" / "model_cards").exists()
        else 0
    )
    status = "ok" if all(item["exists"] for item in checks) and model_card_count > 0 else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P11",
        "status": status,
        "checks": checks,
        "model_card_python_file_count": model_card_count,
    }


def _phase12_product_flywheel(root: Path) -> dict[str, Any]:
    checks = [
        {"path": "scripts/training_gap_report.py", "exists": _exists(root, "scripts/training_gap_report.py")},
        {"path": "scripts/full_project_audit.py", "exists": _exists(root, "scripts/full_project_audit.py")},
        {"path": "scripts/system_scorecard.py", "exists": _exists(root, "scripts/system_scorecard.py")},
    ]
    training_data = _read_json(root / "reports" / "TRAINING_DATA.json")
    generated_at = training_data.get("generated_at")
    status = "ok" if all(item["exists"] for item in checks) and generated_at else "attention"
    return {
        "generated_at": _now_utc(),
        "phase": "P12",
        "status": status,
        "checks": checks,
        "latest_training_data_report_generated_at": generated_at,
    }


def _build_master_release_gate(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    phase_order = [f"P{i}" for i in range(13)]
    dependencies = {
        "P0": [],
        "P1": ["P0"],
        "P2": ["P1"],
        "P3": ["P0", "P1", "P2"],
        "P4": ["P3"],
        "P5": ["P3"],
        "P6": ["P3"],
        "P7": ["P6"],
        "P8": ["P6"],
        "P9": ["P6"],
        "P10": ["P0", "P6"],
        "P11": ["P0", "P10"],
        "P12": ["P0", "P3", "P10"],
    }
    phase_status = {phase: payloads.get(phase, {}).get("status", "missing") for phase in phase_order}

    blockers: list[str] = []
    for phase, deps in dependencies.items():
        for dep in deps:
            dep_status = phase_status.get(dep)
            if dep_status != "ok":
                blockers.append(f"{phase} blocked_by {dep} status={dep_status}")

    not_ready = [phase for phase, status in phase_status.items() if status != "ok"]
    release_ready = len(not_ready) == 0 and len(blockers) == 0
    return {
        "generated_at": _now_utc(),
        "status": "ok" if release_ready else "attention",
        "release_ready": release_ready,
        "phase_status": phase_status,
        "dependencies": dependencies,
        "hard_blockers": sorted(set(blockers)),
        "non_ready_phases": not_ready,
    }


def _build_phase_payloads(root: Path, training_data: dict[str, Any], *, target_uplift_pct: float) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {
        "P0": _phase0_protocol_split_contract(root),
        "P0_leakage": _phase0_leakage_test_report(root, training_data),
        "P0_repro": _phase0_reproducibility_report(root),
        "P1": _phase1_data_quality_scorecard(training_data),
        "P1_labels": _phase1_label_review_log(training_data),
        "P1_overlap": _phase1_entity_overlap_audit(root, training_data),
        "P2": _phase2_feature_ablation_matrix(root),
        "P2_lineage": _phase2_feature_lineage(root, training_data),
        "P3": _phase3_model_optimization(root, target_uplift_pct=target_uplift_pct),
        "P4": _phase4_robustness(root),
        "P5": _phase5_mlops(root),
        "P6": _phase6_api_contracts(root),
        "P7": _phase7_dashboard_quality(root),
        "P8": _phase8_sre(root),
        "P9": _phase9_security(root),
        "P10": _phase10_quality(root),
        "P11": _phase11_docs_governance(root),
        "P12": _phase12_product_flywheel(root),
    }
    # P0/P1/P2 top-level statuses should roll up all sub-checks.
    payloads["P0"]["status"] = (
        "ok"
        if payloads["P0"]["status"] == "ok"
        and payloads["P0_leakage"]["status"] == "ok"
        and payloads["P0_repro"]["status"] == "ok"
        else "attention"
    )
    payloads["P1"]["status"] = (
        "ok"
        if payloads["P1"]["status"] == "ok"
        and payloads["P1_labels"]["status"] == "ok"
        and payloads["P1_overlap"]["status"] == "ok"
        else "attention"
    )
    payloads["P2"]["status"] = (
        "ok"
        if payloads["P2"]["status"] == "ok" and payloads["P2_lineage"]["status"] == "ok"
        else "attention"
    )
    return payloads


def generate_phase_0_2_reports(root: Path = ROOT) -> dict[str, Any]:
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    training_data = _read_json(reports_dir / "TRAINING_DATA.json")
    if not training_data:
        raise FileNotFoundError("Missing reports/TRAINING_DATA.json. Run scripts/training_data_audit.py first.")

    outputs = {
        "protocol_split_contract": reports_dir / "protocol_split_contract.json",
        "leakage_test_report": reports_dir / "leakage_test_report.json",
        "reproducibility_report": reports_dir / "reproducibility_report.json",
        "data_quality_scorecard": reports_dir / "data_quality_scorecard.json",
        "label_review_log": reports_dir / "label_review_log.json",
        "entity_overlap_audit": reports_dir / "entity_overlap_audit.json",
        "feature_ablation_matrix": reports_dir / "feature_ablation_matrix.json",
        "feature_lineage": reports_dir / "feature_lineage.json",
    }

    payloads = {
        "protocol_split_contract": _phase0_protocol_split_contract(root),
        "leakage_test_report": _phase0_leakage_test_report(root, training_data),
        "reproducibility_report": _phase0_reproducibility_report(root),
        "data_quality_scorecard": _phase1_data_quality_scorecard(training_data),
        "label_review_log": _phase1_label_review_log(training_data),
        "entity_overlap_audit": _phase1_entity_overlap_audit(root, training_data),
        "feature_ablation_matrix": _phase2_feature_ablation_matrix(root),
        "feature_lineage": _phase2_feature_lineage(root, training_data),
    }

    for key, path in outputs.items():
        _write_json(path, payloads[key])

    return {
        "generated_at": _now_utc(),
        "root": str(root),
        "outputs": {key: str(path) for key, path in outputs.items()},
    }


def generate_phase_0_12_reports(
    root: Path = ROOT,
    *,
    target_uplift_pct: float = 0.31,
) -> dict[str, Any]:
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    training_data = _read_json(reports_dir / "TRAINING_DATA.json")
    if not training_data:
        raise FileNotFoundError("Missing reports/TRAINING_DATA.json. Run scripts/training_data_audit.py first.")

    phase_outputs = {
        "protocol_split_contract": reports_dir / "protocol_split_contract.json",
        "leakage_test_report": reports_dir / "leakage_test_report.json",
        "reproducibility_report": reports_dir / "reproducibility_report.json",
        "data_quality_scorecard": reports_dir / "data_quality_scorecard.json",
        "label_review_log": reports_dir / "label_review_log.json",
        "entity_overlap_audit": reports_dir / "entity_overlap_audit.json",
        "feature_ablation_matrix": reports_dir / "feature_ablation_matrix.json",
        "feature_lineage": reports_dir / "feature_lineage.json",
        "p3_model_optimization": reports_dir / "p3_model_optimization.json",
        "p4_robustness_validation": reports_dir / "p4_robustness_validation.json",
        "p5_mlops_governance": reports_dir / "p5_mlops_governance.json",
        "p6_api_contract_maturity": reports_dir / "p6_api_contract_maturity.json",
        "p7_dashboard_quality": reports_dir / "p7_dashboard_quality.json",
        "p8_sre_readiness": reports_dir / "p8_sre_readiness.json",
        "p9_security_posture": reports_dir / "p9_security_posture.json",
        "p10_quality_engineering": reports_dir / "p10_quality_engineering.json",
        "p11_docs_governance": reports_dir / "p11_docs_governance.json",
        "p12_product_flywheel": reports_dir / "p12_product_flywheel.json",
        "elite_master_release_gate": reports_dir / "elite_master_release_gate.json",
    }

    payloads = _build_phase_payloads(root, training_data, target_uplift_pct=target_uplift_pct)
    master_gate = _build_master_release_gate(payloads)

    output_payloads = {
        "protocol_split_contract": payloads["P0"],
        "leakage_test_report": payloads["P0_leakage"],
        "reproducibility_report": payloads["P0_repro"],
        "data_quality_scorecard": payloads["P1"],
        "label_review_log": payloads["P1_labels"],
        "entity_overlap_audit": payloads["P1_overlap"],
        "feature_ablation_matrix": payloads["P2"],
        "feature_lineage": payloads["P2_lineage"],
        "p3_model_optimization": payloads["P3"],
        "p4_robustness_validation": payloads["P4"],
        "p5_mlops_governance": payloads["P5"],
        "p6_api_contract_maturity": payloads["P6"],
        "p7_dashboard_quality": payloads["P7"],
        "p8_sre_readiness": payloads["P8"],
        "p9_security_posture": payloads["P9"],
        "p10_quality_engineering": payloads["P10"],
        "p11_docs_governance": payloads["P11"],
        "p12_product_flywheel": payloads["P12"],
        "elite_master_release_gate": master_gate,
    }

    for key, path in phase_outputs.items():
        _write_json(path, output_payloads[key])

    return {
        "generated_at": _now_utc(),
        "root": str(root),
        "target_uplift_pct": float(target_uplift_pct),
        "outputs": {key: str(path) for key, path in phase_outputs.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate elite phase governance reports.")
    parser.add_argument(
        "--phase-scope",
        choices=("0-2", "0-12"),
        default="0-12",
        help="Report generation scope (default: 0-12).",
    )
    parser.add_argument(
        "--target-uplift-pct",
        type=float,
        default=0.31,
        help="Target minimum relative uplift percentage used for phase P3 planning.",
    )
    args = parser.parse_args()

    if args.phase_scope == "0-2":
        result = generate_phase_0_2_reports(ROOT)
    else:
        result = generate_phase_0_12_reports(ROOT, target_uplift_pct=float(args.target_uplift_pct))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
