# E-commerce Support Automation

Applied AI support automation MVP for a fictional electronics shop, **TechGear Store**.

This project is my take on a realistic internal support automation system for a small e-commerce team. It is not meant to pretend to be an enterprise SaaS. It is a production-style MVP: Dockerized, testable, observable enough for a portfolio demo, and designed around the kind of support work a small store actually has every day.

Russian version is available below the English README.

## What Problem It Solves

Small stores spend a lot of time answering the same Telegram messages:

- Where is my order?
- How long does delivery take?
- Can I return this?
- Is this product in stock?
- I received a damaged item.
- I want a human manager.

The risky part is not only response speed. It is also making sure the bot does **not** invent a tracking number, promise a refund, guess stock, or ignore an angry customer. This MVP is built around that principle: when the system is uncertain, it creates a ticket instead of guessing.

## What The MVP Does

- Receives customer messages through a Telegram bot.
- Sends all natural-language messages to a FastAPI backend.
- Classifies intent with deterministic rules plus an optional sklearn baseline.
- Uses local RAG over English/Russian FAQ and policy documents.
- Looks up order status in PostgreSQL.
- Searches a seeded product catalog for stock and alternatives.
- Creates support tickets for risky, unknown, or low-confidence cases.
- Escalates complaints and human-agent requests to a manager workflow.
- Tracks SLA deadlines and exposes SLA breach data.
- Emits events to n8n for escalation, reporting, logging, feedback, and CRM-style sync.
- Shows business and AI metrics in a Streamlit dashboard.
- Works locally without Telegram, OpenAI, Google, or Supabase credentials.
- Supports optional OpenAI drafting, but does not require it.

## Architecture

```mermaid
flowchart LR
    Customer["Customer Telegram"] --> Bot["Telegram Bot"]
    Bot --> API["FastAPI Backend"]
    API --> DB["PostgreSQL"]
    API --> AI["Rules + TF-IDF RAG + Optional LLM Drafting"]
    API --> N8N["n8n Workflows"]
    N8N --> Manager["Manager Telegram Alerts"]
    N8N --> Sheets["Optional Google Sheets Logs"]
    N8N --> Supabase["Optional Supabase CRM Mirror"]
    API --> Dashboard["Streamlit Dashboard"]
```

The backend is the source of truth. The bot, dashboard, and n8n workflows call backend APIs instead of duplicating business logic.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2, Pydantic Settings
- **Database:** PostgreSQL
- **Bot:** aiogram, long polling for local development
- **AI/ML:** deterministic rules, sklearn TF-IDF/LogisticRegression baseline, local TF-IDF RAG, optional OpenAI provider
- **Automation:** self-hosted n8n
- **Dashboard:** Streamlit
- **Testing:** pytest, ruff, synthetic MVP audit
- **Runtime:** Docker Compose

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Local URLs:

- Backend docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501
- n8n: http://localhost:5678

Seed the database:

```bash
docker compose exec backend python scripts/seed_db.py
```

Run a no-Telegram demo:

```bash
docker compose exec backend python scripts/demo_conversation.py
```

Run the synthetic MVP audit:

```bash
python scripts/synthetic_mvp_audit.py
```

If you have `make` installed, the same common commands are also available as `make seed`, `make demo`, `make test`, `make lint`, `make evaluate`, and `make synthetic`.

## Environment Variables

Copy `.env.example` to `.env`. The default values are local placeholders.

The project intentionally runs without real external credentials:

- no Telegram token required for backend/dashboard/demo;
- no OpenAI key required;
- no Google credentials required;
- no Supabase credentials required;
- no real n8n credentials committed.

The Telegram bot enters mock/sleep mode when `TELEGRAM_BOT_TOKEN` is empty.

## Telegram Bot

The bot is only an interface layer. It handles `/start`, `/help`, `/order`, `/ticket`, `/faq`, and admin commands, but it does not decide business outcomes. Customer messages are forwarded to `/support/message`, and the backend returns the intent, confidence, reply, ticket status, escalation status, retrieved sources, and guardrail result.

Admin commands are protected by `MANAGER_CHAT_IDS`.

## n8n Automation

Import workflows from `n8n/workflows/`.

For portfolio review, import:

```text
techgear_automation_canvas_v2_workflow.json
```

That is the large connected MVP canvas. It includes:

- support intake webhooks;
- central event routing;
- AI Agent with chat model placeholder, Postgres Chat Memory, structured output parser, backend HTTP tools, Code Tool, Think Tool, and Calculator Tool;
- escalation branches;
- manager-review branches;
- SLA monitor;
- daily and weekly reports;
- feedback handling;
- Google Sheets logging branch;
- optional Supabase CRM mirror;
- PostgreSQL audit snapshots;
- error handler and dead-letter path.

External n8n credentials are placeholders. Replace them in the n8n UI only when you want to connect real Telegram, Google Sheets, Supabase, PostgreSQL memory, or an optional LLM.

## Configured n8n MVP Canvas

This screenshot shows the main connected n8n editor canvas. The AI agent tools are separated into readable lanes, and the rest of the workflow shows the business automation around it.

![TechGear Store n8n automation canvas with AI Agent, Postgres memory, and tools](docs/assets/techgear-n8n-agent-toolbox-canvas.png)

## Demo Scenarios

Good messages to try:

- `Where is my order 10042?`
- `Где мой заказ 10042?`
- `Has my order been shipped?`
- `Where is my order 99999?`
- `How long does delivery take?`
- `Сколько идет доставка?`
- `Do you have iPhone 15 case?`
- `I need a refund`
- `My order arrived broken`
- `Позовите оператора`
- `asdfghjkl`

Expected behavior:

- known order IDs are answered from the database;
- missing order IDs trigger a clarification request;
- unknown orders create tickets;
- FAQ answers come from local retrieval;
- product stock comes from the catalog;
- complaints and human-manager requests escalate;
- refund requests do not receive automatic refund promises;
- unknown/low-confidence messages fall back to human review.

## API Docs

Run the backend and open `/docs`.

Main endpoints:

- `POST /support/message`
- `GET /orders/{order_id}`
- `GET /products/search?q=`
- `POST /knowledge/answer`
- `GET /tickets`
- `GET /tickets/open`
- `GET /tickets/sla-breaches`
- `POST /tickets/{ticket_id}/resolve`
- `GET /analytics/*`
- `POST /ai/evaluate-message`
- `POST /ai/draft-reply`
- `GET /ai/metrics`

Admin endpoints use `X-Admin-API-Key`. This is MVP-level protection, not full production auth.

## AI Engineering Approach

This project is deliberately not an OpenAI wrapper.

The AI design is layered:

1. Deterministic rules catch high-precision cases like order status, complaints, refunds, human-agent requests, spam, urgent words, and order IDs.
2. Local retrieval finds grounded FAQ/policy answers from markdown knowledge files stored in the database.
3. Confidence thresholds decide whether the system may answer or must create a ticket.
4. Guardrails block risky responses.
5. Optional LLM drafting can make wording nicer, but only from verified context.
6. Human-in-the-loop handles complaints, refund risk, unknown intent, low confidence, and customer requests for a manager.

The key rule is simple: uncertainty becomes a ticket, not a hallucinated answer.

## ML And Classification

The default runtime uses deterministic rules because they are easier to trust for business-critical routing. A lightweight sklearn TF-IDF + LogisticRegression classifier is included for experimentation:

```bash
python scripts/train_intent_classifier.py
python scripts/evaluate_classifier.py
```

The sample dataset is intentionally imperfect and imbalanced, like early real support data often is. The point is to show the pipeline and limitations honestly, not to claim a perfect classifier.

## RAG And Knowledge Retrieval

The knowledge base is built from local English and Russian markdown files:

- FAQ
- delivery policy
- returns/refunds policy
- warranty policy
- damaged item instructions
- human support policy

Documents are chunked into `knowledge_articles`. Retrieval uses local TF-IDF-style scoring plus domain keyword boosts. If retrieval confidence is too low, the backend creates a ticket instead of answering confidently.

## Guardrails And Human Review

The assistant must not:

- invent order status;
- invent tracking numbers;
- invent product stock;
- promise refunds;
- make legal claims;
- expose internal prompts or notes;
- answer outside store policy;
- ignore a request for a human manager.

High-risk cases produce tickets and manager review.

## Evaluation And Synthetic Audit

Run:

```bash
pytest backend/tests bot/tests -q
ruff check backend bot dashboard scripts
python scripts/evaluate_classifier.py
docker compose exec backend python scripts/evaluate_ai_system.py
python scripts/synthetic_mvp_audit.py
```

The synthetic audit calls the running backend and checks:

- order status flow;
- missing and nonexistent order handling;
- FAQ retrieval;
- product availability;
- complaint escalation;
- refund safety;
- human-manager request;
- unknown fallback;
- backend endpoints used by n8n AI tools;
- n8n AI Agent wiring;
- Postgres memory/audit nodes;
- approximate layout overlap in the AI tool area.

## Dashboard

The Streamlit dashboard shows:

- total messages;
- auto-resolved messages;
- created/open tickets;
- complaints;
- SLA breaches;
- intent distribution;
- open ticket table;
- recent escalations;
- AI metrics;
- human-review and auto-resolution rates.

It calls the backend API rather than reading the database directly.

## Security Notes

No real secrets are committed. `.env` is ignored.

The repository includes only placeholder credential names for Telegram, OpenAI, Google Sheets, Supabase, PostgreSQL memory, and n8n. Real credentials should be added manually by the project owner in local `.env` files or the n8n UI.

For real production use, this would need stronger auth, signed webhooks, secret management, rate limiting, audit log hardening, network restrictions, backups, and monitoring.

## Limitations

This is a deployable internal MVP foundation, not a fully production-ready SaaS.

Current limitations:

- SQLAlchemy `create_all` instead of Alembic migrations;
- MVP admin key instead of proper RBAC/OAuth;
- local TF-IDF retrieval instead of a production vector search stack;
- optional LLM and external integrations are placeholders by default;
- classifier quality is baseline-level and should improve with real feedback data;
- n8n AI Agent is configured for orchestration/demo and should not replace backend policy decisions.

## Roadmap

- Add Alembic migrations.
- Add production auth/RBAC.
- Add signed webhook verification.
- Add richer manager UI.
- Add queue-based retries for event delivery.
- Improve multilingual classifier evaluation.
- Add production tracing and dashboards.
- Use stored human feedback for model and prompt iteration.

## Commercial Use Case

Target users are small e-commerce teams that spend too much time on repetitive support and do not want angry or urgent cases to disappear in a chat queue.

The MVP can automate safe answers, speed up order/product checks, escalate complaints, track SLA, and produce manager reports while keeping humans in control of risky decisions.

## Folder Structure

```text
backend/     FastAPI, database, AI layer, services, tests
bot/         Telegram bot interface
dashboard/   Streamlit operations dashboard
n8n/         Importable automation workflows
data/        Seed, evaluation, and training data
scripts/     Seed, train, evaluate, demo, synthetic audit scripts
docs/        Architecture, AI, setup, security, roadmap
```

---

# E-commerce Support Automation - русская версия

Applied AI MVP для автоматизации поддержки вымышленного интернет-магазина электроники **TechGear Store**.

Это не демонстрационный "чатбот с OpenAI", а приближенный к реальному внутренний MVP для небольшой e-commerce команды. Проект можно поднять локально через Docker Compose, прогнать на синтетических данных, открыть dashboard, импортировать n8n workflow и показать end-to-end процесс поддержки.

## Какую проблему решает проект

Небольшие магазины часто вручную отвечают на одни и те же вопросы в Telegram:

- где мой заказ;
- сколько идет доставка;
- можно ли вернуть товар;
- есть ли товар в наличии;
- что делать, если товар пришел поврежденным;
- как связаться с менеджером.

Опасность в таких системах не только в скорости ответа. Главное - не позволить автоматизации выдумать трек-номер, наличие товара, дату доставки или пообещать возврат денег без проверки. Поэтому главный принцип проекта: если система не уверена, она создает тикет, а не фантазирует.

## Что умеет MVP

- Принимает сообщения клиентов через Telegram bot.
- Передает всю бизнес-логику в FastAPI backend.
- Классифицирует intent через deterministic rules и optional sklearn baseline.
- Использует локальный RAG по FAQ и policy документам на английском и русском.
- Проверяет статус заказа в PostgreSQL.
- Ищет товары, цены, stock и alternatives в product catalog.
- Создает support tickets для сложных, рискованных и low-confidence случаев.
- Эскалирует жалобы и запросы на живого менеджера.
- Отслеживает SLA deadlines и SLA breaches.
- Отправляет события в n8n для эскалаций, отчетов, логирования, feedback и CRM-style sync.
- Показывает business и AI metrics в Streamlit dashboard.
- Работает локально без Telegram, OpenAI, Google и Supabase credentials.
- Поддерживает optional OpenAI drafting, но не зависит от него.

## Архитектура

```mermaid
flowchart LR
    Customer["Customer Telegram"] --> Bot["Telegram Bot"]
    Bot --> API["FastAPI Backend"]
    API --> DB["PostgreSQL"]
    API --> AI["Rules + TF-IDF RAG + Optional LLM Drafting"]
    API --> N8N["n8n Workflows"]
    N8N --> Manager["Manager Telegram Alerts"]
    N8N --> Sheets["Optional Google Sheets Logs"]
    N8N --> Supabase["Optional Supabase CRM Mirror"]
    API --> Dashboard["Streamlit Dashboard"]
```

Backend является источником истины. Telegram bot, dashboard и n8n workflows вызывают backend API и не дублируют бизнес-логику.

## Стек

- **Backend:** FastAPI, SQLAlchemy 2, Pydantic Settings
- **Database:** PostgreSQL
- **Bot:** aiogram, long polling для локальной разработки
- **AI/ML:** deterministic rules, sklearn TF-IDF/LogisticRegression baseline, local TF-IDF RAG, optional OpenAI provider
- **Automation:** self-hosted n8n
- **Dashboard:** Streamlit
- **Testing:** pytest, ruff, synthetic MVP audit
- **Runtime:** Docker Compose

## Быстрый запуск

```bash
cp .env.example .env
docker compose up --build
```

Локальные URL:

- Backend docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501
- n8n: http://localhost:5678

Заполнить базу синтетическими данными:

```bash
docker compose exec backend python scripts/seed_db.py
```

Запустить demo без Telegram:

```bash
docker compose exec backend python scripts/demo_conversation.py
```

Запустить синтетический аудит MVP:

```bash
python scripts/synthetic_mvp_audit.py
```

Если установлен `make`, можно использовать команды `make seed`, `make demo`, `make test`, `make lint`, `make evaluate` и `make synthetic`.

## Переменные окружения

Скопируйте `.env.example` в `.env`. Значения по умолчанию - локальные placeholders.

Проект намеренно работает без реальных внешних ключей:

- Telegram token не нужен для backend/dashboard/demo;
- OpenAI key не обязателен;
- Google credentials не обязательны;
- Supabase credentials не обязательны;
- реальные n8n credentials не коммитятся.

Если `TELEGRAM_BOT_TOKEN` пустой, bot запускается в mock/sleep mode.

## Telegram bot

Bot - это interface layer. Он обрабатывает `/start`, `/help`, `/order`, `/ticket`, `/faq` и admin commands, но не принимает бизнес-решения. Все customer messages уходят в `/support/message`, а backend возвращает intent, confidence, reply, ticket state, escalation flag, retrieved sources и guardrail result.

Admin commands защищены через `MANAGER_CHAT_IDS`.

## n8n automation

Workflow JSON лежат в `n8n/workflows/`.

Главный canvas для portfolio review:

```text
techgear_automation_canvas_v2_workflow.json
```

Он показывает:

- support intake webhooks;
- central event router;
- AI Agent с chat model placeholder, Postgres Chat Memory, structured output parser, backend HTTP tools, Code Tool, Think Tool и Calculator Tool;
- escalation branches;
- manager-review branches;
- SLA monitor;
- daily и weekly reports;
- feedback handling;
- Google Sheets logging branch;
- optional Supabase CRM mirror;
- PostgreSQL audit snapshots;
- error handler и dead-letter path.

Все внешние credentials в n8n являются placeholders. Реальные Telegram, Google Sheets, Supabase, PostgreSQL memory или optional LLM credentials добавляются вручную в n8n UI.

## Скриншот n8n canvas

На скриншоте показан единый connected n8n workflow. AI tools разнесены по читаемым зонам, а вокруг них показан основной бизнес-процесс автоматизации поддержки.

![TechGear Store n8n automation canvas with AI Agent, Postgres memory, and tools](docs/assets/techgear-n8n-agent-toolbox-canvas.png)

## Demo scenarios

Примеры сообщений:

- `Where is my order 10042?`
- `Где мой заказ 10042?`
- `Has my order been shipped?`
- `Where is my order 99999?`
- `How long does delivery take?`
- `Сколько идет доставка?`
- `Do you have iPhone 15 case?`
- `I need a refund`
- `My order arrived broken`
- `Позовите оператора`
- `asdfghjkl`

Ожидаемое поведение:

- известный order ID обрабатывается через базу данных;
- если order ID не указан, система просит прислать номер заказа;
- неизвестный заказ создает тикет;
- FAQ ответы берутся из local retrieval;
- наличие товара берется из product catalog;
- жалобы и запросы менеджера эскалируются;
- refund не обещается автоматически;
- unknown/low-confidence сообщения уходят на human review.

## API

Основные endpoints:

- `POST /support/message`
- `GET /orders/{order_id}`
- `GET /products/search?q=`
- `POST /knowledge/answer`
- `GET /tickets`
- `GET /tickets/open`
- `GET /tickets/sla-breaches`
- `POST /tickets/{ticket_id}/resolve`
- `GET /analytics/*`
- `POST /ai/evaluate-message`
- `POST /ai/draft-reply`
- `GET /ai/metrics`

Admin endpoints используют `X-Admin-API-Key`. Это MVP-level защита, не полноценная production auth.

## AI Engineering подход

Проект специально сделан не как OpenAI wrapper.

AI logic построена слоями:

1. Deterministic rules ловят важные случаи: order status, complaints, refunds, human-agent requests, spam, urgent words и order IDs.
2. Local retrieval ищет grounded FAQ/policy answers в markdown knowledge base.
3. Confidence thresholds решают, можно ли отвечать автоматически.
4. Guardrails блокируют рискованные ответы.
5. Optional LLM drafting улучшает формулировку, но только на основе verified context.
6. Human-in-the-loop обрабатывает complaints, refund risk, unknown intent, low confidence и запросы живого менеджера.

Ключевая идея: неопределенность превращается в тикет, а не в галлюцинацию для клиента.

## ML и classification

Default runtime использует deterministic rules, потому что они надежнее для бизнес-критичных сценариев. Также есть lightweight sklearn TF-IDF + LogisticRegression baseline:

```bash
python scripts/train_intent_classifier.py
python scripts/evaluate_classifier.py
```

Dataset намеренно не выглядит идеально: он синтетический, bilingual и imbalanced, как ранние support данные в реальном MVP.

## RAG и knowledge retrieval

Knowledge base строится из локальных English/Russian markdown файлов:

- FAQ;
- delivery policy;
- returns/refunds policy;
- warranty policy;
- damaged item instructions;
- human support policy.

Документы chunked в `knowledge_articles`. Retrieval использует local TF-IDF-style scoring и keyword boosts. Если confidence низкий, backend создает тикет вместо уверенного ответа.

## Guardrails и human review

Assistant не должен:

- выдумывать order status;
- выдумывать tracking numbers;
- выдумывать product stock;
- обещать refunds;
- делать legal claims;
- раскрывать internal prompts или notes;
- отвечать вне store policy;
- игнорировать запрос живого менеджера.

High-risk cases создают tickets и отправляются на manager review.

## Evaluation и synthetic audit

Команды проверки:

```bash
pytest backend/tests bot/tests -q
ruff check backend bot dashboard scripts
python scripts/evaluate_classifier.py
docker compose exec backend python scripts/evaluate_ai_system.py
python scripts/synthetic_mvp_audit.py
```

Synthetic audit проверяет:

- order status flow;
- missing/nonexistent order handling;
- FAQ retrieval;
- product availability;
- complaint escalation;
- refund safety;
- human-manager request;
- unknown fallback;
- backend endpoints для n8n AI tools;
- n8n AI Agent wiring;
- Postgres memory/audit nodes;
- approximate layout overlap в AI tool area.

## Dashboard

Streamlit dashboard показывает:

- total messages;
- auto-resolved messages;
- created/open tickets;
- complaints;
- SLA breaches;
- intent distribution;
- open ticket table;
- recent escalations;
- AI metrics;
- human-review и auto-resolution rates.

Dashboard вызывает backend API и не читает базу напрямую.

## Security notes

Реальные секреты не коммитятся. `.env` игнорируется.

В репозитории лежат только placeholder credential names для Telegram, OpenAI, Google Sheets, Supabase, PostgreSQL memory и n8n. Реальные credentials добавляются владельцем проекта локально в `.env` или через n8n UI.

Для production нужны stronger auth, signed webhooks, secret management, rate limiting, audit log hardening, network restrictions, backups и monitoring.

## Ограничения

Это deployable internal MVP foundation, а не fully production-ready SaaS.

Текущие ограничения:

- SQLAlchemy `create_all` вместо Alembic migrations;
- MVP admin key вместо RBAC/OAuth;
- local TF-IDF retrieval вместо production vector search stack;
- optional LLM и внешние integrations по умолчанию placeholders;
- classifier baseline требует улучшения на реальных данных;
- n8n AI Agent настроен для orchestration/demo и не должен заменять backend policy decisions.

## Roadmap

- Добавить Alembic migrations.
- Добавить production auth/RBAC.
- Добавить signed webhook verification.
- Улучшить manager UI.
- Добавить queue-based retries для event delivery.
- Улучшить multilingual classifier evaluation.
- Добавить production tracing и dashboards.
- Использовать stored human feedback для model/prompt iteration.

## Commercial use case

Целевая аудитория - небольшие e-commerce команды, которые тратят много времени на повторяющиеся support вопросы и не хотят терять срочные жалобы в чате.

MVP автоматизирует безопасные ответы, ускоряет order/product checks, эскалирует complaints, отслеживает SLA и формирует manager reports, сохраняя human control над рискованными решениями.

## Структура проекта

```text
backend/     FastAPI, database, AI layer, services, tests
bot/         Telegram bot interface
dashboard/   Streamlit operations dashboard
n8n/         Importable automation workflows
data/        Seed, evaluation, and training data
scripts/     Seed, train, evaluate, demo, synthetic audit scripts
docs/        Architecture, AI, setup, security, roadmap
```
