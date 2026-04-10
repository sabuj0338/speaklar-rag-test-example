from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer

from app.catalog import normalize_text


class Embedder:
    def encode(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError


@dataclass
class SentenceTransformerEmbedder(Embedder):
    model: SentenceTransformer

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.array(
            self.model.encode(texts, normalize_embeddings=True),
            dtype="float32",
        )


class HashingEmbedder(Embedder):
    def __init__(self, dimensions: int = 512) -> None:
        self.dimensions = dimensions

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimensions), dtype="float32")
        for row_index, text in enumerate(texts):
            tokens = normalize_text(text).split()
            for token in tokens:
                digest = hashlib.md5(token.encode("utf-8")).hexdigest()
                index = int(digest, 16) % self.dimensions
                vectors[row_index, index] += 1.0
            norm = np.linalg.norm(vectors[row_index])
            if norm:
                vectors[row_index] /= norm
        return vectors


def load_embedder(model_name: str) -> tuple[Embedder, str]:
    try:
        model = SentenceTransformer(model_name, local_files_only=True)
        return SentenceTransformerEmbedder(model), "sentence-transformers"
    except Exception:
        return HashingEmbedder(), "hashing"


def ensure_embedder_dimensions(embedder: Embedder, dimensions: int) -> tuple[Embedder, str]:
    sample = embedder.encode(["dimension check"])
    if sample.shape[1] == dimensions:
        return embedder, "matched"
    return HashingEmbedder(dimensions=dimensions), "hashing-dimension-fallback"
