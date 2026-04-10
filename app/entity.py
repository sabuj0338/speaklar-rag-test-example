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

    def __post_init__(self) -> None:
        self.normalized_name_map: dict[str, str] = {}
        self.normalized_products: list[tuple[str, str]] = []
        self.token_index: dict[str, set[str]] = {}

        for product_name in self.product_names:
            normalized = normalize_text(product_name)
            self.normalized_name_map[normalized] = product_name
            self.normalized_products.append((normalized, product_name))
            for token in set(normalized.split()):
                self.token_index.setdefault(token, set()).add(product_name)

    def extract_product(self, query: str, threshold: int = 72) -> str | None:
        if not self.product_names:
            return None

        normalized_query = normalize_text(query)
        cleaned_query = re.sub(r"\b(do you have|how much is|how much|what is|what's|is there|available|price of|price|have)\b", " ", normalized_query)
        cleaned_query = " ".join(cleaned_query.split())

        if cleaned_query in self.normalized_name_map:
            return self.normalized_name_map[cleaned_query]
        if normalized_query in self.normalized_name_map:
            return self.normalized_name_map[normalized_query]

        for normalized_name, product_name in self.normalized_products:
            if cleaned_query and cleaned_query in normalized_name:
                return product_name
            if normalized_name in normalized_query:
                return product_name

        query_tokens = [token for token in cleaned_query.split() if len(token) > 1]
        candidate_counts: dict[str, int] = {}
        for token in query_tokens:
            for product_name in self.token_index.get(token, set()):
                candidate_counts[product_name] = candidate_counts.get(product_name, 0) + 1

        if candidate_counts:
            ranked_candidates = sorted(
                candidate_counts.items(),
                key=lambda item: (-item[1], len(item[0])),
            )
            top_candidates = [name for name, _ in ranked_candidates[:25]]
            match = process.extractOne(
                cleaned_query or normalized_query,
                top_candidates,
                scorer=fuzz.WRatio,
                processor=normalize_text,
            )
            if match and match[1] >= threshold:
                return match[0]

        match = process.extractOne(
            cleaned_query or normalized_query,
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
