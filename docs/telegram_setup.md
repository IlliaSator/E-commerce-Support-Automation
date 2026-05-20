# Telegram Setup

1. Create a Telegram bot manually with BotFather.
2. Add the token to `.env` as `TELEGRAM_BOT_TOKEN`.
3. Add manager chat IDs to `MANAGER_CHAT_IDS`, comma-separated.
4. Restart the bot container.

Customer commands:

- `/start`
- `/help`
- `/order <order_id>`
- `/ticket <ticket_id>`
- `/faq`

Admin commands:

- `/open_tickets`
- `/ticket <ticket_id>`
- `/resolve <ticket_id>`
- `/sla`
- `/report`

If `TELEGRAM_BOT_TOKEN` is empty, the bot starts in mock/sleep mode so Docker Compose can still run locally.
