"""
LLM Router Test Script — Tests the system with complex non-linear queries.
Based on test_questions.md stress tests.
"""

import json
import sys
import time
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000"
SESSION_ID = f"test-{int(time.time())}"

# ========================================
# Test Queries from test_questions.md
# ========================================
TEST_QUERIES = [
    # 🔹 1. Vague + Conversational
    ("1.1", "ভাই একটা ভালো জিনিস দেখাও তো"),
    ("1.2", "ভাই, মাঝামাঝি দামের কিছু লাগবে"),

    # 🔹 2. Implicit Intent (No clear product)
    ("2.1", "সস্তার মধ্যে বেস্ট কোনটা?"),
    ("2.2", "কম দামে ভালো কোয়ালিটির কিছু আছে?"),
    ("2.3", "বেশি দিন টিকবে এমন কিছু দেখাও"),

    # 🔹 3. Multi-Intent Queries
    ("3.1", "একটা চার্জার লাগবে, ফাস্টও হবে আবার সস্তাও"),
    ("3.2", "হেডফোন দেখাও কিন্তু সাউন্ড ভালো আর দাম কম"),
    ("3.3", "মোবাইল স্ট্যান্ড আছে? ভালো হলে দামও বলো"),

    # 🔹 4. Comparison-Based Queries
    ("4.1", "এই প্রাইসে বেস্ট অপশন কোনটা?"),

    # 🔹 5. Context-Dependent (Memory Required) — Use a new session
    ("5.1", "ফাস্ট চার্জার আছে?"),  # Set context first
    ("5.2", "এটার দাম কত?"),           # Should reference fast charger

    # 🔹 6. Category + Filter Mixed
    ("6.1", "ইলেকট্রনিক্স এর মধ্যে সস্তা কি আছে?"),
    ("6.2", "কিচেনের জন্য দরকারি কিছু দেখাও"),

    # 🔹 7. Slang / Informal Bangla
    ("7.1", "ভাই একটু জম্পেশ কিছু দেখাও"),
    ("7.2", "ফাটাফাটি কোয়ালিটির কিছু আছে নাকি?"),
    ("7.3", "একদম বাজেট ফ্রেন্ডলি কিছু দাও"),

    # 🔹 8. Misspelled / Noisy Input
    ("8.1", "চার্জারর আছে?"),
    ("8.2", "হেডফুন দাম কত?"),
    ("8.3", "জুতাা আছে?"),

    # 🔹 9. Mixed Language (Bangla + English)
    ("9.1", "একটা fast charger আছে?"),
    ("9.2", "budget friendly headphone দেখাও"),
    ("9.3", "best option under 500 taka কি?"),

    # 🔹 10. Ambiguous Product Reference (context dependent)
    ("10.1", "এটা কি কাজে লাগে?"),

    # 🔹 11. Recommendation + Reasoning
    ("11.1", "গিফট দেওয়ার জন্য কি ভালো হবে?"),
    ("11.2", "কোনটা বেশি ভ্যালু ফর মানি?"),

    # 🔹 12. Hard Edge Cases
    ("12.1", "কিছু দেখাও"),
    ("12.2", "কি কি আছে তোমাদের?"),
    ("12.3", "সব থেকে ভালোটা দেখাও"),
    ("12.4", "ভালো কিছু সাজেস্ট করো"),

    # 🔹 Out of Scope
    ("OOS.1", "আজকের আবহাওয়া কেমন?"),
    ("OOS.2", "বাংলাদেশের প্রধানমন্ত্রী কে?"),
]


def ask(query: str, session_id: str) -> dict:
    """Call the /ask endpoint."""
    params = urllib.parse.urlencode({"query": query, "session_id": session_id})
    url = f"{BASE_URL}/ask?{params}"
    
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        elapsed_ms = (time.perf_counter() - start) * 1000
        data["_e2e_ms"] = round(elapsed_ms, 1)
        return data
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"error": str(e), "_e2e_ms": round(elapsed_ms, 1)}


def main():
    print("=" * 90)
    print(f"🧪 LLM Router Test Suite — {len(TEST_QUERIES)} queries")
    print(f"   Session: {SESSION_ID}")
    print("=" * 90)
    
    results = []
    passed = 0
    failed = 0
    
    for idx, (test_id, query) in enumerate(TEST_QUERIES):
        # Use a separate session for context-dependent tests (5.x)
        sid = f"{SESSION_ID}-ctx" if test_id.startswith("5.") else SESSION_ID

        # Rate limit delay: wait between queries to avoid Groq TPM limit
        if idx > 0:
            time.sleep(2)
        
        resp = ask(query, sid)
        
        if "error" in resp:
            status_icon = "❌"
            failed += 1
            intent = "ERROR"
            answer_preview = resp["error"][:60]
            router_ms = 0
            e2e_ms = resp["_e2e_ms"]
            print(f"\n{status_icon} [{test_id}] {query}")
            print(f"   ERROR: {answer_preview}")
        else:
            resolved = resp.get("resolved", {})
            intent = resolved.get("intent", "?")
            is_relevant = resolved.get("is_relevant", True)
            product = resolved.get("product", "—")
            category = resolved.get("category", "—")
            answer = resp.get("answer", "")
            answer_preview = answer[:80]
            router_ms = resp.get("router_time_ms", 0)
            e2e_ms = resp["_e2e_ms"]
            source = resp.get("source", "?")
            status = resp.get("status", "?")
            
            # Basic pass criteria: got a response, no error
            if resp.get("status") in ("found", "fallback", "ambiguous", "rejected"):
                status_icon = "✅"
                passed += 1
            else:
                status_icon = "⚠️"
                passed += 1
            
            results.append({
                "id": test_id,
                "query": query,
                "intent": intent,
                "product": product,
                "category": category,
                "is_relevant": is_relevant,
                "status": status,
                "source": source,
                "router_ms": round(router_ms, 1),
                "e2e_ms": e2e_ms,
                "answer": answer_preview,
            })
            
            print(f"\n{status_icon} [{test_id}] {query}")
            print(f"   Intent: {intent:<25} Router: {router_ms:.0f}ms  E2E: {e2e_ms:.0f}ms")
            print(f"   Product: {product or '—':<20} Category: {category or '—'}")
            print(f"   Answer: {answer_preview}...")
    
    print("\n" + "=" * 90)
    print(f"📊 Results: {passed}/{len(TEST_QUERIES)} responded  |  {failed} errors")
    
    # Latency stats
    if results:
        router_times = [r["router_ms"] for r in results]
        e2e_times = [r["e2e_ms"] for r in results]
        print(f"⏱️  Router Latency: avg={sum(router_times)/len(router_times):.0f}ms  "
              f"min={min(router_times):.0f}ms  max={max(router_times):.0f}ms")
        print(f"⏱️  E2E Latency:    avg={sum(e2e_times)/len(e2e_times):.0f}ms  "
              f"min={min(e2e_times):.0f}ms  max={max(e2e_times):.0f}ms")
    
    # Intent distribution
    intent_counts: dict[str, int] = {}
    for r in results:
        intent_counts[r["intent"]] = intent_counts.get(r["intent"], 0) + 1
    print(f"\n📋 Intent Distribution:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        print(f"   {intent}: {count}")
    
    # Out-of-scope detection accuracy
    oos_results = [r for r in results if r["id"].startswith("OOS")]
    if oos_results:
        oos_correct = sum(1 for r in oos_results if not r["is_relevant"] or r["intent"] == "out_of_scope")
        print(f"\n🚫 Out-of-scope detection: {oos_correct}/{len(oos_results)} correctly identified")
    
    print("=" * 90)


if __name__ == "__main__":
    main()
