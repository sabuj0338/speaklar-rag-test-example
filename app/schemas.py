from typing import Any, Literal

from pydantic import BaseModel, Field


IntentName = Literal[
    "list_all_products",
    "category_availability",
    "list_category_products",
    "price_min",
    "price_max",
    "availability_product",
    "price_product",
    "unknown",
]


class ResolvedQuery(BaseModel):
    intent: IntentName
    product: str | None = None
    category: str | None = None
    confidence: float = 0.0


class AskResponse(BaseModel):
    answer: str
    status: Literal["found", "ambiguous", "missing", "unavailable", "fallback"]
    source: Literal["exact_cache", "retriever", "llm_fallback", "clarification", "semantic_cache"]
    resolved: ResolvedQuery
    api_time_ms: float = 0.0
    groq_time_ms: float = 0.0
    resolver_time_ms: float = 0.0
    state: dict[str, Any] = Field(default_factory=dict)
    matched_products: list[str] = Field(default_factory=list)
