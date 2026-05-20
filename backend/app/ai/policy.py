AUTO_REPLY_CONFIDENCE = 0.75
LOW_CONFIDENCE_ESCALATION = 0.45
RETRIEVAL_CONFIDENCE = 0.35
PROMPT_TEMPLATE_VERSION = "v1"

AUTO_RESOLVABLE_INTENTS = {
    "order_status",
    "delivery_question",
    "payment_question",
    "warranty",
    "product_availability",
}

HUMAN_REVIEW_INTENTS = {
    "complaint",
    "return_refund",
    "human_agent",
    "spam",
    "unknown",
}

CRITICAL_DECISION_NOTE = (
    "Critical decisions such as refunds, legal claims, order status, delivery ETA, "
    "and product stock must be grounded in verified system data."
)
