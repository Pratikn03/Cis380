from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List


def normalize_text(text: str) -> str:
    text = text.replace("\u0000", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_repeated_lines(pages: Iterable[str], *, min_ratio: float = 0.6) -> List[str]:
    page_list = [p or "" for p in pages]
    if not page_list:
        return []
    if len(page_list) < 3:
        return page_list
    line_counts: Counter[str] = Counter()
    total_pages = len(page_list)
    for page in page_list:
        lines = {ln.strip() for ln in page.splitlines() if ln.strip()}
        line_counts.update(lines)
    repeated = {
        line
        for line, count in line_counts.items()
        if count / total_pages >= min_ratio and len(line) > 6
    }
    cleaned = []
    for page in page_list:
        kept_lines = [ln for ln in page.splitlines() if ln.strip() and ln.strip() not in repeated]
        cleaned.append("\n".join(kept_lines))
    return cleaned
