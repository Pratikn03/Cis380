"""Clothing recommendations by age (static heuristic)."""
from __future__ import annotations

from typing import List, Dict


def recommend_clothes(age: int | None, query: str) -> List[Dict]:
    if age is None:
        return [{"title": "Classic casual", "reason": "Jeans, tee, sneakers; works for most ages."}]
    if age < 13:
        return [{"title": "Kids activewear", "reason": "Comfortable, durable fabrics; bright colors."}]
    if age < 20:
        return [{"title": "Youth streetwear", "reason": "Hoodies, relaxed jeans/joggers, sneakers."}]
    if age < 35:
        return [
            {"title": "Smart casual", "reason": "Chinos/jeans + polo/oxford, clean sneakers/loafers."},
            {"title": "Athleisure", "reason": "Comfortable technical fabrics for daily wear."},
        ]
    if age < 55:
        return [{"title": "Business casual", "reason": "Tailored trousers, button-downs, loafers; versatile layers."}]
    return [{"title": "Comfort-first classic", "reason": "Soft layers, cardigans, supportive footwear."}]


__all__ = ["recommend_clothes"]
