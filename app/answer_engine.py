from __future__ import annotations

from typing import Any

from app.catalog import normalize_text, parse_price
from app.schemas import AskResponse, ResolvedQuery


def _unique_names(results: list[dict[str, Any]], limit: int = 5) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for item in results:
        name = item["text"]
        if name not in seen:
            seen.add(name)
            names.append(name)
        if len(names) >= limit:
            break
    return names


def _filter_by_category(results: list[dict[str, Any]], category: str | None) -> list[dict[str, Any]]:
    if not category:
        return results
    matched = [
        item
        for item in results
        if category in normalize_text(item.get("category", ""))
        or category in normalize_text(item.get("metadata", ""))
    ]
    return matched or results


def _find_product(results: list[dict[str, Any]], product: str) -> dict[str, Any] | None:
    normalized_product = normalize_text(product)
    for item in results:
        haystacks = [
            item.get("text", ""),
            item.get("metadata", ""),
            item.get("category", ""),
        ]
        if any(normalized_product in normalize_text(field) for field in haystacks):
            return item
    return None


def _format_price(price: Any) -> str:
    return f"${parse_price(price):,.2f}"


def build_answer(
    resolved: ResolvedQuery,
    results: list[dict[str, Any]],
    state: dict[str, Any],
) -> AskResponse | None:
    intent = resolved.intent
    product = resolved.product
    category = resolved.category
    filtered = _filter_by_category(results, category)

    if intent == "list_all_products":
        names = _unique_names(results, limit=5)
        updated_state = {k: v for k, v in state.items() if k != "active_product" and k != "active_category"}
        updated_state["active_products"] = names
        return AskResponse(
            answer=f"We sell: {', '.join(names)}.",
            status="found",
            source="retriever",
            resolved=resolved,
            state=updated_state,
            matched_products=names,
        )

    if intent == "category_availability":
        names = _unique_names(filtered, limit=3)
        updated_state = {k: v for k, v in state.items() if k != "active_product"}
        updated_state.update({"active_category": category, "active_products": names})
        if len(names) == 1:
            updated_state["active_product"] = names[0]
        return AskResponse(
            answer=f"Yes, we have {category}. Available items include: {', '.join(names)}." if names else f"Sorry, I could not confirm {category} right now.",
            status="found" if names else "unavailable",
            source="retriever",
            resolved=resolved,
            state=updated_state,
            matched_products=names,
        )

    if intent == "list_category_products":
        names = _unique_names(filtered, limit=5)
        updated_state = {k: v for k, v in state.items() if k != "active_product"}
        updated_state.update({"active_category": category, "active_products": names})
        if len(names) == 1:
            updated_state["active_product"] = names[0]
        return AskResponse(
            answer=f"Available {category} products: {', '.join(names)}." if names else f"Sorry, I could not find any {category} products.",
            status="found" if names else "missing",
            source="retriever",
            resolved=resolved,
            state=updated_state,
            matched_products=names,
        )

    if intent == "price_min":
        item = min(results, key=lambda value: parse_price(value["price"]))
        updated_state = {**state, "active_product": item["text"], "active_category": item.get("category")}
        return AskResponse(
            answer=f"The cheapest product is {item['text']} at {_format_price(item['price'])}.",
            status="found",
            source="retriever",
            resolved=resolved,
            state=updated_state,
            matched_products=[item["text"]],
        )

    if intent == "price_max":
        item = max(results, key=lambda value: parse_price(value["price"]))
        updated_state = {**state, "active_product": item["text"], "active_category": item.get("category")}
        return AskResponse(
            answer=f"The highest priced product is {item['text']} at {_format_price(item['price'])}.",
            status="found",
            source="retriever",
            resolved=resolved,
            state=updated_state,
            matched_products=[item["text"]],
        )

    if intent == "availability_product":
        if not product:
            return AskResponse(
                answer="Which product are you asking about?",
                status="ambiguous",
                source="clarification",
                resolved=resolved,
                state=state,
            )
        item = _find_product(results, product)
        if not item:
            return AskResponse(
                answer=f"Sorry, I could not find {product} in the catalog.",
                status="missing",
                source="retriever",
                resolved=resolved,
                state=state,
            )
        updated_state = {**state, "active_product": item["text"], "active_category": item.get("category")}
        return AskResponse(
            answer=f"Yes, we have {item['text']}.",
            status="found",
            source="retriever",
            resolved=resolved,
            state=updated_state,
            matched_products=[item["text"]],
        )

    if intent == "price_product":
        if not product:
            active_products = state.get("active_products", [])
            if len(active_products) > 1:
                preview_items = [
                    _find_product(results, candidate) for candidate in active_products[:3]
                ]
                preview_pairs = [
                    f"{item['text']} ({_format_price(item['price'])})"
                    for item in preview_items
                    if item
                ]
                preview = ", ".join(preview_pairs or active_products[:3])
                return AskResponse(
                    answer=f"There are multiple products in context. Here are a few prices: {preview}. Please name one if you want an exact price.",
                    status="ambiguous",
                    source="clarification",
                    resolved=resolved,
                    state=state,
                    matched_products=active_products[:3],
                )
            return AskResponse(
                answer="Which product price do you want to know?",
                status="ambiguous",
                source="clarification",
                resolved=resolved,
                state=state,
            )
        item = _find_product(results, product)
        if not item:
            return AskResponse(
                answer=f"Sorry, I could not find a price for {product}.",
                status="missing",
                source="retriever",
                resolved=resolved,
                state=state,
            )
        updated_state = {**state, "active_product": item["text"], "active_category": item.get("category")}
        return AskResponse(
            answer=f"{item['text']} price is {_format_price(item['price'])}.",
            status="found",
            source="retriever",
            resolved=resolved,
            state=updated_state,
            matched_products=[item["text"]],
        )

    return None
