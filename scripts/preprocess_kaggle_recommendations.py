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
        "cell",
        "iphone",
        "galaxy",
        "pixel",
        "android",
        "camera",
        "5g",
    },
    "laptops": {
        "laptop",
        "notebook",
        "macbook",
        "chromebook",
        "dell",
        "lenovo",
        "surface",
        "thinkpad",
        "ssd",
        "intel",
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
        "sound",
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

BRAND_TEMPLATE = {
    "phones": "NovaPhone",
    "laptops": "ApexWorks",
    "headphones": "SonicWave",
}


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


def _tokenize(*texts: Sequence[str]) -> List[str]:
    tokens = []
    pattern = re.compile(r"[a-z0-9]+", re.IGNORECASE)
    for text in texts:
        for match in pattern.findall(text or ""):
            token = match.lower()
            if len(token) > 2:
                tokens.append(token)
    return sorted(set(tokens))


def _open_json_file(path: Path) -> Iterable[str]:
    if path.suffix == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")

def _guess_domain_from_text(text: str) -> Optional[str]:
    search_space = text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in search_space for keyword in keywords):
            return domain
    return None


def _fallback_domain_from_hash(value: str) -> str:
    domains = list(DOMAIN_KEYWORDS.keys())
    if not domains:
        return "phones"
    return domains[hash(value) % len(domains)]


def collect_review_signals(path: Path) -> Dict[str, Dict[str, object]]:
    LOGGER.info("Collecting review signals from %s", path)
    signals: Dict[str, Dict[str, object]] = {}
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
            text_parts = [record.get("summary") or "", record.get("reviewText") or ""]
            combined = " ".join(filter(None, text_parts)).strip()
            if not combined:
                continue
            entry = signals.setdefault(
                asin,
                {
                    "domain_counts": defaultdict(int),
                    "texts": [],
                    "tokens": set(),
                    "summary": record.get("summary") or "",
                },
            )
            entry["texts"].append(combined)
            entry["tokens"].update(_tokenize(combined))
            entry["summary"] = entry["summary"] or record.get("summary") or ""
            domain = _guess_domain_from_text(combined)
            if domain:
                entry["domain_counts"][domain] += 1
    LOGGER.info("Collected signals for %d ASINs", len(signals))
    return signals


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
    reviews: Dict[str, Dict[str, object]],
    ratings: Dict[str, Dict[str, float]],
) -> Dict[str, List[Dict[str, object]]]:
    per_domain: Dict[str, List[Dict[str, object]]] = {"phones": [], "laptops": [], "headphones": []}
    for asin, info in reviews.items():
        domain = (
            max(info["domain_counts"].items(), key=lambda x: x[1])[0]
            if info["domain_counts"]
            else _fallback_domain_from_hash(asin)
        )
        if domain not in per_domain:
            continue
        rating_data = ratings.get(asin, {"avg": 0.0, "count": 0.0})
        summary = info.get("summary") or (info["texts"][0] if info["texts"] else "")
        tokens = sorted(set(info.get("tokens", set())))
        if domain not in tokens:
            tokens.append(domain)
        summary_words = [w.strip(".,!\"'") for w in summary.split() if w.strip()]
        assigned_brand = summary_words[0].title() if summary_words else BRAND_TEMPLATE.get(domain, "OmniTech")
        model_name = " ".join(summary_words[1:4]).title() if len(summary_words) > 1 else asin
        price = 100 + (rating_data.get("avg", 3.0) * 100) + min(400, int(rating_data.get("count", 0) / 5))
        rows = per_domain[domain]
        rows.append(
            {
                "itemId": asin,
                "brand": assigned_brand,
                "model": model_name or asin,
                "price": round(price, 2),
                "rating": round(float(rating_data.get("avg", 0.0)), 2),
                "popularity": int(rating_data.get("count", 0)) or len(info["texts"]),
                "tags": ", ".join(tokens[:10]),
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
        reviews = collect_review_signals(metadata_path)
        ratings = load_ratings(ratings_path)
        domain_rows = build_domain_rows(reviews, ratings)
        for domain, rows in domain_rows.items():
            rows_sorted = sorted(rows, key=lambda x: (x.get("rating", 0.0), x.get("popularity", 0)), reverse=True)
            destination = output_dir / f"{domain}.csv"
            _write_csv(rows_sorted, destination, ELECTRONICS_FIELDS)
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
    for pattern in ("meta*Electronics*.json", "Electronics*.json"):
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
