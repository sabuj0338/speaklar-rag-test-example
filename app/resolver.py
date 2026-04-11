import re
from app.entity import EntityResolver
from app.intent import detect_intent
from app.schemas import ResolvedQuery


VAGUE_REFERENCES = {
    "it",
    "this",
    "that",
    "this one",
    "that one",
    "how much",
    "price",
    "which",
    "which one",
    "one",
    "the cheapest",
    "the highest",
    "eta",
    "ota",
    "etar",
    "otar",
    "এটা",
    "ওটা",
    "এটার",
    "ওটার",
    "দাম",
    "কত",
    "কত টাকা",
}


def is_vague_reference(query: str) -> bool:
    normalized = " ".join(query.lower().split())
    for token in VAGUE_REFERENCES:
        if re.search(r'\b' + re.escape(token) + r'\b', normalized):
            return True
    return False


def resolve_query(query: str, state: dict, entity_resolver: EntityResolver) -> ResolvedQuery:
    intent = detect_intent(query)
    product = None
    category = None

    if intent == "list_all_products":
        confidence = 0.98
        return ResolvedQuery(intent=intent, product=None, category=None, confidence=confidence)

    vague = is_vague_reference(query)

    if intent in {"price_min", "price_max"}:
        category = entity_resolver.detect_category(query)
        if not category and vague:
            category = state.get("active_category")
        confidence = 0.98 if category else 0.98
        return ResolvedQuery(intent=intent, product=None, category=category, confidence=confidence)

    if intent in {"category_availability", "list_category_products"}:
        category = entity_resolver.detect_category(query)
        if not category and vague:
            category = state.get("active_category")
        confidence = 0.95 if category else 0.45
        return ResolvedQuery(intent=intent, product=None, category=category, confidence=confidence)

    category = entity_resolver.detect_category(query)
    product = entity_resolver.extract_product(query)

    if not product and vague:
        if state.get("active_product"):
            product = state["active_product"]
        elif state.get("active_products"):
            active_products = state["active_products"]
            if len(active_products) == 1:
                product = active_products[0]

    if not category and vague:
        category = state.get("active_category")

    confidence = 0.95 if product or category else 0.45

    return ResolvedQuery(intent=intent, product=product, category=category, confidence=confidence)
