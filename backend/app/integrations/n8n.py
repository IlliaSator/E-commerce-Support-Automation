from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from backend.app.core.config import get_settings
from backend.app.models import EscalationEvent
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


WEBHOOK_ATTRS = {
    "escalation": "n8n_escalation_webhook_url",
    "report": "n8n_report_webhook_url",
    "feedback": "n8n_feedback_webhook_url",
    "logging": "n8n_logging_webhook_url",
    "negative_feedback": "n8n_negative_feedback_webhook_url",
}


def _post_webhook(url: str, payload: dict[str, Any]) -> tuple[bool, str | None]:
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return True, None
    except Exception as exc:
        return False, str(exc)


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
        delivered, error = _post_webhook(url, payload)
        if error:
            logger.warning("n8n webhook failed for %s: %s", event_type, error)
    else:
        error = "webhook_url_not_configured"
        logger.info("n8n webhook for %s is not configured; event logged locally", event_type)

    hub_url = settings.n8n_event_hub_webhook_url
    if hub_url:
        hub_payload = {
            "source": "backend",
            "event_type": event_type,
            "ticket_id": ticket_id,
            "emitted_at": datetime.now(UTC).isoformat(),
            **payload,
        }
        hub_delivered, hub_error = _post_webhook(hub_url, hub_payload)
        if hub_error:
            logger.warning("n8n event hub webhook failed for %s: %s", event_type, hub_error)
            db.add(
                EscalationEvent(
                    ticket_id=ticket_id,
                    reason=f"{event_type}_event_hub",
                    channel="n8n_event_hub",
                    payload=hub_payload,
                    delivered=hub_delivered,
                    error=hub_error,
                )
            )
            db.flush()

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
