import json
import sys
from pathlib import Path

import faiss
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.embeddings import load_embedder


def main() -> None:
    settings = get_settings()
    settings.faiss_index_path.parent.mkdir(parents=True, exist_ok=True)

    with settings.products_path.open("r", encoding="utf-8") as file:
        products = json.load(file)

    embedder, embedder_name = load_embedder(settings.embedding_model)
    texts = [f"{item['text']} {item.get('category', '')} {item.get('metadata', '')}" for item in products]
    embeddings = embedder.encode(texts)
    vectors = np.array(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(settings.faiss_index_path))

    id_map = {str(i): products[i] for i in range(len(products))}
    with settings.product_map_path.open("w", encoding="utf-8") as file:
        json.dump(id_map, file, ensure_ascii=False, indent=2)

    print(
        f"Built index with {len(products)} products at {settings.faiss_index_path} using {embedder_name} embeddings"
    )


if __name__ == "__main__":
    main()
