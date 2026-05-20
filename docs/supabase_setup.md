# Supabase Optional CRM Mirror

Supabase is optional in this MVP. The local PostgreSQL database remains the source of truth for orders, tickets, AI interactions, feedback, and SLA data. Supabase is used only as an external CRM/analytics mirror through n8n HTTP Request nodes.

## Environment

Add these values locally in `.env` or in the n8n environment. Do not commit real values.

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

The n8n workflow uses Supabase REST endpoints such as:

```text
${SUPABASE_URL}/rest/v1/support_events
```

## Tables

Run this SQL in a Supabase SQL editor for a demo project.

```sql
create table if not exists public.support_events (
  id bigserial primary key,
  event_type text not null,
  ticket_id bigint,
  intent text,
  priority text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.support_tickets (
  id bigserial primary key,
  ticket_id bigint unique,
  status text,
  priority text,
  intent text,
  subject text,
  message_text text,
  escalated boolean default false,
  payload jsonb not null default '{}'::jsonb,
  synced_at timestamptz not null default now()
);

create table if not exists public.ai_interactions (
  id bigserial primary key,
  support_message_id bigint,
  detected_intent text,
  intent_confidence numeric,
  retrieval_confidence numeric,
  auto_resolved boolean,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.daily_metrics (
  id bigserial primary key,
  report_date date not null,
  period text not null default 'daily',
  total_messages integer,
  auto_resolved_messages integer,
  created_tickets integer,
  open_tickets integer,
  complaints integer,
  sla_breaches integer,
  ai_auto_resolution_rate numeric,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.feedback_events (
  id bigserial primary key,
  ticket_id bigint,
  rating integer,
  comment text,
  event_type text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

## Security

Supabase Data API access has two layers: Postgres grants determine whether an API role can reach a table, and RLS policies determine which rows are visible or writable. New Supabase projects may require explicit grants before tables are reachable through the Data API.

For this MVP mirror, use server-side n8n credentials and avoid public client access:

```sql
alter table public.support_events enable row level security;
alter table public.support_tickets enable row level security;
alter table public.ai_interactions enable row level security;
alter table public.daily_metrics enable row level security;
alter table public.feedback_events enable row level security;

revoke all on public.support_events from anon, authenticated;
revoke all on public.support_tickets from anon, authenticated;
revoke all on public.ai_interactions from anon, authenticated;
revoke all on public.daily_metrics from anon, authenticated;
revoke all on public.feedback_events from anon, authenticated;

grant select, insert, update on public.support_events to service_role;
grant select, insert, update on public.support_tickets to service_role;
grant select, insert, update on public.ai_interactions to service_role;
grant select, insert, update on public.daily_metrics to service_role;
grant select, insert, update on public.feedback_events to service_role;
```

References:

- Supabase Data REST API: https://supabase.com/docs/guides/api
- Securing your API: https://supabase.com/docs/guides/api/securing-your-api
- May 2026 Data API change: https://supabase.com/changelog/45702-developer-update-may-2026
