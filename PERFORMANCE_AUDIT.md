# `/ask` API Performance Audit

## Audit Scope

This audit focuses on the FastAPI `/ask` endpoint when Groq is **not** used.

The goal was to answer:

- where time is being spent
- which part of the request path is the real bottleneck
- whether FAISS is the slow part
- why the endpoint may still feel slow even when no LLM call happens

## Environment Notes

This audit was run locally against the current codebase and current 5,000-product dataset.

The current dataset and stack are:

- 5,000 synthetic FMCG-style product records
- FAISS index built locally
- runtime currently using hashing embedder fallback
- no Groq fallback on the measured requests

## Key Conclusion

The `/ask` endpoint is **not slow because of FAISS** and **not slow because of Groq**.

The main recurring bottleneck is:

`fuzzy product extraction in resolver -> EntityResolver.extract_product()`

That step is currently the most expensive operation on most requests.

## High-Level Finding Summary

### Finding 1

The dominant hot path is fuzzy product matching over all product names.

Measured average:

- `extract_product`: about `12.8 ms`

This is the biggest cost in the current request path.

### Finding 2

FAISS search is relatively cheap.

Measured average:

- `retriever_search`: about `1.05 ms`
- `embed_encode`: about `0.05 ms`
- `faiss_search`: about `0.97 ms`

This means FAISS is not the main latency problem.

### Finding 3

Cache hits still pay most of the expensive resolver cost.

The current flow is:

1. load session state
2. resolve query
3. build cache key
4. check cache

Because the cache key depends on the resolved query, the app must run the expensive fuzzy matching before cache lookup.

This means:

- even cache hits are not cheap
- exact caching does not remove the biggest cost

### Finding 4

Aggregate intents like `cheapest` and `highest` still pay the fuzzy extraction cost even though they do not need product matching.

So the app is doing unnecessary work for:

- `price_min`
- `price_max`
- `list_all_products`

### Finding 5

Category queries are not only spending time in fuzzy matching, they are also producing poor retrieval quality.

Example:

- `Do you have noodles?`
- response returned unrelated juice/oil products in the available list

This is a correctness issue rather than a latency issue, but it matters because the app is paying retrieval cost and still returning wrong category candidates.

## Measured Timing Breakdown

## Mixed Request Probe

Average timings over 25 local requests:

- `state_get`: `0.001 ms`
- `extract_product`: `12.799 ms`
- `detect_category`: `0.004 ms`
- `cache_get`: `0.001 ms`
- `retriever_search`: `1.055 ms`
- `embed_encode`: `0.049 ms`
- `faiss_search`: `0.972 ms`
- `state_set`: `0.001 ms`
- `cache_set`: `0.001 ms`
- `request_total`: `13.730 ms`

### Interpretation

This means roughly:

- about 90% of the request cost is coming from resolver-side fuzzy matching
- only a small fraction is from retrieval
- state and cache operations are negligible

## Cold Request Probe by Query Type

Measured one-by-one using fresh session ids:

### `Do you have noodles?`

- browser round trip: `18.311 ms`
- API time: `16.246 ms`
- Groq time: `0.0 ms`

### `What noodles do you have?`

- browser round trip: `13.885 ms`
- API time: `12.954 ms`
- Groq time: `0.0 ms`

### `How much?`

- browser round trip: `14.937 ms`
- API time: `14.216 ms`
- Groq time: `0.0 ms`

### `What is the cheapest product?`

- browser round trip: `13.288 ms`
- API time: `12.622 ms`
- Groq time: `0.0 ms`

### `What is the highest price product?`

- browser round trip: `12.984 ms`
- API time: `12.338 ms`
- Groq time: `0.0 ms`

### `Do you have Pran Fresh Litchi Juice 250ml?`

- browser round trip: `12.875 ms`
- API time: `12.260 ms`
- Groq time: `0.0 ms`

### `How much is Pran Fresh Litchi Juice 250ml?`

- browser round trip: `13.655 ms`
- API time: `12.882 ms`
- Groq time: `0.0 ms`

## Important Observation

These results show that even when the query is simple, API time stays around `12-16 ms`, because the resolver cost is being paid almost every time.

## cProfile Result

Profiling a single request for:

- `Do you have noodles?`

showed:

- `/ask`: about `20 ms`
- `resolve_query`: about `18 ms`
- `extract_product`: about `13 ms`
- `retriever.search`: about `2 ms`
- `normalize_text` inside fuzzy matching: called more than `5,000` times

### Interpretation

The resolver is the dominant path, and inside it the fuzzy product extraction is the main CPU consumer.

## Root Causes

## 1. Product Extraction Runs for Almost Every Query

File:

- [app/resolver.py](/Users/sabujislam/Documents/ai/app/resolver.py)

Current behavior:

- every request calls `entity_resolver.extract_product(query)`
- this uses RapidFuzz against the full product-name list

With 5,000 products, this is expensive enough to dominate the request.

## 2. Cache Lookup Happens Too Late

File:

- [app/routes.py](/Users/sabujislam/Documents/ai/app/routes.py)

Current flow:

1. `resolve_query(...)`
2. build cache key
3. `cache_store.get(...)`

Because resolution happens before cache lookup, cache hits still pay resolver cost.

This reduces the value of caching from a performance perspective.

## 3. Aggregate Intents Do Unnecessary Product Extraction

Files:

- [app/resolver.py](/Users/sabujislam/Documents/ai/app/resolver.py)
- [app/intent.py](/Users/sabujislam/Documents/ai/app/intent.py)

The code nulls out product/category later for aggregate intents, but it still computes product extraction first.

That means:

- `cheapest`
- `highest`
- `list all products`

all waste time on fuzzy matching they do not need.

## 4. Category Queries Still Use Retriever Path

Files:

- [app/routes.py](/Users/sabujislam/Documents/ai/app/routes.py)
- [app/answer_engine.py](/Users/sabujislam/Documents/ai/app/answer_engine.py)

For category intents, the app still performs retrieval rather than a direct category filter from the catalog.

This has two downsides:

- extra work
- worse correctness for category-only questions

## 5. Current Cache Design Is Exact but Not Resolver-Skipping

The current cache is technically correct, but not optimized for latency.

It only helps after:

- state load
- intent detection
- product/category resolution

So the cache does not eliminate the hottest step.

## Bottleneck Ranking

From most important to least important:

1. `EntityResolver.extract_product`
2. query resolution overall
3. category retrieval strategy
4. FAISS search
5. state/cache IO

## Detailed File-Level Audit

## [app/routes.py](/Users/sabujislam/Documents/ai/app/routes.py)

### What it does well

- clean orchestration
- clear branch for aggregate intents
- timing already returned

### Performance problems

- cache check happens after expensive resolution
- category intents still go through retrieval instead of direct filtering

### Impact

- all requests pay the fuzzy extraction cost
- cache does not remove the main latency source

## [app/resolver.py](/Users/sabujislam/Documents/ai/app/resolver.py)

### What it does well

- centralizes context resolution
- handles fallback to session state

### Performance problems

- always calls `extract_product`
- aggregate intents do unnecessary extraction first, then discard result

### Impact

- unnecessary CPU cost on most requests

## [app/entity.py](/Users/sabujislam/Documents/ai/app/entity.py)

### What it does well

- fuzzy matching makes misspellings recoverable
- category mapping support is useful

### Performance problems

- full fuzzy search over all product names every request
- no prefiltering by intent
- no lightweight lexical shortcut

### Impact

- biggest single source of request latency

## [app/retriever.py](/Users/sabujislam/Documents/ai/app/retriever.py)

### What it does well

- simple and fast
- FAISS search is low latency

### Performance problems

- none major in the current measurements

### Impact

- not the main issue

## [app/answer_engine.py](/Users/sabujislam/Documents/ai/app/answer_engine.py)

### What it does well

- deterministic answer policy
- aggregate answers are simple and direct

### Performance problems

- category and product lookup correctness are more concerning than raw speed
- some flows still scan lists when they could use stronger indexed maps

### Impact

- correctness issue more than latency issue

## Performance vs Correctness Notes

There are also correctness issues revealed during the audit:

### Issue 1

Category queries return unrelated products.

Example:

- asking for noodles returned juice and oil items

This suggests category-only questions should use direct catalog filtering, not semantic retrieval over the current fallback embedder path.

### Issue 2

Some product-specific queries resolve to the wrong product.

Example:

- `Do you have Pran Fresh Litchi Juice 250ml?`
- resolved product became `Fresh Fresh Premium Rice 1kg`

This indicates the current fuzzy entity strategy is not strong enough for exact product lookup in its current form.

## Best Optimization Opportunities

## Priority 1. Skip Product Extraction for Aggregate Intents

Before calling `extract_product`, branch early for:

- `price_min`
- `price_max`
- `list_all_products`

Expected win:

- remove the main 12-13 ms cost for those intents

## Priority 2. Skip Fuzzy Product Matching for Category Intents

If the intent is clearly category-based:

- detect category
- use direct category filter
- do not fuzzy match product names first

Expected win:

- lower latency
- better correctness

## Priority 3. Add a Fast Lexical Shortcut Before RapidFuzz

Examples:

- exact normalized name lookup
- substring matching
- token overlap shortlist

Only call RapidFuzz if fast checks fail.

Expected win:

- significantly reduce average entity resolution cost

## Priority 4. Move Some Cache Logic Earlier

Introduce a lightweight “raw query + session” cache for clearly repetitive exact prompts in the same state, or cache the resolved query object separately.

Expected win:

- cache can skip expensive resolution on repeats

## Priority 5. Add Direct Category/Product Maps

At startup, precompute:

- category -> product list
- normalized product name -> product
- maybe token index -> candidate product ids

Expected win:

- fewer linear scans
- less need for full fuzzy matching
- stronger correctness

## Priority 6. Use Structured Filtering for Category Intents Instead of Retriever

For:

- `category_availability`
- `list_category_products`

Do:

- direct filter from in-memory catalog

Instead of:

- vector retrieval

Expected win:

- more correct responses
- simpler logic
- slightly lower latency

## Concrete Optimization Targets

If the above changes are applied, practical expectations are:

- aggregate intents: from `~12-13 ms` to `~1-3 ms`
- category intents: from `~13-16 ms` to `~2-5 ms`
- cached repeated requests: potentially `sub-2 ms`
- product-specific fuzzy requests: still higher, but can be reduced meaningfully with lexical shortcutting

## Final Verdict

The current `/ask` API is not slow because of vector search or Groq.

The real bottleneck is:

- fuzzy entity resolution being executed too often

The most important architectural problem is:

- expensive resolution happens before cache lookup

The most important correctness problem is:

- category and exact-product queries are not being resolved reliably enough with the current fallback retrieval/matching approach

## Recommended Next Step

The best next move is not to optimize FAISS.

The best next move is to refactor the request path into:

1. detect intent early
2. branch aggregate/category intents away from fuzzy product matching
3. use direct category/product maps when possible
4. only use RapidFuzz for truly product-specific uncertain queries
5. keep FAISS for semantic fallback, not for every category question

That will improve both:

- speed
- answer precision
