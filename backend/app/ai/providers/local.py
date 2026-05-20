from typing import Any

from backend.app.ai.providers.base import AIProvider
from backend.app.ai.urgency import detect_negative_tone, detect_urgency


class LocalProvider(AIProvider):
    provider_name = "local"
    model_name = "local-mock"

    def generate_reply(self, context: str, customer_message: str, intent: str) -> str:
        if context:
            return context.strip()
        if intent == "return_refund":
            return (
                "I created a support ticket for your return/refund request. "
                "A manager will review it. Refunds are reviewed after item inspection."
            )
        return "I created a support ticket so a human manager can review your request."

    def summarize_ticket(self, ticket_messages: list[str]) -> str:
        joined = " ".join(ticket_messages)
        if len(joined) <= 240:
            return joined
        return joined[:237].rstrip() + "..."

    def classify_sentiment(self, message: str) -> dict[str, Any]:
        return {
            "negative": detect_negative_tone(message),
            "urgent": detect_urgency(message),
            "label": "negative" if detect_negative_tone(message) else "neutral",
        }

    def draft_manager_note(self, ticket: dict[str, Any]) -> str:
        return (
            f"Ticket #{ticket.get('id', 'new')} needs review. "
            f"Intent: {ticket.get('intent')}. Priority: {ticket.get('priority')}. "
            f"Customer message: {ticket.get('message_text', '')}"
        )

    def format_report_summary(self, metrics: dict[str, Any]) -> str:
        return (
            "Support report: "
            f"{metrics.get('total_messages', 0)} messages, "
            f"{metrics.get('created_tickets', 0)} tickets, "
            f"{metrics.get('open_tickets', 0)} open, "
            f"{metrics.get('sla_breaches', 0)} SLA breaches."
        )
