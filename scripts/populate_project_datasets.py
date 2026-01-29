#!/usr/bin/env python3
"""Populate project dataset layouts from existing archives."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov"}


@dataclass
class LinkStats:
    linked: int = 0
    copied: int = 0
    skipped: int = 0
    failed: int = 0
    per_group: dict[str, int] = field(default_factory=dict)


@dataclass
class WriteStats:
    written: int = 0
    skipped: int = 0
    failed: int = 0
    per_group: dict[str, int] = field(default_factory=dict)


def _hash_path(path: Path) -> str:
    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]


def _safe_link_or_copy(src: Path, dst: Path) -> str:
    if dst.exists():
        return "skipped"
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
        return "linked"
    except OSError:
        try:
            shutil.copy2(src, dst)
            return "copied"
        except Exception:
            return "failed"


def _iter_files(root: Path, exts: set[str]) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def _write_csv_rows(
    path: Path,
    *,
    fieldnames: Sequence[str],
    rows: Iterable[dict[str, object]],
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
            count += 1
    return count


def _normalize_tags(*values: object) -> str:
    tags: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            tags.extend([str(v).strip() for v in value if str(v).strip()])
        else:
            tags.extend([t.strip() for t in str(value).replace("|", ",").split(",") if t.strip()])
    seen = set()
    unique = []
    for tag in tags:
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(tag)
    return ", ".join(unique)


def populate_movielens(stats: LinkStats) -> None:
    dst = Path("data/raw/recommendation/movielens.csv")
    src = Path("data/raw/recommendation/archive (5)/rating.csv")
    if dst.exists():
        stats.skipped += 1
        return
    if not src.exists():
        stats.failed += 1
        print(f"[movielens] missing source: {src}")
        return
    result = _safe_link_or_copy(src, dst)
    setattr(stats, result, getattr(stats, result) + 1)


def populate_movie_items(
    stats: WriteStats,
    *,
    max_rows: int,
    force: bool,
    include_popularity: bool,
) -> None:
    dst = Path("data/raw/recommendation/items.csv")
    src = Path("data/raw/recommendation/archive (5)/movie.csv")
    ratings = Path("data/raw/recommendation/archive (5)/rating.csv")
    if dst.exists() and not force:
        stats.skipped += 1
        return
    if not src.exists():
        stats.failed += 1
        print(f"[items] missing source: {src}")
        return

    popularity: dict[str, int] = {}
    if include_popularity and ratings.exists():
        with ratings.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                movie_id = (row.get("movieId") or row.get("movie_id") or "").strip()
                if not movie_id:
                    continue
                popularity[movie_id] = popularity.get(movie_id, 0) + 1

    def _rows():
        with src.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            count = 0
            for row in reader:
                movie_id = (row.get("movieId") or row.get("movie_id") or "").strip()
                title = (row.get("title") or "").strip()
                genres = (row.get("genres") or "").strip()
                if not movie_id or not title:
                    continue
                yield {
                    "movieId": movie_id,
                    "title": title,
                    "tags": _normalize_tags(genres),
                    "popularity": popularity.get(movie_id, 0),
                }
                count += 1
                if max_rows and count >= max_rows:
                    break

    stats.written = _write_csv_rows(
        dst,
        fieldnames=["movieId", "title", "tags", "popularity"],
        rows=_rows(),
    )


def populate_books_catalog(
    stats: WriteStats,
    *,
    max_rows: int,
    force: bool,
) -> None:
    dst = Path("data/raw/recommendation/books.csv")
    src = Path("data/raw/recommendation/archive (14)/books.csv")
    if dst.exists() and not force:
        stats.skipped += 1
        return
    if not src.exists():
        stats.failed += 1
        print(f"[books] missing source: {src}")
        return

    def _rows():
        with src.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            count = 0
            for row in reader:
                book_id = (row.get("book_id") or row.get("id") or row.get("best_book_id") or "").strip()
                title = (row.get("title") or row.get("original_title") or "").strip()
                authors = (row.get("authors") or "").strip()
                if not book_id or not title:
                    continue
                tags = _normalize_tags(authors, row.get("language_code"))
                yield {
                    "book_id": book_id,
                    "title": title,
                    "authors": authors,
                    "average_rating": (row.get("average_rating") or "").strip(),
                    "ratings_count": (row.get("ratings_count") or "").strip(),
                    "tags": tags,
                }
                count += 1
                if max_rows and count >= max_rows:
                    break

    stats.written = _write_csv_rows(
        dst,
        fieldnames=["book_id", "title", "authors", "average_rating", "ratings_count", "tags"],
        rows=_rows(),
    )


def populate_games_catalog(
    stats: WriteStats,
    *,
    max_rows: int,
    force: bool,
) -> None:
    dst = Path("data/raw/recommendation/games.csv")
    src = Path("data/raw/recommendation/archive (16)/games.csv")
    meta_path = Path("data/raw/recommendation/archive (16)/games_metadata.json")
    if dst.exists() and not force:
        stats.skipped += 1
        return
    if not src.exists():
        stats.failed += 1
        print(f"[games] missing source: {src}")
        return

    meta_tags: dict[str, str] = {}
    if meta_path.exists():
        with meta_path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                app_id = obj.get("app_id")
                if app_id is None:
                    continue
                tags = obj.get("tags") or []
                meta_tags[str(app_id)] = _normalize_tags(tags)

    def _rows():
        with src.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            count = 0
            for row in reader:
                app_id = (row.get("app_id") or row.get("appId") or row.get("id") or "").strip()
                title = (row.get("title") or row.get("name") or "").strip()
                if not app_id or not title:
                    continue
                tags = meta_tags.get(app_id, "")
                yield {
                    "app_id": app_id,
                    "title": title,
                    "tags": tags,
                    "rating": (row.get("rating") or "").strip(),
                    "positive_ratio": (row.get("positive_ratio") or "").strip(),
                    "user_reviews": (row.get("user_reviews") or "").strip(),
                    "price_final": (row.get("price_final") or "").strip(),
                }
                count += 1
                if max_rows and count >= max_rows:
                    break

    stats.written = _write_csv_rows(
        dst,
        fieldnames=[
            "app_id",
            "title",
            "tags",
            "rating",
            "positive_ratio",
            "user_reviews",
            "price_final",
        ],
        rows=_rows(),
    )


def populate_places_catalog(
    stats: WriteStats,
    *,
    max_rows: int,
    force: bool,
) -> None:
    dst = Path("data/raw/recommendation/places.csv")
    src = Path("data/catalogs/places_catalog.jsonl")
    if dst.exists() and not force:
        stats.skipped += 1
        return
    if not src.exists():
        stats.failed += 1
        print(f"[places] missing source: {src}")
        return

    def _rows():
        count = 0
        for line in src.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            title = str(obj.get("title") or "").strip()
            if not title:
                continue
            place_id = (obj.get("id") or obj.get("place_id") or "").strip()
            if not place_id:
                place_id = f"place_{_hash_path(Path(title))}"
            tags = _normalize_tags(
                obj.get("tags"),
                obj.get("category"),
                obj.get("type"),
                obj.get("city"),
                obj.get("country"),
            )
            yield {
                "place_id": place_id,
                "title": title,
                "category": str(obj.get("category") or obj.get("type") or "").strip(),
                "city": str(obj.get("city") or "").strip(),
                "country": str(obj.get("country") or "").strip(),
                "tags": tags,
            }
            count += 1
            if max_rows and count >= max_rows:
                break

    stats.written = _write_csv_rows(
        dst,
        fieldnames=["place_id", "title", "category", "city", "country", "tags"],
        rows=_rows(),
    )


def populate_electronics_catalogs(
    stats: WriteStats,
    *,
    force: bool,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from app.streamlit_chatbot.handlers.electronics_catalog import ELECTRONICS_CATALOG
    except Exception as exc:
        stats.failed += 1
        print(f"[electronics] failed to load fallback catalog: {exc}")
        return

    for domain, items in ELECTRONICS_CATALOG.items():
        dst = Path("data/raw/recommendation") / f"{domain}.csv"
        if dst.exists() and not force:
            stats.skipped += 1
            continue
        rows = []
        for item in items:
            rows.append(
                {
                    "itemId": item.get("itemId"),
                    "title": item.get("title"),
                    "price": item.get("price"),
                    "rating": item.get("rating"),
                    "popularity": item.get("popularity"),
                    "tags": _normalize_tags(item.get("tags")),
                }
            )
        written = _write_csv_rows(
            dst,
            fieldnames=["itemId", "title", "price", "rating", "popularity", "tags"],
            rows=rows,
        )
        stats.written += written
        stats.per_group[domain] = written


def populate_vision_real_fake(stats: LinkStats) -> None:
    src_root = Path("data/raw/vision/Dataset")
    dst_root = Path("data/raw/vision")
    split_map = {"Train": "train", "Validation": "validation"}
    class_map = {"Real": "train_real", "Fake": "train_fake"}

    for split_src, split_dst in split_map.items():
        for cls_src, cls_dst in class_map.items():
            src_dir = src_root / split_src / cls_src
            if not src_dir.exists():
                continue
            dst_dir = dst_root / cls_dst / split_dst
            for img in _iter_files(src_dir, IMAGE_EXTS):
                rel = img.relative_to(src_dir)
                dest = dst_dir / rel
                result = _safe_link_or_copy(img, dest)
                setattr(stats, result, getattr(stats, result) + 1)
                stats.per_group[f"{split_src}/{cls_src}"] = (
                    stats.per_group.get(f"{split_src}/{cls_src}", 0) + (1 if result != "failed" else 0)
                )


def populate_processed_vision(stats: LinkStats) -> None:
    src_root = Path("data/raw/vision/Dataset")
    dst_root = Path("data/processed/vision")
    split_map = {"Train": "train", "Validation": "val"}
    class_map = {"Real": "real", "Fake": "fake"}

    for split_src, split_dst in split_map.items():
        for cls_src, cls_dst in class_map.items():
            src_dir = src_root / split_src / cls_src
            if not src_dir.exists():
                continue
            dst_dir = dst_root / split_dst / cls_dst
            for img in _iter_files(src_dir, IMAGE_EXTS):
                rel = img.relative_to(src_dir)
                dest = dst_dir / rel
                result = _safe_link_or_copy(img, dest)
                setattr(stats, result, getattr(stats, result) + 1)
                stats.per_group[f"{split_src}/{cls_src}"] = (
                    stats.per_group.get(f"{split_src}/{cls_src}", 0) + (1 if result != "failed" else 0)
                )


def populate_celeb_video_links(stats: LinkStats) -> None:
    src_root = Path("data/Celeb_V2/archive (11)")
    dst_root = Path("data/raw/vision/video")
    real_dirs = [src_root / "Celeb-real", src_root / "YouTube-real"]
    fake_dirs = [src_root / "Celeb-synthesis"]

    for label, dirs in [("real", real_dirs), ("fake", fake_dirs)]:
        out_dir = dst_root / label
        for d in dirs:
            if not d.exists():
                continue
            for vid in _iter_files(d, VIDEO_EXTS):
                dest = out_dir / f"{vid.stem}_{_hash_path(vid)}{vid.suffix.lower()}"
                result = _safe_link_or_copy(vid, dest)
                setattr(stats, result, getattr(stats, result) + 1)
                stats.per_group[label] = stats.per_group.get(label, 0) + (1 if result != "failed" else 0)


def _ffmpeg_path() -> str | None:
    return os.environ.get("FFMPEG") or shutil.which("ffmpeg")


def extract_celeb_frames(
    stats: LinkStats,
    *,
    train_ratio: float,
    val_ratio: float,
    seed: int,
    frame_time: str,
    max_videos: int,
) -> None:
    ffmpeg = _ffmpeg_path()
    if not ffmpeg:
        stats.failed += 1
        print("[celeb_frames] ffmpeg not found; skipping frame extraction.")
        return

    src_root = Path("data/Celeb_V2/archive (11)")
    real_dirs = [src_root / "Celeb-real", src_root / "YouTube-real"]
    fake_dirs = [src_root / "Celeb-synthesis"]

    items: list[tuple[Path, str]] = []
    for label, dirs in [("real", real_dirs), ("fake", fake_dirs)]:
        for d in dirs:
            if not d.exists():
                continue
            for vid in _iter_files(d, VIDEO_EXTS):
                items.append((vid, label))

    if max_videos > 0:
        items = items[:max_videos]

    if not items:
        print("[celeb_frames] no videos found under Celeb_V2 archive.")
        return

    random.seed(seed)
    random.shuffle(items)

    total = len(items)
    train_n = int(total * train_ratio)
    val_n = int(total * val_ratio)
    test_n = total - train_n - val_n

    splits = [
        ("Train", items[:train_n]),
        ("Val", items[train_n : train_n + val_n]),
        ("Test", items[train_n + val_n :]),
    ]

    for split_name, split_items in splits:
        for vid, label in split_items:
            out_dir = Path("data/Celeb_V2") / split_name / label
            out_dir.mkdir(parents=True, exist_ok=True)
            dest = out_dir / f"{vid.stem}_{_hash_path(vid)}.jpg"
            if dest.exists():
                stats.skipped += 1
                continue
            cmd = [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                frame_time,
                "-i",
                str(vid),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(dest),
            ]
            try:
                subprocess.run(cmd, check=True)
                stats.copied += 1
                stats.per_group[f"{split_name}/{label}"] = (
                    stats.per_group.get(f"{split_name}/{label}", 0) + 1
                )
            except Exception:
                stats.failed += 1

    print(
        f"[celeb_frames] split counts -> Train: {train_n}, Val: {val_n}, Test: {test_n}"
    )


def _print_stats(title: str, stats: LinkStats) -> None:
    print("\n" + title)
    print("-" * len(title))
    print(f"linked: {stats.linked}")
    print(f"copied: {stats.copied}")
    print(f"skipped: {stats.skipped}")
    print(f"failed: {stats.failed}")
    for key in sorted(stats.per_group):
        print(f"{key}: {stats.per_group[key]}")


def _print_write_stats(title: str, stats: WriteStats) -> None:
    print("\n" + title)
    print("-" * len(title))
    print(f"written: {stats.written}")
    print(f"skipped: {stats.skipped}")
    print(f"failed: {stats.failed}")
    for key in sorted(stats.per_group):
        print(f"{key}: {stats.per_group[key]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate project datasets from archives.")
    parser.add_argument("--skip-movielens", action="store_true")
    parser.add_argument("--skip-vision-raw", action="store_true")
    parser.add_argument("--skip-vision-processed", action="store_true")
    parser.add_argument("--skip-video-links", action="store_true")
    parser.add_argument("--skip-celeb-frames", action="store_true")
    parser.add_argument("--skip-recommender-catalogs", action="store_true")
    parser.add_argument("--skip-electronics-catalogs", action="store_true")
    parser.add_argument("--skip-movie-popularity", action="store_true")
    parser.add_argument("--force-recommender", action="store_true")
    parser.add_argument(
        "--recommender-max-rows",
        type=int,
        default=0,
        help="Cap rows per recommender catalog (0 uses all).",
    )
    parser.add_argument("--frame-time", default="00:00:01")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-videos", type=int, default=0)
    args = parser.parse_args()

    if args.train_ratio <= 0 or args.val_ratio <= 0 or (args.train_ratio + args.val_ratio) >= 1:
        raise SystemExit("train_ratio and val_ratio must be >0 and sum to <1.")

    if not args.skip_movielens:
        stats = LinkStats()
        populate_movielens(stats)
        _print_stats("MovieLens (movielens.csv)", stats)

    if not args.skip_recommender_catalogs:
        max_rows = int(args.recommender_max_rows) if int(args.recommender_max_rows) > 0 else 0
        stats = WriteStats()
        populate_movie_items(
            stats,
            max_rows=max_rows,
            force=bool(args.force_recommender),
            include_popularity=not bool(args.skip_movie_popularity),
        )
        _print_write_stats("Recommender catalog (movies -> items.csv)", stats)

        stats = WriteStats()
        populate_books_catalog(stats, max_rows=max_rows, force=bool(args.force_recommender))
        _print_write_stats("Recommender catalog (books.csv)", stats)

        stats = WriteStats()
        populate_games_catalog(stats, max_rows=max_rows, force=bool(args.force_recommender))
        _print_write_stats("Recommender catalog (games.csv)", stats)

        stats = WriteStats()
        populate_places_catalog(stats, max_rows=max_rows, force=bool(args.force_recommender))
        _print_write_stats("Recommender catalog (places.csv)", stats)

        if not args.skip_electronics_catalogs:
            stats = WriteStats()
            populate_electronics_catalogs(stats, force=bool(args.force_recommender))
            _print_write_stats(
                "Recommender catalog (electronics: phones/laptops/headphones/cameras)",
                stats,
            )

    if not args.skip_vision_raw:
        stats = LinkStats()
        populate_vision_real_fake(stats)
        _print_stats("Vision raw (train_real/train_fake)", stats)

    if not args.skip_vision_processed:
        stats = LinkStats()
        populate_processed_vision(stats)
        _print_stats("Vision processed (data/processed/vision)", stats)

    if not args.skip_video_links:
        stats = LinkStats()
        populate_celeb_video_links(stats)
        _print_stats("Video temporal (data/raw/vision/video)", stats)

    if not args.skip_celeb_frames:
        stats = LinkStats()
        extract_celeb_frames(
            stats,
            train_ratio=float(args.train_ratio),
            val_ratio=float(args.val_ratio),
            seed=int(args.seed),
            frame_time=str(args.frame_time),
            max_videos=int(args.max_videos),
        )
        _print_stats("Celeb_V2 frames (Train/Val/Test)", stats)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
