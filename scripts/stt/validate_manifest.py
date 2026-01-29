from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate STT manifest CSV.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/raw/stt/manifest.csv"),
        help="Manifest CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = args.manifest
    if not manifest.exists():
        raise SystemExit(f"Manifest not found: {manifest}")

    total = 0
    missing_audio = 0
    empty_text = 0
    durations = 0
    duration_sum = 0.0
    splits: Dict[str, int] = {}

    with manifest.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            audio_path = row.get("audio_path") or ""
            text = (row.get("text") or "").strip()
            duration = row.get("duration_sec")
            split = row.get("split")

            if split:
                splits[split] = splits.get(split, 0) + 1

            if not audio_path or not Path(audio_path).exists():
                missing_audio += 1
            if not text:
                empty_text += 1
            if duration:
                try:
                    duration_sum += float(duration)
                    durations += 1
                except ValueError:
                    pass

    print(f"[validate] rows={total}")
    print(f"[validate] missing_audio={missing_audio}")
    print(f"[validate] empty_text={empty_text}")
    if durations:
        avg = duration_sum / durations
        print(f"[validate] avg_duration_sec={avg:.2f}")
    if splits:
        print(f"[validate] splits={splits}")


if __name__ == "__main__":
    main()
