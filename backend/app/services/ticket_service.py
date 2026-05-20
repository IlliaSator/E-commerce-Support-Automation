from datetime import UTC, datetime, timedelta

from backend.app.integrations.n8n import emit_n8n_event
from backend.app.models import AISuggestion, Feedback, Ticket, TicketEvent
from backend.app.schemas.api import TicketCreate, TicketResolve, TicketUpdate
from backend.app.services.customer_service import get_or_create_customer
from backend.app.services.sla_service import calculate_sla_due
from fastapi import HTTPException
from sqlalchemy.orm import Session


def get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def get_ticket_detail(db: Session, ticket_id: int) -> dict:
    ticket = get_ticket_or_404(db, ticket_id)
    return {
        "ticket": ticket,
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "payload": event.payload,
                "created_at": event.created_at.isoformat(),
            }
            for event in ticket.events
        ],
        "ai_suggestions": [
            {
                "id": suggestion.id,
                "status": suggestion.status,
                "suggestion_text": suggestion.suggestion_text,
                "final_human_reply": suggestion.final_human_reply,
                "created_at": suggestion.created_at.isoformat(),
            }
            for suggestion in ticket.suggestions
        ],
        "feedback": [
            {
                "id": feedback.id,
                "rating": feedback.rating,
                "comment": feedback.comment,
                "source": feedback.source,
                "created_at": feedback.created_at.isoformat(),
            }
            for feedback in ticket.feedback
        ],
    }


def list_tickets(db: Session) -> list[Ticket]:
    return db.query(Ticket).order_by(Ticket.created_at.desc()).limit(200).all()


def list_open_tickets(db: Session, older_than_minutes: int | None = None) -> list[Ticket]:
    query = db.query(Ticket).filter(Ticket.status.in_(["open", "in_progress", "waiting_customer"]))
    if older_than_minutes is not None:
        cutoff = datetime.now(UTC) - timedelta(minutes=older_than_minutes)
        query = query.filter(Ticket.created_at <= cutoff)
    return query.order_by(Ticket.sla_due_at.asc()).all()


def list_sla_breaches(db: Session) -> list[Ticket]:
    now = datetime.now(UTC)
    return (
        db.query(Ticket)
        .filter(Ticket.status.in_(["open", "in_progress", "waiting_customer"]))
        .filter(Ticket.sla_due_at.is_not(None))
        .filter(Ticket.sla_due_at < now)
        .order_by(Ticket.sla_due_at.asc())
        .all()
    )


def create_ticket(db: Session, payload: TicketCreate) -> Ticket:
    customer = None
    if payload.customer_id:
        customer = get_or_create_customer(db, payload.customer_id)
    ticket = Ticket(
        customer_id=customer.id if customer else None,
        status="open",
        priority=payload.priority,
        intent=payload.intent,
        subject=payload.subject[:255],
        message_text=payload.message_text,
        suggested_reply=payload.suggested_reply,
        sla_due_at=calculate_sla_due(payload.priority),
        escalated=payload.escalated,
    )
    db.add(ticket)
    db.flush()
    db.add(TicketEvent(ticket_id=ticket.id, event_type="created", payload=payload.model_dump()))
    if payload.suggested_reply:
        db.add(AISuggestion(ticket_id=ticket.id, suggestion_text=payload.suggested_reply))
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, ticket_id: int, payload: TicketUpdate) -> Ticket:
    ticket = get_ticket_or_404(db, ticket_id)
    changes = payload.model_dump(exclude_unset=True)
    for field in ["status", "priority", "assigned_to", "suggested_reply"]:
        if field in changes and changes[field] is not None:
            setattr(ticket, field, changes[field])
    if "priority" in changes and changes["priority"] is not None:
        ticket.sla_due_at = calculate_sla_due(changes["priority"], ticket.created_at)
    if payload.ai_suggestion_status:
        suggestion = ticket.suggestions[-1] if ticket.suggestions else None
        if suggestion:
            suggestion.status = payload.ai_suggestion_status
            suggestion.final_human_reply = payload.final_human_reply
    db.add(TicketEvent(ticket_id=ticket.id, event_type="updated", payload=changes))
    db.commit()
    db.refresh(ticket)
    return ticket


def resolve_ticket(db: Session, ticket_id: int, payload: TicketResolve) -> Ticket:
    ticket = get_ticket_or_404(db, ticket_id)
    ticket.status = "resolved"
    ticket.resolved_at = datetime.now(UTC)
    if payload.final_reply:
        ticket.suggested_reply = payload.final_reply
    suggestion = ticket.suggestions[-1] if ticket.suggestions else None
    if suggestion and payload.ai_suggestion_status:
        suggestion.status = payload.ai_suggestion_status
        suggestion.final_human_reply = payload.final_reply
    if payload.feedback_rating is not None or payload.feedback_comment:
        db.add(
            Feedback(
                ticket_id=ticket.id,
                customer_id=ticket.customer_id,
                rating=payload.feedback_rating,
                comment=payload.feedback_comment,
            )
        )
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            event_type="resolved",
            payload=payload.model_dump(exclude_none=True),
        )
    )
    feedback_payload = {
        "ticket_id": ticket.id,
        "customer_id": ticket.customer_id,
        "telegram_chat_id": ticket.customer.telegram_user_id if ticket.customer else None,
        "status": ticket.status,
        "rating": payload.feedback_rating,
        "comment": payload.feedback_comment,
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
    }
    emit_n8n_event(db, "feedback", feedback_payload, ticket_id=ticket.id)
    if payload.feedback_rating is not None and payload.feedback_rating <= 2:
        emit_n8n_event(db, "negative_feedback", feedback_payload, ticket_id=ticket.id)
    db.commit()
    db.refresh(ticket)
    return ticket
