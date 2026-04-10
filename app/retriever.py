from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import faiss
import numpy as np

from app.embeddings import Embedder


@dataclass
class Retriever:
    model: Embedder
    index: faiss.Index
    id_map: dict[str, dict[str, Any]]

    def search(self, query: str, k: int = 8) -> list[dict[str, Any]]:
        embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(embedding, dtype="float32"), k)
        results: list[dict[str, Any]] = []
        for idx in indices[0]:
            if idx < 0:
                continue
            item = self.id_map.get(str(idx))
            if item:
                results.append(item)
        return results
