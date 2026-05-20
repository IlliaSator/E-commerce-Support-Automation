from __future__ import annotations

import os
from typing import Any

import httpx
import pandas as pd
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-local-only")


def _headers() -> dict[str, str]:
    return {"X-Admin-API-Key": ADMIN_API_KEY}


@st.cache_data(ttl=15)
def get_json(path: str) -> Any:
    with httpx.Client(timeout=8.0) as client:
        response = client.get(f"{BACKEND_URL}{path}", headers=_headers())
        response.raise_for_status()
        return response.json()


def metric_row(summary: dict[str, Any]) -> None:
    cols = st.columns(7)
    cols[0].metric("Messages", summary["total_messages"])
    cols[1].metric("Auto-resolved", summary["auto_resolved_messages"])
    cols[2].metric("Tickets", summary["created_tickets"])
    cols[3].metric("Open", summary["open_tickets"])
    cols[4].metric("Complaints", summary["complaints"])
    cols[5].metric("SLA breaches", summary["sla_breaches"])
    cols[6].metric("Auto-rate", f"{summary['ai_auto_resolution_rate'] * 100:.1f}%")


def dataframe(data: list[dict[str, Any]], key: str) -> None:
    if not data:
        st.info("No records.")
        return
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True, key=key)


def system_map(summary: dict[str, Any], ai_metrics: dict[str, Any]) -> None:
    auto_rate = summary["ai_auto_resolution_rate"] * 100
    human_rate = ai_metrics["human_review_rate"] * 100
    st.markdown(
        f"""
        <style>
        .system-panel {{
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 18px 20px;
            margin: 4px 0 18px 0;
            background: #f8fafc;
        }}
        .system-head {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 16px;
        }}
        .system-head h2 {{
            font-size: 1.25rem;
            margin: 0;
            color: #102a43;
        }}
        .system-head p {{
            margin: 4px 0 0 0;
            color: #52606d;
        }}
        .status-pill {{
            border: 1px solid #7cc4a1;
            background: #e3fcef;
            color: #014d40;
            padding: 6px 10px;
            border-radius: 999px;
            white-space: nowrap;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .flow-grid {{
            display: grid;
            grid-template-columns: 1fr 28px 1.3fr 28px 1fr;
            gap: 8px;
            align-items: stretch;
        }}
        .node {{
            border: 1px solid #bcccdc;
            background: white;
            border-radius: 8px;
            padding: 12px;
            min-height: 96px;
        }}
        .node strong {{
            display: block;
            color: #102a43;
            margin-bottom: 6px;
        }}
        .node span {{
            display: block;
            color: #52606d;
            font-size: 0.88rem;
            line-height: 1.35;
        }}
        .arrow {{
            color: #627d98;
            font-weight: 700;
            align-self: center;
            text-align: center;
            font-size: 1.2rem;
        }}
        .automation-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
            margin-top: 8px;
        }}
        .evidence-grid {{
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 8px;
            margin-top: 12px;
        }}
        .evidence {{
            border: 1px solid #d9e2ec;
            background: white;
            border-radius: 8px;
            padding: 10px 12px;
        }}
        .evidence strong {{
            display: block;
            color: #102a43;
            font-size: 1rem;
        }}
        .evidence span {{
            color: #52606d;
            font-size: 0.78rem;
        }}
        </style>
        <div class="system-panel">
            <div class="system-head">
                <div>
                    <h2>TechGear Store Applied AI Support Automation</h2>
                    <p>One connected local MVP: Telegram intake, FastAPI orchestration, RAG, guardrails, tickets, SLA, n8n automations, and analytics.</p>
                </div>
                <div class="status-pill">Docker stack online</div>
            </div>
            <div class="flow-grid">
                <div class="node">
                    <strong>Telegram Bot</strong>
                    <span>Customer EN/RU messages, order commands, manager-only admin commands.</span>
                </div>
                <div class="arrow">&rarr;</div>
                <div class="node">
                    <strong>FastAPI AI Orchestrator</strong>
                    <span>Intent rules, optional sklearn classifier, order/product lookup, local RAG, guardrails, ticket policy.</span>
                </div>
                <div class="arrow">&rarr;</div>
                <div class="node">
                    <strong>PostgreSQL System of Record</strong>
                    <span>Orders, products, messages, tickets, AI interactions, feedback, SLA, escalation events.</span>
                </div>
            </div>
            <div class="automation-grid">
                <div class="node">
                    <strong>n8n Automation Bus</strong>
                    <span>Escalations, SLA checks, reports, unresolved follow-up, feedback, Google Sheets/mock CRM logging.</span>
                </div>
                <div class="node">
                    <strong>Manager Review Loop</strong>
                    <span>High-risk, low-confidence, complaint, refund, and human-agent cases require review before final handling.</span>
                </div>
                <div class="node">
                    <strong>Streamlit Ops Dashboard</strong>
                    <span>Business metrics, open tickets, SLA breaches, recent escalations, AI quality and retrieval metrics.</span>
                </div>
            </div>
            <div class="evidence-grid">
                <div class="evidence"><strong>{summary["total_messages"]}</strong><span>messages logged</span></div>
                <div class="evidence"><strong>{summary["created_tickets"]}</strong><span>tickets created</span></div>
                <div class="evidence"><strong>{summary["sla_breaches"]}</strong><span>SLA breaches</span></div>
                <div class="evidence"><strong>{auto_rate:.1f}%</strong><span>auto-resolution rate</span></div>
                <div class="evidence"><strong>{human_rate:.1f}%</strong><span>human-review rate</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="TechGear Support Ops", layout="wide")
st.title("TechGear Support Ops")

try:
    summary = get_json("/analytics/summary")
    ai_metrics = get_json("/ai/metrics")
    tickets = get_json("/tickets/open")
    breaches = get_json("/analytics/sla-breaches")
    intents = get_json("/analytics/intent-distribution")
    escalations = get_json("/analytics/recent-escalations")
except Exception as exc:
    st.error(f"Backend unavailable: {exc}")
    st.stop()

system_map(summary, ai_metrics)
metric_row(summary)

tab_overview, tab_tickets, tab_sla, tab_escalations, tab_ai, tab_detail = st.tabs(
    ["Overview", "Open Tickets", "SLA Breaches", "Escalations", "AI Metrics", "Ticket Detail"]
)

with tab_overview:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Intent Distribution")
        if intents:
            intent_df = pd.DataFrame(intents)
            st.bar_chart(intent_df.set_index("intent"))
        else:
            st.info("No intent data yet.")
    with right:
        st.subheader("Daily Summary")
        st.json(get_json("/analytics/daily"))
        complaint_rate = (
            summary["complaints"] / summary["created_tickets"]
            if summary["created_tickets"]
            else 0
        )
        st.metric("Complaint rate", f"{complaint_rate * 100:.1f}%")

with tab_tickets:
    st.subheader("Open Tickets")
    dataframe(tickets, "open-tickets")

with tab_sla:
    st.subheader("SLA Breaches")
    dataframe(breaches.get("breaches", []), "sla-breaches")

with tab_escalations:
    st.subheader("Recent Escalations")
    dataframe(escalations, "recent-escalations")

with tab_ai:
    st.subheader("AI Metrics")
    cols = st.columns(6)
    cols[0].metric("AI interactions", ai_metrics["total_ai_interactions"])
    cols[1].metric("Auto-resolution", f"{ai_metrics['auto_resolution_rate'] * 100:.1f}%")
    cols[2].metric("Human review", f"{ai_metrics['human_review_rate'] * 100:.1f}%")
    cols[3].metric("Low confidence", ai_metrics["low_confidence_fallback_count"])
    cols[4].metric("Unsafe prevented", ai_metrics["unsafe_answer_prevention_count"])
    cols[5].metric("Avg latency ms", ai_metrics["average_ai_latency_ms"])
    st.subheader("Retrieval Confidence Distribution")
    st.bar_chart(pd.DataFrame([ai_metrics["retrieval_confidence_distribution"]]).T)
    st.subheader("Top Intents")
    dataframe(ai_metrics.get("top_intents", []), "ai-top-intents")

with tab_detail:
    st.subheader("Conversation / Ticket Detail")
    ticket_id = st.number_input("Ticket ID", min_value=1, step=1)
    if st.button("Load ticket"):
        try:
            ticket = get_json(f"/tickets/{int(ticket_id)}/detail")
            st.json(ticket)
        except Exception as exc:
            st.error(f"Could not load ticket: {exc}")

st.caption("Internal MVP dashboard. Data is served through the FastAPI backend, not direct database access.")
