# Architecture

TechGear Store support automation uses a hub-and-spoke design centered on the FastAPI backend.

```mermaid
flowchart TD
    Telegram["Telegram Bot"] --> Backend["FastAPI Backend"]
    Backend --> Postgres["PostgreSQL"]
    Backend --> AI["AI Layer"]
    AI --> Rules["Rules + Urgency"]
    AI --> RAG["Local TF-IDF RAG"]
    AI --> LLM["Optional OpenAI Drafting"]
    Backend --> N8N["n8n Webhooks"]
    N8N --> Alerts["Manager Alerts and Reports"]
    N8N --> Sheets["Google Sheets Logs"]
    N8N --> Supabase["Optional Supabase CRM Mirror"]
    Backend --> Dashboard["Streamlit Dashboard"]
```

The backend owns all business decisions. The bot and dashboard are interface layers. n8n is used for operational workflows: alerts, scheduled reports, SLA checks, feedback requests, Google Sheets logging, optional Supabase CRM mirroring, and error handling.

Data is stored in PostgreSQL in Docker. Local development can use SQLite through `DATABASE_URL` when running scripts/tests outside Docker.
