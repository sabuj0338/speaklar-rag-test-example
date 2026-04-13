"""
LLM Router — Replaces the heuristic intent/entity/resolver pipeline.

Sends the raw user query to Groq LLM and gets back structured JSON
with intent, product, category, filters, and relevance flag.
"""

from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any

from groq import Groq

from app.schemas import RouterResult

logger = logging.getLogger(__name__)

# Compact system prompt — optimized for low token usage
ROUTER_SYSTEM_PROMPT = """You are a query router for a Bangladeshi e-commerce chatbot. Analyze Bangla/English queries and return JSON.

INTENTS: list_all_products, category_availability, list_category_products, price_min, price_max, availability_product, price_product, product_search, product_detail, recommendation, comparison, out_of_scope, unknown

CATEGORIES: ইলেকট্রনিক্স, আসবাবপত্র, খেলাধুলা, প্রসাধনী, ফ্যাশন ও পোশাক, খাদ্য ও পানীয়, স্বাস্থ্য ও ঔষধ, যন্ত্রপাতি ও সরঞ্জাম, গৃহস্থালী সামগ্রী, বই ও স্টেশনারি, খেলনা ও শিশু পণ্য, মোবাইল আনুষঙ্গিক, কৃষি ও বাগান, ডিজিটাল সেবা

RULES:
- Fix misspellings (চার্জারর→চার্জার, হেডফুন→হেডফোন)
- Understand slang (জম্পেশ=good, ফাটাফাটি=excellent, বাজেট ফ্রেন্ডলি=cheap)
- is_relevant=false ONLY for non-commerce queries (weather, politics etc)
- Use conversation state for context (এটা, ওটা, আগেরটা = reference to active product)
- If asked about ANY item, generic term, or English word (e.g. "শ্যাম্পু", "ল্যাপটপ", "salt"), MUST extract it as `product` and set intent to `availability_product` or `product_search`. Do NOT default to `list_all_products`. Do NOT assume it is a category unless explicitly a category name.
- product: extracted product name or null
- category: from valid list above or null
- price_filter: min/max/budget/mid_range/under_X or null

Return ONLY valid JSON:
{"intent":"...","product":null,"category":null,"price_filter":null,"is_relevant":true,"confidence":0.9,"reasoning":"brief"}"""


def _build_user_prompt(query: str, state: dict[str, Any]) -> str:
    """Build the user prompt with query and conversation context."""
    parts = [f"Q: {query}"]

    # Add conversation context if available
    ctx = []
    if state.get("active_product"):
        ctx.append(f"product={state['active_product']}")
    if state.get("active_category"):
        ctx.append(f"category={state['active_category']}")
    if state.get("active_products"):
        ctx.append(f"shown=[{','.join(state['active_products'][:3])}]")

    if ctx:
        parts.append(f"State: {'; '.join(ctx)}")

    return "\n".join(parts)


def _parse_router_response(raw_text: str) -> RouterResult:
    """Parse LLM response text into RouterResult, handling malformed JSON."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        import re
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                logger.warning("Failed to parse router response: %s", raw_text[:200])
                return RouterResult(intent="unknown", is_relevant=True, confidence=0.1)
        else:
            logger.warning("Failed to parse router response: %s", raw_text[:200])
            return RouterResult(intent="unknown", is_relevant=True, confidence=0.1)

    return RouterResult(
        intent=data.get("intent", "unknown"),
        product=data.get("product"),
        category=data.get("category"),
        price_filter=data.get("price_filter"),
        is_relevant=data.get("is_relevant", True),
        confidence=data.get("confidence", 0.5),
        reasoning=data.get("reasoning"),
    )


class LLMRouter:
    """Routes user queries using Groq LLM for intent + entity extraction."""

    def __init__(self, api_key: str | None, model: str) -> None:
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = model

    def route(self, query: str, state: dict[str, Any] | None = None) -> tuple[RouterResult, float]:
        """
        Route a user query through the LLM.

        Returns:
            tuple of (RouterResult, router_time_ms)
        """
        if not self.client:
            logger.warning("Groq client not configured. Returning unknown intent.")
            return RouterResult(intent="unknown", is_relevant=True, confidence=0.0), 0.0

        state = state or {}
        user_prompt = _build_user_prompt(query, state)

        started_at = perf_counter()
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_completion_tokens=300,
                response_format={"type": "json_object"},
            )
            router_time_ms = (perf_counter() - started_at) * 1000

            raw_text = completion.choices[0].message.content.strip()
            result = _parse_router_response(raw_text)
            logger.info(
                "Router [%.0fms]: intent=%s product=%s category=%s relevant=%s",
                router_time_ms, result.intent, result.product, result.category, result.is_relevant,
            )
            return result, router_time_ms

        except Exception as exc:
            router_time_ms = (perf_counter() - started_at) * 1000
            logger.error("LLM Router error (%.0fms): %s", router_time_ms, exc)
            return RouterResult(intent="unknown", is_relevant=True, confidence=0.0), router_time_ms
