from __future__ import annotations

import argparse
import csv
import re
import wave
from pathlib import Path
from typing import Iterable


DEFAULT_EMOTIONS = ["angry", "happy", "neutral", "sad", "fearful", "disgust"]


def _read_wav_stats(path: Path) -> tuple[float, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        duration = n / float(sr) if sr else 0.0
    return duration, sr


def _iter_files(folder: Path) -> Iterable[Path]:
    yield from sorted(folder.glob("*.wav"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a voice emotion manifest CSV.")
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/voice"))
    ap.add_argument("--out", type=Path, default=Path("data/raw/voice/manifest.csv"))
    ap.add_argument(
        "--emotions",
        type=str,
        default=",".join(DEFAULT_EMOTIONS),
        help="Comma-separated label folders to include.",
    )
    ap.add_argument(
        "--pattern",
        type=str,
        default=r"^(?P<speaker>\d{4})_.*\.wav$",
        help="Regex to extract speaker ID from filename.",
    )
    ap.add_argument("--min-duration", type=float, default=0.0)
    ap.add_argument("--max-duration", type=float, default=0.0)
    args = ap.parse_args()

    emotions = [e.strip() for e in args.emotions.split(",") if e.strip()]
    pattern = re.compile(args.pattern)

    rows = []
    for emo in emotions:
        folder = args.data_root / emo
        if not folder.exists():
            continue
        for f in _iter_files(folder):
            try:
                duration, sr = _read_wav_stats(f)
            except Exception:
                continue
            if args.min_duration and duration < args.min_duration:
                continue
            if args.max_duration and duration > args.max_duration:
                continue
            m = pattern.match(f.name)
            speaker = m.group("speaker") if m and "speaker" in m.groupdict() else "unknown"
            rows.append(
                {
                    "path": str(f.resolve()),
                    "label": emo,
                    "speaker_id": speaker,
                    "duration_sec": round(float(duration), 6),
                    "sample_rate": int(sr),
                    "source": "voice",
                }
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["path", "label", "speaker_id", "duration_sec", "sample_rate", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[manifest] wrote {args.out} rows={len(rows)}")


if __name__ == "__main__":
    main()
