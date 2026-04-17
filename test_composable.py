import json
import urllib.request, urllib.parse
from dotenv import load_dotenv
import os

def ask(query, session_id):
    q = urllib.parse.quote(query)
    url = f"http://localhost:8000/ask?query={q}&session_id={session_id}"
    req = urllib.request.urlopen(url)
    return json.loads(req.read())

print("Test 1: ২০০ টাকার মধ্যে ভালো কিছু পাবো?")
res1 = ask("২০০ টাকার মধ্যে ভালো কিছু পাবো?", "test_c1")
print(f"Answer: {res1['answer']}")
print(f"Intent: {res1['resolved']['intent']}, Sort: {res1['resolved']['sort_by']}, PriceFilter: {res1['resolved']['price_filter']}")

print("\nTest 2: ফাস্ট চার্জার আছে?")
res2 = ask("ফাস্ট চার্জার আছে?", "test_c2")
print(f"Answer: {res2['answer']}")
print(f"Attributes: {res2['resolved']['attributes']}")

print("\nTest 3: Context Test")
sid = "test_context_new"
print("Step 1: স্টাইলিশ ব্যাগ দেখাও")
res3a = ask("স্টাইলিশ ব্যাগ দেখাও", sid)
print(f"Answer: {res3a['answer']}")
print(f"Active Product: {res3a['state'].get('active_product')}")

print("\nStep 2: এটার দাম কত?")
res3b = ask("এটার দাম কত?", sid)
print(f"Answer: {res3b['answer']}")
print(f"Reasoning: {res3b['resolved']['reasoning']}")
