from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any

from sqlalchemy.orm import Session

from backend.app.ai.classifier import ClassificationResult, classify_message, extract_order_id
from backend.app.ai.guardrails import run_guardrails
from backend.app.ai.policy import (
    AUTO_REPLY_CONFIDENCE,
    AUTO_RESOLVABLE_INTENTS,
    LOW_CONFIDENCE_ESCALATION,
    PROMPT_TEMPLATE_VERSION,
    RETRIEVAL_CONFIDENCE,
)
from backend.app.ai.providers.factory import get_provider
from backend.app.ai.retrieval.service import retrieve_knowledge
from backend.app.ai.urgency import detect_language, detect_negative_tone, detect_urgency, priority_for_intent
from backend.app.integrations.n8n import emit_n8n_event
from backend.app.models import AIInteraction, AISuggestion, Order, Product, SupportMessage, Ticket, TicketEvent
from backend.app.schemas.api import GuardrailResult, RetrievedSource, SupportMessageIn, SupportMessageOut
from backend.app.services.customer_service import get_or_create_customer
from backend.app.services.product_service import search_products
from backend.app.services.sla_service import calculate_sla_due


def _ticket_subject(intent: str, message: str) -> str:
    clean = " ".join(message.split())
    return f"{intent.replace('_', ' ').title()}: {clean[:80]}"


def _format_order_reply(order: Order, language: str) -> str:
    items = ", ".join(f"{item['qty']} x {item['name']}" for item in order.items)
    eta = order.eta_date.isoformat() if order.eta_date else "not available yet"
    if language == "ru":
        status_map = {
            "pending": "ожидает оплаты",
            "paid": "оплачен",
            "packed": "упакован",
            "shipped": "отправлен",
            "delivered": "доставлен",
            "cancelled": "отменен",
            "returned": "возвращен",
            "refund_requested": "ожидает рассмотрения возврата",
        }
        return (
            f"Заказ {order.order_id}: статус - {status_map.get(order.status, order.status)}. "
            f"Товары: {items}. Перевозчик: {order.carrier or 'пока не назначен'}. "
            f"Трек-номер: {order.tracking_number or 'пока нет'}. ETA: {eta}."
        )
    return (
        f"Order {order.order_id}: status is {order.status}. Items: {items}. "
        f"Carrier: {order.carrier or 'not assigned yet'}. "
        f"Tracking number: {order.tracking_number or 'not available yet'}. ETA: {eta}."
    )


def _format_product_reply(products: list[Product], language: str) -> str:
    lines: list[str] = []
    for product in products:
        stock = "in stock" if product.stock > 0 else "out of stock"
        if language == "ru":
            stock = "в наличии" if product.stock > 0 else "нет в наличии"
            lines.append(
                f"{product.name} - {product.price:.2f} {product.currency}, {stock} ({product.stock} шт.)."
            )
        else:
            lines.append(
                f"{product.name} - {product.price:.2f} {product.currency}, {stock} ({product.stock} units)."
            )
        if product.stock <= 0 and product.alternatives:
            lines.append(
                ("Alternatives: " if language == "en" else "Альтернативы: ")
                + ", ".join(product.alternatives)
            )
    prefix = "Found matching products:" if language == "en" else "Нашел подходящие товары:"
    return prefix + "\n" + "\n".join(lines)


def _fallback_ticket_reply(ticket: Ticket, language: str, escalated: bool = False) -> str:
    if language == "ru":
        if escalated:
            return f"Мы создали тикет #{ticket.id} и передали вопрос менеджеру."
        return f"Мы создали тикет #{ticket.id}. Менеджер проверит вопрос и ответит."
    if escalated:
        return f"We created ticket #{ticket.id} and escalated it to a human manager."
    return f"We created ticket #{ticket.id}. A support manager will review it."


def _create_ticket(
    db: Session,
    *,
    customer_id: int | None,
    intent: str,
    priority: str,
    message_text: str,
    suggested_reply: str,
    escalated: bool,
) -> Ticket:
    ticket = Ticket(
        customer_id=customer_id,
        status="open",
        priority=priority,
        intent=intent,
        subject=_ticket_subject(intent, message_text),
        message_text=message_text,
        suggested_reply=suggested_reply,
        sla_due_at=calculate_sla_due(priority),
        escalated=escalated,
    )
    db.add(ticket)
    db.flush()
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            event_type="created",
            payload={"intent": intent, "priority": priority, "escalated": escalated},
        )
    )
    db.add(AISuggestion(ticket_id=ticket.id, suggestion_text=suggested_reply))
    return ticket


def _source_models(sources: list[Any]) -> list[RetrievedSource]:
    return [
        RetrievedSource(
            title=item.title,
            section=item.section,
            source_file=item.source_file,
            confidence=item.confidence,
            content_preview=item.content[:220],
        )
        for item in sources
    ]


def _log_ai_interaction(
    db: Session,
    *,
    support_message_id: int,
    classification: ClassificationResult,
    retrieval_query: str | None,
    retrieved_sources: list[dict[str, Any]],
    retrieval_confidence: float | None,
    generated_reply: str,
    final_reply: str,
    auto_resolved: bool,
    ticket_created: bool,
    escalation: bool,
    latency_ms: int,
    guardrail_result: dict[str, Any],
) -> None:
    provider = get_provider()
    db.add(
        AIInteraction(
            support_message_id=support_message_id,
            detected_intent=classification.intent,
            intent_confidence=classification.confidence,
            retrieval_query=retrieval_query,
            retrieved_source_sections=retrieved_sources,
            retrieval_confidence=retrieval_confidence,
            model_provider=provider.provider_name,
            model_name=provider.model_name,
            prompt_template_version=PROMPT_TEMPLATE_VERSION,
            generated_reply=generated_reply,
            final_reply_sent=final_reply,
            auto_resolved=auto_resolved,
            ticket_created=ticket_created,
            escalation=escalation,
            latency_ms=latency_ms,
            estimated_cost=0.0 if provider.provider_name == "local" else None,
            guardrail_result=guardrail_result,
        )
    )


def _should_escalate(intent: str, confidence: float, urgent: bool, human_requested: bool) -> bool:
    return (
        intent in {"complaint", "human_agent"}
        or urgent
        or human_requested
        or confidence < LOW_CONFIDENCE_ESCALATION
    )


def handle_message(db: Session, payload: SupportMessageIn) -> SupportMessageOut:
    start = time.perf_counter()
    language = detect_language(payload.message_text)
    customer = get_or_create_customer(
        db,
        payload.customer_id,
        telegram_user_id=payload.telegram_chat_id,
        username=payload.username,
        language=language,
    )
    support_message = SupportMessage(
        customer_id=customer.id,
        channel=payload.channel,
        message_text=payload.message_text,
        telegram_chat_id=payload.telegram_chat_id,
        username=payload.username,
        metadata_json=payload.metadata,
    )
    db.add(support_message)
    db.flush()

    classification = classify_message(payload.message_text)
    intent = classification.intent
    urgent = detect_urgency(payload.message_text)
    negative = detect_negative_tone(payload.message_text)
    human_requested = intent == "human_agent"
    priority = priority_for_intent(intent, urgent, negative)
    escalated = _should_escalate(intent, classification.confidence, urgent, human_requested)
    provider = get_provider()

    reply = ""
    generated_reply = ""
    ticket: Ticket | None = None
    auto_resolved = False
    retrieved_sources: list[RetrievedSource] = []
    retrieval_confidence: float | None = None
    retrieval_query: str | None = None
    has_verified_order = False
    has_verified_product = False

    if intent == "order_status":
        order_id = extract_order_id(payload.message_text)
        if not order_id:
            reply = (
                "Please send your order number so I can check the status."
                if language == "en"
                else "Пожалуйста, отправьте номер заказа, чтобы я проверил статус."
            )
            generated_reply = reply
        else:
            order = db.query(Order).filter(Order.order_id == order_id).one_or_none()
            if order:
                has_verified_order = True
                reply = _format_order_reply(order, language)
                generated_reply = reply
                auto_resolved = classification.confidence >= AUTO_REPLY_CONFIDENCE
            else:
                suggested = (
                    f"Customer asked about missing order {order_id}. Verify order history manually."
                )
                ticket = _create_ticket(
                    db,
                    customer_id=customer.id,
                    intent=intent,
                    priority="normal",
                    message_text=payload.message_text,
                    suggested_reply=suggested,
                    escalated=False,
                )
                reply = _fallback_ticket_reply(ticket, language)
                generated_reply = suggested
    elif intent in {"delivery_question", "payment_question", "warranty"}:
        retrieval_query = payload.message_text
        retrieval = retrieve_knowledge(db, payload.message_text, language=language, top_k=3)
        retrieval_confidence = retrieval.confidence
        retrieved_sources = _source_models(retrieval.sources)
        if classification.confidence >= AUTO_REPLY_CONFIDENCE and retrieval.confidence >= RETRIEVAL_CONFIDENCE:
            generated_reply = provider.generate_reply(retrieval.answer, payload.message_text, intent)
            reply = generated_reply
            auto_resolved = True
        else:
            suggested = provider.generate_reply(retrieval.answer, payload.message_text, intent)
            ticket = _create_ticket(
                db,
                customer_id=customer.id,
                intent=intent,
                priority="normal",
                message_text=payload.message_text,
                suggested_reply=suggested,
                escalated=False,
            )
            reply = _fallback_ticket_reply(ticket, language)
            generated_reply = suggested
    elif intent == "product_availability":
        products = search_products(db, payload.message_text)
        if products and classification.confidence >= AUTO_REPLY_CONFIDENCE:
            has_verified_product = True
            reply = _format_product_reply(products, language)
            generated_reply = reply
            auto_resolved = True
        else:
            suggested = "No confident product match found. Ask a clarifying question or check catalog manually."
            ticket = _create_ticket(
                db,
                customer_id=customer.id,
                intent=intent,
                priority="normal",
                message_text=payload.message_text,
                suggested_reply=suggested,
                escalated=False,
            )
            reply = _fallback_ticket_reply(ticket, language)
            generated_reply = suggested
    else:
        if intent == "return_refund":
            retrieval_query = payload.message_text
            retrieval = retrieve_knowledge(db, payload.message_text, language=language, top_k=2)
            retrieval_confidence = retrieval.confidence
            retrieved_sources = _source_models(retrieval.sources)
            policy = retrieval.answer or (
                "Returns are available within 14 days. Refunds are reviewed after inspection."
            )
            suggested = provider.generate_reply(policy, payload.message_text, intent)
        elif intent == "complaint":
            suggested = (
                "Apologize, request order number and photos if relevant, and review the case urgently."
            )
        elif intent == "human_agent":
            suggested = "Customer requested a human manager. Assign a manager and reply manually."
        elif intent == "spam":
            suggested = "Potential spam. Review only if repeated."
            priority = "low"
            escalated = False
        else:
            suggested = "Low-confidence or unknown request. Ask a human manager to review."
        ticket = _create_ticket(
            db,
            customer_id=customer.id,
            intent=intent,
            priority=priority,
            message_text=payload.message_text,
            suggested_reply=suggested,
            escalated=escalated,
        )
        generated_reply = suggested
        if intent == "return_refund":
            reply = (
                f"We created ticket #{ticket.id} for your return/refund request. "
                "Returns are possible within 14 days after receiving the order. "
                "Refunds are reviewed after the returned item is inspected."
                if language == "en"
                else f"Мы создали тикет #{ticket.id} по возврату. "
                "Возврат возможен в течение 14 дней после получения заказа. "
                "Возврат денег рассматривается после проверки товара."
            )
        else:
            reply = _fallback_ticket_reply(ticket, language, escalated=escalated)

    guardrail = run_guardrails(
        customer_message=payload.message_text,
        proposed_reply=reply,
        intent=intent,
        retrieval_confidence=retrieval_confidence,
        has_verified_order=has_verified_order,
        has_verified_product=has_verified_product,
        human_requested=human_requested,
    )

    if auto_resolved and (not guardrail.allowed or intent not in AUTO_RESOLVABLE_INTENTS):
        auto_resolved = False
        if not ticket:
            ticket = _create_ticket(
                db,
                customer_id=customer.id,
                intent=intent,
                priority=priority,
                message_text=payload.message_text,
                suggested_reply=generated_reply,
                escalated=guardrail.requires_human or escalated,
            )
        reply = _fallback_ticket_reply(ticket, language, escalated=ticket.escalated)
        escalated = ticket.escalated

    if ticket and escalated:
        emit_n8n_event(
            db,
            "escalation",
            {
                "ticket_id": ticket.id,
                "priority": ticket.priority,
                "intent": ticket.intent,
                "message_text": ticket.message_text,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            ticket_id=ticket.id,
        )

    if ticket:
        emit_n8n_event(
            db,
            "logging",
            {
                "event": "ticket_created",
                "ticket_id": ticket.id,
                "intent": ticket.intent,
                "priority": ticket.priority,
            },
            ticket_id=ticket.id,
        )

    latency_ms = int((time.perf_counter() - start) * 1000)
    _log_ai_interaction(
        db,
        support_message_id=support_message.id,
        classification=classification,
        retrieval_query=retrieval_query,
        retrieved_sources=[source.model_dump() for source in retrieved_sources],
        retrieval_confidence=retrieval_confidence,
        generated_reply=generated_reply,
        final_reply=reply,
        auto_resolved=auto_resolved,
        ticket_created=ticket is not None,
        escalation=escalated,
        latency_ms=latency_ms,
        guardrail_result=guardrail.as_dict(),
    )
    db.commit()

    suggested_action = "auto_replied" if auto_resolved else "human_review"
    if intent == "order_status" and not extract_order_id(payload.message_text) and not ticket:
        suggested_action = "ask_for_order_id"

    return SupportMessageOut(
        intent=intent,
        confidence=round(classification.confidence, 4),
        reply_text=reply,
        auto_resolved=auto_resolved,
        ticket_id=ticket.id if ticket else None,
        escalation=escalated,
        priority=ticket.priority if ticket else priority,
        suggested_next_action=suggested_action,
        retrieved_sources=retrieved_sources,
        guardrail_result=GuardrailResult(**guardrail.as_dict()),
    )
