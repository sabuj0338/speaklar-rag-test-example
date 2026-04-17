from time import perf_counter

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from app.answer_engine import build_answer
from app.catalog import normalize_text
from app.cache import make_cache_key
from app.schemas import AskResponse

router = APIRouter()

@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ask", response_model=AskResponse)
def ask(
    request: Request,
    query: str,
    session_id: str,
    background_tasks: BackgroundTasks
) -> AskResponse:
    started_at = perf_counter()
    settings = request.app.state.settings
    retriever = request.app.state.retriever
    catalog = request.app.state.catalog
    category_products = request.app.state.category_products
    product_lookup = request.app.state.product_lookup
    state_store = request.app.state.state_store
    cache_store = request.app.state.cache_store
    llm_router = request.app.state.llm_router
    llm_fallback = request.app.state.llm_fallback

    # 1. Get conversation state
    state = state_store.get_state(session_id)

    def _finalize_response(resp: AskResponse) -> AskResponse:
        history = resp.state.get("history", [])
        history.append({"user": query, "assistant": resp.answer})
        resp.state["history"] = history[-6:]
        state_store.set_state(session_id, resp.state)
        return resp

    # 2. Route through LLM Router (replaces intent.py + entity.py + resolver.py)
    resolved, router_time_ms = llm_router.route(query, state)
    
    # Eagerly update context mappings so Fallback and subsequent vague queries don't lose context
    if resolved.product:
        state["active_product"] = resolved.product
    if resolved.category:
        state["active_category"] = resolved.category

    # 3. If query is out of scope, reject immediately
    if not resolved.is_relevant or resolved.intent == "out_of_scope":
        response = AskResponse(
            answer="দুঃখিত, আমি শুধুমাত্র আমাদের পণ্য সম্পর্কিত প্রশ্নের উত্তর দিতে পারি। আপনি কি কোনো পণ্য সম্পর্কে জানতে চান?",
            status="rejected",
            source="router",
            resolved=resolved,
            api_time_ms=(perf_counter() - started_at) * 1000,
            groq_time_ms=0.0,
            router_time_ms=router_time_ms,
            total_groq_time_ms=router_time_ms,
            state=state,
            matched_products=[],
        )
        return _finalize_response(response)

    # 4. Check cache
    cache_key = make_cache_key(session_id, resolved.intent, resolved.product, resolved.category)

    # 5. Determine retrieval strategy based on router output
    if resolved.intent == "list_all_products":
        results = catalog
    elif resolved.intent in {"price_min", "price_max"} and resolved.category:
        results = category_products.get(normalize_text(resolved.category), [])
    elif resolved.intent in {"price_min", "price_max"}:
        results = catalog
    elif resolved.intent == "budget_search" and resolved.price_filter:
        try:
            from app.catalog import parse_price
            budget = float(resolved.price_filter)
            source_list = category_products.get(normalize_text(resolved.category), []) if resolved.category else catalog
            matches = [p for p in source_list if parse_price(p["price"]) <= budget]
            if resolved.product:
                product_norm = normalize_text(resolved.product)
                matches = [
                    p for p in matches 
                    if product_norm in normalize_text(p.get("text", "")) or product_norm in normalize_text(p.get("category", ""))
                ]
            matches = sorted(matches, key=lambda p: parse_price(p["price"]), reverse=True)
            results = matches[:settings.top_k]
        except ValueError:
            results = catalog
    elif resolved.intent in {"category_availability", "list_category_products"} and resolved.category:
        results = category_products.get(normalize_text(resolved.category), [])
    elif resolved.intent in {"availability_product", "price_product"} and resolved.product:
        direct_match = product_lookup.get(normalize_text(resolved.product))
        results = [direct_match] if direct_match else []
        # If no direct match, try FAISS semantic search
        if not results:
            try:
                results = retriever.search(resolved.product, k=settings.top_k)
            except FileNotFoundError as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
    elif resolved.intent == "price_product" and not resolved.product and len(state.get("active_products", [])) > 1:
        results = catalog
    else:
        # For product_search, recommendation, comparison, unknown — use FAISS
        search_query = resolved.product or resolved.category or query
        try:
            results = retriever.search(search_query, k=settings.top_k)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # 6. Try structured answer first
    answer = build_answer(resolved, results, state)
    if answer:
        answer.api_time_ms = (perf_counter() - started_at) * 1000
        answer.groq_time_ms = 0.0
        answer.router_time_ms = router_time_ms
        answer.total_groq_time_ms = router_time_ms
        ttl = settings.cache_ttl_seconds if answer.status == "found" else settings.negative_cache_ttl_seconds
        cache_store.set(cache_key, answer.model_dump(), ttl)
        return _finalize_response(answer)

    # 7. Check semantic cache
    semantic_cache = request.app.state.semantic_cache
    semantic_hit = semantic_cache.search(query)
    if semantic_hit:
        semantic_response = AskResponse.model_validate(semantic_hit)
        semantic_response.api_time_ms = (perf_counter() - started_at) * 1000
        semantic_response.router_time_ms = router_time_ms
        semantic_response.total_groq_time_ms = semantic_response.groq_time_ms + router_time_ms
        semantic_response.state = state  # PRESERVE user state (do not leak cached state)
        cache_store.set(cache_key, semantic_response.model_dump(), settings.cache_ttl_seconds)
        return _finalize_response(semantic_response)

    # 8. LLM Fallback for answer generation
    llm_text, groq_time_ms = llm_fallback.answer(query, results[:3])
    # Update active product blindly based on the top vector match used in the fallback
    if results:
        state["active_product"] = results[0]["text"]
        if "category" in results[0]:
            state["active_category"] = results[0]["category"]

    response = AskResponse(
        answer=llm_text or "দুঃখিত, আমাদের তালিকায় এটি নেই।",
        status="fallback",
        source="llm_fallback",
        resolved=resolved,
        api_time_ms=0.0,
        groq_time_ms=groq_time_ms,
        router_time_ms=router_time_ms,
        total_groq_time_ms=router_time_ms + groq_time_ms,
        state=state,
        matched_products=[item["text"] for item in results[:3]],
    )
    response.api_time_ms = (perf_counter() - started_at) * 1000
    cache_store.set(cache_key, response.model_dump(), settings.negative_cache_ttl_seconds)
    
    semantic_cache.add(query, response.model_dump())
    background_tasks.add_task(semantic_cache.save)

    return _finalize_response(response)
