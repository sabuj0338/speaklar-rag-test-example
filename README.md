# Commerce RAG Assistant

Context-aware FastAPI product assistant for ecommerce sales conversations. It supports:

- product availability
- product price
- category availability
- listing products
- listing products in a category
- cheapest and highest priced products
- follow-up questions like `দাম কত?` using session state

## Quick start

1. Create a virtual environment and install dependencies.
2. Copy `.env.example` to `.env`.
3. Prepare product JSON from a CSV:

```bash
python3 scripts/prepare_catalog.py --input /Users/sabujislam/Downloads/products_100.csv --output data/products.json
```

4. Build the FAISS index:

```bash
python3 scripts/build_index.py
```

5. Run the API:

```bash
uvicorn app.main:app --reload
```

## Example request

```bash
curl 'http://127.0.0.1:8000/ask?query=Do%20you%20have%20Product%201&session_id=test-1'
```

## Notes

- Redis is used when available for session state and exact caching.
- If Redis is unavailable, the app falls back to in-memory state/cache so local development still works.
- Groq is optional and only used as a constrained fallback when deterministic logic cannot safely answer.
