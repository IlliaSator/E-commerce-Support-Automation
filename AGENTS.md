# Agent Instructions

This repository is a production-style Applied AI MVP for a fictional TechGear Store support team.

- Never commit real secrets, `.env`, Telegram tokens, OpenAI keys, Google credentials, n8n passwords, service account JSON, or real chat IDs.
- Keep OpenAI optional. Local/mock mode must remain the default.
- Backend owns support business logic. The Telegram bot and dashboard call backend APIs.
- Deterministic rules and retrieval grounding control customer-facing decisions.
- If unsure about order status, product stock, refunds, or policy, create a ticket instead of guessing.
- Prefer small, focused modules and tests that cover business behavior.
- Run tests, lint, Docker Compose config validation, n8n JSON validation, and a secret scan before final handoff.
