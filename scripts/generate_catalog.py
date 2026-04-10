import argparse
import json
import random
from pathlib import Path


CATEGORY_SPECS = {
    "Noodles": {
        "brands": ["Rupchanda", "Pran", "ACI", "Fresh", "Bashundhara", "Mr. Noodles", "Cocola", "Ifad"],
        "items": ["Instant Noodles", "Masala Noodles", "Chicken Noodles", "Thai Soup Noodles", "Cup Noodles"],
        "sizes": ["40g", "62g", "75g", "120g", "8 Pack", "16 Pack"],
        "price": (18, 320),
        "unit": "pack",
    },
    "Salt": {
        "brands": ["Rupchanda", "ACI Pure", "Fresh", "Molla", "Confidence", "Muskan", "Teer", "Pusti"],
        "items": ["Iodized Salt", "Premium Salt", "Table Salt", "Crystal Salt"],
        "sizes": ["200g", "500g", "1kg", "2kg"],
        "price": (22, 145),
        "unit": "pack",
    },
    "Juice": {
        "brands": ["Pran", "Shezan", "Frutika", "Mango Plus", "Frooti", "Minute Maid", "Teer", "Fresh"],
        "items": ["Mango Juice", "Orange Juice", "Apple Juice", "Mixed Fruit Juice", "Litchi Juice"],
        "sizes": ["200ml", "250ml", "500ml", "1L", "2L"],
        "price": (25, 285),
        "unit": "bottle",
    },
    "Biscuits": {
        "brands": ["Olympic", "Pran", "Fresh", "Nabisco", "Sunfeast", "Haque", "Bisk Club", "Mr. Cookie"],
        "items": ["Digestive Biscuit", "Chocolate Biscuit", "Salt Biscuit", "Cream Biscuit", "Tea Biscuit"],
        "sizes": ["45g", "80g", "120g", "250g", "Family Pack"],
        "price": (15, 240),
        "unit": "pack",
    },
    "Rice": {
        "brands": ["Chinigura Gold", "Nazirshail", "Miniket", "Akij", "ACI", "Fresh", "Teer", "Bashundhara"],
        "items": ["Premium Rice", "Miniket Rice", "Chinigura Rice", "Basmati Rice"],
        "sizes": ["1kg", "2kg", "5kg", "10kg", "25kg"],
        "price": (85, 2950),
        "unit": "bag",
    },
    "Oil": {
        "brands": ["Rupchanda", "Fresh", "Teer", "Pusti", "Bashundhara", "ACI Nutrilife", "Muskan", "Sunlife"],
        "items": ["Soybean Oil", "Mustard Oil", "Rice Bran Oil", "Sunflower Oil"],
        "sizes": ["500ml", "1L", "2L", "5L"],
        "price": (135, 980),
        "unit": "bottle",
    },
    "Milk": {
        "brands": ["Milk Vita", "Pran", "Aarong", "Farm Fresh", "Dano", "Marks", "Starship", "Diploma"],
        "items": ["UHT Milk", "Fresh Milk", "Powder Milk", "Full Cream Milk"],
        "sizes": ["200ml", "500ml", "1L", "400g", "1kg"],
        "price": (35, 960),
        "unit": "pack",
    },
    "Tea": {
        "brands": ["Ispahani", "Finlay", "Tetley", "Brooke Bond", "Kazi & Kazi", "Fresh", "Pran", "Danish"],
        "items": ["Black Tea", "Premium Tea", "Gold Tea", "Masala Tea", "Green Tea"],
        "sizes": ["25 Bags", "50 Bags", "100g", "200g", "400g"],
        "price": (45, 620),
        "unit": "box",
    },
    "Soap": {
        "brands": ["Lux", "Lifebuoy", "Dettol", "Savlon", "Meril", "Sandalina", "Dove", "Keya"],
        "items": ["Beauty Soap", "Antibacterial Soap", "Herbal Soap", "Moisturizing Soap"],
        "sizes": ["75g", "100g", "125g", "3 Pack", "6 Pack"],
        "price": (35, 310),
        "unit": "bar",
    },
    "Shampoo": {
        "brands": ["Sunsilk", "Head & Shoulders", "Pantene", "Clear", "Dove", "Tresemme", "Meril", "Parachute"],
        "items": ["Anti Dandruff Shampoo", "Silky Smooth Shampoo", "Hair Fall Shampoo", "Herbal Shampoo"],
        "sizes": ["80ml", "170ml", "340ml", "650ml", "Sachet Pack"],
        "price": (25, 890),
        "unit": "bottle",
    },
}

QUALIFIERS = [
    "Regular",
    "Premium",
    "Classic",
    "Family",
    "Value",
    "Special",
    "Fresh",
    "Daily",
]


def size_multiplier(size: str) -> float:
    normalized = size.lower()
    if "25kg" in normalized:
        return 12.0
    if "10kg" in normalized:
        return 5.5
    if "5kg" in normalized or "5l" in normalized:
        return 3.1
    if "2kg" in normalized or "2l" in normalized:
        return 1.9
    if "1kg" in normalized or "1l" in normalized:
        return 1.0
    if "500ml" in normalized or "500g" in normalized:
        return 0.72
    if "400g" in normalized or "340ml" in normalized:
        return 0.62
    if "250ml" in normalized or "200g" in normalized or "200ml" in normalized:
        return 0.45
    if "170ml" in normalized or "125g" in normalized or "120g" in normalized:
        return 0.36
    if "100g" in normalized or "100ml" in normalized or "80g" in normalized or "80ml" in normalized:
        return 0.28
    if "75g" in normalized or "62g" in normalized:
        return 0.22
    if "45g" in normalized or "40g" in normalized:
        return 0.18
    if "16 pack" in normalized:
        return 3.4
    if "8 pack" in normalized or "6 pack" in normalized:
        return 2.2
    if "3 pack" in normalized:
        return 1.35
    if "family" in normalized:
        return 1.7
    if "50 bags" in normalized:
        return 1.5
    if "25 bags" in normalized:
        return 0.9
    if "sachet" in normalized:
        return 0.2
    return 1.0


def build_price(price_range: tuple[int, int], size: str) -> float:
    low, high = price_range
    base = random.uniform(low, high / 2.2)
    adjusted = base * size_multiplier(size)
    capped = max(low, min(high, adjusted))
    return round(capped, 2)


def build_catalog(total: int) -> list[dict[str, str]]:
    random.seed(42)
    categories = list(CATEGORY_SPECS.keys())
    products: list[dict[str, str]] = []

    for product_id in range(1, total + 1):
        category = categories[(product_id - 1) % len(categories)]
        spec = CATEGORY_SPECS[category]
        brand = random.choice(spec["brands"])
        item = random.choice(spec["items"])
        size = random.choice(spec["sizes"])
        qualifier = random.choice(QUALIFIERS)
        sku = f"{category[:3].upper()}-{product_id:05d}"
        price = build_price(spec["price"], size)
        stock = random.randint(0, 250)
        rating = round(random.uniform(3.6, 4.9), 1)
        text = f"{brand} {qualifier} {item} {size}"
        metadata = (
            f"{text} from {category}. Brand: {brand}. Variant: {item}. Size: {size}. "
            f"Current Price: ${price:.2f}. Stock: {stock}. Rating: {rating}. SKU: {sku}."
        )
        products.append(
            {
                "id": product_id,
                "text": text,
                "price": f"{price:.2f}",
                "category": category,
                "metadata": metadata,
            }
        )
    return products


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5000, help="Number of products to generate")
    parser.add_argument("--output", default="data/products.json", help="Output JSON path")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    products = build_catalog(args.count)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=2)

    print(f"Wrote {len(products)} products to {output_path}")


if __name__ == "__main__":
    main()
