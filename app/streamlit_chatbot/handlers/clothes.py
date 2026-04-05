"""Clothing recommendations from a simple local catalog.

This supports the Streamlit chatbot image-upload flow:
- Image -> tags (via CLIP) -> passed as extra context
- We use query + tags to pick clothing items including brand names.

If no catalog file exists, we fall back to a simple age-based heuristic.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG = REPO_ROOT / "data" / "catalogs" / "clothing_catalog.jsonl"


@dataclass(frozen=True)
class ClothingItem:
    id: str
    category: str
    title: str
    brand: str
    tags: tuple[str, ...]
    gender: str | None = None
    price_usd: float | None = None
    season: str | None = None
    material: str | None = None
    style: str | None = None
    occasion: str | None = None
    color: str | None = None
    fit: str | None = None


def _load_catalog(path: Path = DEFAULT_CATALOG) -> list[ClothingItem]:
    if not path.exists():
        return []
    items: list[ClothingItem] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            raw_tags = obj.get("tags") or []
            tag_set = {str(t).lower() for t in raw_tags if str(t).strip()}
            for extra in (
                obj.get("category"),
                obj.get("gender"),
                obj.get("season"),
                obj.get("material"),
                obj.get("style"),
                obj.get("occasion"),
                obj.get("color"),
                obj.get("fit"),
            ):
                if extra:
                    tag_set |= _tokenize(str(extra))
            items.append(
                ClothingItem(
                    id=str(obj.get("id", "")),
                    category=str(obj.get("category", "clothes")),
                    title=str(obj.get("title", "")),
                    brand=str(obj.get("brand", "")),
                    tags=tuple(sorted(tag_set)),
                    gender=(str(obj.get("gender")) if obj.get("gender") is not None else None),
                    price_usd=(
                        float(obj.get("price_usd")) if obj.get("price_usd") is not None else None
                    ),
                    season=(str(obj.get("season")) if obj.get("season") is not None else None),
                    material=(
                        str(obj.get("material")) if obj.get("material") is not None else None
                    ),
                    style=(str(obj.get("style")) if obj.get("style") is not None else None),
                    occasion=(
                        str(obj.get("occasion")) if obj.get("occasion") is not None else None
                    ),
                    color=(str(obj.get("color")) if obj.get("color") is not None else None),
                    fit=(str(obj.get("fit")) if obj.get("fit") is not None else None),
                )
            )
        except Exception:
            continue
    return [it for it in items if it.title and it.brand]


def _tokenize(text: str) -> set[str]:
    import re

    return {t.lower() for t in re.findall(r"[a-zA-Z0-9']+", text) if len(t) > 2}


def _score_item(item: ClothingItem, tokens: set[str]) -> float:
    # Basic keyword overlap scoring
    itags = set(item.tags)
    overlap = len(tokens.intersection(itags))
    # Small boosts for direct category mentions
    cat_boost = 0.0
    if item.category.lower() in tokens:
        cat_boost += 0.75
    if item.brand.lower() in tokens:
        cat_boost += 0.5
    return overlap + cat_boost


def recommend_clothes(
    age: int | None,
    query: str,
    preferred_tags: Sequence[str] | None = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Recommend clothes with brand names.

    preferred_tags can come from image tags (e.g. CLIP labels) or user preference tags.
    """
    catalog = _load_catalog()
    tokens = _tokenize(query)
    if preferred_tags:
        tokens |= {str(t).lower() for t in preferred_tags}

    if catalog:
        ranked = sorted(catalog, key=lambda it: _score_item(it, tokens), reverse=True)
        picked = [it for it in ranked if _score_item(it, tokens) > 0][:top_k]
        if not picked:
            picked = ranked[: min(top_k, len(ranked))]

        out: list[dict[str, Any]] = []
        for it in picked:
            price = f"${it.price_usd:.0f}" if it.price_usd is not None else ""
            reason_bits = []
            if tokens.intersection(set(it.tags)):
                reason_bits.append(
                    f"Matches: {', '.join(sorted(tokens.intersection(set(it.tags)))[:5])}"
                )
            if it.gender:
                reason_bits.append(f"Fit: {it.gender}")
            if it.season:
                reason_bits.append(f"Season: {it.season}")
            if it.material:
                reason_bits.append(f"Material: {it.material}")
            if it.style:
                reason_bits.append(f"Style: {it.style}")
            if it.occasion:
                reason_bits.append(f"Occasion: {it.occasion}")
            if it.color:
                reason_bits.append(f"Color: {it.color}")
            if it.fit:
                reason_bits.append(f"Fit: {it.fit}")
            if price:
                reason_bits.append(f"Price: {price}")

            out.append(
                {
                    "title": it.title,
                    "brand": it.brand,
                    "category": it.category,
                    "price_usd": it.price_usd,
                    "reason": (
                        " • ".join(reason_bits)
                        if reason_bits
                        else "Recommended from your style tags."
                    ),
                }
            )
        return out

    # Fallback: original age heuristic if no catalog exists.
    if age is None:
        return [
            {
                "title": "Classic casual",
                "brand": "(various)",
                "reason": "Jeans, tee, sneakers; works for most ages.",
            }
        ]
    if age < 13:
        return [
            {
                "title": "Kids activewear",
                "brand": "(various)",
                "reason": "Comfortable, durable fabrics; bright colors.",
            }
        ]
    if age < 20:
        return [
            {
                "title": "Youth streetwear",
                "brand": "(various)",
                "reason": "Hoodies, relaxed jeans/joggers, sneakers.",
            }
        ]
    if age < 35:
        return [
            {
                "title": "Smart casual",
                "brand": "(various)",
                "reason": "Chinos/jeans + polo/oxford, clean sneakers/loafers.",
            },
            {
                "title": "Athleisure",
                "brand": "(various)",
                "reason": "Comfortable technical fabrics for daily wear.",
            },
        ]
    if age < 55:
        return [
            {
                "title": "Business casual",
                "brand": "(various)",
                "reason": "Tailored trousers, button-downs, loafers; versatile layers.",
            }
        ]
    return [
        {
            "title": "Comfort-first classic",
            "brand": "(various)",
            "reason": "Soft layers, cardigans, supportive footwear.",
        }
    ]


__all__ = ["recommend_clothes"]
