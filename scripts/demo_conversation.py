from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.db.session import SessionLocal, init_db
from backend.app.schemas.api import SupportMessageIn
from backend.app.services.support_service import handle_message

DEMO_MESSAGES = [
    "Where is my order 10042?",
    "Где мой заказ 10042?",
    "How long does delivery take?",
    "Хочу вернуть товар",
    "My order arrived broken",
    "Do you have iPhone 15 case?",
    "Позовите оператора",
    "Can I get my money back right now?",
    "What is your warranty policy?",
    "asdfghjkl",
]


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        for index, text in enumerate(DEMO_MESSAGES, start=1):
            result = handle_message(
                db,
                SupportMessageIn(
                    customer_id=f"demo-{index}",
                    channel="demo",
                    message_text=text,
                    metadata={"demo": True},
                ),
            )
            print("=" * 80)
            print(f"Input: {text}")
            print(f"Intent: {result.intent} ({result.confidence:.2f})")
            print(f"Sources: {[s.section for s in result.retrieved_sources]}")
            print(f"Guardrails: {result.guardrail_result.model_dump() if result.guardrail_result else None}")
            print(f"Reply: {result.reply_text}")
            print(f"Ticket: {result.ticket_id}")
            print(f"Escalation: {result.escalation}")
            print(f"Auto-resolved: {result.auto_resolved}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
