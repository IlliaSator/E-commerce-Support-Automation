# n8n Setup

Local n8n runs at http://localhost:5678.

Import each JSON file from `n8n/workflows/` manually in the n8n UI. The `techgear_automation_canvas_v2_workflow.json` file is the main connected n8n canvas for portfolio review and end-to-end walkthrough. It shows intake, AI decision routing, ticket ops, SLA, manager review, Google Sheets, Supabase, feedback, and error handling in one editor view. The smaller workflow files keep individual production-style automations easy to inspect.

Credential placeholders:

- `TechGear Telegram Bot Placeholder`
- `TechGear Google Sheets Placeholder`
- `TechGear Supabase Placeholder`

Replace placeholders with real credentials in n8n UI. Do not commit exported workflows containing real credentials.

Docker network URLs:

- Backend from n8n: `http://backend:8000`
- Escalation webhook: `http://n8n:5678/webhook/support-escalation`
- Logging webhook: `http://n8n:5678/webhook/support-logging`
- Feedback webhook: `http://n8n:5678/webhook/feedback-followup`
- Negative feedback webhook: `http://n8n:5678/webhook/negative-feedback`
- Event hub webhook: `http://n8n:5678/webhook/support-event-hub`
- Supabase CRM sync webhook: `http://n8n:5678/webhook/supabase-crm-sync`

Optional environment values:

- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Google Sheets and Supabase are optional sinks. If they are not configured, the local backend and mock/demo flows still work.

n8n Cloud can use the same workflows after changing backend URLs to a public HTTPS endpoint.
