from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.ai.policy import RETRIEVAL_CONFIDENCE
from backend.app.ai.urgency import detect_urgency, normalize_text


@dataclass(frozen=True)
class GuardrailCheck:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    requires_human: bool = False

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reasons": self.reasons,
            "requires_human": self.requires_human,
        }


def run_guardrails(
    *,
    customer_message: str,
    proposed_reply: str,
    intent: str,
    retrieval_confidence: float | None = None,
    has_verified_order: bool = False,
    has_verified_product: bool = False,
    human_requested: bool = False,
) -> GuardrailCheck:
    reasons: list[str] = []
    message = normalize_text(customer_message)
    reply = normalize_text(proposed_reply)

    if human_requested or intent == "human_agent":
        reasons.append("customer_requested_human_manager")
    if detect_urgency(customer_message) or intent == "complaint":
        reasons.append("urgent_or_complaint_requires_human")
    if intent == "return_refund" and any(word in message for word in ["refund", "money back", "верните деньги"]):
        if any(word in reply for word in ["approved", "guaranteed", "одобрен", "гарант"]):
            reasons.append("refund_promise_not_allowed")
        reasons.append("refund_requires_human_review")
    if intent in {"delivery_question", "payment_question", "warranty"}:
        if retrieval_confidence is None or retrieval_confidence < RETRIEVAL_CONFIDENCE:
            reasons.append("retrieval_confidence_too_low")
    if intent == "order_status" and not has_verified_order:
        if any(word in reply for word in ["tracking", "shipped", "eta", "трек", "отправ"]):
            reasons.append("order_status_without_verified_order")
    if intent == "product_availability" and not has_verified_product:
        if any(word in reply for word in ["in stock", "available", "наличии", "есть"]):
            reasons.append("product_stock_without_verified_catalog_match")
    if any(word in reply for word in ["system prompt", "internal note", "developer message", "системный промпт"]):
        reasons.append("internal_prompt_exposure")
    if any(word in reply for word in ["legal advice", "sue", "lawsuit guaranteed", "юридическая консультация"]):
        reasons.append("legal_claim_not_allowed")

    return GuardrailCheck(
        allowed=not reasons,
        reasons=reasons,
        requires_human=bool(reasons),
    )
