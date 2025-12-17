"""Recommendation helpers for consumer electronics domains."""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any

try:
    from .electronics_catalog import ELECTRONICS_CATALOG
except ImportError:  # pragma: no cover
    from electronics_catalog import ELECTRONICS_CATALOG

BASE_DIR = Path(__file__).resolve().parents[3]
RECOMMENDATION_DIR = BASE_DIR / "data" / "raw" / "recommendation"

DOMAIN_FILES = {
    "phones": RECOMMENDATION_DIR / "phones.csv",
    "laptops": RECOMMENDATION_DIR / "laptops.csv",
    "headphones": RECOMMENDATION_DIR / "headphones.csv",
}

_DOMAIN_BRANDS: dict[str, set[str]] = {
    "phones": {"google", "samsung", "apple", "oneplus", "motorola"},
    "laptops": {"dell", "lenovo", "apple", "asus", "acer", "hp"},
    "headphones": {"sony", "bose", "apple", "anker", "sennheiser"},
}

_SUSPICIOUS_BRANDS = {
    "a",
    "an",
    "the",
    "best",
    "great",
    "excellent",
    "amazing",
    "wow",
    "works",
    "so",
    "it",
    "ideal",
    "cheap",
}


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _normalize_tags(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(t).strip().lower() for t in value if str(t).strip()]
    return [t.strip().lower() for t in str(value).split(",") if t.strip()]


def _display_title(item: Dict[str, Any]) -> str:
    for key in ("title", "name", "product_title", "productName"):
        val = (item.get(key) or "").strip()
        if val:
            return val
    brand = (item.get("brand") or "").strip()
    model = (item.get("model") or "").strip()
    combined = f"{brand} {model}".strip()
    return combined or (item.get("itemId") or "Item")


@lru_cache(maxsize=4)
def _load_domain(domain: str) -> List[Dict[str, Any]]:
    path = DOMAIN_FILES.get(domain)
    if path is None or not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = [f.strip().lower() for f in (reader.fieldnames or []) if f]
        has_title_column = "title" in fieldnames
        for row in reader:
            row["price"] = _parse_float(row.get("price", "0"))
            row["rating"] = _parse_float(row.get("rating", "0"))
            row["popularity"] = _parse_float(row.get("popularity", "0"))
            tags = set(_normalize_tags(row.get("tags")))
            brand = str(row.get("brand") or "").strip().lower()
            if brand and brand not in _SUSPICIOUS_BRANDS and len(brand) > 2:
                tags.add(brand)
            row["tags"] = sorted(tags)
            row["title"] = _display_title(row)
            row["_has_title_column"] = has_title_column
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
    # If the CSV looks like it was generated from review summaries (no real product titles),
    # fall back to a curated offline catalog for a better demo experience.
    if data:
        sample = data[:200]
        has_title_column = bool(sample and sample[0].get("_has_title_column"))
        asin_re = re.compile(r"^[A-Z0-9]{10}$")
        asin_like = sum(1 for it in sample if asin_re.match(str(it.get("itemId") or "").strip()))
        model_asin = sum(1 for it in sample if asin_re.match(str(it.get("model") or "").strip()))
        suspicious = sum(
            1
            for it in sample
            if (str(it.get("brand") or "").strip().lower() in _SUSPICIOUS_BRANDS)
            or len(str(it.get("brand") or "").strip()) <= 2
        )
        if (
            suspicious / max(1, len(sample)) > 0.35
            or (
                not has_title_column
                and asin_like / max(1, len(sample)) > 0.80
                and model_asin / max(1, len(sample)) > 0.05
            )
        ):
            data = []
    if not data:
        data = [dict(item) for item in ELECTRONICS_CATALOG.get(domain, [])]
        for item in data:
            item["price"] = float(item.get("price", 0) or 0)
            item["rating"] = float(item.get("rating", 0) or 0)
            item["popularity"] = float(item.get("popularity", 0) or 0)
            item["tags"] = _normalize_tags(item.get("tags"))
            item["title"] = _display_title(item)

    if not data:
        return []

    price_limit = price_limit if price_limit is not None else _extract_price(query)
    desired_tags = preferred_tags if preferred_tags else set(_extract_tags(query))
    use_case_tags = {"programming", "gaming", "travel", "photo", "camera", "noise", "study", "budget"}
    use_case = next((t for t in desired_tags if t in use_case_tags), None)
    brand_tags = _DOMAIN_BRANDS.get(domain, set())

    filtered = []
    for item in data:
        if price_limit is not None and item["price"] > price_limit:
            continue
        item_tags = set(item.get("tags") or [])
        matches = desired_tags.intersection(item_tags) if desired_tags else set()
        score = float(len(matches))
        if matches:
            score += 0.5
        if brand_tags and matches.intersection(brand_tags):
            score += 3.0
        filtered.append((score, item))

    if not filtered:
        filtered = [(0.0, item) for item in data]

    # Prefer matches to the user query (tags/keywords), then rating, then popularity.
    filtered.sort(key=lambda x: (x[0], x[1]["rating"], x[1]["popularity"]), reverse=True)

    results: List[Dict[str, Any]] = []
    for _, item in filtered[:limit]:
        title = _display_title(item)
        price_val = float(item.get("price") or 0.0)
        rating_val = float(item.get("rating") or 0.0)
        popularity_val = float(item.get("popularity") or 0.0)
        tag_list = item.get("tags") or []
        results.append(
            {
                "title": title,
                "reason": f"Price: ${price_val:.0f} · Rating: {rating_val:.1f} · Popularity: {int(popularity_val)}",
                "price": f"${price_val:.0f}",
                "rating": rating_val,
                "overview": f"Tags: {', '.join(tag_list)}" if tag_list else "",
                "popularity": popularity_val,
                "itemId": item.get("itemId"),
            }
        )
    if not results:
        return results
    tradeoff = (
        f"Budget <= ${price_limit:.0f}" if price_limit is not None else "No strict budget; focus on ratings/popularity."
    )
    if use_case:
        tradeoff += f" Use case: {use_case}."
    if ELECTRONICS_CATALOG.get(domain) and results and results[0].get("itemId", "").startswith(("phone_", "laptop_", "hp_")):
        tradeoff += " (Using curated offline catalog.)"
    results[0]["tradeoff"] = tradeoff
    return results
