These are designed to stress:

ambiguity
multi-intent
slang
missing entities
conversational references
vague filters
comparison logic
context dependency

🧪 50+ Complex Non-Linear Test Queries
🔹 1. Vague + Conversational
ভাই একটা ভালো জিনিস দেখাও তো
এই টাইপের আর কিছু আছে?
আগেরটার থেকে ভালো কিছু আছে নাকি?
ওইটার মতো কিন্তু একটু সস্তা কিছু দেখাও
নতুন কি আসছে এই ক্যাটাগরিতে?
যেটা সবাই বেশি নেয় সেটা দেখাও
ভাই, মাঝামাঝি দামের কিছু লাগবে
🔹 2. Implicit Intent (No clear product)
২০০ টাকার মধ্যে ভালো কিছু পাবো?
সস্তার মধ্যে বেস্ট কোনটা?
কম দামে ভালো কোয়ালিটির কিছু আছে?
দাম কম কিন্তু টেকসই এমন কিছু আছে?
বেশি দিন টিকবে এমন কিছু দেখাও
🔹 3. Multi-Intent Queries
একটা চার্জার লাগবে, ফাস্টও হবে আবার সস্তাও
হেডফোন দেখাও কিন্তু সাউন্ড ভালো আর দাম কম
জুতা চাই, স্টাইলিশও হবে আবার আরামদায়কও
ব্যাগ দেখাও যেটা বড়ও হবে আবার দেখতে ভালোও
মোবাইল স্ট্যান্ড আছে? ভালো হলে দামও বলো
🔹 4. Comparison-Based Queries
এইটা আর ওইটার মধ্যে কোনটা ভালো?
স্যামসাং না শাওমি কোনটা ভালো এই দামে?
এইটার থেকে সস্তা কিন্তু একই রকম কিছু আছে?
এই প্রাইসে বেস্ট অপশন কোনটা?
ওইটার চেয়ে এইটা কেন নেবো?
🔹 5. Context-Dependent (Memory Required)
এটার দাম কত?
আগের যেটা দেখাইছিলা ওটার দাম বলো
ওই লালটার স্টক আছে?
আগেরটার থেকে বড় সাইজ আছে?
ওইটার অন্য কালার আছে?
🔹 6. Category + Filter Mixed
ইলেকট্রনিক্স এর মধ্যে সস্তা কি আছে?
কসমেটিকস এর মধ্যে বেস্ট সেলার কোনটা?
পুরুষদের জন্য ভালো পারফিউম আছে?
মেয়েদের ব্যাগ দেখাও, একটু স্টাইলিশ হলে ভালো হয়
কিচেনের জন্য দরকারি কিছু দেখাও
🔹 7. Slang / Informal Bangla
ভাই একটু জম্পেশ কিছু দেখাও
ফাটাফাটি কোয়ালিটির কিছু আছে নাকি?
একদম বাজেট ফ্রেন্ডলি কিছু দাও
টেকসই টাইপের কিছু লাগবে
লাইট ইউজের জন্য কিছু আছে?
🔹 8. Misspelled / Noisy Input
চার্জার → চার্জারর
হেডফোন → হেডফুন
জুতা → জুতাা
মোবাইল → মোবাইল্ল
ব্যাগ → ব্যাগগ

(👉 These are critical for robustness testing)

🔹 9. Mixed Language (Bangla + English)
একটা fast charger আছে?
budget friendly headphone দেখাও
stylish bag for girls আছে?
cheap but good quality shoes আছে?
best option under 500 taka কি?
🔹 10. Ambiguous Product Reference
এটা কি কাজে লাগে?
এই জিনিসটা ভালো নাকি?
এটা কেন কিনবো?
এটা টেকসই হবে?
এটা কয়দিন চলবে?
🔹 11. Recommendation + Reasoning
আমার জন্য কোনটা ভালো হবে?
গিফট দেওয়ার জন্য কি ভালো হবে?
ডেইলি ইউজের জন্য কি নিলে ভালো?
কোনটা বেশি দিন টিকবে?
কোনটা বেশি ভ্যালু ফর মানি?
🔹 12. Hard Edge Cases (Very Important)
কিছু দেখাও
কি কি আছে তোমাদের?
সব থেকে ভালোটা দেখাও
আমার বাজেট কম, কি নিতে পারি?
ভালো কিছু সাজেস্ট করো
🧠 Why These Are Important

These queries will test if your system can:

❌ Break Heuristics
“ভাই একটা ভালো জিনিস দেখাও”
→ No product, no category
❌ Break Entity Extraction
“সস্তার মধ্যে বেস্ট কোনটা?”
→ No entity, only intent
❌ Break Intent Classification
“একটা চার্জার লাগবে, ফাস্টও হবে আবার সস্তাও”
→ Multiple constraints
❌ Break Retrieval
“এইটা আর ওইটার মধ্যে কোনটা ভালো?”
→ Needs comparison logic
❌ Break Stateless Systems
“আগেরটার দাম কত?”
→ Requires memory
🔥 How to Use This List (Very Important)

Don’t just test manually.

Create a test framework:

test_queries = [ ... ]

for q in test_queries:
result = pipeline(q)
log(q, result)

Then check:

intent accuracy
entity extraction
response correctness
fallback usage
🎯 Final Insight

If your system can handle even 70% of these correctly:

👉 You are already ahead of most production chatbots in Bangladesh.

If you want next step, I can:

✅ Turn this into evaluation benchmark with scoring system
✅ Show expected JSON output for each query (LLM router training)
✅ Build auto test script for your FastAPI pipeline
✅ Or simulate real user conversations (multi-turn)

Just tell me 👍
