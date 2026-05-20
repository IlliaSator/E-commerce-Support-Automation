from datetime import UTC, datetime

from backend.app.ai.guardrails import run_guardrails
from backend.app.ai.retrieval.service import retrieve_knowledge
from backend.app.services.sla_service import calculate_sla_due


def test_low_retrieval_confidence_is_visible(db_session):
    result = retrieve_knowledge(db_session, "banana spacecraft insurance", language="en")
    assert result.confidence < 0.35


def test_guardrail_blocks_unverified_order_status():
    result = run_guardrails(
        customer_message="Where is my order 10042?",
        proposed_reply="Your order shipped with tracking ABC.",
        intent="order_status",
        has_verified_order=False,
    )
    assert result.allowed is False
    assert "order_status_without_verified_order" in result.reasons


def test_sla_urgent_due_in_15_minutes():
    created = datetime(2026, 5, 20, 12, 0, tzinfo=UTC)
    due = calculate_sla_due("urgent", created)
    assert int((due - created).total_seconds() // 60) == 15
