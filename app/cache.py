from __future__ import annotations

import json
from typing import Any, Protocol

from redis import Redis
from redis.exceptions import RedisError

from pathlib import Path
import faiss
import numpy as np
from app.embeddings import Embedder


class CacheStore(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None: ...


class InMemoryCacheStore:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        cached = self._store.get(key)
        return cached.copy() if cached else None

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self._store[key] = value.copy()


class RedisCacheStore:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    def get(self, key: str) -> dict[str, Any] | None:
        try:
            payload = self.redis_client.get(key)
        except RedisError:
            return None
        return json.loads(payload) if payload else None

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        try:
            self.redis_client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
        except RedisError:
            return


def make_cache_key(session_id: str, intent: str, product: str | None, category: str | None) -> str:
    parts = [
        "ask",
        session_id,
        intent or "none",
        product or "none",
        category or "none",
    ]
    return ":".join(parts)


class FaissSemanticCache:
    def __init__(self, embedder: Embedder, cache_dir: str | Path, threshold: float = 0.12):
        self.embedder = embedder
        self.threshold = threshold
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / "semantic.index"
        self.map_path = self.cache_dir / "semantic_map.json"
        
        self.id_map: dict[str, dict[str, Any]] = {}
        dim = self.embedder.encode(["dummy"]).shape[1]
        
        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
            except Exception:
                self.index = faiss.IndexFlatL2(dim)
        else:
            self.index = faiss.IndexFlatL2(dim)
            
        if self.map_path.exists():
            try:
                with open(self.map_path, "r", encoding="utf-8") as f:
                    self.id_map = json.load(f)
            except Exception:
                self.id_map = {}

    def search(self, query: str) -> dict[str, Any] | None:
        if self.index.ntotal == 0:
            return None
        embedding = self.embedder.encode([query])
        distances, indices = self.index.search(np.array(embedding, dtype="float32"), 1)
        if len(distances) > 0 and len(distances[0]) > 0:
            best_distance = distances[0][0]
            best_index = indices[0][0]
            if best_distance < self.threshold and best_index >= 0:
                item = self.id_map.get(str(best_index))
                if item:
                    item_copy = item.copy()
                    item_copy["source"] = "semantic_cache"
                    item_copy["api_time_ms"] = 0.0
                    item_copy["groq_time_ms"] = 0.0
                    return item_copy
        return None

    def add(self, query: str, response: dict[str, Any]) -> None:
        embedding = self.embedder.encode([query])
        next_id = str(self.index.ntotal)
        self.index.add(np.array(embedding, dtype="float32"))
        self.id_map[next_id] = response.copy()

    def save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        with open(self.map_path, "w", encoding="utf-8") as f:
            json.dump(self.id_map, f, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        self.index.reset()
        self.id_map.clear()
        self.save()
