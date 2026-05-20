from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SupportMessageIn(BaseModel):
    customer_id: str
    channel: str = "telegram"
    message_text: str
    telegram_chat_id: str | None = None
    username: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedSource(BaseModel):
    title: str
    section: str
    source_file: str
    confidence: float
    content_preview: str


class GuardrailResult(BaseModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)
    requires_human: bool = False


class SupportMessageOut(BaseModel):
    intent: str
    confidence: float
    reply_text: str
    auto_resolved: bool
    ticket_id: int | None = None
    escalation: bool
    priority: str
    suggested_next_action: str
    retrieved_sources: list[RetrievedSource] = Field(default_factory=list)
    guardrail_result: GuardrailResult | None = None


class KnowledgeAnswerIn(BaseModel):
    question: str
    language: str | None = None


class KnowledgeAnswerOut(BaseModel):
    answer: str
    confidence: float
    sources: list[RetrievedSource]
    auto_answer_allowed: bool


class TicketCreate(BaseModel):
    customer_id: str | None = None
    intent: str = "unknown"
    priority: str = "normal"
    subject: str
    message_text: str
    suggested_reply: str | None = None
    escalated: bool = False


class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    suggested_reply: str | None = None
    ai_suggestion_status: str | None = None
    final_human_reply: str | None = None


class TicketResolve(BaseModel):
    final_reply: str | None = None
    ai_suggestion_status: str | None = Field(default=None, pattern="^(accepted|rejected|edited)$")
    feedback_rating: int | None = Field(default=None, ge=1, le=5)
    feedback_comment: str | None = None


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int | None
    status: str
    priority: str
    intent: str
    subject: str
    message_text: str
    suggested_reply: str | None
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    sla_due_at: datetime | None
    escalated: bool


class TicketDetailRead(BaseModel):
    ticket: TicketRead
    events: list[dict[str, Any]]
    ai_suggestions: list[dict[str, Any]]
    feedback: list[dict[str, Any]]


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    customer_name: str
    telegram_user_id: str | None
    email: str | None
    status: str
    items: list[dict[str, Any]]
    total_amount: float
    currency: str
    payment_status: str
    delivery_method: str
    carrier: str | None
    tracking_number: str | None
    eta_date: date | None
    created_at: datetime


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    name: str
    category: str
    brand: str | None
    price: float
    currency: str
    stock: int
    attributes: dict[str, Any]
    alternatives: list[str]


class AnalyticsSummary(BaseModel):
    total_messages: int
    auto_resolved_messages: int
    created_tickets: int
    open_tickets: int
    complaints: int
    sla_breaches: int
    average_response_time_minutes: float
    top_intents: list[dict[str, Any]]
    ai_auto_resolution_rate: float
    human_review_rate: float


class AIEvaluateMessageIn(BaseModel):
    message_text: str


class AIEvaluateMessageOut(BaseModel):
    intent: str
    confidence: float
    urgent: bool
    priority: str
    should_escalate: bool


class DraftReplyIn(BaseModel):
    customer_message: str
    context: str = ""
    intent: str = "unknown"


class DraftReplyOut(BaseModel):
    reply: str
    provider: str
    model_name: str


class TicketSummaryIn(BaseModel):
    messages: list[str]


class TicketSummaryOut(BaseModel):
    summary: str
