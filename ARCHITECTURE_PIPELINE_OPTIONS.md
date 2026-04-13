# Architecture: Scaling Bangla RAG Comprehension

## The Problem: Brittleness of Traditional NLP
The current architecture relies heavily on heuristic rules, manual Bengali stop-word dictionaries (`app/entity.py`), and keyword array mapping (`app/resolver.py`). 

While this traditional NLP logic is highly efficient, it begins to collapse under the weight of human natural language variations. It becomes impossible to maintain code definitions for:
- Colloquial Bangla phrasing and slang.
- Unexpected spelling mistakes and syntactic errors.
- Disambiguation of complex queries (e.g., separating "Bata shoes" from generic "shoes").
- Out-of-context or adversarial questions.

## The Solution: The LLM Router Node
To solve this at scale, the modern architectural standard mandates installing a **Semantic LLM Router** at the very front of the API execution pipeline. 

Instead of relying on Python arrays to predict what a user wants, the raw query is dispatched instantly to a Large Language Model. The LLM is strictly prompted to process the Bangla text, identify the context, and extract parameters into a machine-readable JSON object (e.g., `{"intent": "availability", "target_product": "নাইলন দড়ি"}`).

If the LLM flags the `is_relevant_to_ecommerce` variable as `false`, the API ignores the RAG logic entirely and cleanly rejects the question, instantly securing the pipeline boundary.

---

## Processing Overheads: Latency vs. Infrastructure

Transitioning from local Python code to a Neural Network Router adds undeniable calculation overhead to every single query the user asks. Below are the tested options available for deployment:

### 1. Legacy Heuristics (Current Code)
- **Architecture:** `app/resolver.py` -> `app/entity.py` -> Vector Search
- **Latency:** `~10 to 20 milliseconds` (Instant)
- **Tradeoff:** Extremely brittle logic. Cannot properly identify complex Bangla sentence structures or nuance natively without thousands of lines of manual regex.

### 2. Cloud LLM Router (Groq Llama 3)
- **Architecture:** FastAPI -> Groq API (JSON Router) -> Vector Search
- **Latency:** `~150 to 300 milliseconds` (Virtually Instant)
- **Tradeoff:** This utilizes Groq's specialized LPU hardware, allowing insane parameter extraction speeds over 800 tokens per second. It provides state-of-the-art semantic accuracy. However, it requires active internet connectivity, relies entirely on third-party cloud infrastructure, and is subject to active API billing/limitations.

### 3. Local Offline Router (Ollama + Qwen 2.5 3B)
- **Architecture:** FastAPI -> Localhost Ollama API (JSON Router) -> Vector Search
- **Latency:** `~1.0 to 1.8 seconds` (Noticeable Delay)
- **Tradeoff:** Provides identical high-grade semantic accuracy for Bangla queries completely offline. It guarantees 100% data privacy and zero cloud costs. However, generating the initial routing JSON requires Mac GPU/CPU calculations per query (~40-60 t/s), resulting in the end-user waiting over a full second to receive a response text structure.

---

## Achieving Sub-100ms Scale (The Enterprise ML Approach)
If sub-100ms execution is a hard requirement, Generative LLMs (like LLaMA or GPT) must be entirely removed from the critical routing path. The industry standard for instantaneous, highly-accurate semantic NLP routing without generating text relies on small Transformer or Machine Learning Classifiers:

### 1. BERT/Transformer Sequence Classifiers (e.g., Bangla-BERT)
- **How it works:** Instead of generating text, a small 100MB model reads the Bangla structure and mathematically assigns it a pre-learned category (Intent) while extracting nouns (Named Entity Recognition). This is the underlying technology fueling systems like **Rasa NLU**.
- **Latency:** `~20 to 50 milliseconds` (via ONNX runtime)
- **Tradeoff:** Blazing fast and understands complex language perfectly. However, this is NOT zero-shot capable. A developer must manually curate a dataset of hundreds of distinct Bangla examples (`"টাকা কত?" -> price_check`) to train and compile the model.

### 2. FastText / Shallow ML Classifiers
- **How it works:** Breaking sentences down into statistical n-grams.
- **Latency:** `~1 to 5 milliseconds`
- **Tradeoff:** Hyper-fast and resilient to spelling errors, but struggles with understanding complex grammatical contexts. Also requires strict manual dataset building.

### 3. Advanced BM25 Vector Spaces (Elasticsearch)
- **How it works:** Migrating away from Python fuzzy-matching entirely. Using an engine like Elasticsearch handles Bangla language stemming, tokenization, and synonym graphs automatically. Any reference to `"বাটার জুতা"` is dynamically mapped to related product hierarchies instantly.
- **Latency:** `< 5 milliseconds`

### The "Hybrid" Architecture
Modern large-scale corporations solve the scale-to-latency puzzle by combining these layers:
1. **Tier 1 (Fast Classifier):** The user's query hits a Bangla-BERT intent classifier first. If confidence is >95%, it routes instantly `(20ms)`.
2. **Tier 2 (LLM Fallback):** If the user types a strange, highly-nuanced Bangla query and confidence drops below 60%, the API intercepts the flow and delegates decoding to the Groq/LLaMA semantic router `(250ms)`.
