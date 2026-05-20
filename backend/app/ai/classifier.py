from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import joblib

from backend.app.ai.urgency import detect_urgency, normalize_text

MODEL_PATH = Path("data/training/intent_classifier.joblib")


@dataclass(frozen=True)
class ClassificationResult:
    intent: str
    confidence: float
    source: str = "rules"


ORDER_RE = re.compile(r"(?:order|заказ)\D{0,10}(\d{4,8})|\\b(\d{5})\\b", re.IGNORECASE)


def extract_order_id(text: str) -> str | None:
    match = ORDER_RE.search(text)
    if not match:
        return None
    return next((group for group in match.groups() if group), None)


def _contains_any(text: str, phrases: set[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _rule_classify(text: str) -> ClassificationResult | None:
    normalized = normalize_text(text)
    if not normalized or len(normalized) <= 2:
        return ClassificationResult("unknown", 0.35)
    if re.fullmatch(r"[a-zа-яё]{8,}", normalized) and normalized in {"asdfghjkl", "qwertyuiop"}:
        return ClassificationResult("unknown", 0.3)
    if _contains_any(normalized, {"crypto", "free money", "click link", "buy now", "купите рекламу"}):
        return ClassificationResult("spam", 0.92)
    if _contains_any(
        normalized,
        {
            "human",
            "manager",
            "operator",
            "real person",
            "оператор",
            "менеджер",
            "человек",
            "живой",
        },
    ):
        return ClassificationResult("human_agent", 0.94)
    if detect_urgency(normalized) or _contains_any(
        normalized,
        {"broken", "arrived broken", "damaged", "lawyer", "lawsuit", "обман", "сломанный", "суд"},
    ):
        return ClassificationResult("complaint", 0.95)
    if _contains_any(
        normalized,
        {"return", "refund", "money back", "вернуть", "возврат", "верните деньги", "refund"},
    ):
        return ClassificationResult("return_refund", 0.88)
    if extract_order_id(normalized) or _contains_any(
        normalized,
        {"where is my order", "track order", "shipped", "заказ", "где мой заказ", "когда приедет"},
    ):
        return ClassificationResult("order_status", 0.9 if extract_order_id(normalized) else 0.78)
    if _contains_any(normalized, {"delivery", "shipping", "доставка", "срок", "доставк"}):
        return ClassificationResult("delivery_question", 0.86)
    if _contains_any(normalized, {"in stock", "available", "do you have", "налич", "есть ли", "есть "}):
        return ClassificationResult("product_availability", 0.82)
    if _contains_any(normalized, {"pay", "payment", "card", "cash", "оплат", "карт"}):
        return ClassificationResult("payment_question", 0.85)
    if _contains_any(normalized, {"warranty", "guarantee", "гарант"}):
        return ClassificationResult("warranty", 0.86)
    return None


def _model_classify(text: str) -> ClassificationResult | None:
    if not MODEL_PATH.exists():
        return None
    try:
        model = joblib.load(MODEL_PATH)
        probabilities = model.predict_proba([text])[0]
        index = int(probabilities.argmax())
        intent = str(model.classes_[index])
        confidence = float(probabilities[index])
        return ClassificationResult(intent, confidence, "sklearn")
    except Exception:
        return None


def classify_message(text: str) -> ClassificationResult:
    rule_result = _rule_classify(text)
    if rule_result:
        return rule_result
    model_result = _model_classify(text)
    if model_result:
        return model_result
    return ClassificationResult("unknown", 0.4)
