#!/usr/bin/env python3
"""Map CREMA-D AudioWAV clips into data/raw/voice/<emotion> folders."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

PATTERN = re.compile(
    r"^(?P<speaker>\d{4})_(?P<sent>[A-Z]{3})_(?P<emotion>[A-Z]{3})_(?P<intensity>[A-Z]{2})\.wav$",
    re.IGNORECASE,
)

EMO_MAP = {
    "ANG": "angry",
    "HAP": "happy",
    "NEU": "neutral",
    "SAD": "sad",
    "FEA": "fearful",
    "DIS": "angry",
}


@dataclass
class Stats:
    total: int = 0
    matched: int = 0
    unmatched: int = 0
    dropped: int = 0
    copied: int = 0
    linked: int = 0
    skipped: int = 0
    failed: int = 0
    link_fallback: int = 0
    per_class: dict[str, int] = field(default_factory=dict)


def _safe_link(src: Path, dst: Path) -> bool:
    try:
        os.link(src, dst)
        return True
    except FileExistsError:
        return False
    except OSError:
        return False


def _safe_copy(src: Path, dst: Path) -> bool:
    try:
        shutil.copy2(src, dst)
        return True
    except FileExistsError:
        return False
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy/link CREMA-D AudioWAV files into data/raw/voice/<emotion> folders."
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=Path("data/raw/voice/AudioWAV"),
        help="Source directory containing AudioWAV files.",
    )
    parser.add_argument(
        "--dst",
        type=Path,
        default=Path("data/raw/voice"),
        help="Destination root for emotion folders.",
    )
    parser.add_argument(
        "--mode",
        choices=["copy", "link"],
        default="copy",
        help="Use 'link' to hardlink instead of copying (same disk only).",
    )
    parser.add_argument(
        "--limit-per-class",
        type=int,
        default=0,
        help="Max files per class (0 means no limit).",
    )
    args = parser.parse_args()

    src_dir = args.src
    dst_root = args.dst
    limit = int(args.limit_per_class or 0)

    if not src_dir.exists():
        print(f"[prepare_voice_from_audiowav] Missing source directory: {src_dir}")
        return 2

    for cls in sorted(set(EMO_MAP.values())):
        (dst_root / cls).mkdir(parents=True, exist_ok=True)

    stats = Stats()

    per_class_limit: dict[str, int] = {cls: 0 for cls in set(EMO_MAP.values())}

    for wav in sorted(src_dir.glob("*.wav")):
        stats.total += 1
        match = PATTERN.match(wav.name)
        if not match:
            stats.unmatched += 1
            continue
        stats.matched += 1

        emotion_code = match.group("emotion").upper()
        mapped = EMO_MAP.get(emotion_code)
        if not mapped:
            stats.dropped += 1
            continue

        if limit > 0 and per_class_limit.get(mapped, 0) >= limit:
            stats.skipped += 1
            continue

        dest = dst_root / mapped / wav.name
        if dest.exists():
            stats.skipped += 1
            continue

        ok = False
        linked = False
        if args.mode == "link":
            if _safe_link(wav, dest):
                ok = True
                linked = True
            else:
                ok = _safe_copy(wav, dest)
                if ok:
                    stats.link_fallback += 1
        else:
            ok = _safe_copy(wav, dest)

        if ok:
            per_class_limit[mapped] = per_class_limit.get(mapped, 0) + 1
            stats.per_class[mapped] = stats.per_class.get(mapped, 0) + 1
            if linked:
                stats.linked += 1
            else:
                stats.copied += 1
        else:
            stats.failed += 1

    print("AudioWAV -> voice folder mapping summary")
    print("--------------------------------------")
    print(f"total files: {stats.total}")
    print(f"matched: {stats.matched}")
    print(f"unmatched: {stats.unmatched}")
    print(f"dropped: {stats.dropped}")
    print(f"copied: {stats.copied}")
    print(f"linked: {stats.linked}")
    print(f"link fallback copies: {stats.link_fallback}")
    print(f"skipped: {stats.skipped}")
    print(f"failed: {stats.failed}")
    for cls in sorted(stats.per_class):
        print(f"{cls}: {stats.per_class[cls]}")

    print("\nNext:")
    print("- Run training: python app/models/voice/emotion_train.py --limit-per-class 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
