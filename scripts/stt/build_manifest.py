from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stt.stt_utils import audio_duration_and_rate, normalize_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build STT manifest CSV from transcripts JSONL.")
    parser.add_argument(
        "--transcripts",
        type=Path,
        default=Path("data/raw/stt/transcripts.jsonl"),
        help="Input transcripts JSONL.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/raw/stt/manifest.csv"),
        help="Output manifest CSV.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize text for training.",
    )
    parser.add_argument(
        "--require-text",
        action="store_true",
        help="Skip entries with empty transcript.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transcripts_path = args.transcripts
    if not transcripts_path.exists():
        raise SystemExit(f"Transcripts not found: {transcripts_path}")

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with (
        transcripts_path.open("r", encoding="utf-8") as handle,
        args.out.open("w", encoding="utf-8", newline="") as out_handle,
    ):
        writer = csv.DictWriter(
            out_handle,
            fieldnames=[
                "audio_path",
                "text",
                "language",
                "duration_sec",
                "sample_rate",
                "speaker_id",
                "source",
                "dataset",
                "sentence_code",
            ],
        )
        writer.writeheader()
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = (record.get("text") or "").strip()
            if args.normalize and text:
                text = normalize_text(text)
            if args.require_text and not text:
                continue

            audio_path = record.get("audio_path")
            duration = record.get("duration_sec")
            sample_rate = record.get("sample_rate")

            if audio_path and (duration is None or sample_rate is None):
                duration, sample_rate = audio_duration_and_rate(Path(audio_path))

            writer.writerow(
                {
                    "audio_path": audio_path,
                    "text": text,
                    "language": record.get("language"),
                    "duration_sec": duration,
                    "sample_rate": sample_rate,
                    "speaker_id": record.get("speaker_id"),
                    "source": record.get("source"),
                    "dataset": record.get("dataset"),
                    "sentence_code": record.get("sentence_code"),
                }
            )

    print(f"[manifest] wrote {args.out}")


if __name__ == "__main__":
    main()
