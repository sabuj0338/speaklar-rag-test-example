import argparse
import csv
import json
from pathlib import Path


def build_metadata(row: dict[str, str]) -> str:
    category = row.get("category", "").strip()
    description = row.get("description", "").strip()
    quantity = row.get("quantity", "").strip()
    sku = row.get("sku", "").strip()
    return f"{row['name']} from {category}. SKU: {sku}. Quantity: {quantity}. {description}".strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", default="data/products.json", help="Output JSON path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    products: list[dict[str, str]] = []
    with input_path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            products.append(
                {
                    "id": int(row["id"]),
                    "text": row["name"],
                    "price": row["price"],
                    "category": row.get("category", ""),
                    "metadata": build_metadata(row),
                }
            )

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=2)

    print(f"Wrote {len(products)} products to {output_path}")


if __name__ == "__main__":
    main()
