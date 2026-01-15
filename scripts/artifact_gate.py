from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
REPORT_MD = REPORT_DIR / "ARTIFACT_GATE.md"
REPORT_JSON = REPORT_DIR / "ARTIFACT_GATE.json"


def _path_ready(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_dir():
        try:
            return any(path.iterdir())
        except Exception:
            return False
    return True


def _collect(items: Iterable[tuple[str, str]], required: bool) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for name, rel_path in items:
        path = ROOT / rel_path
        ok = _path_ready(path)
        results.append(
            {
                "name": name,
                "path": rel_path,
                "required": required,
                "status": "ok" if ok else "missing",
            }
        )
    return results


def main() -> int:
    strict = os.getenv("ARTIFACT_GATE_STRICT", "true").lower() in {"1", "true", "yes"}

    required_items = [
        ("Fraud model", "models/fraud/supervised/fraud_model.pkl"),
        ("Cyber model", "models/cyber/supervised/cyber_model.pkl"),
        ("Behavior model", "models/behavior/behavior_supervised.pkl"),
        ("Behavior LOF", "models/behavior/behavior_lof.pkl"),
        ("Voice emotion", "models/voice_emotion.pkl"),
        ("Recommender model", "models/recommender/recommender_model.pkl"),
        ("Recommender meta", "models/recommender/recommender_meta.joblib"),
        ("MovieLens model", "models/recommender/movielens_model.pkl"),
        ("MovieLens meta", "models/recommender/movielens_meta.joblib"),
        ("Vision ResNet", "models/vision/resnet/model.pt"),
        ("Vision ResNet classes", "models/vision/resnet/classes.txt"),
        ("Face emotion model", "models/vision/face_emotion/model.pt"),
        ("Face emotion classes", "models/vision/face_emotion/classes.txt"),
        ("Vision temporal model", "models/vision/video_temporal_model.pkl"),
        ("Temporal LSTM", "artifacts/vision_temporal/temporal_lstm.pt"),
        ("Brand YOLO", "artifacts/brand/yolo_logo_det.pt"),
        ("Fusion model", "models/fusion/fusion_meta_model.pkl"),
        ("DVC lock", "dvc.lock"),
    ]

    optional_items = [
        ("DSA embeddings", "data/dsa_embeddings"),
        ("DSA Chroma index", "chroma/dsa"),
        ("RAG embeddings", "data/embeddings"),
    ]

    required = _collect(required_items, required=True)
    optional = _collect(optional_items, required=False)

    missing_required = [item for item in required if item["status"] == "missing"]
    missing_optional = [item for item in optional if item["status"] == "missing"]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "required": required,
        "optional": optional,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "strict": strict,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = ["# Artifact Gate Report", ""]
    lines.append(f"- Generated: {report['generated_at']}")
    lines.append(f"- Strict mode: {strict}")
    lines.append("")
    lines.append("## Required artifacts")
    for item in required:
        marker = "ok" if item["status"] == "ok" else "missing"
        lines.append(f"- {marker}: `{item['path']}` ({item['name']})")
    lines.append("")
    lines.append("## Optional artifacts")
    for item in optional:
        marker = "ok" if item["status"] == "ok" else "missing"
        lines.append(f"- {marker}: `{item['path']}` ({item['name']})")
    lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    if missing_required and strict:
        print("Artifact gate failed. Missing required artifacts:")
        for item in missing_required:
            print(f"- {item['path']} ({item['name']})")
        return 1

    if missing_required:
        print("Artifact gate: missing required artifacts (strict mode disabled).")
    if missing_optional:
        print("Artifact gate: missing optional artifacts.")
    print(f"Wrote {REPORT_MD} and {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
