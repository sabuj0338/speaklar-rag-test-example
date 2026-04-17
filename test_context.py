import json
import urllib.request, urllib.parse
from dotenv import load_dotenv
import os

def ask(query, session_id):
    q = urllib.parse.quote(query)
    url = f"http://localhost:8000/ask?query={q}&session_id={session_id}"
    req = urllib.request.urlopen(url)
    return json.loads(req.read())

session_id = "context_test_8"
print("Step 1: মেয়েদের ব্যাগ দেখাও")
res1 = ask("মেয়েদের ব্যাগ দেখাও", session_id)
print(f"Answer: {res1['answer']}")
print(f"State active_product: {res1['state'].get('active_product')}")

print("\nStep 2: এটার দাম কত?")
res2 = ask("এটার দাম কত?", session_id)
print(f"Answer: {res2['answer']}")
print(f"Resolved reasoning: {res2['resolved']['reasoning']}")
