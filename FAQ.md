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
