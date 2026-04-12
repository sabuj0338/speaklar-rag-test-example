from app.catalog import normalize_text
from app.schemas import IntentName


def detect_intent(query: str) -> IntentName:
    q = normalize_text(query)

    if any(phrase in q for phrase in ["কি কি পণ্য", "কি কি product", "what products", "all products"]):
        return "list_all_products"
    if any(phrase in q for phrase in ["কি কি noodles", "কি কি নুডলস", "কি কি নুডুলস", "what noodles", "which noodles"]):
        return "list_category_products"
    if any(phrase in q for phrase in ["সবচেয়ে কম", "সবচেয়ে কম", "lowest", "cheapest", "minimum price"]):
        return "price_min"
    if any(phrase in q for phrase in ["সবচাইতে বেশি", "সবচেয়ে বেশি", "সবচেয়ে বেশি", "highest", "maximum price", "most expensive"]):
        return "price_max"
    if any(phrase in q for phrase in ["দাম", "price", "how much", "cost", "কত", "কত টাকা"]):
        return "price_product"
    if any(phrase in q for phrase in ["আছে", "available", "do you have", "have", "sell", "stock", "বিক্রি", "বিক্রি করে", "পাওয়া যায়", "পাওয়া যায়", "পাওয়া কি যায়", "পাওয়া কি যায়"]):
        if any(token in q for token in ["noodles", "নুডলস", "নুডুলস", "dress", "salt", "fashion", "home", "sports", "books", "electronics"]):
            return "category_availability"
        return "availability_product"
    return "unknown"
