# API

Interactive API docs are available at `http://localhost:8000/docs`.

Important endpoints:

- `GET /health`
- `POST /support/message`
- `GET /orders/{order_id}`
- `GET /products/search?q=`
- `POST /knowledge/answer`
- `GET /tickets`
- `GET /tickets/open`
- `GET /tickets/sla-breaches`
- `POST /tickets`
- `PATCH /tickets/{ticket_id}`
- `POST /tickets/{ticket_id}/resolve`
- `GET /analytics/summary`
- `GET /analytics/daily`
- `GET /analytics/weekly`
- `GET /analytics/intent-distribution`
- `GET /analytics/sla-breaches`
- `GET /analytics/ai-metrics`
- `POST /ai/evaluate-message`
- `POST /ai/draft-reply`
- `POST /ai/summarize-ticket`

Admin endpoints require `X-Admin-API-Key`.
