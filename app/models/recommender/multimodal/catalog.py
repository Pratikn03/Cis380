from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class CatalogItem:
    item_id: str
    title: str
    category: str | None = None
    brand: str | None = None
    price: float | None = None
    image_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "category": self.category,
            "brand": self.brand,
            "price": self.price,
            "image_path": self.image_path,
        }


_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# When electronics CSVs are generated from review summaries (common in Kaggle exports),
# they often contain non-product "brands" like "great"/"works" and model phrases like
# "must buy for". In those cases we fall back to a small curated catalog so demos
# return realistic titles offline.
_SUSPICIOUS_ELECTRONICS_BRANDS: set[str] = {
    "a",
    "an",
    "the",
    "best",
    "great",
    "excellent",
    "amazing",
    "wow",
    "works",
    "work",
    "good",
    "nice",
    "perfect",
    "just",
    "very",
    "so",
    "well",
    "it",
    "this",
    "that",
    "you",
}

_ELECTRONICS_FALLBACK: dict[str, list[CatalogItem]] = {
    "phones": [
        CatalogItem(item_id="phone_pixel_7a", title="Google Pixel 7a", category="electronics", brand="google", price=499),
        CatalogItem(item_id="phone_galaxy_a54", title="Samsung Galaxy A54 5G", category="electronics", brand="samsung", price=449),
        CatalogItem(item_id="phone_iphone_se_3", title="iPhone SE (3rd gen)", category="electronics", brand="apple", price=429),
        CatalogItem(item_id="phone_oneplus_nord_n30", title="OnePlus Nord N30 5G", category="electronics", brand="oneplus", price=299),
        CatalogItem(item_id="phone_moto_g_power", title="Motorola Moto G Power", category="electronics", brand="motorola", price=249),
    ],
    "laptops": [
        CatalogItem(item_id="laptop_dell_inspiron_14", title="Dell Inspiron 14", category="electronics", brand="dell", price=799),
        CatalogItem(item_id="laptop_lenovo_thinkpad_e14", title="Lenovo ThinkPad E14", category="electronics", brand="lenovo", price=899),
        CatalogItem(item_id="laptop_macbook_air_m2", title="MacBook Air (M2)", category="electronics", brand="apple", price=1099),
        CatalogItem(item_id="laptop_asus_zenbook_14", title="ASUS ZenBook 14", category="electronics", brand="asus", price=999),
        CatalogItem(item_id="laptop_acer_swift_3", title="Acer Swift 3", category="electronics", brand="acer", price=749),
    ],
    "headphones": [
        CatalogItem(item_id="hp_sony_wh_1000xm5", title="Sony WH-1000XM5", category="electronics", brand="sony", price=399),
        CatalogItem(item_id="hp_bose_qc45", title="Bose QuietComfort 45", category="electronics", brand="bose", price=329),
        CatalogItem(item_id="hp_airpods_pro_2", title="Apple AirPods Pro (2nd gen)", category="electronics", brand="apple", price=249),
        CatalogItem(item_id="hp_soundcore_q30", title="Anker Soundcore Life Q30", category="electronics", brand="anker", price=79),
        CatalogItem(item_id="hp_sennheiser_hd560s", title="Sennheiser HD 560S", category="electronics", brand="sennheiser", price=199),
    ],
}


def _slug(text: str) -> str:
    text = text.strip().lower()
    text = _NON_ALNUM.sub("-", text).strip("-")
    return text or "item"


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("$", "")
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _pick_first(row: dict[str, str], keys: list[str]) -> str | None:
    for key in keys:
        val = (row.get(key) or "").strip()
        if val:
            return val
    return None


def _load_csv_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {str(k): ("" if v is None else str(v)) for k, v in row.items()}


def _image_key_for_item(domain: str, item_id: str, title: str) -> str:
    """Stable synthetic key used when an actual image_path isn't provided.

    This lets the system return rich metadata consistently even before you add images.
    When you later add real images + index, set image_path in CSV and it will override.
    """
    return f"catalog://{domain}/{_slug(item_id)}/{_slug(title)}"


def _looks_like_review_summary_catalog(rows: list[dict[str, str]]) -> bool:
    """Heuristic for low-quality electronics CSVs (review-summary derived)."""
    if not rows:
        return False
    sample = rows[:200]
    if not sample:
        return False

    # If a proper title column exists and is populated, treat as high-quality.
    has_title = any((row.get("title") or row.get("name") or "").strip() for row in sample)
    if has_title:
        return False

    brands = [(row.get("brand") or "").strip().lower() for row in sample]
    suspicious = sum(1 for b in brands if (not b) or (b in _SUSPICIOUS_ELECTRONICS_BRANDS) or len(b) <= 2)
    ratio = suspicious / max(1, len(sample))
    return ratio >= 0.25


def load_unified_catalog() -> dict[str, CatalogItem]:
    """Load Movies + Electronics + Courses into one catalog.

    Output: dict keyed by *image key*.

    Key behavior:
    - If a row has `image_path`, we key by that normalized path.
    - Otherwise we key by a stable synthetic URI: catalog://<domain>/<id>/<slug>
    """
    root = Path("data/raw/recommendation")

    mapping: dict[str, CatalogItem] = {}

    # Movies (MovieLens-style)
    items_path = root / "items.csv"
    if items_path.exists():
        for row in _load_csv_rows(items_path):
            item_id = _pick_first(row, ["movieId", "item_id", "id"]) or ""
            title = _pick_first(row, ["title", "name"]) or ""
            if not item_id or not title:
                continue
            image_path = _pick_first(row, ["image_path", "image", "path", "img", "imageUrl"])
            key = str(Path(image_path)) if image_path else _image_key_for_item("movies", item_id, title)
            mapping[key] = CatalogItem(item_id=str(item_id), title=str(title), category="movies", image_path=image_path)

    # Courses
    courses_path = root / "courses.csv"
    if courses_path.exists():
        for row in _load_csv_rows(courses_path):
            item_id = _pick_first(row, ["courseId", "item_id", "id"]) or ""
            title = _pick_first(row, ["title", "name"]) or ""
            if not item_id or not title:
                continue
            image_path = _pick_first(row, ["image_path", "image", "path", "img", "imageUrl"])
            key = str(Path(image_path)) if image_path else _image_key_for_item("courses", item_id, title)
            mapping[key] = CatalogItem(item_id=str(item_id), title=str(title), category="courses", image_path=image_path)

    # Electronics domains already used in Streamlit (phones/laptops/headphones)
    for domain_file, domain_name in (("phones.csv", "phones"), ("laptops.csv", "laptops"), ("headphones.csv", "headphones")):
        path = root / domain_file
        if path.exists():
            rows = list(_load_csv_rows(path))
            if rows and not _looks_like_review_summary_catalog(rows):
                for row in rows:
                    item_id = _pick_first(row, ["itemId", "item_id", "id"]) or ""
                    brand = _pick_first(row, ["brand"]) or None
                    model = _pick_first(row, ["model"]) or ""
                    title = _pick_first(row, ["title", "name"]) or " ".join([t for t in [brand or "", model] if t]).strip()
                    if not item_id or not title:
                        continue
                    price = _coerce_float(_pick_first(row, ["price"]))
                    image_path = _pick_first(row, ["image_path", "image", "path", "img", "imageUrl"])
                    key = str(Path(image_path)) if image_path else _image_key_for_item(domain_name, item_id, title)
                    mapping[key] = CatalogItem(
                        item_id=str(item_id),
                        title=str(title),
                        category="electronics",
                        brand=brand,
                        price=price,
                        image_path=image_path,
                    )
                continue

        # Fallback: curated catalog items for demo-quality results.
        for item in _ELECTRONICS_FALLBACK.get(domain_name, []):
            key = _image_key_for_item(domain_name, item.item_id, item.title)
            mapping[key] = item

    return mapping


def load_default_catalog() -> dict[str, CatalogItem]:
    """Backward-compatible alias."""
    return load_unified_catalog()
