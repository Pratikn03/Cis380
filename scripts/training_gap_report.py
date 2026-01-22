from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
TRAINING_DATA = ROOT / "reports" / "TRAINING_DATA.json"
OUT_MD = ROOT / "reports" / "TRAINING_GAPS.md"
OUT_JSON = ROOT / "reports" / "TRAINING_GAPS.json"


def _path_ready(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_dir():
        try:
            return any(path.iterdir())
        except Exception:
            return False
    return True


def _artifact_status(items: List[tuple[str, str]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for name, rel_path in items:
        path = ROOT / rel_path
        results.append(
            {
                "name": name,
                "path": rel_path,
                "status": "ok" if _path_ready(path) else "missing",
            }
        )
    return results


def _summarize_items(items: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for item in items:
        status = item.get("status", "missing")
        name = item.get("name", "unknown")
        lines.append(f"- **{name}** — **{status}**")
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
    missing_artifacts = [a for a in artifacts if a["status"] != "ok"]

    dsa_embed = ROOT / "data" / "dsa_embeddings"
    dsa_docs = _summarize_dsa_docs(ROOT)
    dvc_yaml = ROOT / "dvc.yaml"
    dvc_lock = ROOT / "dvc.lock"

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "training_data": training_data,
        "artifacts": artifacts,
        "missing_artifacts": missing_artifacts,
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
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("# Training Gap Analysis\n")
    lines.append(f"- Generated: {payload['generated_at']}\n")

    lines.append("## Data readiness (from TRAINING_DATA.json)\n")
    lines.append("### Required datasets\n")
    lines.extend(_summarize_items(required))
    lines.append("\n### Optional datasets\n")
    lines.extend(_summarize_items(optional))
    lines.append("")

    lines.append("## Model artifact readiness\n")
    for artifact in artifacts:
        lines.append(f"- `{artifact['path']}` — **{artifact['status']}**")
    lines.append("")

    lines.append("## Missing artifacts (must train/build)\n")
    if missing_artifacts:
        for artifact in missing_artifacts:
            lines.append(f"- `{artifact['path']}`")
    else:
        lines.append("- None")
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

    lines.append("## Accuracy + training recommendations\n")
    lines.append("- Video temporal: retrain if new real/fake videos are added; monitor LSTM drift.")
    lines.append(
        "- Behavior model: add more insider-style patterns if false positives remain high."
    )
    lines.append("- Voice emotion: augment with noise if `tests/test_voice_noise.py` fails.")
    lines.append(
        "- Brand YOLO: multi-class (car/fashion) requires its own dataset + retrain."
        " Use BRAND_DATA_YAML + BRAND_OUT_PATH, then set BRAND_MODEL_CAR_PATH/BRAND_MODEL_FASHION_PATH."
    )
    if len(payload["dsa_rag"]["topics"]) <= 4:
        lines.append(
            "- DSA RAG: expand docs beyond arrays/search/linked-lists/stack-queue as coverage grows."
        )
    else:
        lines.append(
            "- DSA RAG: continue adding advanced topics (tries, segment trees, suffix arrays)."
        )
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD} and {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
