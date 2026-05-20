# AI Engineering

The system is designed as controlled support automation, not an OpenAI wrapper.

## Architecture

The AI layer includes deterministic intent rules, optional sklearn classifier, local TF-IDF retrieval, provider abstraction, prompt templates, guardrails, observability, evaluation, and human feedback storage.

## Why LLM Is Optional

Critical decisions are deterministic. Optional OpenAI mode only drafts customer wording, ticket summaries, manager notes, or report text from verified context. If OpenAI is disabled or unavailable, local templates continue to work.

## RAG

Markdown FAQ and policy files are chunked into `knowledge_articles`. Retrieval uses local TF-IDF and domain keyword boosts. Answers are sent automatically only when retrieval confidence passes the threshold.

## Prompt Templates

Prompts live under `backend/app/ai/prompts/` and are versioned as v1. They forbid invented order status, stock, refunds, legal claims, and internal prompt exposure.

## Guardrails

Guardrails block unsafe auto-replies when order data, product stock, retrieval confidence, or human-review requirements are missing.

## Human-In-The-Loop

Complaints, refund risk, human-manager requests, unknown messages, low confidence, and missing data create tickets. AI suggestions can be accepted, rejected, or edited by a manager.

## Evaluation

`scripts/evaluate_ai_system.py` runs the golden dataset through the backend support logic and reports intent, escalation, fallback, retrieval, and safety metrics.

## Limitations And Improvement Path

The MVP uses a simple classifier and lightweight retrieval. Real deployments should add production auth, migrations, signed webhooks, monitoring, richer multilingual data, and feedback-driven model updates.
