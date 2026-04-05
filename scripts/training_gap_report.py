from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.monitoring.status import normalize_freshness_status, normalize_readiness_status

TRAINING_DATA = ROOT / "reports" / "TRAINING_DATA.json"
OUT_MD = ROOT / "reports" / "TRAINING_GAPS.md"
OUT_JSON = ROOT / "reports" / "TRAINING_GAPS.json"
STALE_HOURS = int(os.getenv("REPORT_STALE_HOURS", "48"))


def _path_ready(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_dir():
        try:
            return any(path.iterdir())
        except Exception:
            return False
    return True


def _artifact_status(items: list[tuple[str, str]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name, rel_path in items:
        path = ROOT / rel_path
        status = "ok" if _path_ready(path) else "missing"
        results.append(
            {
                "name": name,
                "path": rel_path,
                "status": status,
                "readiness_status": normalize_readiness_status(status),
                "blocking": normalize_readiness_status(status) == "blocked",
            }
        )
    return results


def _summarize_items(items: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for item in items:
        status = item.get("status", "missing")
        name = item.get("name", "unknown")
        readiness = item.get("readiness_status") or normalize_readiness_status(status)
        lines.append(f"- **{name}** — **{status}**")
        lines.append(f"  - readiness_status: {readiness}")
    return lines


def _summarize_dsa_docs(root: Path) -> dict[str, Any]:
    docs_dir = root / "data" / "dsa_docs"
    if not docs_dir.exists():
        return {"docs_dir": "data/dsa_docs", "doc_count": 0, "topics": []}
    doc_paths = [
        p for p in docs_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt"}
    ]
    topics = sorted(
        {p.relative_to(docs_dir).parts[0] for p in doc_paths if p.relative_to(docs_dir).parts}
    )
    return {"docs_dir": "data/dsa_docs", "doc_count": len(doc_paths), "topics": topics}


def _report_freshness(paths: list[Path]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            rows.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "status": "missing",
                    "readiness_status": "blocked",
                    "blocking": True,
                    "updated_at": None,
                    "age_hours": None,
                }
            )
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        age_hours = round((now - mtime).total_seconds() / 3600, 2)
        rows.append(
            {
                "path": str(path.relative_to(ROOT)),
                "status": "stale" if age_hours > STALE_HOURS else "fresh",
                "readiness_status": normalize_freshness_status(
                    "stale" if age_hours > STALE_HOURS else "fresh"
                ),
                "blocking": age_hours > STALE_HOURS,
                "updated_at": mtime.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "age_hours": age_hours,
            }
        )
    return rows


def _has_text(path: Path, needle: str) -> bool:
    try:
        return needle in path.read_text(encoding="utf-8")
    except OSError:
        return False


def _voice_pipeline_contract() -> dict[str, Any]:
    train_script = ROOT / "app" / "models" / "voice" / "emotion_train.py"
    verify_script = ROOT / "scripts" / "verify_voice_pipeline.py"
    predict_script = ROOT / "app" / "models" / "voice" / "emotion_predict.py"

    checks = [
        {
            "name": "trainer_supports_out_model_arg",
            "status": "ok" if _has_text(train_script, '"--out-model"') else "missing",
            "path": str(train_script.relative_to(ROOT)),
        },
        {
            "name": "verify_script_uses_out_model_arg",
            "status": "ok" if _has_text(verify_script, '"--out-model"') else "missing",
            "path": str(verify_script.relative_to(ROOT)),
        },
        {
            "name": "verify_script_uses_keyword_audio_bytes",
            "status": "ok" if _has_text(verify_script, "predict_emotion(audio_bytes=") else "missing",
            "path": str(verify_script.relative_to(ROOT)),
        },
        {
            "name": "predict_api_keyword_only_audio_bytes",
            "status": "ok" if _has_text(predict_script, "def predict_emotion(*, audio_bytes: bytes") else "missing",
            "path": str(predict_script.relative_to(ROOT)),
        },
    ]
    missing = [check for check in checks if check["status"] != "ok"]
    return {
        "status": "ok" if not missing else "mismatch",
        "readiness_status": "ready" if not missing else "blocked",
        "checks": checks,
        "missing": missing,
    }


def _build_recommendations(
    *,
    missing_artifacts: list[dict[str, Any]],
    required_items: list[dict[str, Any]],
    freshness: list[dict[str, Any]],
    voice_contract: dict[str, Any],
    dsa_topics: list[str],
) -> list[str]:
    recommendations: list[str] = []

    if missing_artifacts:
        missing_paths = ", ".join(sorted({artifact["path"] for artifact in missing_artifacts[:6]}))
        recommendations.append(f"Train/build missing model artifacts: {missing_paths}.")

    required_not_ready = [
        item
        for item in required_items
        if normalize_readiness_status(item.get("readiness_status") or item.get("status")) != "ready"
    ]
    if required_not_ready:
        names = ", ".join(item.get("name", "unknown") for item in required_not_ready)
        recommendations.append(f"Resolve required dataset readiness gaps: {names}.")

    stale_reports = [row for row in freshness if row.get("status") == "stale"]
    missing_reports = [row for row in freshness if row.get("status") == "missing"]
    if stale_reports:
        stale_paths = ", ".join(row["path"] for row in stale_reports)
        recommendations.append(f"Refresh stale audit artifacts: {stale_paths}.")
    if missing_reports:
        missing_paths = ", ".join(row["path"] for row in missing_reports)
        recommendations.append(f"Regenerate missing audit artifacts: {missing_paths}.")

    if voice_contract.get("readiness_status") != "ready":
        recommendations.append(
            "Fix voice pipeline CLI/API contract mismatches before running verify_voice_pipeline."
        )

    if len(dsa_topics) <= 4:
        recommendations.append(
            "Expand DSA RAG docs beyond arrays/search/linked-lists/stack-queue for broader coverage."
        )
    else:
        recommendations.append(
            "Keep extending advanced DSA topics (tries, segment trees, suffix arrays)."
        )

    if not recommendations:
        recommendations.append("No blocking gaps detected. Continue periodic retraining readiness checks.")

    return recommendations


def main() -> int:
    if not TRAINING_DATA.exists():
        raise SystemExit(
            "Missing reports/TRAINING_DATA.json. Run scripts/training_data_audit.py first."
        )

    training_data = json.loads(TRAINING_DATA.read_text(encoding="utf-8"))
    required = training_data.get("required", [])
    optional = training_data.get("optional", [])

    artifacts = _artifact_status(
        [
            ("fraud_model", "models/fraud/supervised/fraud_model.pkl"),
            ("cyber_model", "models/cyber/supervised/cyber_model.pkl"),
            ("behavior_model", "models/behavior/behavior_supervised.pkl"),
            ("behavior_lof", "models/behavior/behavior_lof.pkl"),
            ("voice_emotion", "models/voice_emotion.pkl"),
            ("recommender_model", "models/recommender/recommender_model.pkl"),
            ("recommender_meta", "models/recommender/recommender_meta.joblib"),
            ("movielens_model", "models/recommender/movielens_model.pkl"),
            ("movielens_meta", "models/recommender/movielens_meta.joblib"),
            ("vision_resnet", "models/vision/resnet/model.pt"),
            ("vision_resnet_classes", "models/vision/resnet/classes.txt"),
            ("vision_face_emotion", "models/vision/face_emotion/model.pt"),
            ("vision_face_emotion_classes", "models/vision/face_emotion/classes.txt"),
            ("vision_temporal_sklearn", "models/vision/video_temporal_model.pkl"),
            ("vision_temporal_lstm", "artifacts/vision_temporal/temporal_lstm.pt"),
            ("vision_brand_yolo", "artifacts/brand/yolo_logo_det.pt"),
            ("fusion_model", "models/fusion/fusion_meta_model.pkl"),
        ]
    )
    missing_artifacts = [a for a in artifacts if a["readiness_status"] != "ready"]

    dsa_embed = ROOT / "data" / "dsa_embeddings"
    dsa_docs = _summarize_dsa_docs(ROOT)
    dvc_yaml = ROOT / "dvc.yaml"
    dvc_lock = ROOT / "dvc.lock"

    report_freshness = _report_freshness(
        [
            ROOT / "reports" / "TRAINING_DATA.json",
            ROOT / "reports" / "TRAINING_DATA.md",
            ROOT / "reports" / "TRAINING_GAPS.json",
            ROOT / "reports" / "TRAINING_GAPS.md",
            ROOT / "reports" / "PROJECT_AUDIT.json",
            ROOT / "reports" / "PROJECT_AUDIT.md",
        ]
    )
    voice_contract = _voice_pipeline_contract()
    recommendations = _build_recommendations(
        missing_artifacts=missing_artifacts,
        required_items=required,
        freshness=report_freshness,
        voice_contract=voice_contract,
        dsa_topics=dsa_docs["topics"],
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "advisory": True,
        "status_vocabulary": {
            "canonical": ["ready", "degraded", "blocked", "advisory"],
            "legacy": ["ok", "missing", "warn", "stale", "fresh", "mismatch"],
        },
        "training_data": training_data,
        "artifacts": artifacts,
        "missing_artifacts": missing_artifacts,
        "pipeline_contracts": {
            "voice_pipeline": voice_contract,
        },
        "report_freshness": report_freshness,
        "dvc": {
            "dvc_yaml": str(dvc_yaml),
            "dvc_yaml_exists": dvc_yaml.exists(),
            "dvc_lock": str(dvc_lock),
            "dvc_lock_exists": dvc_lock.exists(),
        },
        "dsa_rag": {
            "docs_dir": dsa_docs["docs_dir"],
            "embed_dir": str(dsa_embed),
            "embed_dir_ready": _path_ready(dsa_embed),
            "doc_count": dsa_docs["doc_count"],
            "topics": dsa_docs["topics"],
        },
        "recommendations": recommendations,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("# Training Gap Analysis\n")
    lines.append(f"- Generated: {payload['generated_at']}\n")
    lines.append("- Advisory: historical evidence only; release readiness is determined by the release bar.\n")

    lines.append("## Data readiness (from TRAINING_DATA.json)\n")
    lines.append("### Required datasets\n")
    lines.extend(_summarize_items(required))
    lines.append("\n### Optional datasets\n")
    lines.extend(_summarize_items(optional))
    lines.append("")

    lines.append("## Model artifact readiness\n")
    for artifact in artifacts:
        lines.append(f"- `{artifact['path']}` — **{artifact['status']}**")
        lines.append(f"  - readiness_status: {artifact['readiness_status']}")
    lines.append("")

    lines.append("## Missing artifacts (must train/build)\n")
    if missing_artifacts:
        for artifact in missing_artifacts:
            lines.append(f"- `{artifact['path']}`")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Pipeline contract checks\n")
    lines.append(f"- Voice pipeline contract: **{voice_contract['status']}**")
    lines.append(f"  - readiness_status: {voice_contract['readiness_status']}")
    for check in voice_contract["checks"]:
        lines.append(f"- `{check['name']}` (`{check['path']}`): **{check['status']}**")
    lines.append("")

    lines.append(f"## Report freshness (stale threshold: {STALE_HOURS}h)\n")
    for row in report_freshness:
        updated_at = row["updated_at"] or "missing"
        age = row["age_hours"] if row["age_hours"] is not None else "n/a"
        lines.append(f"- `{row['path']}` — **{row['status']}** (updated: {updated_at}, age_h: {age})")
        lines.append(f"  - readiness_status: {row['readiness_status']}")
        lines.append(f"  - blocking: {row['blocking']}")
    lines.append("")

    lines.append("## DSA RAG index\n")
    lines.append(
        f"- `{payload['dsa_rag']['embed_dir']}` ready: **{payload['dsa_rag']['embed_dir_ready']}**"
    )
    lines.append(f"- Docs: **{payload['dsa_rag']['doc_count']}**")
    if payload["dsa_rag"]["topics"]:
        topics = ", ".join(payload["dsa_rag"]["topics"])
        lines.append(f"- Topics: {topics}")
    lines.append("")

    lines.append("## DVC status\n")
    lines.append(f"- `dvc.yaml` present: **{payload['dvc']['dvc_yaml_exists']}**")
    lines.append(f"- `dvc.lock` present: **{payload['dvc']['dvc_lock_exists']}**")
    lines.append("")

    lines.append("## Recommendations (current state)\n")
    for item in recommendations:
        lines.append(f"- {item}")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD} and {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
