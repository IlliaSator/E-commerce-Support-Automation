# n8n Setup

Local n8n runs at http://localhost:5678.

Import each JSON file from `n8n/workflows/` manually in the n8n UI. The `techgear_unified_mvp_workflow.json` file is a connected n8n canvas for portfolio review and end-to-end walkthrough; the other workflow files keep the individual production-style automations easy to inspect.

Credential placeholders:

- `TechGear Telegram Bot Placeholder`
- `TechGear Google Sheets Placeholder`

Replace placeholders with real credentials in n8n UI. Do not commit exported workflows containing real credentials.

Docker network URLs:

- Backend from n8n: `http://backend:8000`
- Escalation webhook: `http://n8n:5678/webhook/support-escalation`
- Logging webhook: `http://n8n:5678/webhook/support-logging`
- Feedback webhook: `http://n8n:5678/webhook/feedback-followup`
- Negative feedback webhook: `http://n8n:5678/webhook/negative-feedback`

n8n Cloud can use the same workflows after changing backend URLs to a public HTTPS endpoint.
