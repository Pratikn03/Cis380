"""Import Celeb-DF v2 videos into OmniChatX vision folders.

This script keeps the original dataset intact and *copies or hardlinks* videos into:

- data/raw/vision/video/real/
- data/raw/vision/video/fake/

Expected source layout (common for Celeb-DF v2):

data/Video-2/
  Celeb-real/*.mp4
  YouTube-real/*.mp4   (optional)
  Celeb-synthesis/*.mp4

Usage:
  python scripts/import_celeb_df_v2_videos.py
  python scripts/import_celeb_df_v2_videos.py --src data/Video-2 --mode link
  python scripts/import_celeb_df_v2_videos.py --cap 500
  python scripts/import_celeb_df_v2_videos.py --fps 1 --frames-out data/raw/vision/video_frames
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}


@dataclass
class ImportStats:
    scanned: int = 0
    linked: int = 0
    copied: int = 0
    skipped_existing: int = 0
    collisions_deduped: int = 0
    extracted_frames: int = 0


def _iter_videos(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            yield p


def _deduped_dest(out_dir: Path, src_path: Path) -> Path:
    candidate = out_dir / src_path.name
    if not candidate.exists():
        return candidate
    h = hashlib.sha1(str(src_path).encode("utf-8")).hexdigest()[:8]
    return out_dir / f"{src_path.stem}_{h}{src_path.suffix}"


def _link_or_copy(src: Path, dst: Path, *, mode: str) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "skipped"

    if mode == "copy":
        shutil.copy2(src, dst)
        return "copied"

    # mode == "link" (default): try hardlink for zero extra disk; fallback to copy.
    try:
        os.link(src, dst)
        return "linked"
    except OSError:
        shutil.copy2(src, dst)
        return "copied"


def _resolve_source_layout(src: Path, *, include_youtube_real: bool) -> tuple[list[Path], list[Path]]:
    """Return lists of real_dirs, fake_dirs when the expected layout exists."""
    real_dirs: list[Path] = []
    fake_dirs: list[Path] = []

    celeb_real = src / "Celeb-real"
    youtube_real = src / "YouTube-real"
    celeb_synth = src / "Celeb-synthesis"

    if celeb_real.exists():
        real_dirs.append(celeb_real)
    if include_youtube_real and youtube_real.exists():
        real_dirs.append(youtube_real)
    if celeb_synth.exists():
        fake_dirs.append(celeb_synth)

    if real_dirs and fake_dirs:
        return real_dirs, fake_dirs

    # Fallback: keyword scan if the canonical folder names are not present.
    def first_dir(patterns: list[str]) -> Path | None:
        for pat in patterns:
            matches = list(src.glob(pat))
            for m in matches:
                if m.is_dir():
                    return m
        return None

    detected_real = first_dir(["*real*", "*original*", "*auth*"])
    detected_fake = first_dir(["*synth*", "*fake*", "*deepfake*", "*manip*"])
    if detected_real is not None:
        real_dirs.append(detected_real)
    if detected_fake is not None:
        fake_dirs.append(detected_fake)

    if not real_dirs or not fake_dirs:
        raise FileNotFoundError(
            f"Could not find expected Celeb-DF v2 layout under {src}. "
            "Expected at least Celeb-real + Celeb-synthesis (and optionally YouTube-real)."
        )
    return real_dirs, fake_dirs


def _sample_paths(paths: list[Path], *, cap: int | None, seed: int) -> list[Path]:
    if cap is None or cap <= 0 or len(paths) <= cap:
        return paths
    rng = random.Random(seed)
    paths_copy = list(paths)
    rng.shuffle(paths_copy)
    return paths_copy[:cap]


def _extract_frames(
    *,
    video_paths: list[Path],
    out_dir: Path,
    fps: float,
    overwrite: bool,
) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found in PATH; install it or run with --fps 0 to skip extraction.")

    for video in video_paths:
        stem = video.stem
        pattern = out_dir / f"{stem}_%06d.jpg"

        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
        ]
        if not overwrite:
            cmd.append("-n")
        cmd += [
            "-i",
            str(video),
            "-vf",
            f"fps={fps}",
            str(pattern),
        ]
        subprocess.run(cmd, check=False)

    return sum(1 for p in out_dir.rglob("*.jpg") if p.is_file())


def run(
    *,
    src: Path,
    mode: str,
    cap: int | None,
    seed: int,
    include_youtube_real: bool,
    fps: float,
    frames_out: Path,
    overwrite_frames: bool,
) -> dict[str, object]:
    real_dirs, fake_dirs = _resolve_source_layout(src, include_youtube_real=include_youtube_real)

    raw_video_root = Path("data/raw/vision/video")
    out_real = raw_video_root / "real"
    out_fake = raw_video_root / "fake"

    real_videos: list[Path] = []
    fake_videos: list[Path] = []
    for d in real_dirs:
        real_videos.extend(list(_iter_videos(d)))
    for d in fake_dirs:
        fake_videos.extend(list(_iter_videos(d)))

    real_videos = _sample_paths(real_videos, cap=cap, seed=seed)
    fake_videos = _sample_paths(fake_videos, cap=cap, seed=seed + 1)

    stats = ImportStats()

    def ingest(paths: list[Path], dest_dir: Path) -> None:
        for p in paths:
            stats.scanned += 1
            dst = _deduped_dest(dest_dir, p)
            if dst.name != p.name:
                stats.collisions_deduped += 1
            action = _link_or_copy(p, dst, mode=mode)
            if action == "skipped":
                stats.skipped_existing += 1
            elif action == "linked":
                stats.linked += 1
            else:
                stats.copied += 1

    ingest(real_videos, out_real)
    ingest(fake_videos, out_fake)

    # Optional frame extraction (disabled by default; can be large).
    if fps and fps > 0:
        real_frames_out = frames_out / "real"
        fake_frames_out = frames_out / "fake"
        extracted_real_frames = _extract_frames(
            video_paths=real_videos,
            out_dir=real_frames_out,
            fps=fps,
            overwrite=overwrite_frames,
        )
        extracted_fake_frames = _extract_frames(
            video_paths=fake_videos,
            out_dir=fake_frames_out,
            fps=fps,
            overwrite=overwrite_frames,
        )
        stats.extracted_frames = int(extracted_real_frames or 0) + int(extracted_fake_frames or 0)

    def count_videos(p: Path) -> int:
        return sum(1 for _ in _iter_videos(p)) if p.exists() else 0

    return {
        "src": str(src),
        "mode": mode,
        "cap": cap,
        "seed": seed,
        "include_youtube_real": include_youtube_real,
        "dest_real": str(out_real),
        "dest_fake": str(out_fake),
        "real_videos_imported": len(real_videos),
        "fake_videos_imported": len(fake_videos),
        "dest_real_videos_total": count_videos(out_real),
        "dest_fake_videos_total": count_videos(out_fake),
        "fps": fps,
        "frames_out": str(frames_out) if fps and fps > 0 else None,
        "extracted_real_frames": extracted_real_frames if fps and fps > 0 else 0,
        "extracted_fake_frames": extracted_fake_frames if fps and fps > 0 else 0,
        "extracted_frames_total": stats.extracted_frames if fps and fps > 0 else 0,
        "stats": stats.__dict__,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Celeb-DF v2 videos into OmniChatX folders.")
    parser.add_argument("--src", type=Path, default=Path("data/Video-2"))
    parser.add_argument(
        "--mode",
        choices=["link", "copy"],
        default="link",
        help="Use hardlinks (default, saves disk) or copy files.",
    )
    parser.add_argument(
        "--cap",
        type=int,
        default=None,
        help="Optional cap per class (e.g. 500). Applies independently to real and fake.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Seed used when --cap is set.")
    parser.add_argument(
        "--include-youtube-real",
        action="store_true",
        help="Include YouTube-real videos if present (default: true).",
    )
    parser.add_argument(
        "--no-youtube-real",
        action="store_true",
        help="Do not include YouTube-real videos (use only Celeb-real).",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=0.0,
        help="Optional frame extraction FPS (0 disables). WARNING: may generate lots of images.",
    )
    parser.add_argument(
        "--frames-out",
        type=Path,
        default=Path("data/raw/vision/video_frames"),
        help="Output directory for extracted frames when --fps > 0.",
    )
    parser.add_argument(
        "--overwrite-frames",
        action="store_true",
        help="Allow overwriting extracted frames if they already exist.",
    )
    args = parser.parse_args()

    include_youtube_real = True
    if args.no_youtube_real:
        include_youtube_real = False
    if args.include_youtube_real:
        include_youtube_real = True

    out = run(
        src=args.src,
        mode=args.mode,
        cap=args.cap,
        seed=args.seed,
        include_youtube_real=include_youtube_real,
        fps=float(args.fps),
        frames_out=args.frames_out,
        overwrite_frames=args.overwrite_frames,
    )

    print("CELEB_DF_V2 VIDEO IMPORT SUMMARY")
    print("-------------------------------")
    for k, v in out.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
