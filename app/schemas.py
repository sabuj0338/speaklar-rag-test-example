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
    "product_search",
    "product_detail",
    "recommendation",
    "comparison",
    "out_of_scope",
    "unknown",
]


class RouterResult(BaseModel):
    """Structured output from the LLM Router."""
    intent: str = "unknown"
    product: str | None = None
    category: str | None = None
    price_filter: str | None = None  # "min", "max", "under_500", etc.
    is_relevant: bool = True
    confidence: float = 0.0
    reasoning: str | None = None  # LLM's brief explanation of its routing decision


class AskResponse(BaseModel):
    answer: str
    status: Literal["found", "ambiguous", "missing", "unavailable", "fallback", "rejected"]
    source: Literal["exact_cache", "retriever", "llm_fallback", "clarification", "semantic_cache", "router"]
    resolved: RouterResult
    api_time_ms: float = 0.0
    groq_time_ms: float = 0.0
    router_time_ms: float = 0.0
    total_groq_time_ms: float = 0.0
    state: dict[str, Any] = Field(default_factory=dict)
    matched_products: list[str] = Field(default_factory=list)
