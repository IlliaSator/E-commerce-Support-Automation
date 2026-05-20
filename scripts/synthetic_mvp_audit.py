from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "n8n" / "workflows" / "techgear_automation_canvas_v2_workflow.json"

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-local-only")
ADMIN_HEADERS = {"X-Admin-API-Key": ADMIN_API_KEY}

REQUIRED_AGENT_TOOLS = {
    "Order Status Tool",
    "Product Catalog Tool",
    "Knowledge RAG Tool",
    "Ticket Detail Tool",
    "Open Tickets Tool",
    "SLA Policy Tool",
    "Analytics Summary Tool",
    "Recent Escalations Tool",
    "AI Evaluate Message Tool",
    "AI Draft Reply Tool",
    "Ticket Risk Tool",
    "Policy Think Tool",
    "SLA Calculator Tool",
    "Create Review Ticket Tool",
    "Manager Resolution Tool",
}

REQUIRED_POSTGRES_NODES = {
    "Postgres Memory",
    "Postgres AI Interaction Audit",
    "Postgres Support Event Audit",
    "Postgres Ticket State Snapshot",
    "Postgres SLA Breach Snapshot",
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


class Audit:
    def __init__(self) -> None:
        self.results: list[CheckResult] = []

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        self.results.append(CheckResult(name=name, ok=condition, detail=detail))

    def require(self, name: str, condition: bool, detail: str = "") -> None:
        self.check(name, condition, detail)
        if not condition:
            raise AssertionError(f"{name}: {detail}")

    def print_summary(self) -> None:
        for result in self.results:
            status = "PASS" if result.ok else "FAIL"
            suffix = f" - {result.detail}" if result.detail else ""
            print(f"[{status}] {result.name}{suffix}")
        passed = sum(1 for result in self.results if result.ok)
        print(f"\nSynthetic audit: {passed}/{len(self.results)} checks passed")


def request_json(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    response = client.request(method, f"{BACKEND_URL}{path}", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def support_message(client: httpx.Client, message: str, customer_id: str) -> dict[str, Any]:
    return request_json(
        client,
        "POST",
        "/support/message",
        payload={
            "customer_id": customer_id,
            "channel": "synthetic",
            "message_text": message,
            "metadata": {"synthetic_audit": True},
        },
    )


def assert_no_phrase(text: str, forbidden_phrases: set[str]) -> bool:
    lowered = text.lower()
    return not any(phrase in lowered for phrase in forbidden_phrases)


def audit_backend_flows(audit: Audit, client: httpx.Client) -> int:
    run_id = uuid4().hex[:10]

    order = support_message(client, "Where is my order 10042?", f"synthetic-order-{run_id}")
    audit.require("order status auto-resolves", order["auto_resolved"] is True, order["reply_text"])
    audit.require("order status is grounded", "10042" in order["reply_text"], order["reply_text"])

    missing_order_id = support_message(
        client,
        "Has my order been shipped?",
        f"synthetic-missing-order-{run_id}",
    )
    audit.require(
        "missing order id asks clarification",
        missing_order_id["suggested_next_action"] == "ask_for_order_id"
        and missing_order_id["ticket_id"] is None,
        missing_order_id["reply_text"],
    )

    unknown_order = support_message(client, "Where is my order 99999?", f"synthetic-unknown-order-{run_id}")
    audit.require(
        "nonexistent order creates ticket",
        unknown_order["auto_resolved"] is False and unknown_order["ticket_id"] is not None,
        unknown_order["reply_text"],
    )

    faq = support_message(client, "How long does delivery take?", f"synthetic-faq-{run_id}")
    audit.require(
        "FAQ answer is retrieval grounded",
        faq["auto_resolved"] is True and len(faq["retrieved_sources"]) > 0,
        faq["reply_text"],
    )

    product = support_message(client, "Do you have iPhone 15 case?", f"synthetic-product-{run_id}")
    audit.require(
        "product availability uses catalog",
        product["auto_resolved"] is True and "stock" in product["reply_text"].lower(),
        product["reply_text"],
    )

    complaint = support_message(client, "My order arrived broken", f"synthetic-complaint-{run_id}")
    audit.require(
        "complaint escalates",
        complaint["ticket_id"] is not None and complaint["escalation"] is True,
        complaint["reply_text"],
    )

    refund = support_message(
        client,
        "Can I get my money back right now?",
        f"synthetic-refund-{run_id}",
    )
    audit.require(
        "refund demand requires human review",
        refund["ticket_id"] is not None and refund["auto_resolved"] is False,
        refund["reply_text"],
    )
    audit.require(
        "refund is not promised",
        assert_no_phrase(
            refund["reply_text"],
            {"refund approved", "refund has been issued", "we guarantee a refund"},
        ),
        refund["reply_text"],
    )

    human = support_message(client, "I need a human manager", f"synthetic-human-{run_id}")
    audit.require(
        "human manager request escalates",
        human["ticket_id"] is not None and human["escalation"] is True,
        human["reply_text"],
    )

    unknown = support_message(client, "asdfghjkl", f"synthetic-unknown-{run_id}")
    audit.require(
        "unknown low-confidence message creates ticket",
        unknown["ticket_id"] is not None and unknown["auto_resolved"] is False,
        unknown["reply_text"],
    )

    return int(complaint["ticket_id"])


def audit_backend_tool_endpoints(audit: Audit, client: httpx.Client, ticket_id: int) -> int:
    order = request_json(client, "GET", "/orders/10042", headers=ADMIN_HEADERS)
    audit.require("order tool endpoint works", order["order_id"] == "10042")

    products = request_json(client, "GET", "/products/search?q=iPhone%2015%20case")
    audit.require("product tool endpoint works", len(products) > 0)

    knowledge = request_json(
        client,
        "POST",
        "/knowledge/answer",
        payload={"question": "How long does delivery take?", "language": "en"},
    )
    audit.require("knowledge tool endpoint works", knowledge["confidence"] >= 0.35)

    ticket_detail = request_json(client, "GET", f"/tickets/{ticket_id}/detail", headers=ADMIN_HEADERS)
    audit.require("ticket detail tool endpoint works", ticket_detail["ticket"]["id"] == ticket_id)

    open_tickets = request_json(client, "GET", "/tickets/open?older_than_minutes=0", headers=ADMIN_HEADERS)
    audit.require("open tickets tool endpoint works", isinstance(open_tickets, list))

    sla = request_json(client, "GET", "/analytics/sla-breaches", headers=ADMIN_HEADERS)
    audit.require("SLA policy tool endpoint works", "breaches" in sla)

    summary = request_json(client, "GET", "/analytics/summary", headers=ADMIN_HEADERS)
    audit.require("analytics summary tool endpoint works", "total_messages" in summary)

    escalations = request_json(client, "GET", "/analytics/recent-escalations?limit=5", headers=ADMIN_HEADERS)
    audit.require("recent escalations tool endpoint works", isinstance(escalations, list))

    evaluation = request_json(
        client,
        "POST",
        "/ai/evaluate-message",
        payload={"message_text": "My order arrived broken"},
    )
    audit.require(
        "AI evaluate tool endpoint works",
        evaluation["intent"] == "complaint" and evaluation["should_escalate"] is True,
    )

    draft = request_json(
        client,
        "POST",
        "/ai/draft-reply",
        payload={
            "customer_message": "How long does delivery take?",
            "context": "Standard delivery: 2-5 business days.",
            "intent": "delivery_question",
        },
    )
    audit.require("AI draft tool endpoint works", bool(draft["reply"]))

    created = request_json(
        client,
        "POST",
        "/tickets",
        headers=ADMIN_HEADERS,
        payload={
            "customer_id": "synthetic-tooling",
            "intent": "unknown",
            "priority": "normal",
            "subject": "Synthetic review ticket",
            "message_text": "Synthetic n8n tool audit ticket",
            "suggested_reply": "Manager should review this synthetic ticket.",
            "escalated": False,
        },
    )
    audit.require("create review ticket tool endpoint works", created["id"] > 0)

    resolved = request_json(
        client,
        "POST",
        f"/tickets/{created['id']}/resolve",
        headers=ADMIN_HEADERS,
        payload={
            "final_reply": "Synthetic audit resolved.",
            "ai_suggestion_status": "accepted",
            "feedback_rating": 5,
            "feedback_comment": "Synthetic audit feedback.",
        },
    )
    audit.require("manager resolution tool endpoint works", resolved["status"] == "resolved")

    return int(created["id"])


def audit_workflow(audit: Audit) -> None:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    nodes = {node["name"]: node for node in workflow["nodes"]}
    connections = workflow.get("connections", {})

    missing_tools = sorted(REQUIRED_AGENT_TOOLS - set(nodes))
    audit.require("all required AI tools exist", not missing_tools, ", ".join(missing_tools))

    missing_postgres = sorted(REQUIRED_POSTGRES_NODES - set(nodes))
    audit.require("Postgres memory and audit nodes exist", not missing_postgres, ", ".join(missing_postgres))

    connected_tools = {name for name, connection in connections.items() if "ai_tool" in connection}
    missing_connections = sorted(REQUIRED_AGENT_TOOLS - connected_tools)
    audit.require("all AI tools are connected to AI agent", not missing_connections, ", ".join(missing_connections))

    for name in ["Support LLM Model", "Postgres Memory", "Structured Output Parser"]:
        audit.require(f"{name} exists", name in nodes)

    audit.require(
        "LLM model is connected to AI agent",
        "ai_languageModel" in connections.get("Support LLM Model", {}),
    )
    audit.require(
        "Postgres memory is connected to AI agent",
        "ai_memory" in connections.get("Postgres Memory", {}),
    )
    audit.require(
        "structured parser is connected to AI agent",
        "ai_outputParser" in connections.get("Structured Output Parser", {}),
    )

    optional_external_nodes = [
        name
        for name, node in nodes.items()
        if any(token in name.lower() for token in ("google", "supabase", "telegram", "openai"))
        or "lmChatOpenAi" in node.get("type", "")
    ]
    audit.check(
        "external integrations remain optional placeholders",
        bool(optional_external_nodes),
        f"{len(optional_external_nodes)} optional external nodes documented",
    )

    cluster_names = (
        REQUIRED_AGENT_TOOLS
        | {
            "AI agent",
            "Support LLM Model",
            "Postgres Memory",
            "Structured Output Parser",
            "AI Response Check",
            "Build AI Agent Review Note",
            "Tool Boundary Comment",
            "Agent Tooling Boundary",
            "Controlled Mutation Tools",
            "10 AI Agent Orchestration: model, memory, backend tools, policy-safe drafting",
            "AI Agent Safety Contract",
            "Agent Guardrail Comment",
        }
    )
    cluster = [nodes[name] for name in cluster_names if name in nodes]
    overlap_pairs = find_approximate_overlaps(cluster)
    audit.require("AI tool layout has no approximate node overlaps", not overlap_pairs, str(overlap_pairs[:5]))


def find_approximate_overlaps(nodes: list[dict[str, Any]]) -> list[tuple[str, str]]:
    def box(node: dict[str, Any]) -> tuple[int, int, int, int]:
        x, y = node["position"]
        if node["type"] == "n8n-nodes-base.stickyNote":
            width = int(node.get("parameters", {}).get("width", 380))
            height = int(node.get("parameters", {}).get("height", 160))
        else:
            width = 260
            height = 120
        return x, y, x + width, y + height

    overlaps: list[tuple[str, str]] = []
    for index, left in enumerate(nodes):
        left_box = box(left)
        for right in nodes[index + 1 :]:
            right_box = box(right)
            if boxes_overlap(left_box, right_box):
                overlaps.append((left["name"], right["name"]))
    return overlaps


def boxes_overlap(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> bool:
    return left[0] < right[2] and left[2] > right[0] and left[1] < right[3] and left[3] > right[1]


def main() -> int:
    audit = Audit()
    try:
        with httpx.Client(timeout=15) as client:
            health = request_json(client, "GET", "/health")
            audit.require("backend health", health.get("status") == "ok", str(health))
            complaint_ticket_id = audit_backend_flows(audit, client)
            audit_backend_tool_endpoints(audit, client, complaint_ticket_id)
        audit_workflow(audit)
    except Exception as exc:
        audit.check("synthetic audit completed", False, str(exc))
        audit.print_summary()
        return 1

    audit.check("synthetic audit completed", True)
    audit.print_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
