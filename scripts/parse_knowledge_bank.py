"""
Parse Knowledge_Bank.txt into structured JSON for the RAG system.

Each non-blank line is treated as a product entry. The script extracts:
- Product name (first sentence before the first ।)
- Description (second sentence)
- Price (regex: মূল্য ... টাকা)
- Brand (regex: ... ব্র্যান্ডের)
- Category (regex: ... বিভাগে)
- Quality (regex: ... কোয়ালিটির)
- Full text (entire line for embedding)

Usage:
    python3 scripts/parse_knowledge_bank.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INPUT_PATH = ROOT / "data" / "Knowledge_Bank.txt"
OUTPUT_PATH = ROOT / "data" / "knowledge_bank.json"


def extract_price(line: str) -> int:
    """Extract price from 'মূল্য XXXX টাকা' pattern."""
    match = re.search(r"মূল্য\s*(\d+)\s*টাকা", line)
    return int(match.group(1)) if match else 0


def extract_brand(line: str) -> str:
    """Extract brand from 'XXX ব্র্যান্ডের' pattern."""
    match = re.search(r"([\u0980-\u09FF\w]+)\s*ব্র্যান্ডের", line)
    return match.group(1).strip() if match else ""


def extract_category(line: str) -> str:
    """Extract category from 'XXX বিভাগে' pattern."""
    match = re.search(r"([\u0980-\u09FF\s\w&ও]+?)\s*বিভাগে", line)
    return match.group(1).strip() if match else ""


def extract_quality(line: str) -> str:
    """Extract quality from 'XXX কোয়ালিটির' pattern."""
    match = re.search(r"([\u0980-\u09FF\w]+)\s*কোয়ালিটির", line)
    return match.group(1).strip() if match else ""


def extract_warranty(line: str) -> str:
    """Extract warranty brand from 'XXX ওয়ারেন্টি' pattern."""
    match = re.search(r"([\u0980-\u09FF\w]+)\s*ওয়ারেন্টি", line)
    return match.group(1).strip() if match else ""


def has_offer(line: str) -> bool:
    """Check if line mentions special offers."""
    return "ছাড়" in line or "অফার" in line


def has_home_delivery(line: str) -> bool:
    """Check if line mentions home delivery."""
    return "হোম ডেলিভারি" in line or "সারা বাংলাদেশে" in line


def parse_product_line(line: str, product_id: int) -> dict:
    """Parse a single product line into a structured dict."""
    # Split by Bangla full stop
    sentences = [s.strip() for s in line.split("।") if s.strip()]

    # Product name is the first sentence
    name = sentences[0] if sentences else line[:50]

    # Description is the second sentence (if exists)
    description = sentences[1] if len(sentences) > 1 else ""

    return {
        "id": product_id,
        "text": name,
        "description": description,
        "price": extract_price(line),
        "brand": extract_brand(line),
        "category": extract_category(line),
        "quality": extract_quality(line),
        "warranty": extract_warranty(line),
        "has_offer": has_offer(line),
        "has_home_delivery": has_home_delivery(line),
        "full_text": line.strip(),
    }


def main() -> None:
    if not INPUT_PATH.exists():
        print(f"Error: {INPUT_PATH} not found.")
        sys.exit(1)

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        raw_text = f.read()

    # Each product is on a non-blank line, separated by blank lines
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    products = []
    for idx, line in enumerate(lines, start=1):
        product = parse_product_line(line, idx)
        products.append(product)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # Print stats
    total = len(products)
    with_category = sum(1 for p in products if p["category"])
    with_brand = sum(1 for p in products if p["brand"])
    with_price = sum(1 for p in products if p["price"] > 0)
    categories = sorted({p["category"] for p in products if p["category"]})

    print(f"✅ Parsed {total} products → {OUTPUT_PATH}")
    print(f"   With price:    {with_price}/{total}")
    print(f"   With brand:    {with_brand}/{total}")
    print(f"   With category: {with_category}/{total}")
    print(f"   Categories found ({len(categories)}):")
    for cat in categories:
        count = sum(1 for p in products if p["category"] == cat)
        print(f"     - {cat} ({count})")


if __name__ == "__main__":
    main()
