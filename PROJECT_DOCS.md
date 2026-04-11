# Project Documentation

## Project Name

Context-Aware Conversational RAG for Precise Dataset-Grounded Answers

## Key Principles

These are the foundational principles that guided every architectural and implementation decision in this system:

1. **Determinism Over Generation** — Never let the LLM guess when the system can decide from structured data. Product availability, pricing, and category lookups are answered deterministically from the catalog, not generated.

2. **Intent-First Routing** — Classify what the user wants before doing any heavy work. Intent detection runs first and gates which code paths execute, preventing unnecessary computation.

3. **Context Inheritance Over Re-Asking** — Resolve vague follow-up queries (`"How much?"`, `"এটার দাম কত?"`) by inheriting session state from the previous turn, instead of asking the user to repeat themselves.

4. **Fail Safe, Not Fail Silent** — When the system cannot confidently identify a product, it asks for clarification rather than hallucinating an answer. Ambiguity triggers a clarification response, not a guess.

5. **Structured Data as Source of Truth** — All factual answers (price, availability, category membership) come directly from the product catalog. The LLM is never the authority on catalog facts.

6. **Graceful Degradation** — Every external dependency has a fallback. Redis unavailable → in-memory storage. Sentence-transformer model missing → hashing embedder. Groq API key absent → no fallback, direct "I don't know." The system always starts.

7. **Cost-Aware Computation** — Expensive operations (fuzzy matching, FAISS search, LLM calls) are gated behind cheaper checks. Token index pre-filtering narrows candidates before fuzzy matching. Direct map lookups run before vector search. Semantic cache prevents redundant LLM calls.

8. **Separation of Concerns** — Each layer has a single responsibility: intent detection → entity resolution → state management → retrieval → answer construction → caching. No layer makes decisions that belong to another.

## Project Purpose

This project is a FastAPI-based conversational RAG system designed to answer user questions from a dataset with:

- context awareness across multiple turns
- coreference handling for follow-up questions like `এটার দাম কত?`
- user-intent understanding
- precise and specific answers
- low hallucination risk
- structured, deterministic behavior before using an LLM
- Bangla-localized responses for all deterministic answer paths

The system is built for commerce-style conversations, where users may ask about:

- product availability
- product price
- cheapest product
- highest priced product
- category-level product listing
- follow-up price questions after a previous product or category mention

The main goal is not just "search and answer." The goal is to build a decision-driven assistant that understands what the user means, resolves context safely, retrieves from dataset-backed knowledge, and responds with the most reliable answer possible.

## Why This Project Exists

A normal chatbot or naive RAG pipeline often fails in multi-turn conversations.

Example:

1. User: `Do you have noodles?`
2. System: `হ্যাঁ, আমাদের কাছে noodles আছে।`
3. User: `Which one is the cheapest?`

A weak system may search only for `cheapest` or `price`, which is too vague and can return the wrong answer. This project solves that by tracking conversation state and resolving the follow-up question using previous session context.

This makes the project useful for:

- ecommerce sales assistant bots
- catalog assistants
- product inquiry systems
- support systems that must answer from controlled data
- demos or interviews for context-aware RAG architecture

## Core Design Philosophy

This project follows a simple principle:

`Do not let the model guess when the system can decide safely.`

That means:

- detect intent first
- resolve entities and context first
- retrieve from structured dataset
- answer directly whenever possible
- ask clarification when the request is ambiguous
- only use Groq fallback when deterministic logic cannot safely answer

This reduces hallucination, improves consistency, and helps maintain speed.

## Strategies Used to Meet the Purpose

### 1. Intent-Driven Answering

The system first determines what the user wants.

Supported intent groups include:

- `availability_product`
- `price_product`
- `category_availability`
- `list_category_products`
- `list_all_products`
- `price_min`
- `price_max`
- `unknown`

This is important because price questions, list questions, and availability questions should not all follow the same logic.

Intent detection is rule-based using keyword and phrase matching against both English and Bangla tokens in `intent.py`. The system detects intents like `price_min` and `price_max` early and branches them away from expensive product extraction.

### 2. Context-Aware Resolution

The system does not rely only on the current query text. It also uses session state to understand follow-up questions.

For example:

- if the user previously asked about a product, the system stores it as `active_product`
- if the user saw multiple products, the system stores them as `active_products`
- if the user mentioned a category, the system stores it as `active_category`

So when the user later says `দাম কত?`, the resolver tries to map that vague question to the current product or category context.

The resolver maintains a set of vague reference tokens including English anaphora (`it`, `this one`, `that one`) and Bangla equivalents (`এটা`, `ওটা`, `এটার`, `ওটার`, `দাম`, `কত`, `কত টাকা`). When a query contains only vague references and no extractable product/category, the system inherits the context from session state instead of attempting a fuzzy product match.

### 3. Structured Retrieval Before LLM

The project uses a dataset of products and retrieves from it instead of generating answers freely.

The system uses precomputed lookup maps built at startup:

- `category_products`: a dictionary mapping normalized category names to their product lists
- `product_lookup`: a dictionary mapping normalized product names to their records

The answer engine tries to answer directly from:

- product name
- category
- price field
- metadata field

For category intents (`category_availability`, `list_category_products`), the system uses the direct `category_products` map instead of vector retrieval. For product-specific intents (`availability_product`, `price_product`), the system first checks the `product_lookup` map for exact matches before falling back to FAISS search.

This is much safer and faster than asking an LLM to invent answers from scratch.

### 4. Clarification Instead of Guessing

If the system cannot identify a single product confidently, it does not hallucinate.

Example:

- user asks `দাম কত?`
- but session contains multiple possible products

Instead of guessing, the system responds with clarification behavior and shows several candidate prices, asking the user to name one.

The system also distinguishes between vague references and genuinely unknown products. If a query contains only vague anaphora like `it` or `এটা` but no session context exists, the system returns a clarification prompt. If the query contains actual product terms that simply don't match anything, the system returns a definitive "not found" response.

### 5. Optional LLM Fallback

When deterministic logic cannot answer properly, the app can call Groq as a constrained fallback.

The fallback prompt tells the model:

- use only the provided context
- keep the answer short
- say `I don't know` if not supported

This keeps the LLM under control and reduces unsupported answers.

Before calling Groq, the system also checks a semantic cache. If a semantically similar query was already answered by the LLM, the cached response is reused, avoiding redundant API calls.

### 6. Caching and Session Memory

The app stores:

- conversation state by `session_id`
- exact answer cache using resolved intent/entity context
- semantic cache using FAISS L2 similarity

There are three caching layers:

1. **Exact cache**: Keyed by `(session_id, intent, product, category)`. Returns in <5ms on hit. Uses configurable TTLs: 300s for positive results, 60s for negative/missing results.
2. **Semantic cache**: A FAISS-based L2 index that stores LLM fallback responses. When exact cache misses and deterministic logic fails, this layer checks if a semantically similar query was previously answered. Uses a configurable distance threshold (default 0.12).
3. **Session state**: Tracks `active_product`, `active_products`, and `active_category` per session.

Redis is used when available. If Redis is not available, the app automatically falls back to in-memory storage so development can continue.

On startup, both Redis and semantic caches are explicitly cleared to ensure a clean state for testing and demonstrations.

### 7. Offline Index Building

The FAISS index is built offline from the product dataset. This avoids doing expensive indexing inside the request path.

This keeps request handling faster and cleaner.

### 8. Entity Resolution with Token Index Pre-filtering

The entity resolver uses a multi-tier strategy to match products:

1. **Exact normalized name lookup**: Direct dictionary match after text normalization
2. **Substring containment**: Checks if the query contains or is contained within a product name
3. **Token index shortlist**: At startup, a reverse index maps every token to its containing product names. During extraction, the query tokens are looked up in this index to produce a small candidate set
4. **Fuzzy matching on shortlist**: RapidFuzz `token_set_ratio` is run only against the shortlisted candidates (up to 25), not the full product list
5. **Full fuzzy fallback**: Only if the token index produces no candidates, RapidFuzz runs against the full product name list

This tiered approach significantly reduces the cost of entity extraction compared to running full fuzzy matching on every query.

The resolver also filters out vague anaphora tokens (e.g., `it`, `this one`, `এটা`) before attempting product extraction, preventing false matches on short reference words.

### 9. Bangla Localization

All deterministic answer paths in `answer_engine.py` return Bangla-language responses. The original English response strings are preserved as comments for reference. This includes:

- product availability confirmations and denials
- price responses
- category listings
- cheapest/highest price results
- clarification prompts

The intent detection system also recognizes Bangla keywords like `দাম`, `কত টাকা`, `আছে`, `বিক্রি`, and `সবচেয়ে কম/বেশি`.

## Tools and Techniques Used

## API Layer

### FastAPI

Used for:

- building the HTTP API
- exposing `/ask`
- exposing `/health`
- loading app dependencies at startup using lifespan
- CORS middleware for browser-based testing

Why used:

- fast development
- clean request/response models
- strong typing
- production-friendly structure

### Pydantic

Used for:

- typed response schema (`AskResponse`)
- resolved query schema (`ResolvedQuery`)
- settings model (`Settings`)
- `IntentName` literal type for compile-time intent validation

Why used:

- validation
- clearer API contracts
- easier maintenance

## Retrieval and Embeddings

### FAISS

Used for:

- vector index storage for product retrieval
- semantic cache index for LLM response deduplication
- similarity search over product records

Why used:

- fast nearest-neighbor search
- suitable for RAG retrieval
- lightweight for local experiments

### Sentence Transformers

Preferred embedding path:

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Why used:

- multilingual semantic retrieval
- suitable for English and Bangla-oriented systems
- useful for product retrieval by meaning, not just exact string matching

### Hashing Embedder Fallback

Used when the sentence-transformer model is unavailable locally.

Why used:

- keeps the project runnable offline
- avoids startup/index build failure in restricted environments
- ensures FAISS and runtime retrieval still work

The embedder layer also includes dimension validation. If the loaded model's embedding dimensions don't match the FAISS index dimensions, the system automatically falls back to a `HashingEmbedder` with matching dimensions.

## State, Cache, and Session Handling

### Redis

Used for:

- session state (keyed as `state:{session_id}`)
- exact cache (keyed as `ask:{session_id}:{intent}:{product}:{category}`)

Why used:

- fast access
- suitable for conversation state
- common choice for production conversational systems

### In-Memory Fallback

If Redis is unavailable, the app uses in-memory state and cache objects.

Why used:

- local development convenience
- graceful degradation

### FAISS Semantic Cache

Used for:

- storing LLM fallback responses with their query embeddings
- finding semantically similar previously-answered queries
- avoiding redundant Groq API calls

Implementation:

- uses a separate `IndexFlatL2` index stored in `artifacts/semantic_cache/`
- persisted to disk via `semantic.index` and `semantic_map.json`
- threshold-based matching (default L2 distance < 0.12)
- cleared on every server startup for clean state

## Entity and Intent Understanding

### Rule-Based Intent Detection

Used because:

- it is fast
- predictable
- easy to debug
- often better than LLM classification for a small fixed intent set
- supports both English and Bangla keyword patterns

### RapidFuzz

Used for fuzzy product and category matching.

Why used:

- handles small spelling errors
- supports approximate user mentions
- useful when product names are not typed exactly

Fuzzy matching uses two scorers:

- `token_set_ratio` for product matching (threshold: 85)
- `ratio` for category matching (threshold: 90)

Example:

- `Basundhara Noddles` matches `Basundhara Noodles`
- `Fres famly chicken nudle` matches `Fresh Family Chicken Noodle`

### Bangla Category Mapping

The entity resolver maintains an explicit mapping of Bangla category names to their English equivalents:

- `নুডলস` / `নুডুলস` → `noodles`
- `লবণ` → `salt`
- `ড্রেস` → `dress`

## LLM Layer

### Groq

Used as an optional fallback LLM provider.

Why used:

- low-latency inference
- useful for constrained fallback responses
- supports a hybrid architecture where structured logic is primary and LLM is secondary

Configuration:

- model: `llama-3.1-8b-instant` (configurable via `GROQ_MODEL`)
- temperature: `0`
- max completion tokens: `80`
- top 3 FAISS results provided as context

## Frontend

### HTML + Tailwind CDN

Used for:

- a standalone test chat UI (`chat.html`)
- quick browser testing of the `/ask` endpoint

Features:

- session-aware multi-turn chat
- quick prompts organized by category (Basic, Multilingual, Adversarial)
- response metadata inspector panel
- browser round-trip timing
- API time display
- Groq time display
- glassmorphism dark-mode design
- auto-scrolling message area

## Dataset Strategy

The system uses a structured JSON dataset with these fields:

- `id`
- `text` (product name)
- `price`
- `category`
- `metadata`

This dataset is intentionally simple but expressive enough for:

- direct price lookup
- category-based retrieval
- follow-up context tests

The project includes a synthetic 5,000-product FMCG-style dataset generator (`scripts/generate_catalog.py`) for realistic testing.

## Request Flow

The `/ask` flow works like this:

1. Receive `query` and `session_id`
2. Load current state from Redis or memory
3. Detect user intent
4. Resolve product/category using query plus state (with early branching for aggregate intents)
5. Build a context-aware cache key from `(session_id, intent, product, category)`
6. Check exact cache
7. If the intent is product-specific and a product was resolved, check `product_lookup` for a direct match
8. If the intent is category-based, use `category_products` map for direct catalog filtering
9. Otherwise retrieve from FAISS using the resolved query
10. Run answer engine to build deterministic response
11. If answer engine returns a result, cache it and return
12. If answer engine returns `None`, check semantic cache for similar past queries
13. If semantic cache hits, return cached LLM response
14. Fall back to Groq only if all above fail
15. Cache Groq response in both exact and semantic caches
16. Save updated session state
17. Return answer with timing information (`api_time_ms`, `groq_time_ms`, `resolver_time_ms`)

## Answer Strategy

The answer engine uses intent-specific behavior. All responses are in Bangla.

### Product Availability

If a product is resolved:

- answer `হ্যাঁ, আমাদের কাছে {product} আছে।` from the catalog
- or `দুঃখিত, আমি তালিকায় {product} খুঁজে পাইনি।` if not found

If a vague reference is detected but no product is in context:

- return `আপনি কোন পণ্যটি সম্পর্কে জানতে চাইছেন?`

### Product Price

If a single product is resolved:

- return `{product}-এর দাম {price}।`

If multiple products are active:

- show several prices and ask `নির্দিষ্ট দাম জানতে অনুগ্রহ করে যেকোনো একটির নাম বলুন।`

### Category Availability

If a category is resolved:

- confirm `হ্যাঁ, আমাদের কাছে {category} আছে।`
- list example products from direct catalog map

### Category Product List

If category list intent is detected:

- return distinct products from that category
- update session state with `active_category` and `active_products`
- if only one product in category, also set `active_product`

### Cheapest and Highest Price

For these aggregate intents:

- use the full catalog (or category-filtered list if category is resolved)
- compute `min`/`max` by the structured `price` field
- set the result as `active_product` in session state

### Unknown

If structured logic cannot safely answer:

1. Check semantic cache for similar past queries
2. Use Groq fallback if configured
3. Otherwise return `I don't know.`

## Timing Strategy

The API returns:

- `api_time_ms`: total server-side processing time
- `groq_time_ms`: only the time spent inside the Groq API call
- `resolver_time_ms`: time spent in intent detection and entity resolution

The chat UI also measures:

- browser round-trip time (E2E)

This helps compare:

- frontend network time
- backend processing time
- resolver overhead
- LLM fallback time

## Project Files Explanation

## Root Files

### [README.md](/Users/sabujislam/Documents/ai/README.md)

Quick-start guide and project overview with installation, running, and testing instructions.

### [requirements.txt](/Users/sabujislam/Documents/ai/requirements.txt)

Python dependencies: `fastapi`, `uvicorn`, `faiss-cpu`, `redis`, `sentence-transformers`, `numpy`, `rapidfuzz`, `groq`, `pydantic-settings`, `python-dotenv`.

### [.env.example](/Users/sabujislam/Documents/ai/.env.example)

Sample environment variables including `APP_NAME`, `REDIS_URL`, `GROQ_API_KEY`, `GROQ_MODEL`, `EMBEDDING_MODEL`, `TOP_K`, `CACHE_TTL_SECONDS`, `NEGATIVE_CACHE_TTL_SECONDS`, `PRODUCTS_PATH`, `FAISS_INDEX_PATH`, `PRODUCT_MAP_PATH`.

### [chat.html](/Users/sabujislam/Documents/ai/chat.html)

Browser-based chat UI for talking to the `/ask` API. Features glassmorphism design, response inspector, and organized quick prompts.

### [PROJECT_DOCS.md](/Users/sabujislam/Documents/ai/PROJECT_DOCS.md)

This full documentation file.

### [PROJECT_ARCHITECTURE.md](/Users/sabujislam/Documents/ai/PROJECT_ARCHITECTURE.md)

High-level architecture overview with Mermaid flow diagrams.

### [PERFORMANCE_AUDIT.md](/Users/sabujislam/Documents/ai/PERFORMANCE_AUDIT.md)

Detailed performance analysis and optimization audit.

## Data and Artifacts

### [data/products.json](/Users/sabujislam/Documents/ai/data/products.json)

Product dataset used for indexing and answering.

### [artifacts/index.faiss](/Users/sabujislam/Documents/ai/artifacts/index.faiss)

FAISS index built from the dataset.

### [artifacts/id_map.json](/Users/sabujislam/Documents/ai/artifacts/id_map.json)

Mapping from FAISS row id to product record.

### artifacts/semantic_cache/

Directory containing the semantic cache FAISS index (`semantic.index`) and response map (`semantic_map.json`). Cleared on every server startup.

## App Folder

### [app/main.py](/Users/sabujislam/Documents/ai/app/main.py)

Main FastAPI application entry point.

Responsibilities:

- startup lifecycle using `asynccontextmanager`
- loading settings
- loading FAISS index and id_map
- building `category_products` and `product_lookup` maps at startup
- loading embedder with dimension validation
- setting up Redis or memory fallback for state and cache
- initializing `EntityResolver` with product names and categories
- initializing `FaissSemanticCache`
- clearing Redis and semantic cache on startup
- registering CORS middleware
- registering routes

### [app/config.py](/Users/sabujislam/Documents/ai/app/config.py)

Application configuration using `pydantic-settings`.

Fields:

- `app_name`: API display name
- `redis_url`: Redis connection URL
- `groq_api_key`: optional Groq API key
- `groq_model`: LLM model name (default: `llama-3.1-8b-instant`)
- `embedding_model`: sentence-transformer model name
- `top_k`: FAISS search result count (default: 8)
- `cache_ttl_seconds`: positive cache TTL (default: 300)
- `negative_cache_ttl_seconds`: negative/missing cache TTL (default: 60)
- `products_path`: path to product JSON
- `faiss_index_path`: path to FAISS index
- `product_map_path`: path to id_map JSON

### [app/schemas.py](/Users/sabujislam/Documents/ai/app/schemas.py)

Typed request/response-related data models.

Models:

- `IntentName`: Literal type covering all 8 supported intents
- `ResolvedQuery`: contains `intent`, `product`, `category`, `confidence`
- `AskResponse`: contains `answer`, `status`, `source`, `resolved`, `api_time_ms`, `groq_time_ms`, `resolver_time_ms`, `state`, `matched_products`

Status values: `found`, `ambiguous`, `missing`, `unavailable`, `fallback`

Source values: `exact_cache`, `retriever`, `llm_fallback`, `clarification`, `semantic_cache`

### [app/catalog.py](/Users/sabujislam/Documents/ai/app/catalog.py)

Small utilities for dataset handling.

Functions:

- `load_json`: loads and parses a JSON file
- `normalize_text`: lowercases, strips, and collapses whitespace
- `parse_price`: converts price values (int, float, string with `$`/`,`) to float

### [app/intent.py](/Users/sabujislam/Documents/ai/app/intent.py)

Rule-based intent detection module.

Supports both English and Bangla keyword patterns:

- `list_all_products`: `কি কি পণ্য`, `what products`, `all products`
- `list_category_products`: `কি কি noodles`, `কি কি নুডলস`, `what noodles`, `which noodles`
- `price_min`: `সবচেয়ে কম`, `cheapest`, `lowest`, `minimum price`
- `price_max`: `সবচাইতে বেশি`, `সবচেয়ে বেশি`, `highest`, `most expensive`, `maximum price`
- `price_product`: `দাম`, `price`, `how much`, `cost`, `কত`, `কত টাকা`
- `category_availability`: availability keywords + category token match
- `availability_product`: `আছে`, `available`, `do you have`, `sell`, `stock`, `বিক্রি`, `পাওয়া যায়`
- `unknown`: default fallback

### [app/entity.py](/Users/sabujislam/Documents/ai/app/entity.py)

Entity extraction module using `EntityResolver` dataclass.

Responsibilities:

- Bangla-to-English category mapping
- Multi-tier product extraction:
  1. Exact normalized name match
  2. Substring containment check
  3. Token index pre-filtering to build candidate shortlist
  4. RapidFuzz `token_set_ratio` on shortlisted candidates (threshold: 85)
  5. Full fuzzy fallback if no token index hits
- Vague anaphora filtering (prevents `it`, `this one`, etc. from triggering false matches)
- Category detection with regex boundary matching and fuzzy fallback (threshold: 90)

### [app/state.py](/Users/sabujislam/Documents/ai/app/state.py)

Conversation state storage layer with Protocol-based interface.

Implementations:

- `RedisStateStore`: keys as `state:{session_id}`, JSON-serialized state
- `InMemoryStateStore`: dictionary-based fallback with copy semantics

### [app/cache.py](/Users/sabujislam/Documents/ai/app/cache.py)

Answer cache layer with three components.

1. `CacheStore` Protocol with `get`/`set` interface
2. `InMemoryCacheStore`: dictionary fallback
3. `RedisCacheStore`: Redis `setex` with TTL
4. `make_cache_key`: builds `ask:{session_id}:{intent}:{product}:{category}`
5. `FaissSemanticCache`: FAISS L2-based semantic deduplication for LLM responses with `search`, `add`, `save`, and `clear` methods

### [app/embeddings.py](/Users/sabujislam/Documents/ai/app/embeddings.py)

Embedding loader and fallback strategy.

Components:

- `Embedder` base class with `encode` interface
- `SentenceTransformerEmbedder`: wraps `SentenceTransformer` with normalized embeddings
- `HashingEmbedder`: MD5-based token hashing with configurable dimensions
- `load_embedder`: tries local sentence-transformer first, falls back to hashing
- `ensure_embedder_dimensions`: validates embedding dimensions match FAISS index, falls back to `HashingEmbedder` with matching dimensions if mismatched

### [app/retriever.py](/Users/sabujislam/Documents/ai/app/retriever.py)

FAISS retrieval wrapper.

Responsibilities:

- embed incoming query using the loaded embedder
- search FAISS index for top-k nearest neighbors
- map FAISS indices back to product records via `id_map`
- filter out invalid (negative) FAISS indices

### [app/resolver.py](/Users/sabujislam/Documents/ai/app/resolver.py)

Query resolution layer.

Responsibilities:

- combine current query with session state
- early-return for `list_all_products` without product/category extraction
- early-branch for `price_min`/`price_max` with category-only detection
- early-branch for `category_availability`/`list_category_products` with category-only detection
- extract product and category for remaining intents
- inherit `active_product` or `active_products` from state when query is vague
- inherit `active_category` from state when query is vague
- produce `ResolvedQuery` with confidence scores (0.95 for resolved, 0.45 for unresolved)

This file is one of the most important parts of the system because it turns vague user input into something the answer engine can work with safely.

### [app/answer_engine.py](/Users/sabujislam/Documents/ai/app/answer_engine.py)

Core decision engine with Bangla-localized responses.

Responsibilities:

- apply intent-specific answer rules
- return direct structured answers in Bangla
- update session state (`active_product`, `active_products`, `active_category`)
- handle clarification behavior for ambiguous queries
- compute cheapest and highest-price answers
- handle multi-product price disambiguation

This is the main "business logic" layer of the project.

### [app/llm.py](/Users/sabujislam/Documents/ai/app/llm.py)

Groq fallback wrapper.

Responsibilities:

- create constrained fallback prompt with context from top 3 FAISS results
- call Groq with `temperature=0` and `max_completion_tokens=80`
- measure Groq call latency
- return `None` gracefully if no API key is configured

### [app/routes.py](/Users/sabujislam/Documents/ai/app/routes.py)

Main API route logic.

Endpoints:

- `GET /health`: returns `{"status": "ok"}`
- `GET /ask`: main query endpoint

`/ask` orchestration:

- timing measurement for total and resolver phases
- session state loading
- query resolution
- cache key generation and exact cache lookup
- vague reference vs unknown product disambiguation
- intent-based retrieval strategy selection
- answer engine execution
- semantic cache check on answer engine miss
- Groq fallback on all-miss
- semantic cache persistence via background tasks
- state and cache updates

## Scripts Folder

### [scripts/prepare_catalog.py](/Users/sabujislam/Documents/ai/scripts/prepare_catalog.py)

Converts CSV product data into the internal JSON format.

### [scripts/build_index.py](/Users/sabujislam/Documents/ai/scripts/build_index.py)

Builds the FAISS index and id map from the dataset.

### [scripts/generate_catalog.py](/Users/sabujislam/Documents/ai/scripts/generate_catalog.py)

Generates a synthetic 5,000-product dataset with realistic names, categories, prices, and metadata.

### [scripts/test_pipeline.py](/Users/sabujislam/Documents/ai/scripts/test_pipeline.py)

Sequential multi-turn test script that runs 28 queries through a single session to validate:

- basic product queries
- context inheritance across turns
- Bangla queries and mixed-language input
- typo/misspelling tolerance
- adversarial and out-of-scope prompts
- category context switching

## What Is Good About This Architecture

- deterministic before generative
- context-aware across turns
- clear separation of concerns
- practical for local development
- supports offline fallback behavior
- easy to extend with more intents
- easy to replace synthetic data with real catalog data
- Bangla-localized responses
- three-tier caching (exact, semantic, session)
- token index pre-filtering for faster entity resolution
- startup cache clearing for predictable demo state
- comprehensive test pipeline for regression testing

## Current Limitations

- current dataset is synthetic, not a real business catalog
- Bangla coreference handling is still rule-oriented, not full linguistic resolution
- semantic retrieval quality is better when the real sentence-transformer model is available locally
- no persistent database yet
- no auth or admin panel
- no streaming response
- category detection keywords are partially hardcoded in intent.py

## Recommended Next Improvements

- add more Bangla aliases for products and categories
- add stock field and stock-aware answering
- add variant disambiguation like size or flavor selection
- add Postgres for real catalog storage
- add admin import flow for product updates
- serve `chat.html` directly from FastAPI static files
- add logs/metrics dashboard
- expand test suite coverage with assertion-based validation
- add dynamic category detection that reads categories from catalog at startup

## Final Summary

This project is a context-aware conversational RAG system focused on precise answers from dataset-backed product knowledge.

Its biggest strengths are:

- strong multi-turn behavior
- intent-aware routing with early branching
- structured answer policy with Bangla localization
- controlled LLM usage with semantic cache deduplication
- three-tier caching strategy
- practical local usability with graceful degradation

In short, this project is not just a chatbot. It is a controlled conversational retrieval system designed to understand what the user means, resolve context safely, retrieve from grounded data, and answer as precisely as possible — all in Bangla.
