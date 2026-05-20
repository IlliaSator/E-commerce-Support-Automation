from backend.app.integrations.n8n import emit_n8n_event
from backend.app.models import EscalationEvent, Ticket
from backend.app.schemas.api import SupportMessageIn, TicketResolve
from backend.app.services.support_service import handle_message
from backend.app.services.ticket_service import get_ticket_detail, resolve_ticket


def _message(text: str) -> SupportMessageIn:
    return SupportMessageIn(customer_id="test-customer", channel="telegram", message_text=text)


def test_order_status_returns_verified_tracking(db_session):
    result = handle_message(db_session, _message("Where is my order 10042?"))
    assert result.intent == "order_status"
    assert result.auto_resolved is True
    assert result.ticket_id is None
    assert "TG10042042" in result.reply_text


def test_missing_order_id_asks_for_clarification(db_session):
    result = handle_message(db_session, _message("Has my order been shipped?"))
    assert result.intent == "order_status"
    assert result.ticket_id is None
    assert "order number" in result.reply_text.lower()


def test_nonexistent_order_creates_ticket(db_session):
    result = handle_message(db_session, _message("Where is my order 99999?"))
    assert result.intent == "order_status"
    assert result.ticket_id is not None
    assert db_session.get(Ticket, result.ticket_id) is not None


def test_delivery_question_uses_retrieved_knowledge(db_session):
    result = handle_message(db_session, _message("How long does delivery take?"))
    assert result.intent == "delivery_question"
    assert result.auto_resolved is True
    assert "2-5" in result.reply_text
    assert result.retrieved_sources


def test_damaged_item_always_escalates(db_session):
    result = handle_message(db_session, _message("My order arrived broken"))
    assert result.intent == "complaint"
    assert result.ticket_id is not None
    assert result.escalation is True
    assert result.priority == "urgent"


def test_refund_demand_is_not_auto_promised(db_session):
    result = handle_message(db_session, _message("I need a refund"))
    assert result.intent == "return_refund"
    assert result.auto_resolved is False
    assert result.ticket_id is not None
    assert "approved" not in result.reply_text.lower()
    assert "guaranteed" not in result.reply_text.lower()


def test_unknown_question_creates_ticket(db_session):
    result = handle_message(db_session, _message("asdfghjkl"))
    assert result.intent == "unknown"
    assert result.ticket_id is not None
    assert result.auto_resolved is False


def test_product_stock_is_not_invented_for_missing_product(db_session):
    result = handle_message(db_session, _message("Do you have invisible drone in stock?"))
    assert result.ticket_id is not None
    assert result.auto_resolved is False
    assert "in stock" not in result.reply_text.lower()


def test_product_availability_returns_catalog_stock(db_session):
    result = handle_message(db_session, _message("Do you have iPhone 15 case?"))
    assert result.intent == "product_availability"
    assert result.auto_resolved is True
    assert "iPhone 15 Clear Case" in result.reply_text
    assert "12 units" in result.reply_text


def test_human_manager_request_creates_escalated_ticket(db_session):
    result = handle_message(db_session, _message("I need a human manager"))
    assert result.intent == "human_agent"
    assert result.ticket_id is not None
    assert result.escalation is True


def test_n8n_webhook_missing_url_logs_event_locally(db_session):
    delivered = emit_n8n_event(db_session, "escalation", {"ticket_id": 123}, ticket_id=None)
    db_session.commit()
    assert delivered is False
    event = db_session.query(EscalationEvent).one()
    assert event.error == "webhook_url_not_configured"


def test_ticket_resolution_emits_feedback_event_and_detail(db_session):
    result = handle_message(db_session, _message("I need a refund"))
    ticket = resolve_ticket(
        db_session,
        result.ticket_id,
        TicketResolve(
            final_reply="Resolved manually.",
            ai_suggestion_status="edited",
            feedback_rating=2,
            feedback_comment="Still unhappy",
        ),
    )
    assert ticket.status == "resolved"
    detail = get_ticket_detail(db_session, ticket.id)
    assert detail["events"][-1]["event_type"] == "resolved"
    assert detail["feedback"][0]["rating"] == 2
    reasons = {event.reason for event in db_session.query(EscalationEvent).all()}
    assert "feedback" in reasons
    assert "negative_feedback" in reasons
