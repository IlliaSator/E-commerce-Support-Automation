# n8n Workflows

Import the workflow JSON files from `n8n/workflows/` into local n8n or n8n Cloud.

`techgear_automation_canvas_v2_workflow.json` is the main connected n8n canvas for demo and portfolio screenshots. It shows backend webhooks, AI decision routing, a real n8n AI Agent cluster with chat model, memory, HTTP tools, and Code Tool, ticket ops, SLA checks, reports, feedback, Telegram alerts, Google Sheets logging, Supabase CRM mirroring, error handling, and mock audit logging in one editor view. The separate workflow files remain available for focused business automations.

The workflows intentionally use placeholder credential names:

- `TechGear Telegram Bot Placeholder`
- `TechGear Google Sheets Placeholder`
- `TechGear Supabase Placeholder`
- `TechGear OpenAI Placeholder`
- `TechGear PostgreSQL Placeholder`

Replace them manually in the n8n UI after import. No real tokens or service account files are stored in this repository.

Local Docker URLs:

- Backend from n8n: `http://backend:8000`
- n8n UI: `http://localhost:5678`
- Webhook examples:
  - `http://n8n:5678/webhook/support-escalation`
  - `http://n8n:5678/webhook/support-logging`
  - `http://n8n:5678/webhook/feedback-followup`
  - `http://n8n:5678/webhook/support-event-hub`
  - `http://n8n:5678/webhook/supabase-crm-sync`

If a webhook URL is missing or n8n is unavailable, the backend logs the event locally and continues.
