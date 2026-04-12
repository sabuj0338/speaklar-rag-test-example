# 🇧🇩 বাংলা RAG সিস্টেম — সম্পূর্ণ পরিকল্পনা
# Bangla RAG System — Complete Implementation Plan

> **ডেটাসোর্স:** `data/Knowledge_Bank.txt`
> **ভাষা:** বাংলা (Bangla)
> **ফ্রেমওয়ার্ক:** FastAPI + FAISS + Groq LLM

---

## 📌 সিস্টেমটি কী করবে? (What Does This System Do?)

এটি একটি **Retrieval-Augmented Generation (RAG)** সিস্টেম যা:

1. ব্যবহারকারী বাংলায় প্রশ্ন করবে (যেমন: "চেয়ারের দাম কত?")
2. সিস্টেম `Knowledge_Bank.txt` থেকে প্রাসঙ্গিক তথ্য খুঁজে বের করবে
3. বাংলায় উত্তর দেবে

```
ব্যবহারকারী → "ফাস্ট চার্জার আছে?"
                    ↓
            [Query Processing]
                    ↓
            [FAISS Vector Search]
                    ↓
            [Answer Generation]
                    ↓
            "হ্যাঁ, আমাদের কাছে ফাস্ট চার্জার আছে। দাম ২৭৩৩ টাকা।"
```

---

## 📊 ডেটা ফরম্যাট বিশ্লেষণ (Data Format Analysis)

### Knowledge_Bank.txt এর গঠন:

প্রতিটি পণ্য **একটি লাইনে** লেখা। প্রতিটি লাইনের মধ্যে একটি **ফাঁকা লাইন** আছে।

```
ফাস্ট চার্জার। দ্রুত চার্জ করে। ১০০% অরিজিনাল পণ্য... প্রোডাক্টটির মূল্য 2733 টাকা

জৈব সার। মাটির উর্বরতা বাড়ায়। ... প্রোডাক্টটির মূল্য 3709 টাকা
```

### প্রতিটি লাইনে যা আছে:

| তথ্য | উদাহরণ | কীভাবে বের করব |
|------|--------|----------------|
| **পণ্যের নাম** | ফাস্ট চার্জার | প্রথম `।` এর আগের অংশ |
| **বিবরণ** | দ্রুত চার্জ করে | দ্বিতীয় বাক্য |
| **দাম** | 2733 টাকা | `মূল্য (\d+) টাকা` regex |
| **ব্র্যান্ড** | রবি, আড়ং, বসুন্ধরা | `([\w]+) ব্র্যান্ডের` regex |
| **কোয়ালিটি** | প্রিমিয়াম, ডিলাক্স | `([\w]+) কোয়ালিটির` regex |
| **ওয়ারেন্টি** | আছে/নেই | `ওয়ারেন্টি` keyword |
| **ক্যাটাগরি** | ইলেকট্রনিক্স, আসবাবপত্র | `([\w\s]+) বিভাগে` regex |
| **অফার** | ১০% ছাড় | `ছাড়` keyword |
| **ডেলিভারি** | সারা বাংলাদেশে | `ডেলিভারি` keyword |

### মোট পণ্য: ~5,000

---

## 🏗️ সিস্টেম আর্কিটেকচার (System Architecture)

```
┌─────────────────────────────────────────────────────┐
│                    chat.html (UI)                     │
│              ব্যবহারকারী বাংলায় প্রশ্ন করে             │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP GET /ask?query=...
                       ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI Server                      │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Intent       │→ │ Entity       │→ │ Query      │ │
│  │ Detection    │  │ Resolution   │  │ Resolver   │ │
│  │ (কী জানতে    │  │ (কোন পণ্য    │  │ (সম্পূর্ণ   │ │
│  │  চাইছে?)     │  │  সম্পর্কে?)   │  │  প্রশ্ন বোঝা)│ │
│  └──────────────┘  └──────────────┘  └─────┬──────┘ │
│                                            │        │
│  ┌─────────────────────────────────────────▼──────┐ │
│  │              Data Retrieval Layer               │ │
│  │                                                 │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │ │
│  │  │ Direct   │  │ FAISS    │  │ Category     │  │ │
│  │  │ Lookup   │  │ Vector   │  │ Lookup       │  │ │
│  │  │ (exact   │  │ Search   │  │ (ক্যাটাগরি   │  │ │
│  │  │  match)  │  │ (semantic│  │  অনুসন্ধান)   │  │ │
│  │  │          │  │  search) │  │              │  │ │
│  │  └──────────┘  └──────────┘  └──────────────┘  │ │
│  └─────────────────────────────────────────┬──────┘ │
│                                            │        │
│  ┌─────────────────────────────────────────▼──────┐ │
│  │              Answer Engine                      │ │
│  │  (intent অনুযায়ী structured উত্তর তৈরি)         │ │
│  │                                                 │ │
│  │  যদি structured উত্তর না পারে:                   │ │
│  │  ┌──────────────────────────────────┐           │ │
│  │  │  Groq LLM Fallback              │           │ │
│  │  │  (AI দিয়ে বাংলায় উত্তর)          │           │ │
│  │  └──────────────────────────────────┘           │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  Caching Layer                                  │ │
│  │  ┌────────┐  ┌────────────┐  ┌──────────────┐  │ │
│  │  │ Redis  │  │ In-Memory  │  │ FAISS        │  │ │
│  │  │ Cache  │  │ Cache      │  │ Semantic     │  │ │
│  │  │        │  │ (fallback) │  │ Cache        │  │ │
│  │  └────────┘  └────────────┘  └──────────────┘  │ │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 📝 ধাপে ধাপে বাস্তবায়ন (Step-by-Step Implementation)

---

### ধাপ ১: ডেটা পার্সিং (Parse Knowledge_Bank.txt → JSON)

**ফাইল:** `scripts/parse_knowledge_bank.py` (নতুন তৈরি করতে হবে)

**কী করবে:**
- `Knowledge_Bank.txt` পড়বে
- প্রতিটি নন-ব্ল্যাঙ্ক লাইনকে একটি পণ্য হিসেবে প্রসেস করবে
- Regex দিয়ে তথ্য বের করবে
- `data/knowledge_bank.json` হিসেবে সেভ করবে

**পার্সিং লজিক:**

```python
import re

def parse_product_line(line, product_id):
    # ১. পণ্যের নাম (প্রথম বাক্য)
    sentences = line.split("।")
    name = sentences[0].strip()
    
    # ২. বিবরণ (দ্বিতীয় বাক্য)
    description = sentences[1].strip() if len(sentences) > 1 else ""
    
    # ৩. দাম বের করা
    price_match = re.search(r'মূল্য\s*(\d+)\s*টাকা', line)
    price = int(price_match.group(1)) if price_match else 0
    
    # ৪. ব্র্যান্ড বের করা
    brand_match = re.search(r'([\u0980-\u09FF\w]+)\s*ব্র্যান্ডের', line)
    brand = brand_match.group(1) if brand_match else ""
    
    # ৫. ক্যাটাগরি বের করা (বিভাগ keyword থেকে)
    category_match = re.search(r'([\u0980-\u09FF\s\w&]+)\s*বিভাগে', line)
    category = category_match.group(1).strip() if category_match else ""
    
    # ৬. কোয়ালিটি বের করা
    quality_match = re.search(r'([\u0980-\u09FF\w]+)\s*কোয়ালিটির', line)
    quality = quality_match.group(1) if quality_match else ""
    
    return {
        "id": product_id,
        "text": name,           # পণ্যের নাম — search ও display এ ব্যবহার হবে
        "description": description,
        "price": price,         # integer, টাকায়
        "brand": brand,
        "category": category,   # "ইলেকট্রনিক্স", "আসবাবপত্র", ইত্যাদি
        "quality": quality,
        "full_text": line,      # সম্পূর্ণ লাইন — embedding ও LLM context এ ব্যবহার হবে
    }
```

**আউটপুট JSON ফরম্যাট:**
```json
[
  {
    "id": 1,
    "text": "ফাস্ট চার্জার",
    "description": "দ্রুত চার্জ করে",
    "price": 2733,
    "brand": "",
    "category": "",
    "quality": "",
    "full_text": "ফাস্ট চার্জার। দ্রুত চার্জ করে। ..."
  }
]
```

**কমান্ড:** `python3 scripts/parse_knowledge_bank.py`

---

### ধাপ ২: FAISS ইনডেক্স তৈরি (Build Search Index)

**ফাইল:** `scripts/build_index.py` (পরিবর্তন করতে হবে)

**কী করবে:**
- `data/knowledge_bank.json` পড়বে
- প্রতিটি পণ্যের `full_text` থেকে embedding তৈরি করবে (multilingual model ব্যবহার করে)
- FAISS index এ সেভ করবে (`artifacts/index.faiss`)
- ID map সেভ করবে (`artifacts/id_map.json`)

**কেন `full_text` ব্যবহার করব?**
- সম্পূর্ণ লাইনে পণ্যের নাম, বিবরণ, ব্র্যান্ড, ক্যাটাগরি সব আছে
- Semantic search এ বেশি তথ্য থাকলে ভালো ফলাফল আসে

**Embedding Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- এই মডেল বাংলা সহ ৫০+ ভাষা সাপোর্ট করে

**কমান্ড:** `python3 scripts/build_index.py`

---

### ধাপ ৩: কনফিগারেশন আপডেট (Update Config)

**ফাইল:** `app/config.py`

**পরিবর্তন:**
```python
# আগে:
products_path: Path = Path("data/products.json")

# পরে:
products_path: Path = Path("data/knowledge_bank.json")
```

---

### ধাপ ৪: ক্যাটালগ লোডিং আপডেট (Update Catalog Loading)

**ফাইল:** `app/catalog.py`

**পরিবর্তন:**
- `parse_price()` ফাংশন আপডেট করতে হবে যেন plain integer (2733) এবং "2733 টাকা" উভয় ফরম্যাট হ্যান্ডেল করে

```python
def parse_price(price):
    if isinstance(price, (int, float)):
        return float(price)
    text = str(price)
    # "2733 টাকা" বা "2733" বা "$2733" সব হ্যান্ডেল করবে
    match = re.search(r'(\d+(?:\.\d+)?)', text)
    return float(match.group(1)) if match else 0.0
```

---

### ধাপ ৫: মেইন অ্যাপ আপডেট (Update Main App Startup)

**ফাইল:** `app/main.py`

**পরিবর্তন:**
- নতুন JSON ফরম্যাট অনুযায়ী catalog, product_names, categories লোড করতে হবে
- `text` ফিল্ড থেকে product names
- `category` ফিল্ড থেকে categories (খালি না হলে)
- `product_lookup` ম্যাপে `full_text` সহ রাখতে হবে

```python
id_map = load_json(settings.product_map_path)
catalog = list(id_map.values())
product_names = [item["text"] for item in catalog]
categories = sorted({
    item.get("category", "") 
    for item in catalog 
    if item.get("category")
})
```

---

### ধাপ ৬: Intent Detection আপডেট (Bangla Intent Recognition)

**ফাইল:** `app/intent.py`

**কী করবে:**
ব্যবহারকারীর প্রশ্ন থেকে বুঝতে হবে সে কী জানতে চাইছে।

**সাপোর্টেড Intents:**

| Intent | বাংলা উদাহরণ | English |
|--------|-------------|---------|
| `list_all_products` | "কি কি পণ্য আছে?" | List all products |
| `category_availability` | "ইলেকট্রনিক্স পণ্য আছে?" | Is category available? |
| `list_category_products` | "আসবাবপত্র কি কি আছে?" | List category products |
| `price_product` | "চেয়ারের দাম কত?" | Product price |
| `price_min` | "সবচেয়ে কম দামের পণ্য?" | Cheapest product |
| `price_max` | "সবচেয়ে বেশি দামের পণ্য?" | Most expensive |
| `availability_product` | "ফাস্ট চার্জার আছে?" | Is product available? |
| `unknown` | অন্য কিছু | Fallback to LLM |

**Bangla Keyword Matching:**
```python
def detect_intent(query):
    q = normalize_text(query)
    
    # সব পণ্য দেখাও
    if any(p in q for p in ["কি কি পণ্য", "সব পণ্য", "কি কি আছে"]):
        return "list_all_products"
    
    # সবচেয়ে কম দাম
    if any(p in q for p in ["সবচেয়ে কম", "সবচেয়ে সস্তা", "cheapest"]):
        return "price_min"
    
    # সবচেয়ে বেশি দাম
    if any(p in q for p in ["সবচেয়ে বেশি", "সবচেয়ে দামি", "most expensive"]):
        return "price_max"
    
    # দাম জানতে চায়
    if any(p in q for p in ["দাম", "কত টাকা", "price", "মূল্য"]):
        return "price_product"
    
    # পণ্য আছে কিনা
    if any(p in q for p in ["আছে", "পাওয়া যায়", "available"]):
        # ক্যাটাগরি নাকি নির্দিষ্ট পণ্য — entity resolver ঠিক করবে
        return "availability_product"
    
    return "unknown"
```

**গুরুত্বপূর্ণ পরিবর্তন:**
- Hardcoded ক্যাটাগরি টোকেন (noodles, salt, ইত্যাদি) সরিয়ে ফেলতে হবে
- Category detection entity resolver এ করবে, intent detection এ নয়

---

### ধাপ ৭: Entity Resolution আপডেট (Bangla Entity Recognition)

**ফাইল:** `app/entity.py`

**কী করবে:**
ব্যবহারকারীর প্রশ্ন থেকে **কোন পণ্য** বা **কোন ক্যাটাগরি** সম্পর্কে জিজ্ঞাসা করছে তা বের করবে।

**ক্যাটাগরি ম্যাপ আপডেট:**
Knowledge_Bank.txt এ যে ক্যাটাগরি পাওয়া যায়:

```python
BANGLA_CATEGORY_MAP = {
    # Knowledge_Bank.txt থেকে পাওয়া ক্যাটাগরি
    "ইলেকট্রনিক্স": "ইলেকট্রনিক্স",
    "আসবাবপত্র": "আসবাবপত্র",
    "খেলাধুলা": "খেলাধুলা",
    "প্রসাধনী": "প্রসাধনী",
    "ফ্যাশন ও পোশাক": "ফ্যাশন ও পোশাক",
    "খাদ্য ও পানীয়": "খাদ্য ও পানীয়",
    "স্বাস্থ্য ও ঔষধ": "স্বাস্থ্য ও ঔষধ",
    "যন্ত্রপাতি ও সরঞ্জাম": "যন্ত্রপাতি ও সরঞ্জাম",
    "গৃহস্থালী সামগ্রী": "গৃহস্থালী সামগ্রী",
    "বই ও স্টেশনারি": "বই ও স্টেশনারি",
    "খেলনা ও শিশু পণ্য": "খেলনা ও শিশু পণ্য",
    "মোবাইল আনুষঙ্গিক": "মোবাইল আনুষঙ্গিক",
    "কৃষি ও বাগান": "কৃষি ও বাগান",
    
    # শর্ট ফর্ম / বিকল্প নাম
    "ইলেক্ট্রনিক্স": "ইলেকট্রনিক্স",
    "ফ্যাশন": "ফ্যাশন ও পোশাক",
    "পোশাক": "ফ্যাশন ও পোশাক",
    "খাদ্য": "খাদ্য ও পানীয়",
    "খাবার": "খাদ্য ও পানীয়",
    "স্বাস্থ্য": "স্বাস্থ্য ও ঔষধ",
    "ঔষধ": "স্বাস্থ্য ও ঔষধ",
    "যন্ত্রপাতি": "যন্ত্রপাতি ও সরঞ্জাম",
    "সরঞ্জাম": "যন্ত্রপাতি ও সরঞ্জাম",
    "খেলনা": "খেলনা ও শিশু পণ্য",
    "শিশু": "খেলনা ও শিশু পণ্য",
    "বই": "বই ও স্টেশনারি",
    "স্টেশনারি": "বই ও স্টেশনারি",
    "মোবাইল": "মোবাইল আনুষঙ্গিক",
    "কৃষি": "কৃষি ও বাগান",
    "বাগান": "কৃষি ও বাগান",
}
```

**Product Name Matching:**
- `rapidfuzz` লাইব্রেরি দিয়ে fuzzy matching (বানান ভুল হলেও খুঁজে পাবে)
- বাংলা stop words সরিয়ে ফেলতে হবে: "কি", "আছে", "পাওয়া", "যায়", "টা", "টি", "এর", "এই"

---

### ধাপ ৮: Answer Engine আপডেট (Bangla Answer Generation)

**ফাইল:** `app/answer_engine.py`

**কী করবে:**
Intent এবং retrieved data থেকে বাংলায় structured উত্তর তৈরি করবে।

**উদাহরণ উত্তর:**

| Intent | উত্তর |
|--------|-------|
| `availability_product` → পাওয়া গেছে | "হ্যাঁ, আমাদের কাছে **ফাস্ট চার্জার** আছে।" |
| `availability_product` → পাওয়া যায়নি | "দুঃখিত, আমি তালিকায় এই পণ্যটি খুঁজে পাইনি।" |
| `price_product` | "**ফাস্ট চার্জার**-এর দাম ৳২,৭৩৩.০০।" |
| `price_min` | "সবচেয়ে কম দামের পণ্যটি হলো **কলম**, যার দাম ৳৬৮.০০।" |
| `list_category_products` | "আমাদের কাছে থাকা **ইলেকট্রনিক্স** পণ্য হলো: ল্যাপটপ, স্মার্টফোন, পাওয়ার ব্যাংক।" |

**গুরুত্বপূর্ণ পরিবর্তন:**
- `_find_product()` ফাংশনে `full_text` ফিল্ডেও সার্চ করতে হবে
- `_format_price()` ফাংশনে integer price handle করতে হবে

---

### ধাপ ৯: LLM Fallback আপডেট (Bangla Groq Prompt)

**ফাইল:** `app/llm.py`

**কী করবে:**
- যখন structured answer engine উত্তর দিতে পারবে না, তখন Groq LLM ব্যবহার করবে
- LLM কে বাংলায় উত্তর দিতে বলতে হবে
- Context হিসেবে `full_text` পাঠাতে হবে

**প্রম্পট আপডেট:**
```python
prompt = (
    "তুমি একজন বাংলাদেশী ই-কমার্স সহকারী। শুধুমাত্র নিচের তথ্য থেকে উত্তর দাও। "
    "যদি তথ্যে উত্তর না থাকে, বলো 'দুঃখিত, আমাদের তালিকায় এটি নেই।'\n\n"
    f"তথ্য: {context}\n\n"
    f"প্রশ্ন: {query}"
)
```

---

### ধাপ ১০: Routes ও API আপডেট

**ফাইল:** `app/routes.py`

**পরিবর্তন:**
- Fallback response message গুলো সম্পূর্ণ বাংলায় করতে হবে
- `category_products` lookup নতুন Bangla category names দিয়ে কাজ করবে
- `product_lookup` এ `full_text` ফিল্ড ব্যবহার করবে

---

### ধাপ ১১: Query Resolver আপডেট

**ফাইল:** `app/resolver.py`

**পরিবর্তন:**
- বাংলা vague references আপডেট: "এটা", "ওটা", "এটার", "ওটার", ইত্যাদি
- Category vs Product distinction — entity resolver এর output ব্যবহার করে intent re-map করবে
  - যদি entity resolver একটি category পায় + intent "availability_product" → "category_availability"
  - যদি entity resolver একটি product পায় → intent ঠিক আছে

---

## 🔄 সম্পূর্ণ Data Flow (Complete Request Lifecycle)

```
1. ব্যবহারকারী: "চেয়ারের দাম কত?"
   │
2. Intent Detection:
   │  "দাম" keyword পাওয়া গেছে → intent = "price_product"
   │
3. Entity Resolution:
   │  "চেয়ার" → fuzzy match → "আরামদায়ক চেয়ার" (product name)
   │
4. Query Resolver:
   │  resolved = {intent: "price_product", product: "আরামদায়ক চেয়ার", category: None}
   │
5. Cache Check:
   │  cache_key = "ask:session123:price_product:আরামদায়ক চেয়ার:none"
   │  cache miss → continue
   │
6. Data Retrieval:
   │  product_lookup["আরামদায়ক চেয়ার"] → {text: "আরামদায়ক চেয়ার", price: 3802, ...}
   │
7. Answer Engine:
   │  intent = "price_product", product found
   │  → "আরামদায়ক চেয়ার-এর দাম ৳৩,৮০২.০০।"
   │
8. State Update:
   │  state = {active_product: "আরামদায়ক চেয়ার", active_category: None}
   │
9. Cache Store:
   │  Redis/InMemory cache এ response সেভ (TTL: 300s)
   │
10. Response → ব্যবহারকারী
```

---

## 📁 ফাইল স্ট্রাকচার (File Structure)

```
ai/
├── app/
│   ├── __init__.py
│   ├── main.py          ← অ্যাপ startup, ডেটা লোড
│   ├── config.py         ← কনফিগারেশন (paths, API keys)
│   ├── catalog.py        ← ডেটা utility functions
│   ├── schemas.py        ← Pydantic models (ResolvedQuery, AskResponse)
│   ├── intent.py         ← Intent detection (কী জানতে চায়?)
│   ├── entity.py         ← Entity resolution (কোন পণ্য/ক্যাটাগরি?)
│   ├── resolver.py       ← Query resolver (intent + entity + state)
│   ├── retriever.py      ← FAISS vector search
│   ├── answer_engine.py  ← Structured answer generation
│   ├── llm.py            ← Groq LLM fallback
│   ├── cache.py          ← Redis/InMemory/Semantic caching
│   ├── state.py          ← Session state management
│   └── routes.py         ← FastAPI endpoints
│
├── scripts/
│   ├── parse_knowledge_bank.py  ← [নতুন] TXT → JSON parser
│   ├── build_index.py           ← FAISS index builder
│   └── test_pipeline.py         ← Test suite
│
├── data/
│   ├── Knowledge_Bank.txt       ← মূল ডেটা (5,000 পণ্য)
│   ├── knowledge_bank.json      ← [তৈরি হবে] parsed JSON
│   └── products.json            ← পুরানো ডেটা (আর ব্যবহার হবে না)
│
├── artifacts/
│   ├── index.faiss              ← [তৈরি হবে] FAISS search index
│   ├── id_map.json              ← [তৈরি হবে] ID → product mapping
│   └── semantic_cache/          ← semantic cache storage
│
├── chat.html                    ← Chat UI
├── .env                         ← API keys ও config
└── requirements.txt             ← Python dependencies
```

---

## ⚡ চালানোর ধাপ (How to Run)

```bash
# ১. Knowledge_Bank.txt পার্স করো
python3 scripts/parse_knowledge_bank.py

# ২. FAISS index তৈরি করো
python3 scripts/build_index.py

# ৩. সার্ভার চালাও
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ৪. ব্রাউজারে যাও
# chat.html ওপেন করো অথবা API সরাসরি ব্যবহার করো:
# http://localhost:8000/ask?query=চেয়ার আছে?&session_id=test1
```

---

## 🧪 পরীক্ষার কেস (Test Cases)

| # | প্রশ্ন (Query) | প্রত্যাশিত Intent | প্রত্যাশিত উত্তর |
|---|----------------|-------------------|------------------|
| 1 | "ফাস্ট চার্জার আছে?" | availability_product | "হ্যাঁ, আমাদের কাছে ফাস্ট চার্জার আছে।" |
| 2 | "এটার দাম কত?" | price_product (contextual) | "ফাস্ট চার্জার-এর দাম ৳২,৭৩৩.০০।" |
| 3 | "সবচেয়ে সস্তা পণ্য কোনটা?" | price_min | "সবচেয়ে কম দামের পণ্যটি হলো..." |
| 4 | "আসবাবপত্র কি কি আছে?" | list_category_products | "আমাদের কাছে থাকা আসবাবপত্র পণ্য হলো:..." |
| 5 | "ইলেকট্রনিক্স পণ্য আছে?" | category_availability | "হ্যাঁ, আমাদের কাছে ইলেকট্রনিক্স আছে।..." |
| 6 | "কি কি পণ্য বিক্রি করেন?" | list_all_products | "আমাদের কাছে আছে: ..." |
| 7 | "শাড়ির দাম কত?" | price_product | "সুন্দর ডিজাইনের শাড়ি-এর দাম ৳১,২৮৬.০০।" |

---

## 🔑 প্রয়োজনীয় Environment Variables (.env)

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxx      # Groq API key (LLM fallback এর জন্য)
REDIS_URL=redis://localhost:6379/0  # Redis URL (optional, InMemory fallback আছে)
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

---

## 📦 Dependencies (requirements.txt)

```
fastapi
uvicorn
pydantic-settings
sentence-transformers
faiss-cpu
numpy
redis
groq
rapidfuzz
```

---

## ⚠️ গুরুত্বপূর্ণ বিবেচনা (Important Considerations)

1. **ডেটায় ক্যাটাগরি সব entry তে নেই** — অনেক পণ্যের ক্যাটাগরি খালি থাকবে, সেক্ষেত্রে FAISS semantic search কাজ করবে
2. **একই পণ্যের নাম একাধিকবার আছে** — "আরামদায়ক চেয়ার" ৩ বার আছে ভিন্ন দামে। Entity resolver কে handle করতে হবে
3. **ব্র্যান্ড নাম বিশ্বাসযোগ্য নয়** — "নগদ ব্র্যান্ড", "বিকাশ ব্র্যান্ড" এগুলো আসলে ব্র্যান্ড নয়, generated data এর limitation
4. **Price format** — দাম integer (2733), dollar sign নেই, টাকায়
5. **Redis optional** — Redis না থাকলে InMemory cache ব্যবহার হবে

---

## 🎯 সারসংক্ষেপ (Summary)

এই সিস্টেমটি ৩টি স্তরে কাজ করে:

1. **Understanding Layer** — ব্যবহারকারী কী জানতে চায় বুঝতে পারা (Intent + Entity)
2. **Retrieval Layer** — সঠিক তথ্য খুঁজে বের করা (FAISS + Direct Lookup)
3. **Generation Layer** — বাংলায় সুন্দর উত্তর তৈরি করা (Answer Engine + LLM Fallback)

মূল লক্ষ্য: **Knowledge_Bank.txt থেকে বাংলায় প্রশ্নের উত্তর দেওয়া।**
