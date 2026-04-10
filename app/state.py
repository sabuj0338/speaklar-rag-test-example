from __future__ import annotations

import json
from typing import Any, Protocol

from redis import Redis
from redis.exceptions import RedisError


class StateStore(Protocol):
    def get_state(self, session_id: str) -> dict[str, Any]: ...

    def set_state(self, session_id: str, state: dict[str, Any]) -> None: ...


class InMemoryStateStore:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get_state(self, session_id: str) -> dict[str, Any]:
        return self._store.get(session_id, {}).copy()

    def set_state(self, session_id: str, state: dict[str, Any]) -> None:
        self._store[session_id] = state.copy()


class RedisStateStore:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    def get_state(self, session_id: str) -> dict[str, Any]:
        try:
            payload = self.redis_client.get(f"state:{session_id}")
        except RedisError:
            return {}
        return json.loads(payload) if payload else {}

    def set_state(self, session_id: str, state: dict[str, Any]) -> None:
        try:
            self.redis_client.set(f"state:{session_id}", json.dumps(state, ensure_ascii=False))
        except RedisError:
            return
