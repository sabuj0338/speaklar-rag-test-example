from app.catalog import normalize_text
from app.schemas import IntentName


def detect_intent(query: str) -> IntentName:
    q = normalize_text(query)

    # সব পণ্য দেখাও
    if any(phrase in q for phrase in [
        "কি কি পণ্য", "কি কি product", "what products", "all products",
        "সব পণ্য", "পণ্য তালিকা", "সব দেখাও",
    ]):
        return "list_all_products"

    # ক্যাটাগরি ভিত্তিক পণ্য তালিকা
    if any(phrase in q for phrase in [
        "কি কি আছে", "কোন কোন", "তালিকা",
    ]):
        return "list_category_products"

    # সবচেয়ে কম দাম
    if any(phrase in q for phrase in [
        "সবচেয়ে কম", "সবচেয়ে সস্তা", "lowest", "cheapest", "minimum price",
        "কম দামের", "কম দাম", "সস্তা",
    ]):
        return "price_min"

    # সবচেয়ে বেশি দাম
    if any(phrase in q for phrase in [
        "সবচাইতে বেশি", "সবচেয়ে বেশি", "সবচেয়ে দামি",
        "highest", "maximum price", "most expensive",
        "বেশি দামের", "বেশি দাম", "দামি",
    ]):
        return "price_max"

    # দাম জানতে চায়
    if any(phrase in q for phrase in [
        "দাম", "price", "how much", "cost", "কত", "কত টাকা", "মূল্য",
    ]):
        return "price_product"

    # পণ্য বা ক্যাটাগরি আছে কিনা — entity resolver পরে distinguish করবে
    if any(phrase in q for phrase in [
        "আছে", "available", "do you have", "have", "sell", "stock",
        "বিক্রি", "বিক্রি করে", "পাওয়া যায়", "পাওয়া কি যায়",
        "রাখেন", "পাবো", "পাব", "পাওয়া যাবে",
    ]):
        return "availability_product"

    return "unknown"
