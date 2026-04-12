import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


def parse_price(price: Any) -> float:
    """Parse price from various formats: int, float, '2733', '2733 টাকা', '$25.00'."""
    if isinstance(price, (int, float)):
        return float(price)
    text = str(price)
    # Remove currency symbols and common suffixes
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else 0.0
