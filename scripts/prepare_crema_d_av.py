"""Prepare CREMA-D video/audio assets for voice-emotion experiments.

The audit noted:
- videos exist (e.g. many *.flv)
- audio_wav == 0
- labels == 0

This script:
- Ensures folders exist under data/raw/crema_d/{video,audio_wav,labels}
- Extracts 16kHz mono WAV audio from every video using ffmpeg
- Infers labels from CREMA-D filename pattern
- Writes data/raw/crema_d/labels/crema_d_labels.csv
- Copies WAVs into data/raw/voice/{happy,sad,angry,neutral} (and optionally fearful)
    mapping HAP/SAD/ANG/NEU and FEA when present.

Important:
- This script can *create* a `fearful/` folder and copy FEA clips into it.
    However, your voice model will only predict classes it was trained on.
    If the local audio set is sparse/absent, the training code may fall back to
    synthetic data, and class availability/quality may vary.

Requirements
------------
- ffmpeg installed and available on PATH (macOS: brew install ffmpeg)

Usage
-----
python scripts/prepare_crema_d_av.py
python scripts/prepare_crema_d_av.py --limit 200 --no-copy-to-voice
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import os
import shutil as _shutil
from dataclasses import dataclass
from pathlib import Path

CREMA_PATTERN = re.compile(
    r"^(?P<speaker>\d{4})_(?P<sent>[A-Z]{3})_(?P<emotion>[A-Z]{3})_(?P<intensity>[A-Z]{2})\.(?P<ext>flv|mp4|avi|mkv|wav)$",
    re.IGNORECASE,
)

# Map to your voice folders (keep DIS dropped by default).
# Note: including FEA here does not "guarantee" the trained model will support it;
# that depends on training data availability and the trained artifact.
EMO_MAP = {"HAP": "happy", "SAD": "sad", "ANG": "angry", "NEU": "neutral", "FEA": "fearful"}

VIDEO_EXTS = {".flv", ".mp4", ".avi", ".mkv"}


@dataclass
class PrepStats:
    video_files: int = 0
    filename_matched: int = 0
    filename_unmatched: int = 0
    wav_created: int = 0
    wav_skipped_existing: int = 0
    wav_failed: int = 0
    labels_rows: int = 0
    copied_to_voice: int = 0
    dropped_unmapped: int = 0


def _ensure_dirs(root: Path) -> dict[str, Path]:
    crema_root = root / "data" / "raw" / "crema_d"
    voice_root = root / "data" / "raw" / "voice"

    video_dir = crema_root / "video"
    wav_dir = crema_root / "audio_wav"
    labels_dir = crema_root / "labels"

    video_dir.mkdir(parents=True, exist_ok=True)
    wav_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    for cls in EMO_MAP.values():
        (voice_root / cls).mkdir(parents=True, exist_ok=True)

    return {
        "project_root": root,
        "crema_root": crema_root,
        "video_dir": video_dir,
        "wav_dir": wav_dir,
        "labels_dir": labels_dir,
        "voice_root": voice_root,
    }


def _ffmpeg_extract_wav(*, video_path: Path, wav_path: Path) -> None:
    ffmpeg = os.environ.get("FFMPEG") or _shutil.which("ffmpeg")
    if not ffmpeg:
        # Common macOS Homebrew paths
        for candidate in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
            if Path(candidate).exists():
                ffmpeg = candidate
                break
    if not ffmpeg:
        raise FileNotFoundError(
            "ffmpeg not found on PATH. Install it (macOS: `brew install ffmpeg`) or set FFMPEG=/path/to/ffmpeg"
        )

    # -ac 1 mono, -ar 16000 resample to 16k
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(wav_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffmpeg failed")


def prepare(
    *,
    project_root: Path,
    limit: int | None = None,
    copy_to_voice: bool = True,
) -> PrepStats:
    paths = _ensure_dirs(project_root)
    video_dir = paths["video_dir"]
    wav_dir = paths["wav_dir"]
    labels_dir = paths["labels_dir"]
    voice_root = paths["voice_root"]

    # Detect videos
    videos = [
        p for p in sorted(video_dir.glob("*")) if p.is_file() and p.suffix.lower() in VIDEO_EXTS
    ]
    if limit is not None:
        videos = videos[:limit]

    stats = PrepStats(video_files=len(videos))

    rows: list[dict[str, str]] = []

    for vp in videos:
        m = CREMA_PATTERN.match(vp.name)
        if not m:
            stats.filename_unmatched += 1
            continue
        stats.filename_matched += 1

        speaker = m.group("speaker")
        sent = m.group("sent").upper()
        emo = m.group("emotion").upper()
        intensity = m.group("intensity").upper()

        wavp = wav_dir / f"{vp.stem}.wav"
        if wavp.exists():
            stats.wav_skipped_existing += 1
        else:
            try:
                _ffmpeg_extract_wav(video_path=vp, wav_path=wavp)
                stats.wav_created += 1
            except Exception:
                stats.wav_failed += 1

        mapped = EMO_MAP.get(emo)
        if mapped is None:
            stats.dropped_unmapped += 1

        if mapped and copy_to_voice and wavp.exists():
            dest = voice_root / mapped / wavp.name
            # Copy (not move) so crema_d/audio_wav remains a full archive
            shutil.copy2(wavp, dest)
            stats.copied_to_voice += 1

        rows.append(
            {
                "file_stem": vp.stem,
                "video_file": str(vp),
                "wav_file": str(wavp),
                "speaker_id": speaker,
                "sentence_code": sent,
                "emotion_code": emo,
                "intensity_code": intensity,
                "mapped_class": mapped if mapped else "DROP",
            }
        )

    out_csv = labels_dir / "crema_d_labels.csv"
    with out_csv.open("w", newline="") as f:
        fieldnames = [
            "file_stem",
            "video_file",
            "wav_file",
            "speaker_id",
            "sentence_code",
            "emotion_code",
            "intensity_code",
            "mapped_class",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    stats.labels_rows = len(rows)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract WAVs + labels from CREMA-D videos")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--no-copy-to-voice",
        action="store_true",
        help="Don't copy mapped WAVs into data/raw/voice/*",
    )

    args = parser.parse_args()
    stats = prepare(
        project_root=args.project_root, limit=args.limit, copy_to_voice=not args.no_copy_to_voice
    )

    print("CREMA-D PREP SUMMARY")
    print("--------------------")
    for k, v in stats.__dict__.items():
        print(f"{k}: {v}")

    print("\nOutputs:")
    print("- data/raw/crema_d/audio_wav/*.wav")
    print("- data/raw/crema_d/labels/crema_d_labels.csv")
    print("- data/raw/voice/{happy,sad,angry,neutral,fearful}/*.wav (copied subset)")


if __name__ == "__main__":
    main()
