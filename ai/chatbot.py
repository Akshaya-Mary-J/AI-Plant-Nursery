"""Interactive plant shop chatbot logic.

This module intentionally avoids paid external AI APIs so the college project
works offline on localhost. It uses lightweight intent detection, fuzzy plant
matching, conversation context and product retrieval from the database.
"""

from __future__ import annotations

import difflib
import random
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "best", "buy", "can", "do", "for", "give",
    "good", "help", "how", "i", "in", "is", "it", "me", "my", "need", "of", "on", "or",
    "plant", "plants", "please", "should", "show", "suggest", "tell", "the", "this", "to",
    "u", "want", "what", "which", "with", "you", "your",
}

SYMPTOM_KNOWLEDGE = [
    {
        "keys": ("yellow", "yellowing", "pale", "chlorosis"),
        "title": "Yellow leaves",
        "advice": (
            "Yellow leaves are commonly caused by overwatering, poor drainage, low light or nutrient shortage. "
            "Check whether the top 2 cm of soil is still wet before watering again, keep the pot drainage open, "
            "and move the plant to bright indirect light."
        ),
    },
    {
        "keys": ("brown", "tips", "edge", "crispy", "burn"),
        "title": "Brown or crispy tips",
        "advice": (
            "Brown tips usually indicate low humidity, irregular watering, fertilizer burn or harsh direct sun. "
            "Trim only the dry portion, water deeply when soil is dry, and avoid strong afternoon sunlight for indoor plants."
        ),
    },
    {
        "keys": ("spot", "spots", "black", "fungal", "blight", "lesion"),
        "title": "Leaf spots",
        "advice": (
            "Leaf spots may be fungal or bacterial, especially when leaves stay wet. Remove badly affected leaves, "
            "keep air circulation good, water near the soil instead of on leaves, and isolate the plant for a few days."
        ),
    },
    {
        "keys": ("droop", "drooping", "wilting", "wilt", "soft"),
        "title": "Drooping plant",
        "advice": (
            "Drooping can happen from both underwatering and overwatering. Feel the soil first: if it is dry, water slowly; "
            "if it is soggy, stop watering and improve drainage."
        ),
    },
    {
        "keys": ("pest", "bugs", "insect", "mealy", "aphid", "whitefly", "mites"),
        "title": "Pest problem",
        "advice": (
            "For common pests, isolate the plant, wipe leaves with a damp cloth, and spray mild neem-oil solution in the evening. "
            "Repeat weekly until pests reduce."
        ),
    },
]

CATEGORY_HINTS = {
    "indoor": ("indoor", "room", "bedroom", "office", "desk", "home", "inside"),
    "outdoor": ("outdoor", "balcony", "garden", "terrace", "outside", "sunny"),
    "flowering": ("flower", "flowers", "flowering", "colour", "color", "decorative"),
    "herb": ("herb", "kitchen", "cooking", "mint", "curry", "basil"),
    "succulent": ("succulent", "cactus", "low water", "less water"),
    "medicinal": ("medicinal", "medicine", "health", "ayurvedic", "tulsi", "aloe"),
    "premium": ("premium", "gift", "bonsai", "luxury"),
}

BENEFIT_HINTS = {
    "beginner": ("beginner", "easy", "low maintenance", "low-maintenance", "new", "first"),
    "air": ("air", "oxygen", "purify", "purifier", "pollution"),
    "gift": ("gift", "present", "birthday", "anniversary"),
    "budget": ("cheap", "budget", "affordable", "low price", "under", "below", "less than"),
}

SUGGESTION_BANK = {
    "start": [
        "Suggest beginner plants",
        "Plants under 300",
        "How often to water Snake Plant?",
        "Why are leaves turning yellow?",
    ],
    "care": ["Tell me sunlight need", "What soil is best?", "Fertilizer tips", "Show similar plants"],
    "shop": ["Add best indoor plant", "Show flowering plants", "Checkout help", "Payment options"],
    "disease": ["Leaf has brown tips", "Leaf has black spots", "Upload disease image", "Neem oil treatment"],
}


def _normalise(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9₹\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> List[str]:
    return [t for t in _normalise(text).split() if t and t not in STOP_WORDS]


def _money_limit(text: str) -> Optional[int]:
    match = re.search(r"(?:under|below|less than|upto|up to|within|budget|₹|rs\.?|rupees?)\s*(\d{2,5})", text, re.I)
    if not match:
        match = re.search(r"(\d{2,5})\s*(?:budget|rupees?|rs\.?|₹)", text, re.I)
    return int(match.group(1)) if match else None


def _plant_lookup(plants: List[Dict[str, Any]], plant_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if not plant_id:
        return None
    for plant in plants:
        if int(plant["id"]) == int(plant_id):
            return plant
    return None


def _find_plant_mentions(message: str, plants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    text = _normalise(message)
    compact = text.replace(" ", "")
    found: List[Dict[str, Any]] = []

    for plant in plants:
        name = _normalise(plant["name"])
        if not name:
            continue
        if name in text or name.replace(" ", "") in compact:
            found.append(plant)

    if found:
        return found

    # Fuzzy match multi-word plant names such as "snake" -> "Snake Plant" or spelling mistakes.
    words = _tokens(message)
    if not words:
        return []

    candidates: List[Tuple[float, Dict[str, Any]]] = []
    for plant in plants:
        name = _normalise(plant["name"])
        name_words = name.split()
        score = difflib.SequenceMatcher(None, text, name).ratio()
        for word in words:
            score = max(score, difflib.SequenceMatcher(None, word, name).ratio())
            score = max(score, max((difflib.SequenceMatcher(None, word, n).ratio() for n in name_words), default=0))
        if score >= 0.72:
            candidates.append((score, plant))

    candidates.sort(reverse=True, key=lambda item: item[0])
    return [plant for _, plant in candidates[:2]]


def _category_from_message(text: str) -> Optional[str]:
    normal = _normalise(text)
    for category, hints in CATEGORY_HINTS.items():
        if any(hint in normal for hint in hints):
            return category
    return None


def _matches_hint(text: str, hint_group: Iterable[str]) -> bool:
    normal = _normalise(text)
    return any(hint in normal for hint in hint_group)


def _score_plant(plant: Dict[str, Any], message: str, budget: Optional[int], category: Optional[str]) -> int:
    text = _normalise(message)
    score = 0
    searchable = _normalise(" ".join([
        plant.get("name", ""), plant.get("category", ""), plant.get("benefits", ""),
        plant.get("description", ""), plant.get("difficulty", ""), plant.get("sunlight", ""),
        plant.get("water", ""), plant.get("soil", ""), plant.get("size", ""),
    ]))
    for token in _tokens(text):
        if token in searchable:
            score += 2
    if category and category in plant.get("category", "").lower():
        score += 8
    if budget and int(plant.get("price", 0)) <= budget:
        score += 8
    if _matches_hint(text, BENEFIT_HINTS["beginner"]):
        if "easy" in plant.get("difficulty", "").lower() or "low" in plant.get("description", "").lower():
            score += 7
    if _matches_hint(text, BENEFIT_HINTS["air"]):
        if "air" in plant.get("benefits", "").lower() or "oxygen" in plant.get("benefits", "").lower():
            score += 7
    if _matches_hint(text, BENEFIT_HINTS["gift"]):
        if plant.get("category", "").lower() in {"premium", "flowering", "indoor"}:
            score += 5
    if int(plant.get("stock", 0)) > 0:
        score += 1
    return score


def _recommend(plants: List[Dict[str, Any]], message: str, limit: int = 4) -> List[Dict[str, Any]]:
    budget = _money_limit(message)
    category = _category_from_message(message)
    scored = [(_score_plant(plant, message, budget, category), plant) for plant in plants]
    scored = [(score, plant) for score, plant in scored if score > 0]
    if not scored:
        defaults = [p for p in plants if p.get("name") in {"Money Plant", "Snake Plant", "Aloe Vera", "Jade Plant"}]
        return defaults[:limit] if defaults else plants[:limit]
    scored.sort(key=lambda item: (-item[0], int(item[1].get("price", 0))))
    return [plant for _, plant in scored[:limit]]


def _plant_card(plant: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": plant["id"],
        "name": plant["name"],
        "price": plant["price"],
        "stock": plant.get("stock", 0),
        "emoji": plant.get("emoji") or plant.get("image_emoji") or "🌿",
        "category": plant.get("category", "Plant"),
        "subtitle": f"{plant.get('difficulty', 'Easy')} care • {plant.get('sunlight', 'Indirect light')}",
        "url": f"/plant/{plant['id']}",
    }


def _care_reply(plant: Dict[str, Any], message: str) -> str:
    text = _normalise(message)
    name = plant["name"]
    if any(word in text for word in ("water", "watering", "drink")):
        return f"For {name}, watering guidance: {plant['water']}. Before watering, touch the top soil; water only if it feels dry."
    if any(word in text for word in ("sun", "light", "sunlight", "shade")):
        return f"For {name}, light requirement: {plant['sunlight']}. Avoid sudden harsh sunlight if it is mainly an indoor plant."
    if any(word in text for word in ("soil", "pot", "mix", "repot")):
        return f"For {name}, soil requirement: {plant['soil']}. Use a pot with drainage holes so roots do not stay waterlogged."
    if any(word in text for word in ("fertilizer", "fertiliser", "compost", "feed")):
        return f"For {name}, fertilizer guidance: {plant['fertilizer']}. Do not over-fertilize during extreme heat or immediately after repotting."
    if any(word in text for word in ("price", "cost", "rate", "stock", "available")):
        return f"{name} is available at ₹{plant['price']} and current stock is {plant.get('stock', 0)}. It is listed under {plant.get('category', 'Plants')}."
    return (
        f"{name} is a {plant.get('difficulty', 'Easy')} care plant. {plant.get('description', '')} "
        f"Care summary: {plant['sunlight']}; {plant['water']}; soil: {plant['soil']}; fertilizer: {plant['fertilizer']}. "
        f"Price: ₹{plant['price']}."
    )


def _disease_reply(message: str) -> Tuple[str, List[str]]:
    text = _normalise(message)
    matched = [item for item in SYMPTOM_KNOWLEDGE if any(key in text for key in item["keys"])]
    if matched:
        item = matched[0]
        return (
            f"Possible issue: {item['title']}. {item['advice']} For more accurate result, open Disease Check and upload a clear leaf photo.",
            SUGGESTION_BANK["disease"],
        )
    return (
        "Tell me the visible symptom like yellow leaves, brown tips, black spots, drooping, pests or soft roots. "
        "You can also use Disease Check to upload a clear leaf photo for image-based analysis.",
        SUGGESTION_BANK["disease"],
    )


def _compare_reply(plants: List[Dict[str, Any]]) -> str:
    a, b = plants[:2]
    return (
        f"Comparison: {a['name']} is priced at ₹{a['price']}, needs {a['sunlight']} and {a['water']}. "
        f"{b['name']} is priced at ₹{b['price']}, needs {b['sunlight']} and {b['water']}. "
        f"Choose {a['name']} if you prefer {a.get('benefits', '').lower()}; choose {b['name']} if you prefer {b.get('benefits', '').lower()}."
    )


def generate_chat_response(message: str, plants: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a structured chatbot response.

    Response keys: reply, speak, intent, suggestions, cards and context.
    """
    context = context or {}
    raw = message or ""
    text = _normalise(raw)
    reply: str
    cards: List[Dict[str, Any]] = []
    suggestions: List[str] = SUGGESTION_BANK["start"]
    intent = "general"

    if not text:
        return {
            "reply": "Please type or speak your question. I can suggest plants, explain care, help with disease symptoms, cart and checkout.",
            "speak": "Please type or speak your question.",
            "intent": "empty",
            "suggestions": SUGGESTION_BANK["start"],
            "cards": [],
            "context": context,
        }

    plant_mentions = _find_plant_mentions(raw, plants)
    previous_plant = _plant_lookup(plants, context.get("last_plant_id"))
    care_follow_up = previous_plant and any(word in text for word in ("water", "sun", "light", "soil", "fertilizer", "price", "cost", "stock", "care", "about it", "this plant"))

    if any(greet in text.split() for greet in ("hi", "hello", "hey", "namaste")):
        intent = "greeting"
        reply = (
            "Hello! I am your interactive plant assistant. You can ask things like: "
            "best plant for beginners, plants under 300, how to care for Snake Plant, why leaves are yellow, or help me checkout."
        )
        suggestions = SUGGESTION_BANK["start"]

    elif any(word in text for word in ("payment", "razorpay", "upi", "card", "online pay", "cod", "cash")):
        intent = "payment"
        reply = (
            "Payment support: Cash on Delivery works directly in this project. Razorpay online payment is already payment-ready; "
            "add your Razorpay Key ID and Key Secret in the .env file, then restart Flask. The backend creates an order and verifies the payment signature."
        )
        suggestions = ["How to checkout?", "Show cart help", "Razorpay setup", "Suggest plants under 500"]

    elif any(word in text for word in ("cart", "checkout", "order", "delivery", "shipping", "address")):
        intent = "order_help"
        reply = (
            "Ordering flow: open Plants, click Add to Cart, review quantities in Cart, then go to Checkout. "
            "Orders below ₹999 show a small delivery fee, while higher orders get free delivery in the demo."
        )
        suggestions = ["Show beginner plants", "Payment options", "Plants under 500", "Open checkout"]

    elif any(word in text for word in ("disease", "sick", "infection", "yellow", "brown", "spots", "spot", "pest", "wilting", "drooping", "fungal", "leaf problem")):
        intent = "disease"
        reply, suggestions = _disease_reply(raw)
        if plant_mentions:
            context["last_plant_id"] = plant_mentions[0]["id"]

    elif ("compare" in text or " vs " in f" {text} " or " versus " in text) and len(plant_mentions) >= 2:
        intent = "compare"
        reply = _compare_reply(plant_mentions)
        context["last_plant_id"] = plant_mentions[0]["id"]
        cards = [_plant_card(p) for p in plant_mentions[:2]]
        suggestions = ["Which is easier?", "Add one to cart", "Show similar plants", "Care tips"]

    elif plant_mentions or care_follow_up:
        intent = "plant_care"
        plant = plant_mentions[0] if plant_mentions else previous_plant
        context["last_plant_id"] = plant["id"]
        reply = _care_reply(plant, raw)
        cards = [_plant_card(plant)]
        suggestions = SUGGESTION_BANK["care"]

    elif any(word in text for word in ("recommend", "suggest", "which", "show", "available", "list", "under", "below", "budget", "beginner", "indoor", "outdoor", "flower", "herb", "succulent", "medicinal", "gift", "air")):
        intent = "recommendation"
        recommended = _recommend(plants, raw, limit=4)
        cards = [_plant_card(p) for p in recommended]
        if recommended:
            context["last_plant_id"] = recommended[0]["id"]
        budget = _money_limit(raw)
        category = _category_from_message(raw)
        intro_bits = []
        if category:
            intro_bits.append(f"{category} plants")
        if budget:
            intro_bits.append(f"under ₹{budget}")
        intro = " and ".join(intro_bits) if intro_bits else "good matching plants"
        names = ", ".join(p["name"] for p in recommended[:4])
        reply = f"Here are {intro}: {names}. You can view details or add any plant to cart directly from the cards below."
        suggestions = SUGGESTION_BANK["shop"]

    elif any(word in text for word in ("reminder", "schedule", "notify", "watering time")):
        intent = "reminder"
        reply = (
            "For watering reminders, open the Watering Reminder page, choose plant name and date, and save it. "
            "For a final-year demo, browser localStorage reminders are simple and reliable; for production, connect user login and database notifications."
        )
        suggestions = ["Snake Plant watering", "Aloe Vera care", "Show reminder page", "Beginner plants"]

    elif any(word in text for word in ("admin", "dashboard", "login", "stock", "add plant", "delete plant")):
        intent = "admin_help"
        reply = (
            "Admin panel is available from the top navigation button. Login with admin/admin123 for demo, then you can add, edit, delete plants and view recent orders and plant requests."
        )
        suggestions = ["How to add plant?", "Stock update", "Show orders", "Back to shop"]

    else:
        # Friendly fallback: use plant retrieval from message tokens instead of a fixed reply.
        recommended = _recommend(plants, raw, limit=3)
        cards = [_plant_card(p) for p in recommended]
        reply = (
            "I understood that you need plant-shop help. I can answer about plant care, disease symptoms, recommendations, cart, payment and admin. "
            "Based on your message, these plants may be relevant. You can also ask a clearer follow-up, for example: 'best indoor plant for low light'."
        )
        suggestions = ["Best indoor plant", "Low water plants", "Plant disease help", "Checkout help"]

    return {
        "reply": reply,
        "speak": reply[:220],
        "intent": intent,
        "suggestions": suggestions,
        "cards": cards,
        "context": context,
    }


# Backward compatible helper for older imports/tests.
def ask(msg: str) -> str:
    return generate_chat_response(msg, [], {})["reply"]
