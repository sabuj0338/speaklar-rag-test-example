from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz, process

from app.catalog import normalize_text


# Maps Bangla category keywords (including short forms) to canonical category names
# extracted from Knowledge_Bank.txt
BANGLA_CATEGORY_MAP = {
    # Full names from the dataset
    "ইলেকট্রনিক্স": "ইলেকট্রনিক্স",
    "আসবাবপত্র": "আসবাবপত্র",
    "খেলাধুলা": "খেলাধুলা",
    "প্রসাধনী": "প্রসাধনী",
    "ফ্যাশন ও পোশাক": "ফ্যাশন ও পোশাক",
    "খাদ্য ও পানীয়": "খাদ্য ও পানীয়",
    "স্বাস্থ্য ও ঔষধ": "স্বাস্থ্য ও ঔষধ",
    "যন্ত্রপাতি ও সরঞ্জাম": "যন্ত্রপাতি ও সরঞ্জাম",
    "গৃহস্থালী সামগ্রী": "গৃহস্থালী সামগ্রী",
    "বই ও স্টেশনারি": "বই ও স্টেশনারি",
    "খেলনা ও শিশু পণ্য": "খেলনা ও শিশু পণ্য",
    "মোবাইল আনুষঙ্গিক": "মোবাইল আনুষঙ্গিক",
    "কৃষি ও বাগান": "কৃষি ও বাগান",
    "ডিজিটাল সেবা": "ডিজিটাল সেবা",

    # Short forms / alternative names
    "ইলেক্ট্রনিক্স": "ইলেকট্রনিক্স",
    "electronics": "ইলেকট্রনিক্স",
    "ফ্যাশন": "ফ্যাশন ও পোশাক",
    "পোশাক": "ফ্যাশন ও পোশাক",
    "কাপড়": "ফ্যাশন ও পোশাক",
    "fashion": "ফ্যাশন ও পোশাক",
    "খাদ্য": "খাদ্য ও পানীয়",
    "খাবার": "খাদ্য ও পানীয়",
    "পানীয়": "খাদ্য ও পানীয়",
    "food": "খাদ্য ও পানীয়",
    "স্বাস্থ্য": "স্বাস্থ্য ও ঔষধ",
    "ঔষধ": "স্বাস্থ্য ও ঔষধ",
    "health": "স্বাস্থ্য ও ঔষধ",
    "যন্ত্রপাতি": "যন্ত্রপাতি ও সরঞ্জাম",
    "সরঞ্জাম": "যন্ত্রপাতি ও সরঞ্জাম",
    "tools": "যন্ত্রপাতি ও সরঞ্জাম",
    "গৃহস্থালী": "গৃহস্থালী সামগ্রী",
    "home": "গৃহস্থালী সামগ্রী",
    "খেলনা": "খেলনা ও শিশু পণ্য",
    "শিশু": "খেলনা ও শিশু পণ্য",
    "শিশু পণ্য": "খেলনা ও শিশু পণ্য",
    "toys": "খেলনা ও শিশু পণ্য",
    "বই": "বই ও স্টেশনারি",
    "স্টেশনারি": "বই ও স্টেশনারি",
    "books": "বই ও স্টেশনারি",
    "মোবাইল": "মোবাইল আনুষঙ্গিক",
    "mobile": "মোবাইল আনুষঙ্গিক",
    "কৃষি": "কৃষি ও বাগান",
    "বাগান": "কৃষি ও বাগান",
    "agriculture": "কৃষি ও বাগান",
    "sports": "খেলাধুলা",
    "খেলা": "খেলাধুলা",
    "আসবাব": "আসবাবপত্র",
    "furniture": "আসবাবপত্র",
    "cosmetics": "প্রসাধনী",
    "ডিজিটাল": "ডিজিটাল সেবা",
    "digital": "ডিজিটাল সেবা",
}

# Common Bangla suffixes to strip for better fuzzy matching
# e.g., "চেয়ারের" → "চেয়ার", "শাড়ির" → "শাড়ি"
BANGLA_SUFFIXES = [
    "ের", "এর", "র", "ে", "তে", "য়", "গুলো", "গুলি", "সমূহ", "সব",
    "টা", "টি", "খানা", "খানি",
]


def strip_bangla_suffixes(word: str) -> str:
    """Strip common Bangla inflectional suffixes from a word."""
    for suffix in sorted(BANGLA_SUFFIXES, key=len, reverse=True):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[: -len(suffix)]
    return word


@dataclass
class EntityResolver:
    product_names: list[str]
    categories: list[str]

    def __post_init__(self) -> None:
        self.normalized_name_map: dict[str, str] = {}
        self.normalized_products: list[tuple[str, str]] = []
        self.token_index: dict[str, set[str]] = {}
        # Unique product names only (dataset has many duplicates)
        self.unique_product_names: list[str] = list(dict.fromkeys(self.product_names))

        for product_name in self.product_names:
            normalized = normalize_text(product_name)
            self.normalized_name_map[normalized] = product_name
            self.normalized_products.append((normalized, product_name))
            for token in set(normalized.split()):
                self.token_index.setdefault(token, set()).add(product_name)

    # Bangla stop words to remove from queries before matching.
    # These are matched as whole tokens (space-delimited), not via regex \b
    STOP_WORDS = {
        # English
        "do", "you", "have", "how", "much", "is", "which", "one", "what",
        "what's", "is", "there", "available", "price", "of", "the",
        # Bangla question/function words  
        "কি", "আছে", "পাওয়া", "যায়", "টা", "টি", "এর", "এই", "ওই",
        "কোন", "সেই", "আমার", "আমি", "চাই", "দাও", "দিন", "বলুন",
        "জানতে", "চাইছেন", "সম্পর্কে", "কত", "টাকা", "মূল্য", "দাম",
        "না", "হয়", "নাকি", "অনুগ্রহ", "করে", "বলেন", "বলো", "একটু", 
        "তো", "প্লিজ", "ভাই", "কিভাবে", "কোথায়", "কবে", "দিয়ে",
    }

    def extract_product(self, query: str, threshold: int = 70) -> str | None:
        if not self.product_names:
            return None

        normalized_query = normalize_text(query)
        # Strip punctuation before tokenizing
        cleaned_query_no_punct = re.sub(r"[?,.!।]", "", normalized_query)
        # Remove stop words by splitting into tokens and filtering
        tokens = cleaned_query_no_punct.split()
        cleaned_tokens = [t for t in tokens if t not in self.STOP_WORDS]
        cleaned_query = " ".join(cleaned_tokens)
        stripped_query = cleaned_query.strip()

        # Vague anaphora like 'it', 'this one', etc. shouldn't trigger product search
        from app.resolver import VAGUE_REFERENCES
        if stripped_query in VAGUE_REFERENCES or len(stripped_query) <= 2:
            return None

        # Strip Bangla suffixes from query tokens for better matching
        suffix_stripped_tokens = [strip_bangla_suffixes(t) for t in cleaned_query.split()]
        suffix_stripped_query = " ".join(suffix_stripped_tokens)

        # 1. Exact match on normalized name
        for query_variant in [cleaned_query, suffix_stripped_query, normalized_query]:
            if query_variant in self.normalized_name_map:
                return self.normalized_name_map[query_variant]

        # 2. Substring match — query inside product name or vice versa
        for normalized_name, product_name in self.normalized_products:
            for query_variant in [cleaned_query, suffix_stripped_query]:
                if query_variant and query_variant in normalized_name:
                    return product_name
            if normalized_name in normalized_query:
                return product_name

        # 3. Fuzzy match using token overlap index
        query_tokens = [t for t in suffix_stripped_tokens if len(t) > 1]
        candidate_counts: dict[str, int] = {}
        for token in query_tokens:
            # Direct index lookup
            for product_name in self.token_index.get(token, set()):
                candidate_counts[product_name] = candidate_counts.get(product_name, 0) + 1
            # Also try suffix-stripped version against token index
            stripped = strip_bangla_suffixes(token)
            if stripped != token:
                for product_name in self.token_index.get(stripped, set()):
                    candidate_counts[product_name] = candidate_counts.get(product_name, 0) + 1

        if candidate_counts:
            ranked_candidates = sorted(
                candidate_counts.items(),
                key=lambda item: (-item[1], len(item[0])),
            )
            top_candidates = [name for name, _ in ranked_candidates[:25]]
            match = process.extractOne(
                suffix_stripped_query or cleaned_query,
                top_candidates,
                scorer=fuzz.token_set_ratio,
                processor=normalize_text,
            )
            if match and match[1] >= threshold:
                return match[0]

        # 5. Global fuzzy match against unique names
        match = process.extractOne(
            suffix_stripped_query or cleaned_query,
            self.unique_product_names,
            scorer=fuzz.token_set_ratio,
            processor=normalize_text,
        )
        if match and match[1] >= threshold:
            return match[0]
        return None

    def detect_category(self, query: str) -> str | None:
        normalized = normalize_text(query)

        # Check Bangla category map (longer keys first to match "ফ্যাশন ও পোশাক" before "ফ্যাশন")
        sorted_keys = sorted(BANGLA_CATEGORY_MAP.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in normalized:
                return BANGLA_CATEGORY_MAP[key]

        # Check exact match against known categories from data
        for category in self.categories:
            category_normalized = normalize_text(category)
            if category_normalized in normalized:
                return category

        # Fuzzy match individual tokens (also try suffix-stripped)
        query_tokens = normalized.split()
        for raw_token in query_tokens:
            token = re.sub(r"[?,.!।]", "", raw_token)
            if not token or len(token) <= 2:
                continue
            stripped = strip_bangla_suffixes(token)
            for variant in [token, stripped]:
                match = process.extractOne(
                    variant,
                    self.categories,
                    scorer=fuzz.ratio,
                    processor=normalize_text,
                )
                if match and match[1] >= 85:
                    return match[0]
        return None
