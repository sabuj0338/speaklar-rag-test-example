from app.entity import EntityResolver
from app.intent import detect_intent
from app.schemas import ResolvedQuery


def resolve_query(query: str, state: dict, entity_resolver: EntityResolver) -> ResolvedQuery:
    intent = detect_intent(query)
    product = None
    category = None

    if intent == "list_all_products":
        confidence = 0.98
        return ResolvedQuery(intent=intent, product=None, category=None, confidence=confidence)

    if intent in {"price_min", "price_max"}:
        category = entity_resolver.detect_category(query) or state.get("active_category")
        confidence = 0.98 if category else 0.98
        return ResolvedQuery(intent=intent, product=None, category=category, confidence=confidence)

    if intent in {"category_availability", "list_category_products"}:
        category = entity_resolver.detect_category(query) or state.get("active_category")
        confidence = 0.95 if category else 0.45
        return ResolvedQuery(intent=intent, product=None, category=category, confidence=confidence)

    category = entity_resolver.detect_category(query)
    product = entity_resolver.extract_product(query)

    if not product:
        if state.get("active_product"):
            product = state["active_product"]
        elif state.get("active_products"):
            active_products = state["active_products"]
            if len(active_products) == 1:
                product = active_products[0]

    if not category:
        category = state.get("active_category")

    confidence = 0.95 if product or category else 0.45

    return ResolvedQuery(intent=intent, product=product, category=category, confidence=confidence)
