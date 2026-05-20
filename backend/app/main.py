from backend.app.core.security import require_admin_api_key
from backend.app.db.session import get_db, init_db
from backend.app.models import Order
from backend.app.schemas.api import (
    AIEvaluateMessageIn,
    AIEvaluateMessageOut,
    AnalyticsSummary,
    DraftReplyIn,
    DraftReplyOut,
    KnowledgeAnswerIn,
    KnowledgeAnswerOut,
    OrderRead,
    ProductRead,
    SupportMessageIn,
    SupportMessageOut,
    TicketCreate,
    TicketRead,
    TicketResolve,
    TicketSummaryIn,
    TicketSummaryOut,
    TicketUpdate,
)
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

app = FastAPI(
    title="E-commerce Support Automation",
    description="TechGear Store Applied AI support automation backend",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/support/message", response_model=SupportMessageOut)
def handle_support_message(payload: SupportMessageIn, db: Session = Depends(get_db)):
    from backend.app.services.support_service import handle_message

    return handle_message(db, payload)


@app.get("/orders/{order_id}", response_model=OrderRead, dependencies=[Depends(require_admin_api_key)])
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/products/search", response_model=list[ProductRead])
def search_products(q: str = Query(min_length=1), db: Session = Depends(get_db)):
    from backend.app.services.product_service import search_products as do_search

    return do_search(db, q)


@app.post("/knowledge/answer", response_model=KnowledgeAnswerOut)
def answer_knowledge(payload: KnowledgeAnswerIn, db: Session = Depends(get_db)):
    from backend.app.services.knowledge_service import answer_question

    return answer_question(db, payload.question, payload.language)


@app.get("/tickets", response_model=list[TicketRead], dependencies=[Depends(require_admin_api_key)])
def list_tickets(db: Session = Depends(get_db)):
    from backend.app.services.ticket_service import list_tickets as do_list

    return do_list(db)


@app.get("/tickets/open", response_model=list[TicketRead], dependencies=[Depends(require_admin_api_key)])
def open_tickets(db: Session = Depends(get_db)):
    from backend.app.services.ticket_service import list_open_tickets

    return list_open_tickets(db)


@app.get("/tickets/sla-breaches", response_model=list[TicketRead], dependencies=[Depends(require_admin_api_key)])
def ticket_sla_breaches(db: Session = Depends(get_db)):
    from backend.app.services.ticket_service import list_sla_breaches

    return list_sla_breaches(db)


@app.get("/tickets/{ticket_id}", response_model=TicketRead, dependencies=[Depends(require_admin_api_key)])
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    from backend.app.services.ticket_service import get_ticket_or_404

    return get_ticket_or_404(db, ticket_id)


@app.post("/tickets", response_model=TicketRead, dependencies=[Depends(require_admin_api_key)])
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    from backend.app.services.ticket_service import create_ticket

    return create_ticket(db, payload)


@app.patch("/tickets/{ticket_id}", response_model=TicketRead, dependencies=[Depends(require_admin_api_key)])
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    from backend.app.services.ticket_service import update_ticket

    return update_ticket(db, ticket_id, payload)


@app.post("/tickets/{ticket_id}/resolve", response_model=TicketRead, dependencies=[Depends(require_admin_api_key)])
def resolve_ticket(ticket_id: int, payload: TicketResolve, db: Session = Depends(get_db)):
    from backend.app.services.ticket_service import resolve_ticket

    return resolve_ticket(db, ticket_id, payload)


@app.get("/analytics/summary", response_model=AnalyticsSummary, dependencies=[Depends(require_admin_api_key)])
def analytics_summary(db: Session = Depends(get_db)):
    from backend.app.services.analytics_service import get_summary

    return get_summary(db)


@app.get("/analytics/daily", dependencies=[Depends(require_admin_api_key)])
def analytics_daily(db: Session = Depends(get_db)):
    from backend.app.services.analytics_service import get_daily_report

    return get_daily_report(db)


@app.get("/analytics/weekly", dependencies=[Depends(require_admin_api_key)])
def analytics_weekly(db: Session = Depends(get_db)):
    from backend.app.services.analytics_service import get_weekly_report

    return get_weekly_report(db)


@app.get("/analytics/intent-distribution", dependencies=[Depends(require_admin_api_key)])
def intent_distribution(db: Session = Depends(get_db)):
    from backend.app.services.analytics_service import get_intent_distribution

    return get_intent_distribution(db)


@app.get("/analytics/sla-breaches", dependencies=[Depends(require_admin_api_key)])
def analytics_sla_breaches(db: Session = Depends(get_db)):
    from backend.app.services.analytics_service import get_sla_breaches_payload

    return get_sla_breaches_payload(db)


@app.get("/analytics/auto-resolution-rate", dependencies=[Depends(require_admin_api_key)])
def analytics_auto_resolution_rate(db: Session = Depends(get_db)):
    from backend.app.services.analytics_service import get_auto_resolution_rate

    return get_auto_resolution_rate(db)


@app.get("/analytics/ai-metrics", dependencies=[Depends(require_admin_api_key)])
@app.get("/ai/metrics", dependencies=[Depends(require_admin_api_key)])
def ai_metrics(db: Session = Depends(get_db)):
    from backend.app.services.analytics_service import get_ai_metrics

    return get_ai_metrics(db)


@app.post("/ai/evaluate-message", response_model=AIEvaluateMessageOut)
def evaluate_message(payload: AIEvaluateMessageIn):
    from backend.app.ai.classifier import classify_message
    from backend.app.ai.urgency import detect_urgency, priority_for_intent

    result = classify_message(payload.message_text)
    urgent = detect_urgency(payload.message_text)
    priority = priority_for_intent(result.intent, urgent)
    return AIEvaluateMessageOut(
        intent=result.intent,
        confidence=result.confidence,
        urgent=urgent,
        priority=priority,
        should_escalate=urgent or result.intent in {"complaint", "human_agent"},
    )


@app.post("/ai/draft-reply", response_model=DraftReplyOut)
def draft_reply(payload: DraftReplyIn):
    from backend.app.ai.providers.factory import get_provider

    provider = get_provider()
    reply = provider.generate_reply(payload.context, payload.customer_message, payload.intent)
    return DraftReplyOut(reply=reply, provider=provider.provider_name, model_name=provider.model_name)


@app.post("/ai/summarize-ticket", response_model=TicketSummaryOut)
def summarize_ticket(payload: TicketSummaryIn):
    from backend.app.ai.providers.factory import get_provider

    provider = get_provider()
    return TicketSummaryOut(summary=provider.summarize_ticket(payload.messages))
