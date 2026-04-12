# 🛒 Commerce RAG Assistant

A high-performance, context-aware FastAPI assistant designed for e-commerce sales conversations. This system handles complex product queries, pricing, and category availability with sub-100ms latency.

---

## 🎯 Project Purpose

The **Commerce RAG Assistant** is built to bridge the gap between expensive, unpredictable LLM calls and rigid, traditional search. Its primary goal is to provide **deterministic, factual answers** for sales inquiries (price, availability, product details) while maintaining a **natural conversational flow**.

### Core Philosophy: "Logic First, LLM Second"
Unlike traditional RAG systems that send every query to an LLM, this system uses an **Intelligence-First** approach:
1.  **Deterministic Processing**: Uses high-speed fuzzy matching and structured data lookups for 95% of e-commerce queries.
2.  **Context Resolution**: Inherits session state to resolve vague references like *"How much is it?"* without needing LLM reasoning.
3.  **Fallback with Guardrails**: Only uses Groq/LLMs for complex, open-ended questions where deterministic logic isn't sufficient.

---

## 🚀 Features

- **Product Intelligence**: Query availability, price, and specifications.
- **Advanced RAG**: Semantic search using FAISS for low-latency retrieval.
- **Context Awareness**: Remembers session state (e.g., handles "How much is it?" after asking about a specific product).
- **Hybrid Performance**: Redis-backed session management with in-memory fallback.
- **Multilingual Support**: Optimized for English and Bangla.

---

## 🛠️ Installation

### 1. Clone & Setup
```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the template and configure your connection strings:

```bash
cp .env.example .env
```

Open `.env` and set the following:
- **Redis**: Ensure `REDIS_URL` points to your running Redis instance (default: `redis://localhost:6379/0`). This is required for session management and caching.
- **Groq**: Add your `GROQ_API_KEY`. The system uses Groq for high-performance AI fallbacks when deterministic logic isn't sufficient.

> [!IMPORTANT]
> A running Redis server and a valid Groq API key are required for the application to function correctly.

---

## 📦 Data Preparation

Before running the server, you need to prepare the catalog and build the vector index.

### 1. Prepare Product Catalog
Convert your CSV data into the optimized JSON format:
```bash
python3 scripts/prepare_catalog.py --input path/to/your/products.csv --output data/products.json
```

### 2. Build FAISS Index
Generate embeddings for semantic search:
```bash
python3 scripts/build_index.py
```

---

## 🏃 Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn app.main:app --reload
```
The server will be available at `http://127.0.0.1:8000`.

---

## 💬 Testing with Chat

The repository includes a premium **Test Console** to experience the RAG assistant in a real chat environment.

1.  **Open the Chat Interface**:
    Simply open the [chat.html](chat.html) file in your web browser.
    
2.  **Configure**:
    - Ensure the **API Base URL** is set to `http://127.0.0.1:8000`.
    - Click **Connect** (or just start typing).

3.  **Chat**:
    Use one of the **Quick Prompts** in the sidebar to test context-aware queries like:
    - *"Do you have noodles?"*
    - *"Which one is the cheapest?"* (Tests context resolution)

---

## 🧪 Terminal Testing

You can also test the raw API via `curl`:

```bash
curl 'http://127.0.0.1:8000/ask?query=Do%20you%20have%20Product%201&session_id=test-1'
```

---

## 📂 Project Structure

- `app/`: Core FastAPI application logic.
- `data/`: Storage for product catalog and session state.
- `scripts/`: Utility scripts for data processing and indexing.
- `artifacts/`: Generated vector indexes and transient mapping files.
- `chat.html`: Interactive frontend for testing.

---

## 📖 Further Reading

For a deep dive into the system's internal logic, intent detection, and context resolution strategies, see:
👉 **[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md)**
