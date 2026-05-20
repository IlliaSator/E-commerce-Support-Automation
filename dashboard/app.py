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


st.set_page_config(page_title="TechGear Support Ops", layout="wide")
st.title("TechGear Support Ops")

try:
    summary = get_json("/analytics/summary")
    ai_metrics = get_json("/ai/metrics")
    tickets = get_json("/tickets/open")
    breaches = get_json("/analytics/sla-breaches")
    intents = get_json("/analytics/intent-distribution")
except Exception as exc:
    st.error(f"Backend unavailable: {exc}")
    st.stop()

metric_row(summary)

tab_overview, tab_tickets, tab_sla, tab_ai, tab_detail = st.tabs(
    ["Overview", "Open Tickets", "SLA Breaches", "AI Metrics", "Ticket Detail"]
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

with tab_tickets:
    st.subheader("Open Tickets")
    dataframe(tickets, "open-tickets")

with tab_sla:
    st.subheader("SLA Breaches")
    dataframe(breaches.get("breaches", []), "sla-breaches")

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
            ticket = get_json(f"/tickets/{int(ticket_id)}")
            st.json(ticket)
        except Exception as exc:
            st.error(f"Could not load ticket: {exc}")

st.caption("Internal MVP dashboard. Data is served through the FastAPI backend, not direct database access.")
