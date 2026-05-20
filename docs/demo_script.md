# Demo Script

1. Start services:

   ```bash
   cp .env.example .env
   docker compose up --build
   ```

2. Seed data:

   ```bash
   make seed
   ```

3. Import n8n workflows from `n8n/workflows/`.

4. Optional: set `TELEGRAM_BOT_TOKEN` and `MANAGER_CHAT_IDS` in `.env`, then restart the bot service.

5. Run scripted demo without Telegram:

   ```bash
   make demo
   ```

6. Open dashboard at http://localhost:8501.

7. Run AI evaluation:

   ```bash
   make evaluate
   ```
