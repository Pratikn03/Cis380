from __future__ import annotations

import csv
import json
import re
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = ROOT / "reports" / "TRAINING_DATA.md"
REPORT_JSON = ROOT / "reports" / "TRAINING_DATA.json"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".mpeg", ".mpg"}


def _count_files(root: Path, pattern: str, limit: int = 5000) -> Tuple[int, bool]:
    if not root.exists():
        return 0, False
    count = 0
    capped = False
    for _ in root.rglob(pattern):
        count += 1
        if count >= limit:
            capped = True
            break
    return count, capped


def _count_ext(root: Path, exts: Iterable[str], limit: int = 5000) -> Tuple[int, bool]:
    if not root.exists():
        return 0, False
    count = 0
    capped = False
    ext_set = {e.lower() for e in exts}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in ext_set:
            count += 1
            if count >= limit:
                capped = True
                break
    return count, capped


def _file_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0
    return round(path.stat().st_size / (1024 * 1024), 2)


def _status(exists: bool) -> str:
    return "ok" if exists else "missing"


def _brand_status(raw_ok: bool, prepared_ok: bool) -> Tuple[str, str]:
    if prepared_ok:
        return "ok", "prepared dataset present"
    if raw_ok:
        return "needs_preprocess", "raw dataset present; run scripts/prepare_brand_data.py"
    return "missing", "raw dataset not found"


def _read_csv_header(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            reader = csv.reader(handle)
            row = next(reader, [])
            return [c.strip() for c in row]
    except Exception:
        return []


def _has_any(header: Iterable[str], candidates: Iterable[str]) -> bool:
    lower = {h.lower() for h in header}
    return any(c.lower() in lower for c in candidates)


def _check_fraud_schema(header: Iterable[str]) -> Dict[str, Any]:
    label_ok = _has_any(header, ["Class", "isFraud", "isfraud"])
    amount_ok = _has_any(header, ["Amount", "amount"])
    time_ok = _has_any(header, ["Time", "time", "step"])
    missing = []
    if not label_ok:
        missing.append("label")
    if not amount_ok:
        missing.append("amount")
    status = "ok" if label_ok and amount_ok else "error"
    note = ""
    if missing:
        note = "missing: " + ", ".join(missing)
    if not time_ok:
        note = (note + "; " if note else "") + "time/step not found (optional)"
    return {
        "status": status,
        "label_ok": label_ok,
        "amount_ok": amount_ok,
        "time_ok": time_ok,
        "note": note,
    }


def _check_cyber_schema(header: Iterable[str]) -> Dict[str, Any]:
    label_ok = _has_any(header, ["label", "class", "target", "attack_cat"])
    status = "ok" if label_ok else "error"
    note = "" if label_ok else "missing: label/class/target/attack_cat"
    return {"status": status, "label_ok": label_ok, "note": note}


def _check_behavior_schema(header: Iterable[str]) -> Dict[str, Any]:
    revenue_ok = _has_any(header, ["Revenue", "revenue"])
    status = "ok" if revenue_ok else "warn"
    note = "" if revenue_ok else "missing: Revenue (loader will add placeholder)"
    return {"status": status, "revenue_ok": revenue_ok, "note": note}


def _check_movielens_schema(header: Iterable[str]) -> Dict[str, Any]:
    user_ok = _has_any(header, ["userId", "userid"])
    movie_ok = _has_any(header, ["movieId", "movieid"])
    rating_ok = _has_any(header, ["rating"])
    status = "ok" if user_ok and movie_ok and rating_ok else "warn"
    missing = []
    if not user_ok:
        missing.append("userId")
    if not movie_ok:
        missing.append("movieId")
    if not rating_ok:
        missing.append("rating")
    note = ""
    if missing:
        note = "missing: " + ", ".join(missing)
    return {"status": status, "note": note}


def _probe_wav(folder: Path) -> Dict[str, Any]:
    if not folder.exists():
        return {"ok": False, "note": "folder missing"}
    for wav_path in folder.rglob("*.wav"):
        try:
            with wave.open(str(wav_path), "rb") as handle:
                return {
                    "ok": True,
                    "path": str(wav_path),
                    "channels": handle.getnchannels(),
                    "sample_rate": handle.getframerate(),
                }
        except Exception as exc:
            return {"ok": False, "path": str(wav_path), "note": f"read failed: {exc}"}
    return {"ok": False, "note": "no wav files"}


def _speaker_id_from_name(stem: str) -> str | None:
    lower = stem.lower()
    explicit = re.search(r"(?:speaker|spk|user|actor)[-_]?(\d{1,4})", lower)
    if explicit:
        return f"spk_{int(explicit.group(1)):03d}"

    parts = [part for part in re.split(r"[-_]", lower) if part]
    for part in reversed(parts):
        if part.isdigit():
            return f"spk_{int(part):03d}"
    return None


def _voice_speaker_coverage(root: Path, emotions: list[str]) -> Dict[str, Any]:
    speaker_counts: Dict[str, int] = {}
    unresolved = 0
    for emotion in emotions:
        folder = root / emotion
        if not folder.exists():
            continue
        for wav_path in folder.rglob("*.wav"):
            speaker_id = _speaker_id_from_name(wav_path.stem)
            if speaker_id is None:
                unresolved += 1
                continue
            speaker_counts[speaker_id] = speaker_counts.get(speaker_id, 0) + 1

    sorted_speakers = sorted(speaker_counts.items(), key=lambda item: (-item[1], item[0]))
    return {
        "speaker_count": len(speaker_counts),
        "resolved_samples": sum(speaker_counts.values()),
        "unresolved_samples": unresolved,
        "top_speakers": [{"speaker_id": sid, "samples": count} for sid, count in sorted_speakers[:20]],
    }


def _resolve_yaml_path(yaml_path: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = (yaml_path.parent / path).resolve()
    return path


def _parse_brand_yaml(yaml_path: Path) -> Dict[str, Any]:
    if not yaml_path.exists():
        return {}
    try:
        import yaml

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        data = None
    if isinstance(data, dict):
        names = data.get("names") if isinstance(data.get("names"), list) else []
        return {
            "path": data.get("path"),
            "train": data.get("train"),
            "val": data.get("val"),
            "names_count": len(names),
        }

    info: Dict[str, Any] = {}
    names_count = 0
    for line in yaml_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("path:"):
            info["path"] = line.split(":", 1)[1].strip()
        elif line.startswith("train:"):
            info["train"] = line.split(":", 1)[1].strip()
        elif line.startswith("val:"):
            info["val"] = line.split(":", 1)[1].strip()
        elif line.startswith("- "):
            names_count += 1
    info["names_count"] = names_count
    return info


def main() -> int:
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    required: list[Dict[str, Any]] = []
    optional: list[Dict[str, Any]] = []

    fraud_csv = ROOT / "data" / "raw" / "fraud" / "creditcard.csv"
    fraud_header = _read_csv_header(fraud_csv)
    fraud_schema = _check_fraud_schema(fraud_header)
    required.append(
        {
            "name": "Fraud (creditcard.csv)",
            "path": str(fraud_csv),
            "status": _status(fraud_csv.is_file()),
            "size_mb": _file_size_mb(fraud_csv),
            "schema": fraud_schema,
            "column_count": len(fraud_header),
            "columns_sample": fraud_header[:8],
        }
    )

    cyber_csv = ROOT / "data" / "raw" / "cyber" / "UNSW_NB15_training-set.csv"
    cyber_header = _read_csv_header(cyber_csv)
    cyber_schema = _check_cyber_schema(cyber_header)
    required.append(
        {
            "name": "Cyber (UNSW_NB15_training-set.csv)",
            "path": str(cyber_csv),
            "status": _status(cyber_csv.is_file()),
            "size_mb": _file_size_mb(cyber_csv),
            "schema": cyber_schema,
            "column_count": len(cyber_header),
            "columns_sample": cyber_header[:8],
        }
    )

    behavior_csv = ROOT / "data" / "raw" / "behavior" / "online_shoppers_intention.csv"
    behavior_header = _read_csv_header(behavior_csv)
    behavior_schema = _check_behavior_schema(behavior_header)
    required.append(
        {
            "name": "Behavior (online_shoppers_intention.csv)",
            "path": str(behavior_csv),
            "status": _status(behavior_csv.is_file()),
            "size_mb": _file_size_mb(behavior_csv),
            "schema": behavior_schema,
            "column_count": len(behavior_header),
            "columns_sample": behavior_header[:8],
        }
    )

    voice_root = ROOT / "data" / "raw" / "voice"
    voice_emotions = ["happy", "sad", "angry", "neutral", "fearful"]
    voice_detail = []
    voice_total = 0
    class_counts: Dict[str, int] = {}
    for emotion in voice_emotions:
        folder = voice_root / emotion
        count, capped = _count_files(folder, "*.wav", limit=5000)
        probe = _probe_wav(folder)
        voice_total += count
        class_counts[emotion] = count
        voice_detail.append(
            {
                "emotion": emotion,
                "path": str(folder),
                "wav_count": count,
                "count_capped": capped,
                "status": _status(folder.exists() and count > 0),
                "probe": probe,
            }
        )
    missing_classes = [emotion for emotion, count in class_counts.items() if count == 0]
    nonzero_counts = [count for count in class_counts.values() if count > 0]
    imbalance_ratio = (
        round(max(nonzero_counts) / min(nonzero_counts), 3) if len(nonzero_counts) >= 2 else None
    )
    speaker_coverage = _voice_speaker_coverage(voice_root, voice_emotions)
    required.append(
        {
            "name": "Voice emotion (wav folders)",
            "path": str(voice_root),
            "status": "ok" if voice_total > 0 else "missing",
            "total_wav": voice_total,
            "details": voice_detail,
            "class_balance": {
                "per_class": class_counts,
                "missing_classes": missing_classes,
                "imbalance_ratio_max_to_min_nonzero": imbalance_ratio,
            },
            "speaker_coverage": speaker_coverage,
        }
    )

    brand_raw_a = ROOT / "data" / "raw" / "brand" / "LogoDet-3K"
    brand_raw_b = ROOT / "data" / "raw" / "brand" / "logodet3k"
    brand_raw_ok = brand_raw_a.exists() or brand_raw_b.exists()
    brand_prepared = ROOT / "data" / "processed" / "brand_yolo" / "brands.yaml"
    brand_prepared_ok = brand_prepared.is_file()
    brand_yaml = _parse_brand_yaml(brand_prepared)
    train_path = _resolve_yaml_path(brand_prepared, brand_yaml.get("train"))
    val_path = _resolve_yaml_path(brand_prepared, brand_yaml.get("val"))
    train_exists = bool(train_path and train_path.exists())
    val_exists = bool(val_path and val_path.exists())
    train_count, train_capped = (
        _count_ext(train_path, IMAGE_EXTS, limit=5000) if train_path else (0, False)
    )
    val_count, val_capped = _count_ext(val_path, IMAGE_EXTS, limit=5000) if val_path else (0, False)
    brand_status, brand_note = _brand_status(brand_raw_ok, brand_prepared_ok)
    if brand_prepared_ok:
        brand_status = "ok" if train_exists and val_exists else "warn"
        if not train_exists or not val_exists:
            brand_note = "brands.yaml paths missing; re-run scripts/prepare_brand_data.py"
    required.append(
        {
            "name": "Brand (LogoDet-3K raw)",
            "path": [str(brand_raw_a), str(brand_raw_b)],
            "status": _status(brand_raw_ok),
        }
    )
    required.append(
        {
            "name": "Brand (prepared YOLO dataset)",
            "path": str(brand_prepared),
            "status": brand_status,
            "note": brand_note,
            "yaml": brand_yaml,
            "train_exists": train_exists,
            "val_exists": val_exists,
            "train_images": train_count,
            "val_images": val_count,
            "train_capped": train_capped,
            "val_capped": val_capped,
        }
    )

    # Optional datasets for extended training
    vision_real = ROOT / "data" / "raw" / "vision" / "train_real"
    vision_fake = ROOT / "data" / "raw" / "vision" / "train_fake"
    vision_real_count, vision_real_capped = _count_ext(vision_real, IMAGE_EXTS, limit=5000)
    vision_fake_count, vision_fake_capped = _count_ext(vision_fake, IMAGE_EXTS, limit=5000)
    optional.append(
        {
            "name": "Vision real/fake (raw)",
            "path": [str(vision_real), str(vision_fake)],
            "status": _status(vision_real.exists() and vision_fake.exists()),
            "real_images": vision_real_count,
            "fake_images": vision_fake_count,
            "real_capped": vision_real_capped,
            "fake_capped": vision_fake_capped,
        }
    )

    celeb_train = ROOT / "data" / "Celeb_V2" / "Train"
    celeb_val = ROOT / "data" / "Celeb_V2" / "Val"
    celeb_train_count, celeb_train_capped = _count_ext(celeb_train, IMAGE_EXTS, limit=5000)
    celeb_val_count, celeb_val_capped = _count_ext(celeb_val, IMAGE_EXTS, limit=5000)
    optional.append(
        {
            "name": "Celeb_V2 (deepfake)",
            "path": [str(celeb_train), str(celeb_val)],
            "status": _status(celeb_train.exists() and celeb_val.exists()),
            "train_images": celeb_train_count,
            "val_images": celeb_val_count,
            "train_capped": celeb_train_capped,
            "val_capped": celeb_val_capped,
        }
    )

    face_emotion = ROOT / "data" / "raw" / "vision" / "face_emotion"
    face_emotion_count, face_emotion_capped = _count_ext(face_emotion, IMAGE_EXTS, limit=5000)
    optional.append(
        {
            "name": "Face emotion (image)",
            "path": str(face_emotion),
            "status": _status(face_emotion.exists()),
            "image_count": face_emotion_count,
            "count_capped": face_emotion_capped,
        }
    )

    video_real = ROOT / "data" / "raw" / "vision" / "video" / "real"
    video_fake = ROOT / "data" / "raw" / "vision" / "video" / "fake"
    video_real_count, video_real_capped = _count_ext(video_real, VIDEO_EXTS, limit=2000)
    video_fake_count, video_fake_capped = _count_ext(video_fake, VIDEO_EXTS, limit=2000)
    optional.append(
        {
            "name": "Video temporal (real/fake)",
            "path": [str(video_real), str(video_fake)],
            "status": _status(video_real.exists() and video_fake.exists()),
            "real_videos": video_real_count,
            "fake_videos": video_fake_count,
            "real_capped": video_real_capped,
            "fake_capped": video_fake_capped,
        }
    )

    movielens = ROOT / "data" / "raw" / "recommendation" / "movielens.csv"
    movielens_header = _read_csv_header(movielens)
    movielens_schema = _check_movielens_schema(movielens_header)
    optional.append(
        {
            "name": "MovieLens recommender",
            "path": str(movielens),
            "status": _status(movielens.is_file()),
            "size_mb": _file_size_mb(movielens),
            "schema": movielens_schema,
            "column_count": len(movielens_header),
            "columns_sample": movielens_header[:6],
        }
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "required": required,
        "optional": optional,
    }

    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Training Data Audit\n")
    lines.append(f"- Generated: {payload['generated_at']}\n")

    lines.append("## Required (production training)\n")
    for item in required:
        lines.append(f"- **{item['name']}** — `{item['path']}` — **{item['status']}**")
        if "size_mb" in item and item["size_mb"]:
            lines.append(f"  - size: {item['size_mb']} MB")
        if item.get("schema"):
            schema = item["schema"]
            note = schema.get("note")
            schema_line = f"  - schema: {schema.get('status')}"
            if note:
                schema_line += f" ({note})"
            lines.append(schema_line)
        if item.get("column_count"):
            lines.append(f"  - columns: {item['column_count']}")
        if item.get("columns_sample"):
            lines.append(f"  - columns_sample: {', '.join(item['columns_sample'])}")
        if "note" in item:
            lines.append(f"  - note: {item['note']}")
        if "train_images" in item:
            train_suffix = " (capped)" if item.get("train_capped") else ""
            val_suffix = " (capped)" if item.get("val_capped") else ""
            lines.append(f"  - train_images: {item['train_images']}{train_suffix}")
            lines.append(f"  - val_images: {item['val_images']}{val_suffix}")
        if item.get("yaml"):
            y = item["yaml"]
            lines.append(
                "  - yaml: "
                f"train={y.get('train') or 'missing'}, "
                f"val={y.get('val') or 'missing'}, "
                f"names={y.get('names_count', 0)}"
            )
        if item.get("details"):
            for detail in item["details"]:
                suffix = " (capped)" if detail["count_capped"] else ""
                probe = detail.get("probe") or {}
                probe_status = "ok" if probe.get("ok") else "fail"
                probe_note = probe.get("note")
                probe_line = f", probe={probe_status}"
                if probe_note:
                    probe_line += f" ({probe_note})"
                lines.append(
                    f"  - {detail['emotion']}: {detail['wav_count']} wav{suffix}{probe_line}"
                )
        if item.get("class_balance"):
            balance = item["class_balance"]
            per_class = balance.get("per_class", {})
            if per_class:
                lines.append(
                    "  - class_balance: "
                    + ", ".join(f"{name}={count}" for name, count in sorted(per_class.items()))
                )
            if balance.get("missing_classes"):
                lines.append(
                    "  - missing_classes: "
                    + ", ".join(str(name) for name in balance["missing_classes"])
                )
            if balance.get("imbalance_ratio_max_to_min_nonzero") is not None:
                lines.append(
                    "  - imbalance_ratio(max/min nonzero): "
                    f"{balance['imbalance_ratio_max_to_min_nonzero']}"
                )
        if item.get("speaker_coverage"):
            speaker = item["speaker_coverage"]
            lines.append(f"  - speakers_detected: {speaker.get('speaker_count', 0)}")
            lines.append(
                "  - speaker_samples: "
                f"resolved={speaker.get('resolved_samples', 0)}, "
                f"unresolved={speaker.get('unresolved_samples', 0)}"
            )

    lines.append("\n## Optional (extended training)\n")
    for item in optional:
        lines.append(f"- **{item['name']}** — `{item['path']}` — **{item['status']}**")
        if "size_mb" in item and item["size_mb"]:
            lines.append(f"  - size: {item['size_mb']} MB")
        if item.get("schema"):
            schema = item["schema"]
            note = schema.get("note")
            schema_line = f"  - schema: {schema.get('status')}"
            if note:
                schema_line += f" ({note})"
            lines.append(schema_line)
        if item.get("column_count"):
            lines.append(f"  - columns: {item['column_count']}")
        if item.get("columns_sample"):
            lines.append(f"  - columns_sample: {', '.join(item['columns_sample'])}")
        if "real_images" in item:
            real_suffix = " (capped)" if item.get("real_capped") else ""
            fake_suffix = " (capped)" if item.get("fake_capped") else ""
            lines.append(f"  - real_images: {item['real_images']}{real_suffix}")
            lines.append(f"  - fake_images: {item['fake_images']}{fake_suffix}")
        if "train_images" in item:
            train_suffix = " (capped)" if item.get("train_capped") else ""
            val_suffix = " (capped)" if item.get("val_capped") else ""
            lines.append(f"  - train_images: {item['train_images']}{train_suffix}")
            lines.append(f"  - val_images: {item['val_images']}{val_suffix}")
        if "image_count" in item:
            image_suffix = " (capped)" if item.get("count_capped") else ""
            lines.append(f"  - image_count: {item['image_count']}{image_suffix}")
        if "real_videos" in item:
            real_suffix = " (capped)" if item.get("real_capped") else ""
            fake_suffix = " (capped)" if item.get("fake_capped") else ""
            lines.append(f"  - real_videos: {item['real_videos']}{real_suffix}")
            lines.append(f"  - fake_videos: {item['fake_videos']}{fake_suffix}")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ wrote {REPORT_MD}")
    print(f"✅ wrote {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
