from contextlib import asynccontextmanager

import faiss
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from redis.exceptions import RedisError

from app.cache import InMemoryCacheStore, RedisCacheStore, FaissSemanticCache
from app.catalog import load_json, normalize_text
from app.config import get_settings
from app.embeddings import ensure_embedder_dimensions, load_embedder
from app.entity import EntityResolver
from app.llm import GroqFallback
from app.retriever import Retriever
from app.routes import router
from app.state import InMemoryStateStore, RedisStateStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    if not settings.faiss_index_path.exists():
        raise FileNotFoundError(
            f"Missing FAISS index at {settings.faiss_index_path}. Run `python3 scripts/build_index.py` first."
        )
    if not settings.product_map_path.exists():
        raise FileNotFoundError(
            f"Missing product map at {settings.product_map_path}. Run `python3 scripts/build_index.py` first."
        )

    id_map = load_json(settings.product_map_path)
    catalog = list(id_map.values())
    product_names = [item["text"] for item in id_map.values()]
    categories = sorted({item.get("category", "") for item in id_map.values() if item.get("category")})
    category_products: dict[str, list[dict]] = {}
    product_lookup: dict[str, dict] = {}
    for item in catalog:
        category = item.get("category")
        if not category:
            continue
        category_products.setdefault(normalize_text(category), []).append(item)
        product_lookup[normalize_text(item["text"])] = item

    index = faiss.read_index(str(settings.faiss_index_path))
    model, embedder_name = load_embedder(settings.embedding_model)
    model, dimension_status = ensure_embedder_dimensions(model, index.d)
    if dimension_status == "hashing-dimension-fallback":
        embedder_name = f"{embedder_name}+dimension-fallback"

    redis_client = None
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        redis_client.flushdb()  # Clear redis caches on startup
    except RedisError:
        redis_client = None

    app.state.settings = settings
    app.state.retriever = Retriever(model=model, index=index, id_map=id_map)
    app.state.catalog = catalog
    app.state.category_products = category_products
    app.state.product_lookup = product_lookup
    app.state.embedder_name = embedder_name
    app.state.entity_resolver = EntityResolver(product_names=product_names, categories=categories)
    app.state.state_store = RedisStateStore(redis_client) if redis_client else InMemoryStateStore()
    app.state.cache_store = RedisCacheStore(redis_client) if redis_client else InMemoryCacheStore()
    app.state.llm_fallback = GroqFallback(settings.groq_api_key, settings.groq_model)
    app.state.semantic_cache = FaissSemanticCache(
        embedder=model,
        cache_dir=settings.faiss_index_path.parent / "semantic_cache"
    )
    app.state.semantic_cache.clear()  # Clear semantic cache on startup

    yield


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
