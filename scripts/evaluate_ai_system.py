from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.db.session import SessionLocal, init_db
from backend.app.schemas.api import SupportMessageIn
from backend.app.services.support_service import handle_message

GOLDEN = ROOT / "data" / "eval" / "golden_support_questions.csv"


def expected_auto(action: str) -> bool:
    return action == "auto_answer"


def main() -> None:
    init_db()
    db = SessionLocal()
    rows = list(csv.DictReader(GOLDEN.open(newline="", encoding="utf-8")))
    intent_correct = 0
    escalation_tp = escalation_fp = escalation_fn = 0
    auto_correct = 0
    fallback_correct = 0
    retrieval_hits = 0
    unsafe_prevented = 0

    try:
        for index, row in enumerate(rows, start=1):
            result = handle_message(
                db,
                SupportMessageIn(
                    customer_id=f"eval-{index}",
                    channel="evaluation",
                    message_text=row["customer_message"],
                    metadata={"evaluation": True},
                ),
            )
            if result.intent == row["expected_intent"]:
                intent_correct += 1
            expected_escalate = row["expected_should_escalate"].lower() == "true"
            if result.escalation and expected_escalate:
                escalation_tp += 1
            elif result.escalation and not expected_escalate:
                escalation_fp += 1
            elif not result.escalation and expected_escalate:
                escalation_fn += 1
            if result.auto_resolved == expected_auto(row["expected_action"]):
                auto_correct += 1
            if row["expected_action"] in {"create_ticket", "escalate"} and result.ticket_id:
                fallback_correct += 1
            expected_contains = row["expected_answer_contains"].lower()
            if expected_contains and expected_contains in result.reply_text.lower():
                retrieval_hits += 1
            if result.guardrail_result and not result.guardrail_result.allowed:
                unsafe_prevented += 1
    finally:
        db.close()

    total = len(rows)
    precision = escalation_tp / (escalation_tp + escalation_fp) if escalation_tp + escalation_fp else 0
    recall = escalation_tp / (escalation_tp + escalation_fn) if escalation_tp + escalation_fn else 0
    print(f"intent_accuracy={intent_correct / total:.3f}")
    print(f"escalation_precision={precision:.3f}")
    print(f"escalation_recall={recall:.3f}")
    print(f"auto_resolution_accuracy={auto_correct / total:.3f}")
    print(f"fallback_accuracy={fallback_correct / total:.3f}")
    print(f"retrieval_hit_rate={retrieval_hits / total:.3f}")
    print(f"unsafe_auto_replies_prevented={unsafe_prevented}")


if __name__ == "__main__":
    main()
