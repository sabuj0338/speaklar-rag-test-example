from time import perf_counter

from fastapi import APIRouter, HTTPException, Request

from app.answer_engine import build_answer
from app.catalog import normalize_text
from app.cache import make_cache_key
from app.resolver import resolve_query
from app.schemas import AskResponse

router = APIRouter()

VAGUE_REFERENCES = {
    "it",
    "this",
    "that",
    "this one",
    "that one",
    "how much",
    "price",
    "eta",
    "ota",
    "etar",
    "otar",
    "এটা",
    "ওটা",
    "এটার",
    "ওটার",
}


def is_vague_reference(query: str) -> bool:
    normalized = " ".join(query.lower().split())
    return any(token in normalized for token in VAGUE_REFERENCES)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ask", response_model=AskResponse)
def ask(request: Request, query: str, session_id: str) -> AskResponse:
    started_at = perf_counter()
    settings = request.app.state.settings
    retriever = request.app.state.retriever
    catalog = request.app.state.catalog
    category_products = request.app.state.category_products
    product_lookup = request.app.state.product_lookup
    state_store = request.app.state.state_store
    cache_store = request.app.state.cache_store
    entity_resolver = request.app.state.entity_resolver
    llm_fallback = request.app.state.llm_fallback

    state = state_store.get_state(session_id)
    resolver_started_at = perf_counter()
    resolved = resolve_query(query, state, entity_resolver)
    resolver_time_ms = (perf_counter() - resolver_started_at) * 1000
    cache_key = make_cache_key(session_id, resolved.intent, resolved.product, resolved.category)

    cached = cache_store.get(cache_key)
    if cached:
        cached_response = AskResponse.model_validate(cached)
        cached_response.api_time_ms = (perf_counter() - started_at) * 1000
        cached_response.resolver_time_ms = resolver_time_ms
        return cached_response

    if resolved.intent == "availability_product" and not resolved.product and not resolved.category:
        if is_vague_reference(query) or state.get("active_product") or state.get("active_category"):
            response = AskResponse(
                answer="Which product are you asking about? Please tell me the product name again.",
                status="ambiguous",
                source="clarification",
                resolved=resolved,
                api_time_ms=0.0,
                groq_time_ms=0.0,
                resolver_time_ms=resolver_time_ms,
                state=state,
                matched_products=[],
            )
        else:
            response = AskResponse(
                answer="No, I don't have that product in the catalog.",
                status="missing",
                source="retriever",
                resolved=resolved,
                api_time_ms=0.0,
                groq_time_ms=0.0,
                resolver_time_ms=resolver_time_ms,
                state=state,
                matched_products=[],
            )
        response.api_time_ms = (perf_counter() - started_at) * 1000
        cache_store.set(cache_key, response.model_dump(), settings.negative_cache_ttl_seconds)
        return response

    if resolved.intent == "list_all_products":
        results = catalog
    elif resolved.intent in {"price_min", "price_max"} and resolved.category:
        results = category_products.get(normalize_text(resolved.category), [])
    elif resolved.intent in {"price_min", "price_max"}:
        results = catalog
    elif resolved.intent in {"category_availability", "list_category_products"} and resolved.category:
        results = category_products.get(normalize_text(resolved.category), [])
    elif resolved.intent in {"availability_product", "price_product"} and resolved.product:
        direct_match = product_lookup.get(normalize_text(resolved.product))
        results = [direct_match] if direct_match else []
    elif resolved.intent == "price_product" and not resolved.product and len(state.get("active_products", [])) > 1:
        results = catalog
    else:
        search_query = resolved.product or resolved.category or query
        try:
            results = retriever.search(search_query, k=settings.top_k)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    answer = build_answer(resolved, results, state)
    if answer:
        answer.api_time_ms = (perf_counter() - started_at) * 1000
        answer.groq_time_ms = 0.0
        answer.resolver_time_ms = resolver_time_ms
        state_store.set_state(session_id, answer.state)
        ttl = settings.cache_ttl_seconds if answer.status == "found" else settings.negative_cache_ttl_seconds
        cache_store.set(cache_key, answer.model_dump(), ttl)
        return answer

    llm_text, groq_time_ms = llm_fallback.answer(query, results[:3])
    response = AskResponse(
        answer=llm_text or "I don't know.",
        status="fallback",
        source="llm_fallback",
        resolved=resolved,
        api_time_ms=0.0,
        groq_time_ms=groq_time_ms,
        resolver_time_ms=resolver_time_ms,
        state=state,
        matched_products=[item["text"] for item in results[:3]],
    )
    response.api_time_ms = (perf_counter() - started_at) * 1000
    cache_store.set(cache_key, response.model_dump(), settings.negative_cache_ttl_seconds)
    return response
