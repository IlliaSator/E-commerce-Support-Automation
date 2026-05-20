# Security

No real secrets are stored in this repository.

- `.env` is ignored by git.
- `.env.example` contains placeholders only.
- Telegram tokens, OpenAI keys, Google credentials, Supabase service keys, n8n passwords, service account JSON, and real chat IDs must be added manually outside git.
- n8n workflows use placeholder credential names only.
- The n8n AI Agent canvas uses `TechGear OpenAI Placeholder`; do not connect a real model credential in exported workflow JSON.
- The n8n PostgreSQL nodes use `TechGear PostgreSQL Placeholder`; exported workflows must never include real database passwords.
- Google Sheets and Supabase workflow nodes read IDs/URLs/keys from environment variables or n8n credentials; workflow exports must not contain real tokens.
- Supabase is an optional CRM mirror, not the local source of truth. Use server-side credentials only in n8n or backend environments, never in browser-facing code.
- Admin endpoints use `X-Admin-API-Key`, which is MVP-level local protection.

Production requirements:

- real authentication and authorization
- signed webhooks
- secret manager
- audit logs
- rate limiting and anti-spam
- TLS everywhere
- database migrations
- stricter network isolation
- monitoring and incident alerting
