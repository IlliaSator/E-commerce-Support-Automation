from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models import EscalationEvent

logger = logging.getLogger(__name__)


WEBHOOK_ATTRS = {
    "escalation": "n8n_escalation_webhook_url",
    "report": "n8n_report_webhook_url",
    "feedback": "n8n_feedback_webhook_url",
    "logging": "n8n_logging_webhook_url",
}


def emit_n8n_event(
    db: Session,
    event_type: str,
    payload: dict[str, Any],
    ticket_id: int | None = None,
) -> bool:
    settings = get_settings()
    url = getattr(settings, WEBHOOK_ATTRS.get(event_type, ""), None)
    delivered = False
    error: str | None = None

    if url:
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                delivered = True
        except Exception as exc:
            error = str(exc)
            logger.warning("n8n webhook failed for %s: %s", event_type, exc)
    else:
        error = "webhook_url_not_configured"
        logger.info("n8n webhook for %s is not configured; event logged locally", event_type)

    if event_type == "escalation" or error:
        db.add(
            EscalationEvent(
                ticket_id=ticket_id,
                reason=event_type,
                channel="n8n",
                payload=payload,
                delivered=delivered,
                error=error,
            )
        )
        db.flush()
    return delivered
