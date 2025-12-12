#!/usr/bin/env python3
"""Generate electronics and course CSVs from Kaggle downloads for OmniNex Chat."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

LOGGER = logging.getLogger(__name__)

ELECTRONICS_FIELDS = ["itemId", "brand", "model", "price", "rating", "popularity", "tags"]
COURSE_FIELDS = ["courseId", "title", "platform", "difficulty", "rating", "popularity", "tags"]

DOMAIN_KEYWORDS = {
    "phones": {
        "phone",
        "smartphone",
        "cell phone",
        "mobile",
        "iphone",
        "galaxy",
        "pixel",
        "android",
        "cell",
    },
    "laptops": {
        "laptop",
        "notebook",
        "macbook",
        "chromebook",
        "dell",
        "lenovo",
        "surface",
        "ultrabook",
        "thinkpad",
    },
    "headphones": {
        "headphone",
        "earbud",
        "earphone",
        "headset",
        "audio",
        "wireless",
        "studio",
        "bluetooth",
        "noise",
    },
}

COURSE_SOURCE_CANDIDATES = (
    "courses_source.csv",
    "courses_raw.csv",
    "courses_feed.csv",
)

COURSE_FALLBACKS = [
    {
        "courseId": "ML-BY-ANDREW",
        "title": "Machine Learning (Stanford University)",
        "platform": "Coursera",
        "difficulty": "Intermediate",
        "rating": 4.8,
        "popularity": 200_000,
        "tags": "machine learning, supervised, statistics, python",
    },
    {
        "courseId": "DS-FOUNDATIONS",
        "title": "Data Science Foundations",
        "platform": "IBM",
        "difficulty": "Beginner",
        "rating": 4.5,
        "popularity": 150_000,
        "tags": "data science, python, foundational, statistics",
    },
    {
        "courseId": "BACKEND-PRO",
        "title": "Full Stack Backend Engineer",
        "platform": "Pluralsight",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "popularity": 72_000,
        "tags": "backend, api, docker, cloud, microservices",
    },
    {
        "courseId": "ML-ENGINEER",
        "title": "Machine Learning Engineer Nanodegree",
        "platform": "Udacity",
        "difficulty": "Advanced",
        "rating": 4.7,
        "popularity": 63_000,
        "tags": "ml, deployment, python, ai, production",
    },
    {
        "courseId": "CS-BUILD",
        "title": "Computer Science: Algorithms and Data Structures",
        "platform": "edX",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "popularity": 80_000,
        "tags": "algorithms, data structures, problem solving",
    },
]


def _parse_price(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (float, int)):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"nan", "null"}:
        return 0.0
    text = text.replace("$", "").replace(",", "").replace("USD", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def _flatten_categories(raw: object) -> List[str]:
    if not raw:
        return []
    flattened: List[str] = []
    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, list):
                for sub in entry:
                    if isinstance(sub, str) and sub.strip():
                        flattened.append(sub.strip())
            elif isinstance(entry, str) and entry.strip():
                flattened.append(entry.strip())
    elif isinstance(raw, str) and raw.strip():
        flattened.append(raw.strip())
    return flattened


def _tokenize(*texts: Sequence[str]) -> List[str]:
    tokens = []
    pattern = re.compile(r"[a-z0-9]+", re.IGNORECASE)
    for text in texts:
        for match in pattern.findall(text or ""):
            token = match.lower()
            if len(token) > 2:
                tokens.append(token)
    return sorted(set(tokens))


def _guess_domain(title: str, categories: Sequence[str]) -> Optional[str]:
    search_space = f"{title} {' '.join(categories)}".lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in search_space for keyword in keywords):
            return domain
    # fallback: look for exact categories
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(any(keyword in cat.lower() for keyword in keywords) for cat in categories):
            return domain
    return None


def _open_json_file(path: Path) -> Iterable[str]:
    if path.suffix == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def load_metadata(path: Path) -> Dict[str, Dict[str, object]]:
    LOGGER.info("Loading metadata from %s", path)
    metadata: Dict[str, Dict[str, object]] = {}
    with _open_json_file(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            asin = record.get("asin") or record.get("productId")
            if not asin:
                continue
            metadata[asin] = {
                "title": record.get("title") or record.get("name") or "",
                "brand": record.get("brand") or record.get("manufacturer") or "",
                "price": _parse_price(record.get("price")),
                "categories": _flatten_categories(record.get("categories")),
            }
    LOGGER.info("Loaded metadata for %d products", len(metadata))
    return metadata


def load_ratings(path: Path) -> Dict[str, Dict[str, float]]:
    LOGGER.info("Loading ratings from %s", path)
    stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0.0, "total": 0.0})
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 3:
                continue
            product_id = row[1]
            try:
                rating = float(row[2])
            except ValueError:
                continue
            stats[product_id]["count"] += 1.0
            stats[product_id]["total"] += rating
    results: Dict[str, Dict[str, float]] = {}
    for product_id, agg in stats.items():
        count = agg["count"]
        if count == 0:
            continue
        results[product_id] = {"count": count, "avg": agg["total"] / count}
    LOGGER.info("Computed rating stats for %d products", len(results))
    return results


def build_domain_rows(
    metadata: Dict[str, Dict[str, object]],
    ratings: Dict[str, Dict[str, float]],
) -> Dict[str, List[Dict[str, object]]]:
    per_domain: Dict[str, List[Dict[str, object]]] = {"phones": [], "laptops": [], "headphones": []}
    for asin, info in metadata.items():
        title = str(info.get("title") or "")
        categories = list(info.get("categories") or [])
        domain = _guess_domain(title, categories) or ""
        if domain not in per_domain:
            continue
        rating_data = ratings.get(asin, {"avg": 0.0, "count": 0.0})
        tags = _tokenize(info.get("brand") or "", title, " ".join(categories))
        if not tags:
            tags = ["electronics", domain]
        per_domain[domain].append(
            {
                "itemId": asin,
                "brand": info.get("brand") or "Unknown",
                "model": title or "Untitled",
                "price": round(float(info.get("price") or 0.0), 2),
                "rating": round(float(rating_data["avg"]), 2),
                "popularity": int(rating_data["count"]),
                "tags": ", ".join(tags),
            }
        )
    return per_domain


def _write_csv(rows: List[Dict[str, object]], path: Path, fieldnames: Sequence[str]) -> None:
    if not rows:
        LOGGER.warning("No rows to write for %s; skipping", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    LOGGER.info("Wrote %d rows to %s", len(rows), path)


def load_course_candidates(root: Path) -> Tuple[List[Dict[str, object]], Optional[Path]]:
    for candidate in (root / name for name in COURSE_SOURCE_CANDIDATES):
        if candidate.exists():
            LOGGER.info("Using course source %s", candidate)
            return _read_course_csv(candidate), candidate
    LOGGER.info("No course source found; falling back to curated list")
    return COURSE_FALLBACKS, None


def _read_course_csv(path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            course_id = row.get("courseId") or row.get("id") or row.get("title")
            if not course_id:
                continue
            tags = row.get("tags", "")
            rows.append(
                {
                    "courseId": course_id,
                    "title": row.get("title") or course_id,
                    "platform": row.get("platform") or row.get("provider") or "Unknown",
                    "difficulty": row.get("difficulty") or "Intermediate",
                    "rating": float(row.get("rating") or 0),
                    "popularity": int(float(row.get("popularity") or 0)),
                    "tags": tags,
                }
            )
    return rows


def preprocess(
    metadata_path: Optional[Path],
    ratings_path: Optional[Path],
    output_dir: Path,
) -> None:
    if metadata_path and ratings_path and metadata_path.exists() and ratings_path.exists():
        metadata = load_metadata(metadata_path)
        ratings = load_ratings(ratings_path)
        domain_rows = build_domain_rows(metadata, ratings)
        for domain, rows in domain_rows.items():
            destination = output_dir / f"{domain}.csv"
            _write_csv(rows, destination, ELECTRONICS_FIELDS)
    else:
        LOGGER.warning("Missing metadata or rating files; skipping electronics preprocessing.")

    courses, source = load_course_candidates(output_dir)
    courses_sorted = sorted(courses, key=lambda x: (float(x.get("rating", 0)), int(x.get("popularity", 0))), reverse=True)
    _write_csv(courses_sorted, output_dir / "courses.csv", COURSE_FIELDS)
    if source:
        LOGGER.info("Courses data sourced from %s", source)
    else:
        LOGGER.info("Using curated course fallback cannonically.")


def locate_metadata(root: Path, hint: Optional[Path]) -> Optional[Path]:
    if hint and hint.exists():
        return hint
    for pattern in ("meta*Electronics*.json",):
        for candidate in root.glob(pattern):
            return candidate
    return None


def locate_ratings(root: Path, hint: Optional[Path]) -> Optional[Path]:
    if hint and hint.exists():
        return hint
    candidate = root / "ratings_Electronics.csv"
    if candidate.exists():
        return candidate
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess Kaggle electronics downloads for OmniNex.")
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "raw" / "recommendation", help="Base recommendation folder.")
    parser.add_argument("--metadata-file", type=Path, help="Path to meta_Electronics.json (or .gz).")
    parser.add_argument("--ratings-file", type=Path, help="Path to ratings_Electronics.csv.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    metadata_path = locate_metadata(args.data_root, args.metadata_file)
    ratings_path = locate_ratings(args.data_root, args.ratings_file)
    preprocess(metadata_path, ratings_path, args.data_root)


if __name__ == "__main__":
    main()
