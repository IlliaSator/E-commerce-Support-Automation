from __future__ import annotations

EN_URGENT = {
    "broken",
    "damaged",
    "scam",
    "fraud",
    "refund",
    "angry",
    "complaint",
    "lawyer",
    "lawsuit",
    "police",
    "unacceptable",
    "money back",
}

RU_URGENT = {
    "сломан",
    "поврежден",
    "повреждён",
    "обман",
    "мошенники",
    "верните деньги",
    "жалоба",
    "юрист",
    "суд",
    "полиция",
    "ужасно",
    "отвратительно",
}

NEGATIVE_WORDS = EN_URGENT | RU_URGENT | {"bad", "terrible", "awful", "кошмар", "плохо"}


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def detect_language(text: str) -> str:
    lowered = text.lower()
    return "ru" if any("а" <= ch <= "я" or ch == "ё" for ch in lowered) else "en"


def detect_urgency(text: str) -> bool:
    normalized = normalize_text(text)
    return any(word in normalized for word in EN_URGENT | RU_URGENT)


def detect_negative_tone(text: str) -> bool:
    normalized = normalize_text(text)
    return any(word in normalized for word in NEGATIVE_WORDS)


def priority_for_intent(intent: str, urgent: bool = False, negative: bool = False) -> str:
    if urgent or intent == "complaint":
        return "urgent"
    if intent in {"human_agent", "return_refund"} or negative:
        return "high"
    if intent in {"spam"}:
        return "low"
    return "normal"
