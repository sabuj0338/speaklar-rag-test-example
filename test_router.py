import json
import asyncio
from app.router import LLMRouter
from dotenv import load_dotenv
import os

load_dotenv()
router = LLMRouter(api_key=os.getenv("GROQ_API_KEY"), model=os.getenv("GROQ_ROUTER_MODEL", "llama-3.1-8b-instant"))

queries = [
    "আমাদের কি কি ল্যাপটপ আছে?",
    "ডেলিভারি কিভাবে পাবো?",
    "মেয়েদের ব্যাগ দেখাও, একটু স্টাইলিশ হলে ভালো হয়"
]

for q in queries:
    res, t = router.route(q, {})
    print(f"Q: {q}")
    print(f"Result: {res.model_dump()}")
    print("-" * 50)
