"""Recommendation helpers for learning resources."""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parents[1].parent
RECOMMENDATION_DIR = BASE_DIR / "data" / "raw" / "recommendation"
COURSE_PATH = RECOMMENDATION_DIR / "courses.csv"


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


@lru_cache(maxsize=1)
def _load_courses() -> List[Dict[str, Any]]:
    if not COURSE_PATH.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with COURSE_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row["rating"] = _parse_float(row.get("rating", "0"))
            row["popularity"] = _parse_float(row.get("popularity", "0"))
            row["tags"] = [t.strip().lower() for t in row.get("tags", "").split(",") if t.strip()]
            rows.append(row)
    return rows


def _extract_skill_keywords(query: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
    skills = [t for t in tokens if len(t) > 3]
    return skills


def recommend_courses(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    courses = _load_courses()
    if not courses:
        return []
    desired = set(_extract_skill_keywords(query))

    scored = []
    for course in courses:
        tags = set(course["tags"])
        overlap = len(desired & tags)
        score = overlap + course["rating"] / 5.0
        scored.append((score, course))

    scored.sort(key=lambda x: (x[0], x[1]["popularity"]), reverse=True)
    results: List[Dict[str, Any]] = []
    for _, course in scored[:limit]:
        results.append(
            {
                "title": course.get("title") or course.get("courseId"),
                "platform": course.get("platform"),
                "rating": course["rating"],
                "difficulty": course.get("difficulty"),
                "tags": ", ".join(course["tags"]),
            }
        )
    return results
