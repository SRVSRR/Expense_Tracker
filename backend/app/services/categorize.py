"""Rule-based transaction categorization using keyword matching."""

KEYWORD_MAP: dict[str, list[str]] = {
    # Food & Dining
    "Food & Dining": [
        "restaurant", "cafe", "coffee", "starbucks", "mcdonald", "burger",
        "pizza", "sushi", "thai", "chinese", "mexican", "indian", "italian",
        "diner", "grill", "bistro", "bakery", "donut", "bagel", "deli",
        "grocery", "supermarket", "walmart", "costco", "trader joe",
        "whole foods", "aldi", "kroger", "safeway", "publix", "wegmans",
        "doordash", "uber eats", "grubhub", "postmates", "instacart",
        "chipotle", "subway", "panera", "chick-fil-a", "wendy", "taco bell",
        "panda express", "five guys", "in-n-out", "shake shack",
        "door dash", "ubereats", "grub hub",
    ],
    # Transportation
    "Transportation": [
        "uber", "lyft", "taxi", "cab", "gas", "fuel", "shell", "bp",
        "chevron", "exxon", "mobil", "parking", "toll", "transit",
        "metro", "bus", "train", "amtrak", "airline", "flight",
        "delta", "united", "american airlines", "southwest", "jetblue",
        "hertz", "avis", "enterprise", "car rental", "turo",
        "oil change", "tire", "auto", "car wash", " mechanic",
    ],
    # Shopping
    "Shopping": [
        "amazon", "ebay", "etsy", "target", "best buy", "apple store",
        "nike", "adidas", "zara", "h&m", "uniqlo", "nordstrom",
        "macy", "nordstrom", "sephora", "ulta", "bath & body",
        "home depot", "lowes", "ikea", "wayfair", "overstock",
        "tj maxx", "marshalls", "ross", "dollar tree", "dollar general",
        "store", "shop", "boutique", "outlet", "mall",
    ],
    # Bills & Utilities
    "Bills & Utilities": [
        "electric", "electricity", "gas bill", "water bill", "internet",
        "wifi", "comcast", "at&t", "verizon", "t-mobile", "sprint",
        "utility", "utilities", "power", "sewage", "trash", "garbage",
        "phone bill", "cell phone", "cable", "satellite",
    ],
    # Housing
    "Housing": [
        "rent", "mortgage", "property tax", "hoa", "maintenance",
        "repair", "plumber", "electrician", "contractor", "landlord",
        "insurance", "home insurance",
    ],
    # Entertainment
    "Entertainment": [
        "netflix", "hulu", "disney", "spotify", "apple music", "youtube",
        "hbo", "paramount", "peacock", "prime video", "twitch",
        "cinema", "movie", "theater", "concert", "ticket", "stubhub",
        "gaming", "steam", "playstation", "xbox", "nintendo",
        "bar", "pub", "club", "lounge", "nightlife",
        "gym", "fitness", "yoga", "pilates", " CrossFit",
    ],
    # Health & Medical
    "Health & Medical": [
        "pharmacy", "cvs", "walgreens", "rite aid", "doctor", "dentist",
        "hospital", "clinic", "medical", "health", "prescription",
        "optometrist", "eye doctor", "therapy", "counseling", "vitamin",
    ],
    # Subscriptions
    "Subscriptions": [
        "subscription", "monthly", "annual", "membership", "renewal",
        "adobe", "microsoft 365", "google storage", "icloud", "dropbox",
        "notion", "slack", "zoom", "github", "patreon",
    ],
    # Education
    "Education": [
        "tuition", "university", "college", "school", "course", "class",
        "udemy", "coursera", "skillshare", "book", "textbook",
        "student loan", "education", "learning",
    ],
    # Income
    "Income": [
        "salary", "paycheck", "direct deposit", "payroll", "bonus",
        "commission", "freelance", "invoice", "client payment",
        "refund", "cashback", "dividend", "interest earned",
        "side hustle", "consulting", "contract payment",
    ],
    # Travel
    "Travel": [
        "hotel", "airbnb", "vrbo", "booking.com", "expedia", "tripadvisor",
        "hostel", "resort", "vacation", "travel", "trip", "luggage",
        "passport", "visa", "exchange",
    ],
    # Personal Care
    "Personal Care": [
        "haircut", "salon", "barber", "spa", "manicure", "pedicure",
        "skincare", "cosmetic", "fragrance", "perfume",
    ],
    # Pets
    "Pets": [
        "pet", "vet", "petco", "pet smart", "animal hospital",
        "dog food", "cat food", "pet supplies", "grooming",
    ],
    # Gifts & Donations
    "Gifts & Donations": [
        "gift", "donation", "charity", "tithe", "present", "birthday gift",
        "wedding gift", "holiday gift", "gofundme",
    ],
}


def suggest_category(description: str, merchant: str | None = None) -> str | None:
    """Suggest a category based on description and merchant keywords.
    
    Returns the best matching category name, or None if no match found.
    Matches are case-insensitive and check both description and merchant.
    """
    text = f"{description} {merchant or ''}".lower()

    # Score each category by number of keyword matches
    scores: dict[str, int] = {}
    for category, keywords in KEYWORD_MAP.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                # Longer keyword matches are more specific / valuable
                score += len(keyword)
        if score > 0:
            scores[category] = score

    if not scores:
        return None

    # Return highest-scoring category
    return max(scores, key=scores.get)


def get_all_categories() -> list[str]:
    """Return all predefined category names."""
    return list(KEYWORD_MAP.keys())
