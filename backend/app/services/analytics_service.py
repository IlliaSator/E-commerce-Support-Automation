from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.models import AIInteraction, EscalationEvent, Feedback, SupportMessage, Ticket
from backend.app.services.ticket_service import list_sla_breaches
from sqlalchemy import func
from sqlalchemy.orm import Session


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def get_intent_distribution(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(AIInteraction.detected_intent, func.count(AIInteraction.id))
        .group_by(AIInteraction.detected_intent)
        .order_by(func.count(AIInteraction.id).desc())
        .all()
    )
    return [{"intent": intent, "count": count} for intent, count in rows]


def get_summary(db: Session) -> dict[str, Any]:
    total_messages = db.query(SupportMessage).count()
    auto_resolved = db.query(AIInteraction).filter(AIInteraction.auto_resolved.is_(True)).count()
    created_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status.in_(["open", "in_progress", "waiting_customer"])).count()
    complaints = db.query(Ticket).filter(Ticket.intent == "complaint").count()
    sla_breaches = len(list_sla_breaches(db))
    human_review = db.query(AIInteraction).filter(AIInteraction.ticket_created.is_(True)).count()
    avg_latency = db.query(func.avg(AIInteraction.latency_ms)).scalar() or 0
    return {
        "total_messages": total_messages,
        "auto_resolved_messages": auto_resolved,
        "created_tickets": created_tickets,
        "open_tickets": open_tickets,
        "complaints": complaints,
        "sla_breaches": sla_breaches,
        "average_response_time_minutes": round(float(avg_latency) / 60000, 4),
        "top_intents": get_intent_distribution(db)[:5],
        "ai_auto_resolution_rate": _rate(auto_resolved, total_messages),
        "human_review_rate": _rate(human_review, total_messages),
    }


def get_sla_breaches_payload(db: Session) -> dict[str, Any]:
    breaches = list_sla_breaches(db)
    now = datetime.now(UTC)
    return {
        "count": len(breaches),
        "breaches": [
            {
                "ticket_id": ticket.id,
                "priority": ticket.priority,
                "intent": ticket.intent,
                "status": ticket.status,
                "sla_due_at": ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
                "delay_minutes": int((now - ticket.sla_due_at).total_seconds() // 60)
                if ticket.sla_due_at
                else None,
                "message_text": ticket.message_text,
            }
            for ticket in breaches
        ],
    }


def get_auto_resolution_rate(db: Session) -> dict[str, Any]:
    total = db.query(SupportMessage).count()
    auto = db.query(AIInteraction).filter(AIInteraction.auto_resolved.is_(True)).count()
    return {"total_messages": total, "auto_resolved": auto, "rate": _rate(auto, total)}


def get_ai_metrics(db: Session) -> dict[str, Any]:
    total = db.query(AIInteraction).count()
    auto = db.query(AIInteraction).filter(AIInteraction.auto_resolved.is_(True)).count()
    review = db.query(AIInteraction).filter(AIInteraction.ticket_created.is_(True)).count()
    avg_latency = db.query(func.avg(AIInteraction.latency_ms)).scalar() or 0
    unsafe = sum(
        1
        for interaction in db.query(AIInteraction.guardrail_result).all()
        if isinstance(interaction[0], dict) and interaction[0].get("allowed") is False
    )
    suggestions = db.query(func.count(Feedback.id)).scalar() or 0
    escalations = db.query(EscalationEvent).count()
    return {
        "total_ai_interactions": total,
        "auto_resolution_rate": _rate(auto, total),
        "human_review_rate": _rate(review, total),
        "ai_suggestion_acceptance_rate": 0.0 if suggestions == 0 else None,
        "low_confidence_fallback_count": db.query(AIInteraction)
        .filter(AIInteraction.intent_confidence < 0.75)
        .count(),
        "average_ai_latency_ms": round(float(avg_latency), 2),
        "unsafe_answer_prevention_count": unsafe,
        "complaint_escalation_count": escalations,
        "retrieval_confidence_distribution": {
            "low": db.query(AIInteraction).filter(AIInteraction.retrieval_confidence < 0.35).count(),
            "medium": db.query(AIInteraction)
            .filter(AIInteraction.retrieval_confidence >= 0.35)
            .filter(AIInteraction.retrieval_confidence < 0.7)
            .count(),
            "high": db.query(AIInteraction).filter(AIInteraction.retrieval_confidence >= 0.7).count(),
        },
        "top_intents": get_intent_distribution(db),
    }


def _period_report(db: Session, days: int) -> dict[str, Any]:
    since = datetime.now(UTC) - timedelta(days=days)
    summary = get_summary(db)
    summary["period_days"] = days
    summary["messages_in_period"] = db.query(SupportMessage).filter(SupportMessage.created_at >= since).count()
    summary["tickets_in_period"] = db.query(Ticket).filter(Ticket.created_at >= since).count()
    return summary


def get_daily_report(db: Session) -> dict[str, Any]:
    return _period_report(db, 1)


def get_weekly_report(db: Session) -> dict[str, Any]:
    return _period_report(db, 7)
