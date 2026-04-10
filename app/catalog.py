import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


def parse_price(price: Any) -> float:
    if isinstance(price, (int, float)):
        return float(price)
    cleaned = str(price).replace("$", "").replace(",", "").strip()
    return float(cleaned) if cleaned else 0.0
