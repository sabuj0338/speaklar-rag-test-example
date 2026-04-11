# Frequently Asked Questions

## Q1: Is this a RAG system?

**Yes, but it's a hybrid RAG system.** A pure RAG system follows: **Retrieve → Augment → Generate**. This system does retrieve from a FAISS vector index, but it *doesn't always generate* with an LLM. Most answers are built deterministically from structured data. The LLM (Groq) is only a last-resort fallback. So it's more accurately described as:

> **RAG with deterministic-first answering** — retrieval is always available, but generation is avoided when structured logic can answer safely.

---

## Q2: Does it maintain context awareness / coreference?

**Yes, this is one of the strongest parts of the project.** It handles coreference through session state, not through an LLM. For example:

- User: *"Do you have noodles?"* → system stores `active_category: noodles`
- User: *"Which one is the cheapest?"* → system inherits `noodles` from state, finds the cheapest noodle

This is **rule-based anaphora resolution** — it resolves pronouns like *"it"*, *"this one"*, *"এটা"* by looking at what the previous turn discussed. Most basic RAG tutorials don't do this at all.

---

## Q3: Does it answer accurately?

**Yes, for catalog-grounded questions, it's highly accurate** because it reads directly from structured product data (name, price, category) rather than asking an LLM to guess. The system:

- Uses exact map lookups for known products
- Uses direct category filtering for category queries
- Returns clarification when it's unsure, instead of hallucinating

**Where accuracy drops**: When the hashing embedder fallback is used instead of the real sentence-transformer model, FAISS semantic search quality degrades. Also, the Groq fallback can potentially hallucinate since it's an LLM — but the prompt constrains it heavily.

---

## Q4: Does this project follow RAG?

**It follows the RAG pattern but goes beyond basic RAG.** Here's how it compares:

| Step | Basic RAG | This System |
|------|-----------|-------------|
| **Retrieve** | Vector search on every query | Vector search only when needed; direct map lookups first |
| **Augment** | Pass retrieved docs to LLM | Pass to deterministic answer engine first |
| **Generate** | LLM generates every answer | LLM only used as fallback (~5% of queries) |
| **Context** | Single-turn only | Multi-turn with session state |
| **Caching** | None | Three-tier (exact, semantic, session) |

So this project is a **production-oriented evolution of RAG** — it uses RAG's retrieval concept but adds intent routing, structured answering, and session state on top.

---

## Key Takeaways for Learning RAG

This project demonstrates **why naive RAG isn't enough** for real applications:

1. **Retrieval alone doesn't solve everything** — you need to understand *what* the user is asking (intent) before deciding *how* to answer.
2. **LLMs are expensive and unpredictable** — using them only when necessary is a real production pattern.
3. **Multi-turn conversation is the hard part** — single-turn RAG is easy; maintaining context across turns is where the real engineering happens.

---

## Q5: Can I build an MCP server instead? What's the difference?

### What is MCP?

**MCP (Model Context Protocol)** is a standard created by Anthropic that lets an LLM **call external tools** at runtime. Instead of pre-retrieving data and passing it to the model, the LLM *decides* when and what to fetch.

### How it would work for this dataset

You would expose the product catalog as MCP tools:

- `search_products(query)` → list of matching products
- `get_product_price(product_name)` → price
- `list_category(category)` → products in that category
- `get_cheapest(category?)` → cheapest product

The LLM (Claude, GPT, etc.) would call these tools as needed during conversation. You wouldn't need `intent.py`, `resolver.py`, `answer_engine.py`, or session state — the LLM handles all of that.

### RAG vs MCP Comparison

| Aspect | This RAG System | MCP + LLM |
|---|---|---|
| **Who decides what to retrieve?** | Your code (intent → resolver → retriever) | The LLM decides |
| **Who builds the answer?** | `answer_engine.py` (deterministic) | The LLM generates it |
| **Who manages context?** | `resolver.py` + session state | The LLM via conversation history |
| **Latency** | ~1-10ms (deterministic) | ~500-2000ms (LLM round-trip) |
| **Cost per query** | Near zero (no API calls for 95% of queries) | Every query costs LLM tokens |
| **Accuracy on catalog facts** | Very high (reads structured data directly) | Depends on LLM — can hallucinate prices |
| **Context handling** | Manual session state (custom built) | LLM handles naturally |
| **Bangla support** | Hardcoded in `answer_engine.py` | LLM can respond in any language natively |
| **Code complexity** | ~15 files of custom logic | ~1 MCP server file + tool definitions |
| **Offline capability** | Works without internet | Requires LLM API access |
| **Control** | Full control over every response | LLM may phrase things unpredictably |
| **Scalability** | Handles thousands of QPS easily | Limited by LLM API rate limits |

### Where MCP wins

- Multi-turn conversations (LLMs handle this naturally)
- Complex/open-ended questions (e.g., *"Compare these two noodles"*)
- Language flexibility (no hardcoded Bangla strings needed)
- Development speed (much less code to write)

### Where this RAG system wins

- Speed (~100x faster responses)
- Cost (no per-query API charges)
- Accuracy on structured data (prices are never wrong)
- Predictability (same input → same output, always)
- Offline operation
- Production scale

### How much effort to build an MCP version?

| Task | Effort |
|---|---|
| MCP server with 4-5 product tools | ~2-3 hours |
| Connect to Claude/GPT via MCP client | ~1 hour |
| Get basic conversations working | ~30 minutes |
| Match this system's accuracy on prices | Very hard — LLMs occasionally get prices wrong |
| Match this system's speed | Not possible — LLM latency is inherent |

### The real-world answer

In production, the best systems **combine both**:

```
User Query
    │
    ├─ Can deterministic logic answer? → RAG system (fast, accurate, free)
    │
    └─ Too complex for rules? → MCP/LLM (flexible, natural, expensive)
```

This project already does this with the Groq fallback — that's essentially the same idea. MCP would just formalize the tool-calling interface.

**Bottom line**: MCP is a great learning exercise and perfect for complex queries, but for structured catalog Q&A with speed and accuracy requirements, the current deterministic-first RAG approach is actually the *more sophisticated* architecture.
