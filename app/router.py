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
- Chain of Thought: ALWAYS generate "reasoning" FIRST. Briefly explain the connection between the query and the selected intent.
- Context & Coreference: If the user says "এটা", "ওটা", "এটার", "আগেরটা" (this/that/it/its), you MUST extract the exact `active_product` from the provided STATE or CHAT HISTORY and set it as the `product`.
- Intent mapping for Products: If asked about ANY specific item ("শ্যাম্পু", "ল্যাপটপ", "টি শার্ট"), extract it as `product`, and set intent to `availability_product`. NEVER use `list_all_products` or `list_category_products` for specific items.
- Intent mapping for Pricing: If the query contains "দাম", "কত টাকা" or asks for price, MUST set intent to `price_product`.
- Intent mapping for Categories: ONLY output `category` if the query literally contains the exact category text (e.g., query explicitly contains the string "ইলেকট্রনিক্স"). If the query instead asks for "ল্যাপটপ" or "টি শার্ট", DO NOT output `category`. You MUST output `product="ল্যাপটপ"`.
- Intent mapping for Vague requests: For slang like "জম্পেশ", "ভালো কিছু", use `recommendation`.
- Non-product relevance: Queries about "ডেলিভারি", "শিপিং", "পেমেন্ট" ARE highly relevant. Set `intent` to `unknown` and `is_relevant=true`. NEVER use `out_of_scope` for these.
- EXACT SUBSTRING MATCHING: NEVER translate words into English! If the user says "ল্যাপটপ", extract exactly "ল্যাপটপ" as `product`, NOT "laptop".
- Out of scope: Use `out_of_scope` ONLY for politics, weather, and completely irrelevant topics.

JSON Structure MUST exactly be:
{"reasoning":"Step-by-step logic... User said 'এটার', active_product is 'লবণ', so extracting 'লবণ'","intent":"...","product":null,"category":null,"price_filter":null,"is_relevant":true,"confidence":0.9}"""


def _build_user_prompt(query: str, state: dict[str, Any]) -> str:
    """Build the user prompt with query and linear conversation history."""
    parts = []

    history = state.get("history", [])
    if history:
        parts.append("--- CHAT HISTORY ---")
        for turn in history:
            if "user" in turn:
                parts.append(f"User: {turn['user']}")
            if "assistant" in turn:
                parts.append(f"Assistant: {turn['assistant']}")
        parts.append("--------------------")

    ctx = []
    if state.get("active_product"):
        ctx.append(f"active_product='{state['active_product']}'")
    if state.get("active_category"):
        ctx.append(f"active_category='{state['active_category']}'")
    if state.get("active_products"):
        ctx.append(f"shown_products=[{','.join(state['active_products'][:3])}]")

    if ctx:
        parts.append(f"STATE: {', '.join(ctx)}")

    parts.append(f"CURRENT QUERY: {query}")
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
