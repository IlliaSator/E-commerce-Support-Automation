from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from backend.app.core.config import get_settings

SLA_POLICIES = {
    "urgent": {"minutes": 15, "business": False},
    "high": {"minutes": 120, "business": False},
    "normal": {"minutes": 8 * 60, "business": True},
    "low": {"minutes": 24 * 60, "business": False},
}


def _is_business_time(local_dt: datetime) -> bool:
    return local_dt.weekday() < 5 and time(9, 0) <= local_dt.time() < time(18, 0)


def _next_business_start(local_dt: datetime) -> datetime:
    candidate = local_dt
    if candidate.time() >= time(18, 0):
        candidate = datetime.combine(candidate.date() + timedelta(days=1), time(9, 0), candidate.tzinfo)
    elif candidate.time() < time(9, 0):
        candidate = datetime.combine(candidate.date(), time(9, 0), candidate.tzinfo)
    while candidate.weekday() >= 5:
        candidate = datetime.combine(candidate.date() + timedelta(days=1), time(9, 0), candidate.tzinfo)
    return candidate


def calculate_sla_due(priority: str, created_at: datetime | None = None) -> datetime:
    settings = get_settings()
    policy = SLA_POLICIES.get(priority, SLA_POLICIES["normal"])
    created = created_at or datetime.now(UTC)
    if not policy["business"]:
        return created + timedelta(minutes=policy["minutes"])

    tz = ZoneInfo(settings.app_timezone)
    local_cursor = created.astimezone(tz)
    remaining = int(policy["minutes"])
    cursor = _next_business_start(local_cursor)

    while remaining > 0:
        if not _is_business_time(cursor):
            cursor = _next_business_start(cursor)
        end_of_day = datetime.combine(cursor.date(), time(18, 0), tz)
        available = int((end_of_day - cursor).total_seconds() // 60)
        if remaining <= available:
            return (cursor + timedelta(minutes=remaining)).astimezone(UTC)
        remaining -= available
        cursor = _next_business_start(end_of_day + timedelta(minutes=1))

    return cursor.astimezone(UTC)
