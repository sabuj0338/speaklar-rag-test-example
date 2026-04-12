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
    "প্রাইস",
    "মূল্য",
    "এইটা",
    "সেইটা",
    "এইটার",
    "সেইটার",
}


def is_vague_reference(query: str) -> bool:
    normalized = " ".join(query.lower().split())
    cleaned = re.sub(r'[?,.!।]', '', normalized)
    tokens = cleaned.split()
    from app.entity import strip_bangla_suffixes
    for token in tokens:
        base_token = strip_bangla_suffixes(token)
        if token in VAGUE_REFERENCES or base_token in VAGUE_REFERENCES:
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

    # For availability & price intents, try both entity and category
    category = entity_resolver.detect_category(query)
    product = entity_resolver.extract_product(query)

    # If we found a category but not a product, re-map intent
    if category and not product:
        if intent == "availability_product":
            intent = "category_availability"
        elif intent == "price_product":
            # Keep price_product but with category context
            pass

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
