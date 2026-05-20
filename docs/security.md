# Security

No real secrets are stored in this repository.

- `.env` is ignored by git.
- `.env.example` contains placeholders only.
- Telegram tokens, OpenAI keys, Google credentials, n8n passwords, service account JSON, and real chat IDs must be added manually outside git.
- n8n workflows use placeholder credential names only.
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
