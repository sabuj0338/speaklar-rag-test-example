# Project Documentation

## Project Name

Context-Aware Conversational RAG for Precise Dataset-Grounded Answers

## Project Purpose

This project is a FastAPI-based conversational RAG system designed to answer user questions from a dataset with:

- context awareness across multiple turns
- coreference handling for follow-up questions like `How much?`
- user-intent understanding
- precise and specific answers
- low hallucination risk
- structured, deterministic behavior before using an LLM

The system is built for commerce-style conversations, where users may ask about:

- product availability
- product price
- cheapest product
- highest priced product
- category-level product listing
- follow-up price questions after a previous product or category mention

The main goal is not just “search and answer.” The goal is to build a decision-driven assistant that understands what the user means, resolves context safely, retrieves from dataset-backed knowledge, and responds with the most reliable answer possible.

## Why This Project Exists

A normal chatbot or naive RAG pipeline often fails in multi-turn conversations.

Example:

1. User: `Do you have noodles?`
2. System: `Yes, we have noodles.`
3. User: `How much?`

A weak system may search only for `How much?` or `price`, which is too vague and can return the wrong answer. This project solves that by tracking conversation state and resolving the follow-up question using previous session context.

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

This is important because price questions, list questions, and availability questions should not all follow the same logic.

### 2. Context-Aware Resolution

The system does not rely only on the current query text. It also uses session state to understand follow-up questions.

For example:

- if the user previously asked about a product, the system stores it as `active_product`
- if the user saw multiple products, the system stores them as `active_products`
- if the user mentioned a category, the system stores it as `active_category`

So when the user later says `How much?`, the resolver tries to map that vague question to the current product or category context.

### 3. Structured Retrieval Before LLM

The project uses a dataset of products and retrieves from it instead of generating answers freely.

The answer engine tries to answer directly from:

- product name
- category
- price field
- metadata field

This is much safer than asking an LLM to invent answers from scratch.

### 4. Clarification Instead of Guessing

If the system cannot identify a single product confidently, it does not hallucinate.

Example:

- user asks `How much?`
- but session contains multiple possible products

Instead of guessing, the system responds with clarification behavior and can show several candidate prices.

### 5. Optional LLM Fallback

When deterministic logic cannot answer properly, the app can call Groq as a constrained fallback.

The fallback prompt tells the model:

- use only the provided context
- keep the answer short
- say `I don't know` if not supported

This keeps the LLM under control and reduces unsupported answers.

### 6. Caching and Session Memory

The app stores:

- conversation state by `session_id`
- exact answer cache using resolved intent/entity context

Redis is used when available. If Redis is not available, the app automatically falls back to in-memory storage so development can continue.

### 7. Offline Index Building

The FAISS index is built offline from the product dataset. This avoids doing expensive indexing inside the request path.

This keeps request handling faster and cleaner.

## Tools and Techniques Used

## API Layer

### FastAPI

Used for:

- building the HTTP API
- exposing `/ask`
- exposing `/health`
- loading app dependencies at startup using lifespan

Why used:

- fast development
- clean request/response models
- strong typing
- production-friendly structure

### Pydantic

Used for:

- typed response schema
- resolved query schema
- settings model

Why used:

- validation
- clearer API contracts
- easier maintenance

## Retrieval and Embeddings

### FAISS

Used for:

- vector index storage
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

This is a practical resilience feature. It is not the ideal production embedding strategy, but it keeps the system stable.

## State, Cache, and Session Handling

### Redis

Used for:

- session state
- exact cache

Why used:

- fast access
- suitable for conversation state
- common choice for production conversational systems

### In-Memory Fallback

If Redis is unavailable, the app uses in-memory state and cache objects.

Why used:

- local development convenience
- graceful degradation

## Entity and Intent Understanding

### Rule-Based Intent Detection

Used because:

- it is fast
- predictable
- easy to debug
- often better than LLM classification for a small fixed intent set

### RapidFuzz

Used for fuzzy product matching.

Why used:

- handles small spelling errors
- supports approximate user mentions
- useful when product names are not typed exactly

Example:

- `Addias` could still match an `Adidas`-type product if present

## LLM Layer

### Groq

Used as an optional fallback LLM provider.

Why used:

- low-latency inference
- useful for constrained fallback responses
- supports a hybrid architecture where structured logic is primary and LLM is secondary

## Frontend

### HTML + Tailwind CDN

Used for:

- a standalone test chat UI
- quick browser testing of the `/ask` endpoint

Features:

- session-aware chat
- quick prompts
- response metadata display
- browser round-trip timing
- API time display
- Groq time display

## Dataset Strategy

The system uses a structured JSON dataset:

- `id`
- `text`
- `price`
- `category`
- `metadata`

This dataset is intentionally simple but expressive enough for:

- direct price lookup
- category-based retrieval
- follow-up context tests

The project now includes a synthetic 5,000-product FMCG-style dataset for realistic testing.

## Request Flow

The `/ask` flow works like this:

1. Receive `query` and `session_id`
2. Load current state from Redis or memory
3. Detect user intent
4. Resolve product/category using query plus state
5. Build a context-aware cache key
6. Check cache
7. Retrieve from FAISS or use full catalog depending on intent
8. Run answer logic
9. Return deterministic answer if possible
10. Fall back to Groq only if needed
11. Save updated state
12. Return answer with timing information

## Answer Strategy

The answer engine uses intent-specific behavior.

### Product Availability

If a product is resolved:

- answer yes/no from the catalog

### Product Price

If a single product is resolved:

- return exact price

If multiple products are active:

- show several prices and ask for specificity

### Category Availability

If a category is resolved:

- confirm category exists
- list example products

### Category Product List

If category list intent is detected:

- return distinct products from that category
- update session state

### Cheapest and Highest Price

For these aggregate intents:

- use the full catalog
- compute min/max by the structured `price` field

### Unknown

If structured logic cannot safely answer:

- use Groq fallback if configured
- otherwise return `I don't know.`

## Timing Strategy

The API returns:

- `api_time_ms`: total server-side processing time
- `groq_time_ms`: only the time spent inside the Groq API call

The chat UI also measures:

- browser round-trip time

This helps compare:

- frontend network time
- backend processing time
- LLM fallback time

## Project Files Explanation

## Root Files

### [README.md](/Users/sabujislam/Documents/ai/README.md)

Quick-start guide for running the project.

### [requirements.txt](/Users/sabujislam/Documents/ai/requirements.txt)

Python dependencies for the whole project.

### [.env.example](/Users/sabujislam/Documents/ai/.env.example)

Sample environment variables.

### [chat.html](/Users/sabujislam/Documents/ai/chat.html)

Browser-based chat UI for talking to the `/ask` API.

### [PROJECT_DOCS.md](/Users/sabujislam/Documents/ai/PROJECT_DOCS.md)

This full documentation file.

## Data and Artifacts

### [data/products.json](/Users/sabujislam/Documents/ai/data/products.json)

Product dataset used for indexing and answering.

### [artifacts/index.faiss](/Users/sabujislam/Documents/ai/artifacts/index.faiss)

FAISS index built from the dataset.

### [artifacts/id_map.json](/Users/sabujislam/Documents/ai/artifacts/id_map.json)

Mapping from FAISS row id to product record.

## App Folder

### [app/main.py](/Users/sabujislam/Documents/ai/app/main.py)

Main FastAPI application entry point.

Responsibilities:

- startup lifecycle
- loading settings
- loading FAISS index
- loading embedder
- setting up Redis or memory fallback
- registering middleware
- registering routes

### [app/config.py](/Users/sabujislam/Documents/ai/app/config.py)

Application configuration using `pydantic-settings`.

Responsibilities:

- API name
- Redis URL
- Groq config
- model name
- paths for data and artifacts
- cache TTL values

### [app/schemas.py](/Users/sabujislam/Documents/ai/app/schemas.py)

Typed request/response-related data models.

Responsibilities:

- `ResolvedQuery`
- `AskResponse`
- intent type definitions
- response timing fields

### [app/catalog.py](/Users/sabujislam/Documents/ai/app/catalog.py)

Small utilities for dataset handling.

Responsibilities:

- JSON loading
- text normalization
- price parsing

### [app/intent.py](/Users/sabujislam/Documents/ai/app/intent.py)

Rule-based intent detection module.

Responsibilities:

- map query text to supported intent classes

### [app/entity.py](/Users/sabujislam/Documents/ai/app/entity.py)

Entity extraction helpers.

Responsibilities:

- fuzzy product matching using RapidFuzz
- category detection
- Bangla-to-English category mapping support

### [app/state.py](/Users/sabujislam/Documents/ai/app/state.py)

Conversation state storage layer.

Responsibilities:

- Redis-backed state store
- in-memory fallback state store
- get/set state by session

### [app/cache.py](/Users/sabujislam/Documents/ai/app/cache.py)

Answer cache layer.

Responsibilities:

- exact cache access
- Redis cache implementation
- in-memory fallback cache implementation
- cache key generation from resolved context

### [app/embeddings.py](/Users/sabujislam/Documents/ai/app/embeddings.py)

Embedding loader and fallback strategy.

Responsibilities:

- load sentence-transformer embeddings if locally available
- provide hashing embedder fallback
- ensure runtime embedder dimensions match FAISS index dimensions

This file is important for stability because it prevents runtime crashes caused by embedding dimension mismatch.

### [app/retriever.py](/Users/sabujislam/Documents/ai/app/retriever.py)

FAISS retrieval wrapper.

Responsibilities:

- embed incoming query
- search FAISS index
- return matched product records

### [app/resolver.py](/Users/sabujislam/Documents/ai/app/resolver.py)

Query resolution layer.

Responsibilities:

- combine current query with session state
- resolve product and category
- protect aggregate intents from wrong product carryover
- produce `ResolvedQuery`

This file is one of the most important parts of the system because it turns vague user input into something the answer engine can work with safely.

### [app/answer_engine.py](/Users/sabujislam/Documents/ai/app/answer_engine.py)

Core decision engine.

Responsibilities:

- apply intent-specific answer rules
- return direct structured answers
- update session state
- handle clarification behavior
- compute cheapest and highest-price answers

This is the main “business logic” layer of the project.

### [app/llm.py](/Users/sabujislam/Documents/ai/app/llm.py)

Groq fallback wrapper.

Responsibilities:

- create constrained fallback prompt
- call Groq when needed
- measure Groq call latency

### [app/routes.py](/Users/sabujislam/Documents/ai/app/routes.py)

Main API route logic.

Responsibilities:

- orchestrate the full `/ask` pipeline
- timing measurement
- cache lookup
- state load/store
- retrieval selection
- answer engine call
- Groq fallback handling

## Scripts Folder

### [scripts/prepare_catalog.py](/Users/sabujislam/Documents/ai/scripts/prepare_catalog.py)

Converts CSV product data into the internal JSON format.

### [scripts/build_index.py](/Users/sabujislam/Documents/ai/scripts/build_index.py)

Builds the FAISS index and id map from the dataset.

### [scripts/generate_catalog.py](/Users/sabujislam/Documents/ai/scripts/generate_catalog.py)

Generates a synthetic 5,000-product dataset with realistic names, categories, prices, and metadata.

## What Is Good About This Architecture

- deterministic before generative
- context-aware across turns
- clear separation of concerns
- practical for local development
- supports offline fallback behavior
- easy to extend with more intents
- easy to replace synthetic data with real catalog data

## Current Limitations

- current dataset is synthetic, not a real business catalog
- Bangla coreference handling is still rule-oriented, not full linguistic resolution
- semantic retrieval quality is better when the real sentence-transformer model is available locally
- cache is exact-context based, not full semantic cache yet
- no persistent database yet
- no auth or admin panel
- no streaming response

## Recommended Next Improvements

- add Bangla aliases for products and categories
- add stock field and stock-aware answering
- add variant disambiguation like size or flavor selection
- add semantic cache layer
- add Postgres for real catalog storage
- add admin import flow for product updates
- serve `chat.html` directly from FastAPI
- add logs/metrics dashboard
- add test suite for multi-turn conversation flows

## Final Summary

This project is a context-aware conversational RAG system focused on precise answers from dataset-backed product knowledge.

Its biggest strengths are:

- strong multi-turn behavior
- intent-aware routing
- structured answer policy
- controlled LLM usage
- practical local usability

In short, this project is not just a chatbot. It is a controlled conversational retrieval system designed to understand what the user means, resolve context safely, retrieve from grounded data, and answer as precisely as possible.
