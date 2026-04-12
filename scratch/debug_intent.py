from app.intent import detect_intent
from app.catalog import normalize_text

queries = [
    "শ্যাম্পু কি পাওয়া যায়?",
    "শ্যাম্পু কি পাওয়া যায়?", # Variation with ও vs য়
]

for q in queries:
    norm = normalize_text(q)
    intent = detect_intent(q)
    print(f"Original: {q}")
    print(f"Normalized: {norm}")
    print(f"Detected Intent: {intent}")
    
    # Check if "পাওয়া যায়" or "পাওয়া যায়" is in normalized
    print(f"Contains 'পাওয়া যায়' (with ও): {'পাওয়া যায়' in norm}")
    print(f"Contains 'পাওয়া যায়' (with য়): {'পাওয়া যায়' in norm}")

print("\nKeywords in detect_intent (manually extracted from code):")
keywords = ["আছে", "available", "do you have", "have", "sell", "stock", "বিক্রি", "বিক্রি করে", "পাওয়া যায়", "পাওয়া যায়", "পাওয়া কি যায়", "পাওয়া কি যায়"]
for kw in keywords:
    print(f"'{kw}' in Normalized[0]: {kw in normalize_text(queries[0])}")
