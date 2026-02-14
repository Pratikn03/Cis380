from __future__ import annotations

import argparse
import json
import re
import statistics
import wave
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_EMOTIONS = ["angry", "happy", "neutral", "sad", "fearful"]


def _read_wav_stats(path: Path) -> tuple[float, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        duration = n / float(sr) if sr else 0.0
    return duration, sr


def audit_dataset(root: Path, emotions: list[str], speaker_pattern: re.Pattern[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "root": str(root),
        "classes": {},
        "total_files": 0,
        "total_speakers": 0,
        "speaker_counts": {},
    }

    speaker_counts: Counter[str] = Counter()
    class_speakers: dict[str, set[str]] = defaultdict(set)

    for emo in emotions:
        folder = root / emo
        files = sorted(folder.glob("*.wav"))
        durations = []
        sample_rates = []
        bad = 0
        for f in files:
            try:
                dur, sr = _read_wav_stats(f)
                durations.append(dur)
                sample_rates.append(sr)
                m = speaker_pattern.match(f.name)
                if m and "speaker" in m.groupdict():
                    sp = m.group("speaker")
                    speaker_counts[sp] += 1
                    class_speakers[emo].add(sp)
            except Exception:
                bad += 1
        stats = {
            "count": len(files),
            "bad": bad,
            "sample_rates": sorted(set(sample_rates)),
        }
        if durations:
            stats.update(
                {
                    "duration_min": min(durations),
                    "duration_max": max(durations),
                    "duration_mean": statistics.mean(durations),
                    "duration_median": statistics.median(durations),
                }
            )
        summary["classes"][emo] = stats
        summary["total_files"] += len(files)

    summary["total_speakers"] = len(speaker_counts)
    summary["speaker_counts"] = dict(speaker_counts.most_common(10))
    summary["class_speakers"] = {k: len(v) for k, v in class_speakers.items()}
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit voice emotion dataset.")
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/voice"))
    ap.add_argument(
        "--emotions",
        type=str,
        default=",".join(DEFAULT_EMOTIONS),
        help="Comma-separated label folders to audit.",
    )
    ap.add_argument(
        "--pattern",
        type=str,
        default=r"^(?P<speaker>\d{4})_.*\.wav$",
        help="Regex to extract speaker ID from filename.",
    )
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    emotions = [e.strip() for e in args.emotions.split(",") if e.strip()]
    pattern = re.compile(args.pattern)
    report = audit_dataset(args.data_root, emotions, pattern)

    print(json.dumps(report, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2))
        print(f"[audit] wrote {args.json_out}")


if __name__ == "__main__":
    main()
