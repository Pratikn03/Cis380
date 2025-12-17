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
        if not path.exists():
            continue
        for row in _load_csv_rows(path):
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

    return mapping


def load_default_catalog() -> dict[str, CatalogItem]:
    """Backward-compatible alias."""
    return load_unified_catalog()
