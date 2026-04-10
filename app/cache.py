from __future__ import annotations

import json
from typing import Any, Protocol

from redis import Redis
from redis.exceptions import RedisError


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
