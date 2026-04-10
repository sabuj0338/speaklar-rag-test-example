from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz, process

from app.catalog import normalize_text


BANGLA_CATEGORY_MAP = {
    "নুডলস": "noodles",
    "লবণ": "salt",
    "ড্রেস": "dress",
}


@dataclass
class EntityResolver:
    product_names: list[str]
    categories: list[str]

    def extract_product(self, query: str, threshold: int = 72) -> str | None:
        if not self.product_names:
            return None
        match = process.extractOne(
            query,
            self.product_names,
            scorer=fuzz.WRatio,
            processor=normalize_text,
        )
        if match and match[1] >= threshold:
            return match[0]
        return None

    def detect_category(self, query: str) -> str | None:
        normalized = normalize_text(query)
        for bangla, english in BANGLA_CATEGORY_MAP.items():
            if bangla in normalized:
                return english
        for category in self.categories:
            category_pattern = r"\b" + re.escape(normalize_text(category)) + r"\b"
            if re.search(category_pattern, normalized):
                return category
        return None
