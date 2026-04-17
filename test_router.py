import json
import asyncio
import urllib.request, urllib.parse
from app.router import LLMRouter
from dotenv import load_dotenv
import os

load_dotenv()

q = urllib.parse.quote("২০০ টাকার মধ্যে ভালো কিছু পাবো?")
url = f"http://localhost:8000/ask?query={q}&session_id=tester_budget_1"
req = urllib.request.urlopen(url)
res = json.loads(req.read())

print("Answer: ", res['answer'])
print("Resolved Output: ", res['resolved'])
