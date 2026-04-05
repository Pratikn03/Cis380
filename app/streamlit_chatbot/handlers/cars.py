"""Car recommendation handler with local catalog + static fallback."""

from __future__ import annotations

from typing import Dict, List
import json
import re
from pathlib import Path

try:
    from .static_fallbacks import cars_fallback
except ImportError:
    from static_fallbacks import cars_fallback

BASE_DIR = Path(__file__).resolve().parents[3]
CARS_CATALOG = BASE_DIR / "data" / "catalogs" / "cars_catalog.jsonl"


def _load_catalog(path: Path = CARS_CATALOG) -> List[Dict]:
    if not path.exists():
        return []
    items: List[Dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
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
        raw_tags = obj.get("tags") or []
        tag_set = {str(t).lower() for t in raw_tags if str(t).strip()}
        for extra in (
            obj.get("fuel"),
            obj.get("drivetrain"),
            obj.get("body_style"),
            obj.get("usage"),
            obj.get("segment"),
            obj.get("brand"),
            obj.get("category"),
        ):
            if extra:
                tag_set |= _tokenize(str(extra))
        seats = obj.get("seats")
        if isinstance(seats, (int, float)):
            tag_set.add(f"{int(seats)}-seat")
            tag_set.add(f"{int(seats)}seater")
        obj["tags"] = sorted(tag_set)
        items.append(obj)
    return items


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9]+", text) if len(t) > 2}


def _extract_price(query: str) -> float | None:
    m = re.search(r"under\s*\$?(\d+)", query.lower())
    if m:
        return float(m.group(1))
    m2 = re.search(r"\$(\d+)", query.lower())
    if m2:
        return float(m2.group(1))
    return None


def _score_item(item: Dict, tokens: set[str]) -> float:
    tags = {str(t).lower() for t in (item.get("tags") or []) if str(t).strip()}
    brand = str(item.get("brand") or "").lower()
    score = float(len(tokens.intersection(tags)))
    if brand and brand in tokens:
        score += 1.0
    seats = item.get("seats")
    if isinstance(seats, (int, float)):
        seat_tokens = {str(int(seats)), f"{int(seats)}-seat", f"{int(seats)}seater"}
        if tokens.intersection(seat_tokens):
            score += 0.75
    return score


def recommend_cars(query: str, top_n: int = 5) -> List[Dict]:
    """Return a list of car suggestions using local catalog when available."""
    local_items = _load_catalog()
    if not local_items:
        return cars_fallback(query)

    tokens = _tokenize(query)
    price_limit = _extract_price(query)
    filtered = []
    for item in local_items:
        price = item.get("price_usd")
        if price_limit is not None and isinstance(price, (int, float)) and price > price_limit:
            continue
        filtered.append(item)

    ranked = sorted(filtered, key=lambda it: _score_item(it, tokens), reverse=True)
    picked = ranked[:top_n] if ranked else local_items[:top_n]
    out: List[Dict] = []
    for item in picked:
        title = item.get("title")
        reason = item.get("reason") or ""
        if not reason and item.get("tags"):
            reason = "Tags: " + ", ".join(str(t) for t in item.get("tags")[:4])
        price = item.get("price_usd")
        if price is not None:
            price_str = f"${int(price)}"
            reason = f"{reason} · {price_str}" if reason else price_str
        out.append({"title": title, "reason": reason, "brand": item.get("brand")})
    return out


__all__ = ["recommend_cars"]
