"""Recommendation helpers for consumer electronics domains."""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parents[3]
RECOMMENDATION_DIR = BASE_DIR / "data" / "raw" / "recommendation"

DOMAIN_FILES = {
    "phones": RECOMMENDATION_DIR / "phones.csv",
    "laptops": RECOMMENDATION_DIR / "laptops.csv",
    "headphones": RECOMMENDATION_DIR / "headphones.csv",
}


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


@lru_cache(maxsize=4)
def _load_domain(domain: str) -> List[Dict[str, Any]]:
    path = DOMAIN_FILES.get(domain)
    if path is None or not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row["price"] = _parse_float(row.get("price", "0"))
            row["rating"] = _parse_float(row.get("rating", "0"))
            row["popularity"] = _parse_float(row.get("popularity", "0"))
            row["tags"] = [t.strip().lower() for t in row.get("tags", "").split(",") if t.strip()]
            rows.append(row)
    return rows


def _extract_price(query: str) -> float | None:
    m = re.search(r"under\s*\$?(\d+)", query.lower())
    if m:
        return float(m.group(1))
    m2 = re.search(r"\$(\d+)", query.lower())
    if m2:
        return float(m2.group(1))
    return None


def _extract_tags(query: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
    return [t for t in tokens if len(t) > 2]


def recommend_electronics(
    domain: str,
    query: str,
    limit: int = 5,
    price_limit: float | None = None,
    preferred_tags: set[str] | None = None,
) -> List[Dict[str, Any]]:
    data = _load_domain(domain)
    if not data:
        return []

    price_limit = price_limit if price_limit is not None else _extract_price(query)
    desired_tags = preferred_tags if preferred_tags else set(_extract_tags(query))
    use_case_tags = {"programming", "gaming", "travel", "photo", "camera", "noise", "study", "budget"}
    use_case = next((t for t in desired_tags if t in use_case_tags), None)

    filtered = []
    for item in data:
        if price_limit is not None and item["price"] > price_limit:
            continue
        if desired_tags and desired_tags.intersection(item["tags"]):
            score = 1.0
        else:
            score = 0.5
        filtered.append((score, item))

    if not filtered:
        filtered = [(0.0, item) for item in data]

    filtered.sort(key=lambda x: (x[1]["rating"], x[0], x[1]["popularity"]), reverse=True)

    results: List[Dict[str, Any]] = []
    for _, item in filtered[:limit]:
        results.append(
            {
                "title": f"{item.get('brand', '')} {item.get('model', '')}".strip(),
                "price": f"${item['price']:.0f}",
                "rating": item["rating"],
                "details": f"Tags: {', '.join(item['tags'])}",
                "popularity": item["popularity"],
            }
        )
    if not results:
        return results
    tradeoff = (
        f"Budget <= ${price_limit:.0f}" if price_limit is not None else "No strict budget; focus on ratings/popularity."
    )
    if use_case:
        tradeoff += f" Use case: {use_case}."
    results[0]["tradeoff"] = tradeoff
    return results
